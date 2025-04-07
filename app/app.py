# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム (Supabase版)

このスクリプトは、88会ゴルフコンペのスコアを管理するためのStreamlitアプリケーションです。
ユーザーはスコアデータを閲覧し、データの分析や可視化を行うことができます。
また、管理者はデータベースのバックアップおよびリストアを行うことができます。

機能:
- ユーザー認証
- スコアデータの取得と表示
- データの分析と可視化
- 優勝回数ランキングの表示
- データベースのバックアップとリストア

使用方法:
1. Streamlitをインストールします。
2. このスクリプトを実行します `streamlit run app.py`
3. ブラウザで表示されるアプリケーションにアクセスします。

必要なライブラリ:
- os
- pandas
- streamlit
- matplotlib
- japanize_matplotlib
- datetime
- pytz
- supabase
- dotenv

ログイン情報:
- ユーザー用パスワード "88"
- 管理者用パスワード "admin88"
"""

import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import japanize_matplotlib
from datetime import datetime
import pytz
import json
from supabase import create_client
from dotenv import load_dotenv
import subprocess
import warnings
import logging

# 警告メッセージを非表示にする
warnings.filterwarnings('ignore')
# ログレベルを設定してmatplotlibの警告を抑制
logging.getLogger('matplotlib').setLevel(logging.ERROR)

# ファイル先頭付近に変数定義を追加
APP_VERSION = "1.0.7"
APP_LAST_UPDATE = "2025-04-06"

# ページ最上部に追加（st.titleの前）
st.markdown("""
<style>
    .footer-container {
        position: fixed;
        bottom: 0;
        right: 0;
        left: 0;
        padding: 10px;
        background-color: rgba(255, 255, 255, 0.8);
        border-top: 1px solid #ddd;
        z-index: 999;
    }
    .footer-text {
        font-size: 0.8rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# 環境変数の読み込み
load_dotenv()

# Supabase接続情報 - Streamlit secretsと環境変数の両方をサポート
try:
    # まずStreamlit secretsを試す
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    # ログ出力を削除
except Exception:
    # 次に環境変数を試す
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    # ログ出力を削除

# ログイン用のパスワード設定
USER_PASSWORD = "88"
ADMIN_PASSWORD = "admin88"

# セッション状態を初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"  # デフォルト：ログイン画面

def get_supabase_client():
    """Supabaseクライアントを取得"""
    # 接続情報のデバッグ表示を削除
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Supabase接続情報が設定されていません。.streamlit/secrets.tomlまたは.envファイルを確認してください。")
        return None
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # 接続テスト
        test_response = supabase.table("players").select("count").limit(1).execute()
        # 接続成功メッセージも削除
        return supabase
    except Exception as e:
        st.error(f"Supabase接続エラー: {e}")
        return None

def fetch_scores():
    """スコアデータをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("scores").select("*").execute()
        scores = response.data
        
        # プレイヤー情報を取得
        players_response = supabase.table("players").select("*").execute()
        players = {player["id"]: player["name"] for player in players_response.data}
        
        # スコアデータを整形
        scores_list = []
        for score in scores:
            score_dict = {
                "競技ID": score["competition_id"],
                "日付": score["date"],
                "コース": score["course"],
                "プレイヤー名": players.get(score["player_id"], "不明"),
                "アウトスコア": score["out_score"],
                "インスコア": score["in_score"],
                "合計スコア": score["out_score"] + score["in_score"],
                "ハンディキャップ": score["handicap"],
                "ネットスコア": score["net_score"],
                "順位": score["ranking"]
            }
            scores_list.append(score_dict)
        
        return pd.DataFrame(scores_list)
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

def fetch_players():
    """プレイヤーデータをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("players").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"プレイヤーデータ取得エラー: {e}")
        return pd.DataFrame()

