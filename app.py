import sqlite3
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import japanize_matplotlib
from datetime import datetime
import pytz
<<<<<<< HEAD
import shutil
=======
import io
>>>>>>> 71c34989d080233b34f5ce455216d976817d5c14

# ログイン用のパスワード設定
PASSWORD = "88"

# セッション状態を初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "main"  # デフォルトはメイン画面

# データベース接続関数
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

# スコアデータ取得関数
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

# 集計結果表示関数
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

<<<<<<< HEAD
def backup_database(db_path, backup_dir):
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    shutil.copy(db_path, backup_file)
    st.success(f"バックアップが作成されました: {backup_file}")

=======
# ログインページ
>>>>>>> 71c34989d080233b34f5ce455216d976817d5c14
def login_page():
    st.title("88会ログイン")
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == PASSWORD:
            st.session_state.logged_in = True
        else:
            st.error("パスワードが間違っています")

# メインアプリ
def main_app():
    st.title("88会ゴルフコンペ・スコア管理システム")
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'golf_competition.db'))
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backup'))

    conn = get_db_connection(db_path)
    if conn:
        # 登録後の表示や集計処理は既存コードに従う
        scores_df = fetch_scores(conn)
        display_aggregations(scores_df)
        display_visualizations(scores_df)
        display_winner_count_ranking(scores_df)

            # バックアップボタン
            if st.button("データベースをバックアップ"):
                backup_database(db_path, backup_dir)

        conn.close()
        st.write("データベース接続を閉じました")

    if st.button("ログアウト"):
        st.session_state.logged_in = False

def add_new_scores_screen(conn):
    st.title("新しいスコアの登録")
    num_entries = st.number_input("登録するデータの件数を入力してください", min_value=1, step=1)

    # 入力フォームを動的に生成
    forms = []
    for i in range(num_entries):
        st.write(f"### データ {i+1}")
        form = {
            "competition_id": st.text_input(f"[{i+1}] 競技ID"),
            "date": st.date_input(f"[{i+1}] 日付"),
            "course": st.text_input(f"[{i+1}] コース名"),
            "player_name": st.text_input(f"[{i+1}] プレイヤー名"),
            "out_score": st.number_input(f"[{i+1}] アウトスコア", min_value=0, max_value=50, step=1),
            "in_score": st.number_input(f"[{i+1}] インスコア", min_value=0, max_value=50, step=1),
            "handicap": st.number_input(f"[{i+1}] ハンディキャップ", min_value=0.0, format="%.2f"),
        }
        forms.append(form)

    col1, col2 = st.columns(2)

    with col1:
        # 登録ボタン
        if st.button("一括登録"):
            try:
                # 競技IDごとに順位を計算
                competition_data = {}
                for form in forms:
                    total_score = form["out_score"] + form["in_score"]
                    net_score = total_score - form["handicap"]

                    if form["competition_id"] not in competition_data:
                        competition_data[form["competition_id"]] = []
                    
                    competition_data[form["competition_id"]].append({
                        "date": form["date"],
                        "course": form["course"],
                        "player_name": form["player_name"],
                        "total_score": total_score,
                        "net_score": net_score,
                    })

                # データベースに登録
                for competition_id, players in competition_data.items():
                    # 順位を計算（ネットスコアの昇順）
                    sorted_players = sorted(players, key=lambda x: x["net_score"])
                    for rank, player in enumerate(sorted_players, start=1):
                        conn.execute("""
                        INSERT INTO scores (competition_id, date, course, player_id, out_score, in_score, handicap, net_score, ranking)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            competition_id, player["date"], player["course"], player["player_name"],
                            player["total_score"] - player["net_score"],  # アウトスコア + インスコアから計算
                            player["total_score"],  # 合計スコア
                            player["net_score"],  # ネットスコア
                            rank  # 自動計算した順位
                        ))
                conn.commit()
                st.success(f"{num_entries}件のスコアを登録しました！")
                st.session_state.page = "main"  # 登録後にメイン画面へ遷移
            except Exception as e:
                st.error(f"登録エラー: {e}")

    with col2:
        # キャンセルボタン
        if st.button("キャンセル"):
            st.session_state.page = "main"  # メイン画面へ遷移
            st.warning("入力がキャンセルされました。")

def page_router():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'golf_competition.db'))
    conn = get_db_connection(db_path)

    if st.session_state.page == "main":
        main_app()
    elif st.session_state.page == "add_scores":
        if conn:
            add_new_scores_screen(conn)
            conn.close()
    elif st.session_state.page == "login":
        login_page()

# アプリの起動
if not st.session_state.logged_in:
    st.session_state.page = "login"

page_router()
