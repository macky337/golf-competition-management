"""
88会ゴルフコンペ・スコア管理システム

このスクリプトは、88会ゴルフコンペのスコアを管理するためのStreamlitアプリケーションです。
ユーザーはスコアデータを閲覧し、データの集計や可視化を行うことができます。
また、管理者はデータベースのバックアップおよびリストアを行うことができます。

機能:
- ユーザー認証
- スコアデータの取得と表示
- データの集計と可視化
- 優勝回数ランキングの表示
- データベースのバックアップとリストア

使用方法:
1. Streamlitをインストールします。
2. このスクリプトを実行します: `streamlit run app.py`
3. ブラウザで表示されるアプリケーションにアクセスします。

必要なライブラリ:
- sqlite3
- os
- pandas
- streamlit
- matplotlib
- japanize_matplotlib
- datetime
- pytz
- shutil

ログイン情報:
- ユーザー用パスワード: "88"
- 管理者用パスワード: "admin88"
"""

import sqlite3
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import japanize_matplotlib
from datetime import datetime
import pytz
import shutil

# ログイン用のパスワード設定
USER_PASSWORD = "88"
ADMIN_PASSWORD = "admin88"

# セッション状態を初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"  # デフォルトはログイン画面

def get_db_connection(db_path):
    # st.write("データベース接続を試みています...")
    if not os.path.exists(db_path):
        st.error(f"データベースファイルが存在しません: {db_path}")
        return None
    try:
        conn = sqlite3.connect(db_path)
        # st.write("データベース接続成功")
        return conn
    except sqlite3.Error as e:
        st.error(f"データベース接続エラー: {e}")
        return None

def fetch_scores(conn):
    # st.write("スコアデータを取得しています...")
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
        # st.write("スコアデータの取得に成功しました。")
        return df
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def fetch_players(conn):
    query = "SELECT * FROM players"
    players_df = pd.read_sql_query(query, conn)
    return players_df

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
        
        for container in ax.containers:
            ax.bar_label(container, fmt='%.2f', padding=3)
        
        plt.tight_layout()
        st.pyplot(plt)
    else:
        st.error("必要なカラムがデータフレームに存在しません。")

def display_visualizations(scores_df, players_df):
    st.subheader("スコア推移グラフ")
    
    # 必要なカラムを確認
    required_columns = ['プレイヤー名', '合計スコア', '日付']
    if not all(column in scores_df.columns for column in required_columns):
        st.error("必要なカラムがデータに含まれていません。")
        return

    # ユニークなプレイヤー名を取得
    players = scores_df['プレイヤー名'].unique()
    selected_player = st.selectbox("プレイヤーを選択してください", players)
    
    # 選択されたプレイヤーのスコアデータをフィルタリング
    player_scores = scores_df[scores_df['プレイヤー名'] == selected_player].sort_values(by='日付')
    
    if player_scores.empty:
        st.warning(f"{selected_player} のスコアデータがありません。")
        return
    
    # スコア推移のプロット
    plt.figure(figsize=(10, 5))
    plt.plot(player_scores['日付'], player_scores['合計スコア'], marker='o', linestyle='-')
    plt.title(f"{selected_player} のスコア推移")
    plt.xlabel("日付")
    plt.ylabel("合計スコア")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)

