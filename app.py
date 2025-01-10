import sqlite3
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import japanize_matplotlib
from datetime import datetime
import pytz
import shutil

# ログイン用のパスワード設定
PASSWORD = "88"

# セッション状態を初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

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
            (scores.out_score + scores.in_score) AS 合計スコア,
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
        valid_scores_df = scores_df.dropna(subset=["合計スコア"])
        overall_ranking = valid_scores_df.groupby("プレイヤー名")["合計スコア"].mean().sort_values(ascending=True)
        
        plt.figure(figsize=(10,6))
        ax = overall_ranking.plot(kind='bar', color='skyblue')
        plt.xlabel("プレイヤー名")
        plt.ylabel("平均合計スコア")
        plt.title("プレイヤーごとの平均合計スコア (昇順)")
        plt.xticks(rotation=45, ha='right')
        
        for i in ax.containers:
            ax.bar_label(i, label_type='edge', fmt='%.2f', padding=3)
        
        plt.tight_layout()
        st.pyplot(plt)
    else:
        st.error("必要なカラムがデータフレームに存在しません。")

def display_visualizations(scores_df):
    st.subheader("データ可視化")
    
    st.markdown("### スコア推移")
    
    filtered_scores_df = scores_df.dropna(subset=["アウトスコア", "インスコア", "合計スコア"])

    plt.figure(figsize=(10, 5))
    for player in filtered_scores_df["プレイヤー名"].unique():
        player_data = filtered_scores_df[filtered_scores_df["プレイヤー名"] == player]
        plt.plot(player_data["競技ID"], player_data["合計スコア"], marker='o', label=player)
    
    plt.xlabel("競技ID")
    plt.ylabel("合計スコア")
    plt.title("プレイヤーごとのスコア推移")
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
    plt.tight_layout()
    st.pyplot(plt)

def display_winner_count_ranking(scores_df):
    st.subheader("優勝回数ランキング")

    ranking_type = st.radio("ランキングの種類を選択してください:", ["トータルランキング", "年度ランキング"])

    if ranking_type == "年度ランキング":
        available_years = scores_df['日付'].str[:4].unique()
        year = st.selectbox("表示する年度を選択してください:", sorted(available_years))
        scores_df = scores_df[scores_df['日付'].str.startswith(year)]

    rank_one_winners = scores_df[scores_df['順位'] == 1].groupby('プレイヤー名').size().reset_index(name='優勝回数')
    rank_one_winners = rank_one_winners.sort_values(by='優勝回数', ascending=False).reset_index(drop=True)
    rank_one_winners.index += 1
    rank_one_winners.index.name = '順位'

    st.dataframe(rank_one_winners, use_container_width=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(rank_one_winners['プレイヤー名'], rank_one_winners['優勝回数'], color='skyblue')
    ax.set_ylabel("優勝回数")
    ax.set_title("優勝回数ランキング")
    ax.set_xticklabels(rank_one_winners['プレイヤー名'], rotation=45, ha='right')
    ax.yaxis.get_major_locator().set_params(integer=True)
    st.pyplot(fig)

def backup_database(db_path, backup_dir):
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    shutil.copy(db_path, backup_file)
    st.success(f"バックアップが作成されました: {backup_file}")

def login_page():
    st.title("88会ログイン")
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == PASSWORD:
            st.session_state.logged_in = True
        else:
            st.error("パスワードが間違っています")

def main_app():
    st.title("88会ゴルフコンペ・スコア管理システム")
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'golf_competition.db'))
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backup'))

    conn = get_db_connection(db_path)
    if conn:
        scores_df = fetch_scores(conn)
        if not scores_df.empty:
            display_aggregations(scores_df)
            display_visualizations(scores_df)
            display_winner_count_ranking(scores_df)

            # 過去データを準備
            past_data_df = scores_df.sort_values(by=["競技ID", "順位"], ascending=[True, True])
            past_data_df = past_data_df.reset_index()
            columns_order = ["順位"] + [col for col in past_data_df.columns if col != "順位" and col != "index"] + ["index"]
            past_data_df = past_data_df[columns_order]
            
            st.subheader("過去データ")
            # 過去データのフォーマットを適用
            st.dataframe(
                past_data_df.style.format({
                    "ハンディキャップ": "{:.2f}", 
                    "ネットスコア": "{:.2f}",
                    "アウトスコア": "{:.0f}",
                    "インスコア": "{:.0f}",
                    "合計スコア": "{:.0f}",
                    "順位": "{:.0f}",
                    "競技ID": "{:.0f}"
                }), 
                height=None, 
                use_container_width=True
            )

            # ベストグロススコアトップ10を準備
            st.subheader("ベストグロススコアトップ10")
            best_gross_scores = scores_df.sort_values(by="合計スコア").head(10).reset_index(drop=True)
            best_gross_scores.index += 1
            best_gross_scores.index.name = '順位'

            # ベストグロススコアトップ10のフォーマットを適用
            st.dataframe(
                best_gross_scores.style.format({
                    "ハンディキャップ": "{:.2f}",
                    "ネットスコア": "{:.2f}",
                    "アウトスコア": "{:.0f}",
                    "インスコア": "{:.0f}",
                    "合計スコア": "{:.0f}",
                    "順位": "{:.0f}",
                    "競技ID": "{:.0f}"
                }), 
                height=None, 
                use_container_width=True
            )

            # 最終更新日時を表示
            st.subheader("最終更新日時")
            jst = pytz.timezone('Asia/Tokyo')
            st.write(datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S"))

            # バックアップボタン
            if st.button("データベースをバックアップ"):
                backup_database(db_path, backup_dir)

        conn.close()
        st.write("データベース接続を閉じました")
    if st.button("ログアウト"):
        st.session_state.logged_in = False

if st.session_state.logged_in:
    main_app()
else:
    login_page()