def display_aggregations(scores_df):
    st.subheader("データ分析")
    
    st.markdown("### 総合ランキング")
    if "プレイヤー名" in scores_df.columns and "合計スコア" in scores_df.columns:
        valid_scores_df = scores_df.dropna(subset=["合計スコア"])
        overall_ranking = valid_scores_df.groupby("プレイヤー名")["合計スコア"].mean().sort_values(ascending=True)
        
        plt.figure(figsize=(10,6))
        ax = overall_ranking.plot(kind='bar', color='skyblue')
        plt.xlabel("プレイヤー名")
        plt.ylabel("平均合計スコア")
        plt.title("プレイヤーごとの平均合計スコア (低いほど良い)")
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

    rank_one_winners = scores_df[scores_df['順位'] == 1].groupby('プレイヤー名').size().reset_index(name='優勝回数')
    rank_one_winners = rank_one_winners.sort_values(by='優勝回数', ascending=False).reset_index(drop=True)
    rank_one_winners.index += 1
    rank_one_winners.index.name = '順位'

    st.dataframe(rank_one_winners, use_container_width=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(rank_one_winners['プレイヤー名'], rank_one_winners['優勝回数'], color='skyblue')
    ax.set_ylabel("優勝回数")
    ax.set_title("優勝回数ランキング")
    ax.set_xticks(range(len(rank_one_winners['プレイヤー名'])))
    ax.set_xticklabels(rank_one_winners['プレイヤー名'], rotation=45, ha='right')
    ax.yaxis.get_major_locator().set_params(integer=True)
    st.pyplot(fig)

def backup_database():
    """Supabaseからデータをバックアップする（JSONファイルとして保存）"""
    supabase = get_supabase_client()
    if not supabase:
        return
    
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backup'))
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    try:
        # 各テーブルのデータを取得
        competitions_response = supabase.table("competitions").select("*").execute()
        players_response = supabase.table("players").select("*").execute()
        scores_response = supabase.table("scores").select("*").execute()
        
        # バックアップデータを準備
        backup_data = {
            "competitions": competitions_response.data,
            "players": players_response.data,
            "scores": scores_response.data,
            "backup_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # JSONファイルとして保存
        backup_file = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        st.success(f"バックアップが作成されました: {backup_file}")
    except Exception as e:
        st.error(f"バックアップ中にエラーが発生しました: {e}")

def restore_database():
    """JSONバックアップファイルからSupabaseにデータをリストアする"""
    supabase = get_supabase_client()
    if not supabase:
        return
    
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backup'))
    if not os.path.exists(backup_dir):
        # 一つ上の階層のbackupディレクトリを試す
        parent_backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backup'))
        if os.path.exists(parent_backup_dir):
            backup_dir = parent_backup_dir
            st.info(f"上位ディレクトリのバックアップフォルダを使用します: {backup_dir}")
        else:
            st.warning(f"バックアップディレクトリが存在しません: {backup_dir}")
            return
    
    # JSONバックアップファイルを検索
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
    if not backup_files:
        st.warning("バックアップファイルが見つかりません。")
        return
    
    selected_backup = st.selectbox("リストアするバックアップファイルを選択してください", backup_files)
    
    if st.button("リストア実行"):
        try:
            # バックアップファイルからデータを読み込む
            backup_file_path = os.path.join(backup_dir, selected_backup)
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 既存のデータを削除
            supabase.table("scores").delete().execute()
            supabase.table("competitions").delete().execute()
            supabase.table("players").delete().execute()
            
            # データを復元
            supabase.table("competitions").insert(backup_data["competitions"]).execute()
            supabase.table("players").insert(backup_data["players"]).execute()
            
            # スコアデータは量が多い可能性があるのでチャンクに分ける
            scores = backup_data["scores"]
            chunk_size = 100
            for i in range(0, len(scores), chunk_size):
                chunk = scores[i:i+chunk_size]
                supabase.table("scores").insert(chunk).execute()
            
            st.success(f"データベースがリストアされました: {selected_backup}")
        except Exception as e:
            st.error(f"リストア中にエラーが発生しました: {e}")

def login_page():
    st.title("88会ログイン")
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == USER_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.page = "main"
            st.rerun()  # ページを強制的に再読み込み
        else:
            st.error("パスワードが間違っています")

def admin_login_page():
    st.title("管理者ログイン")
    password = st.text_input("管理者パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.session_state.page = "admin"
            st.rerun()  # ページを強制的に再読み込み
        else:
            st.error("パスワードが間違っています")

def main_app():
    st.title("88会ゴルフコンペ・スコア管理システム")
    
    # Supabaseからデータを取得
    scores_df = fetch_scores()
    players_df = fetch_players()
    
    if not scores_df.empty and not players_df.empty:
        display_aggregations(scores_df)
        display_visualizations(scores_df, players_df)
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
        
        # 競技IDが41でないデータのみを対象にする
        filtered_scores_df = scores_df[scores_df["競技ID"] != 41]
        
        # 合計スコアが0または欠損値のデータを除外する
        filtered_scores_df = filtered_scores_df[
            (filtered_scores_df["合計スコア"] > 0) & 
            (~filtered_scores_df["合計スコア"].isna()) &
            (filtered_scores_df["アウトスコア"] > 0) & 
            (~filtered_scores_df["アウトスコア"].isna()) &
            (filtered_scores_df["インスコア"] > 0) & 
            (~filtered_scores_df["インスコア"].isna())
        ]
        
        # 合計スコアでソートし、トップ10を取得
        best_gross_scores = filtered_scores_df.sort_values(by="合計スコア").head(10).reset_index(drop=True)
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
    else:
        if scores_df.empty:
            st.warning("スコアデータが取得できませんでした。")
        if players_df.empty:
            st.warning("プレイヤーデータが取得できませんでした。")
        st.error("データの取得に失敗しました。Supabase接続情報とRLS設定を確認してください。")
    
    if st.button("設定画面へ"):
        st.session_state.page = "admin"
        st.rerun()  # ページを強制的に再読み込み
    
    if st.button("ログアウト"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()  # ページを強制的に再読み込み

def admin_app():
    st.title("管理者設定画面")
    
    # バックアップボタン
    if st.button("データベースをバックアップ"):
        backup_database()
    
    # リストアセクション
    st.subheader("データベースのリストア")
    restore_database()
    
    if st.button("本体画面へ"):
        st.session_state.page = "main"
        st.rerun()  # ページを強制的に再読み込み
    
    if st.button("ログアウト"):
        st.session_state.admin_logged_in = False
        st.session_state.page = "login"
        st.rerun()  # ページを強制的に再読み込み

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

# Supabase接続状況を取得
def get_supabase_status():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            # 軽量な接続テスト
            test_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            test_client.table("players").select("count").limit(1).execute()
            return "🟢 接続済"
        except Exception:
            return "🔴 未接続"
    else:
        return "🔴 設定なし"

def get_git_revision():
    """現在のGitリビジョン（コミットハッシュ）を取得する"""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "dev"  # Git情報が取得できない場合

def get_git_date():
    """最新コミットの日付を取得する"""
    try:
        return subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short']).decode('ascii').strip()
    except Exception:
        return APP_LAST_UPDATE  # Git情報が取得できない場合は固定の日付を返す

# CSS調整（縦配置用）
st.markdown("""
<style>
    .vertical-footer {
        position: fixed;
        bottom: 10px;
        right: 10px;
        background-color: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 0 5px rgba(0,0,0,0.1);
        z-index: 999;
        text-align: right;
        line-height: 1.5;
    }
    .footer-item {
        font-size: 0.75rem;
        color: #666;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

# フッターを右下に縦に配置
connection_status = get_supabase_status()
git_rev = get_git_revision()
git_date = get_git_date()

st.markdown(f"""
<div class="vertical-footer">
    <span class="footer-item">Ver {APP_VERSION} ({git_rev})</span>
    <span class="footer-item">最終更新: {git_date}</span>
    <span class="footer-item">Supabase: {connection_status}</span>
</div>
""", unsafe_allow_html=True)