def display_winner_count_ranking(scores_df):
    st.subheader("優勝回数ランキング")

    ranking_type = st.radio("ランキングの種類を選択してください:", ["トータルランキング", "年度ランキング"])

    if ranking_type == "年度ランキング":
        available_years = scores_df['日付'].str[:4].unique()
        year = st.selectbox("表示する年度を選択してください:", sorted(available_years))
        scores_df = scores_df[scores_df['日付'].str.startswith(year)]

    # 優勝回数を計算
    rank_one_winners = (
        scores_df[scores_df['順位'] == 1]
        .groupby('プレイヤー名')
        .size()
        .reset_index(name='優勝回数')
        .sort_values(by='優勝回数', ascending=False)
    )

    # 順位を計算（同順位を処理するロジック）
    rank_one_winners["順位"] = rank_one_winners["優勝回数"].rank(method="dense", ascending=False).astype(int)

    st.dataframe(rank_one_winners, use_container_width=True)

    # グラフ描画
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(rank_one_winners['プレイヤー名'], rank_one_winners['優勝回数'], color='skyblue')
    ax.set_ylabel("優勝回数")
    ax.set_title("優勝回数ランキング")
    ax.set_xticks(range(len(rank_one_winners['プレイヤー名'])))
    ax.set_xticklabels(rank_one_winners['プレイヤー名'], rotation=45, ha='right')
    ax.yaxis.get_major_locator().set_params(integer=True)
    st.pyplot(fig)

def backup_database(db_path, backup_dir):
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    shutil.copy(db_path, backup_file)
    st.success(f"バックアップが作成されました: {backup_file}")

def restore_database(db_path, backup_dir):
    st.subheader("データベースのリストア")
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    if not backup_files:
        st.warning("バックアップファイルが見つかりません。")
        return
    selected_backup = st.selectbox("リストアするバックアップファイルを選択してください", backup_files)
    
    if st.button("リストア実行"):
        backup_file_path = os.path.join(backup_dir, selected_backup)
        shutil.copy(backup_file_path, db_path)
        st.success(f"データベースがリストアされました: {selected_backup}")

def login_page():
    st.title("88会ログイン")
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == USER_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.page = "main"
            # st.experimental_rerun() を削除
        else:
            st.error("パスワードが間違っています")

def admin_login_page():
    st.title("管理者ログイン")
    password = st.text_input("管理者パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.session_state.page = "admin"
            # st.experimental_rerun() を削除
        else:
            st.error("パスワードが間違っています")

def main_app():
    st.title("88会ゴルフコンペ・スコア管理システム")
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'golf_competition.db'))
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backup'))

    conn = get_db_connection(db_path)
    if conn:
        scores_df = fetch_scores(conn)
        players_df = fetch_players(conn)  # 追加: プレイヤーデータの取得

        if not scores_df.empty and not players_df.empty:
            display_aggregations(scores_df)
            display_visualizations(scores_df, players_df)  # 修正: players_df を渡す
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

            # ベスグロトップ10（10位までを表示）
            filtered_scores_df = scores_df[scores_df["競技ID"] != 41]

            best_gross_scores = filtered_scores_df.copy()
            best_gross_scores = best_gross_scores.dropna(subset=["合計スコア"])
            best_gross_scores["順位"] = best_gross_scores["合計スコア"].rank(method="min", ascending=True).astype(int)
            best_gross_scores = best_gross_scores.sort_values(by=["順位", "合計スコア"]).head(20)

            st.subheader("ベストグロススコアトップ20")
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

        conn.close()
        st.write("データベース接続を閉じました")
    
    if st.button("設定画面へ"):
        st.session_state.page = "admin"
        # st.experimental_rerun() を削除

    if st.button("ログアウト"):
        st.session_state.logged_in = False
        st.session_state.page = "login"

def admin_app():
    st.title("管理者設定画面")
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'golf_competition.db'))
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backup'))

    # バックアップボタン
    if st.button("データベースをバックアップ"):
        backup_database(db_path, backup_dir)

    # リストアボタン
    restore_database(db_path, backup_dir)

    if st.button("本体画面へ"):
        st.session_state.page = "main"

    if st.button("ログアウト"):
        st.session_state.admin_logged_in = False
        st.session_state.page = "login"

def page_router():
    if st.session_state.page == "main":
        if st.session_state.logged_in:
            main_app()
        else:
            login_page()
    elif st.session_state.page == "admin":
        if st.session_state.admin_logged_in:
            admin_app()
        else:
            admin_login_page()
    else:
        login_page()

# アプリの起動
if not st.session_state.logged_in and not st.session_state.admin_logged_in:
    st.session_state.page = "login"

page_router()