# このスクリプトは、88会ゴルフコンペのスコア管理システムです。
# ユーザーがログインし、データベースからスコアデータを取得して表示します。
# データベース接続を確立し、スコアデータを取得し、集計および可視化を行います。
# また、優勝回数ランキングを表示し、過去のデータを表示します。

import sqlite3
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import japanize_matplotlib  # 追加

# ログイン用のパスワード設定
PASSWORD = "88"

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
    try:
        query = """
        SELECT
            scores.competition_id AS 競技ID,
            scores.date AS 日付,
            scores.course AS コース,
            players.name AS プレイヤー名,
            scores.out_score AS アウトスコア,
            scores.in_score AS インスコア,
            (scores.out_score + scores.in_score) AS 合計スコア,  -- グロススコアを計算
            scores.handicap AS ハンディキャップ,
            scores.net_score AS ネットスコア,
            scores.ranking AS 順位
        FROM scores
        JOIN players ON scores.player_id = players.id
        """
        df = pd.read_sql_query(query, conn)
        st.write("スコアデータの取得に成功しました。")
        return df
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def display_aggregations(scores_df):
    st.subheader("データ集計")
    
    st.markdown("### 総合ランキング")
    if "プレイヤー名" in scores_df.columns and "合計スコア" in scores_df.columns:
        # 合計スコアがNaNでない行のみを使用
        valid_scores_df = scores_df.dropna(subset=["合計スコア"])
        overall_ranking = valid_scores_df.groupby("プレイヤー名")["合計スコア"].mean().sort_values(ascending=True)
        
        plt.figure(figsize=(10,6))
        ax = overall_ranking.plot(kind='bar', color='skyblue')
        plt.xlabel("プレイヤー名")
        plt.ylabel("平均合計スコア")
        plt.title("プレイヤーごとの平均合計スコア (昇順)")
        plt.xticks(rotation=45, ha='right')
        
        # 棒グラフ上に数値を表示
        for i in ax.containers:
            ax.bar_label(i, label_type='edge', fmt='%.2f', padding=3)
        
        plt.tight_layout()
        st.pyplot(plt)
    else:
        st.error("必要なカラムがデータフレームに存在しません。")

def display_visualizations(scores_df):
    st.subheader("データ可視化")
    
    st.markdown("### スコア推移")
    
    # スコア詳細がNoneではない行のみ抽出
    filtered_scores_df = scores_df.dropna(subset=["アウトスコア", "インスコア", "合計スコア"])

    # グラフ作成
    plt.figure(figsize=(10, 5))
    for player in filtered_scores_df["プレイヤー名"].unique():
        player_data = filtered_scores_df[filtered_scores_df["プレイヤー名"] == player]
        plt.plot(player_data["競技ID"], player_data["合計スコア"], marker='o', label=player)
    
    plt.xlabel("競技ID")
    plt.ylabel("合計スコア")
    plt.title("プレイヤーごとのスコア推移")
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')  # 凡例を右に配置
    plt.tight_layout()
    st.pyplot(plt)

def display_winner_count_ranking(scores_df):
    st.subheader("優勝回数ランキング\n2024/12/31追加")

    # ランキングのタイプを選択
    ranking_type = st.radio("ランキングの種類を選択してください:", ["トータルランキング", "年度ランキング"])

    if ranking_type == "年度ランキング":
        # 年を選択するセレクトボックスを追加
        available_years = scores_df['日付'].str[:4].unique()
        year = st.selectbox("表示する年度を選択してください:", sorted(available_years))

        # 選択した年度のデータを抽出
        scores_df = scores_df[scores_df['日付'].str.startswith(year)]

    # 順位が1のデータを抽出
    rank_one_winners = scores_df[scores_df['順位'] == 1].groupby('プレイヤー名').size().reset_index(name='優勝回数')

    # 表示用のデータフレームに順位列を追加
    rank_one_winners = rank_one_winners.sort_values(by='優勝回数', ascending=False).reset_index(drop=True)
    rank_one_winners.index += 1  # インデックスを1から始める
    rank_one_winners.index.name = '順位'

    # データ表示
    st.dataframe(rank_one_winners, use_container_width=True)

    # グラフ表示
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(rank_one_winners['プレイヤー名'], rank_one_winners['優勝回数'], color='skyblue')
    ax.set_ylabel("優勝回数")
    ax.set_title("優勝回数ランキング")
    ax.set_xticklabels(rank_one_winners['プレイヤー名'], rotation=45, ha='right')
    ax.yaxis.get_major_locator().set_params(integer=True)  # Y軸を整数で表示
    st.pyplot(fig)

def main():
    # ログイン画面の表示
    st.title("ログイン")
    password = st.text_input("パスワードを入力してください", type="password")
    if password == PASSWORD:
        st.success("ログイン成功")
        
        # タイトルに改行を含める
        st.markdown("# 88会ゴルフコンペ\nスコア管理システム")
        
        # データベースへのパス設定
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'golf_competition.db'))
        
        conn = get_db_connection(db_path)
        if conn:
            scores_df = fetch_scores(conn)
            if not scores_df.empty:
                display_aggregations(scores_df)
                display_visualizations(scores_df)
                display_winner_count_ranking(scores_df)
                
                # 競技ID 昇順、順位 昇順にソート
                past_data_df = scores_df.sort_values(by=["競技ID", "順位"], ascending=[True, True])
                
                # "順位"を一番左に持ってくる
                columns_order = ["順位"] + [col for col in past_data_df.columns if col != "順位"]
                past_data_df = past_data_df[columns_order]

                st.subheader("過去データ")
                # データフレームを表示する際にインデックスを非表示にする
                st.dataframe(past_data_df.reset_index(drop=True), height=None, use_container_width=True)
            
            conn.close()
            st.write("データベース接続を閉じました")
    else:
        st.error("パスワードが間違っています")

if __name__ == "__main__":
    main()
