import sqlite3
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def get_db_connection(db_path):
    if not os.path.exists(db_path):
        st.error(f"データベースファイルが存在しません: {db_path}")
        return None
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        st.error(f"データベース接続エラー: {e}")
        return None

def fetch_scores(conn):
    query = '''
        SELECT 
            scores.competition_id AS "競技ID",
            players.name AS "プレイヤー名",
            scores.out_score AS "アウトスコア",
            scores.in_score AS "インスコア",
            scores.total_score AS "合計スコア",
            scores.handicap AS "ハンデキャップ",
            scores.net_score AS "ネットスコア",
            scores.ranking AS "ランキング"
        FROM 
            scores
        JOIN 
            players ON scores.player_id = players.id
        ORDER BY 
            scores.competition_id, scores.ranking;
    '''
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except sqlite3.Error as e:
        st.error(f"クエリ実行エラー: {e}")
        return pd.DataFrame()

def display_scores(df):
    st.subheader("スコア一覧")
    st.dataframe(df)

def display_aggregations(df):
    st.subheader("データ集計")
    
    st.markdown("### 総合ランキング")
    overall_ranking = df.groupby("プレイヤー名")["合計スコア"].sum().sort_values()
    st.bar_chart(overall_ranking)
    
    st.markdown("### 優勝回数ランキング")
    win_counts = df[df["ランキング"] == 1].groupby("プレイヤー名").size().sort_values(ascending=False)
    st.bar_chart(win_counts)
    
    st.markdown("### スコア平均")
    average_scores = df.groupby("プレイヤー名")[["アウトスコア", "インスコア", "合計スコア"]].mean()
    st.dataframe(average_scores)

def display_visualizations(df):
    st.subheader("データ可視化")
    
    st.markdown("### スコア推移")
    plt.figure(figsize=(10,5))
    for player in df["プレイヤー名"].unique():
        player_data = df[df["プレイヤー名"] == player]
        plt.plot(player_data["競技ID"], player_data["合計スコア"], marker='o', label=player)
    plt.xlabel("競技ID")
    plt.ylabel("合計スコア")
    plt.title("プレイヤーごとのスコア推移")
    plt.legend()
    st.pyplot(plt)

def main():
    st.title("ゴルフ競技スコア管理システム")
    
    # データベースへのパス設定
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'golf_competition.db'))
    
    # データベースに接続
    conn = get_db_connection(db_path)
    
    if conn:
        # スコアデータを取得
        df_scores = fetch_scores(conn)
        
        if not df_scores.empty:
            # スコア一覧の表示
            display_scores(df_scores)
            
            # データ集計の表示
            display_aggregations(df_scores)
            
            # データ可視化の表示
            display_visualizations(df_scores)
            
            # データベース接続を閉じる
            conn.close()
        else:
            st.info("スコアデータが存在しません。")
    else:
        st.error("データベースに接続できませんでした。")

if __name__ == "__main__":
    main()