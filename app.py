import sqlite3
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib

# 日本語フォントを設定
plt.rcParams['font.family'] = 'Meiryo'  # または 'Yu Gothic'
plt.rcParams['axes.unicode_minus'] = False  # 日本語文字が含まれる場合のマイナス記号対策

def get_db_connection(db_path):
    st.write("データベース接続を試みています...")
    if not os.path.exists(db_path):
        st.error(f"データベースファイルが存在しません: {db_path}")
        return None
    try:
        conn = sqlite3.connect(db_path)
        st.write("データベース接続成功")
        return conn
    except sqlite3.Error as e:
        st.error(f"データベース接続エラー: {e}")
        return None

def fetch_scores(conn):
    st.write("スコアデータを取得しています...")
    query = '''
        SELECT 
            scores.competition_id AS "競技ID",
            competitions.date AS "日付",
            competitions.course AS "コース",
            players.name AS "プレイヤー名",
            scores.out_score AS "アウトスコア",
            scores.in_score AS "インスコア",
            scores.total_score AS "合計スコア",
            scores.handicap AS "ハンディキャップ",
            scores.net_score AS "ネットスコア",
            scores.ranking AS "順位"
        FROM scores
        JOIN players ON scores.player_id = players.id
        JOIN competitions ON scores.competition_id = competitions.competition_id
    '''
    try:
        df = pd.read_sql_query(query, conn)
        st.write("スコアデータの取得に成功しました。")
        # ↓↓↓ デバッグ用の表示を削除またはコメントアウト ↓↓↓
        # st.write("データフレームのカラム:", df.columns.tolist())
        # st.write(df.head())
        return df
    except pd.io.sql.DatabaseError as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def display_aggregations(scores_df):
    st.subheader("データ集計")
    
    st.markdown("### 総合ランキング")
    if "プレイヤー名" in scores_df.columns and "合計スコア" in scores_df.columns:
        overall_ranking = scores_df.groupby("プレイヤー名")["合計スコア"].mean().sort_values(ascending=True)
        
        plt.figure(figsize=(10,6))
        overall_ranking.plot(kind='bar', color='skyblue')
        plt.xlabel("プレイヤー名")
        plt.ylabel("平均合計スコア")
        plt.title("プレイヤーごとの平均合計スコア (昇順)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(plt)
    else:
        st.error("必要なカラムがデータフレームに存在しません。")

def display_visualizations(scores_df):
    st.subheader("データ可視化")
    
    st.markdown("### スコア推移")
    plt.figure(figsize=(10,5))
    for player in scores_df["プレイヤー名"].unique():
        player_data = scores_df[scores_df["プレイヤー名"] == player]
        plt.plot(player_data["競技ID"], player_data["合計スコア"], marker='o', label=player)
    plt.xlabel("競技ID")
    plt.ylabel("合計スコア")
    plt.title("プレイヤーごとのスコア推移")
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plt.legend()
    plt.tight_layout()
    st.pyplot(plt)

def main():
    st.title("88会ゴルフコンペスコア管理システム")
    
    # データベースへのパス設定
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'golf_competition.db'))
    
    conn = get_db_connection(db_path)
    if conn:
        scores_df = fetch_scores(conn)
        if not scores_df.empty:
            display_aggregations(scores_df)
            display_visualizations(scores_df)
            
            # 競技ID 昇順、順位 昇順にソート
            past_data_df = scores_df.sort_values(by=["競技ID", "順位"], ascending=[True, True])
            
            st.subheader("過去データ")
            st.dataframe(past_data_df, height=None, use_container_width=True)
            
        conn.close()
        st.write("データベース接続を閉じました")

if __name__ == "__main__":
    main()
