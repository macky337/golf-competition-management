# -*- coding: utf-8 -*-
import platform
import html


import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
# japanize_matplotlibの代わりに直接日本語フォントを設定
import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'  # Windowsの場合
# Linux/Macの場合は以下のいずれかを使用
# matplotlib.rcParams['font.family'] = 'IPAGothic'
# matplotlib.rcParams['font.family'] = 'Noto Sans CJK JP'
from datetime import datetime
import pytz
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import subprocess
import warnings
import logging
import japanize_matplotlib
from matplotlib.ticker import MaxNLocator
from typing import Optional, Any, Dict, List
import re

# 他のモジュールをインポート
from announcement_management import announcement_management_tab
# プレースホルダーとして他の管理モジュールもインポート
from player_management import player_management_tab
from competition_management import competition_management_tab
from score_entry import score_entry_page as score_entry_tab



def get_project_root():
    """プロジェクトのルートディレクトリを取得"""
    return os.path.dirname(os.path.dirname(__file__))


def _get_static_version_fallback() -> str:
    """環境変数やVERSIONファイルに定義された静的バージョンを取得"""
    try:
        version_from_secrets = st.secrets.get("app", {}).get("version", "")
        if isinstance(version_from_secrets, str) and version_from_secrets.strip():
            return version_from_secrets.strip()
    except Exception:
        pass

    for key in ("APP_VERSION_OVERRIDE", "APP_VERSION"):
        value = os.getenv(key, "").strip()
        if value:
            return value

    version_file = os.path.join(get_project_root(), "VERSION")
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                value = f.read().strip()
                if value:
                    return value
        except Exception:
            pass
    return ""


def _get_static_git_rev_fallback() -> str:
    for key in (
        "APP_GIT_REV",
        "GIT_REVISION",
        "RAILWAY_GIT_COMMIT_SHA",
        "SOURCE_VERSION",
        "GITHUB_SHA",
        "VERCEL_GIT_COMMIT_SHA",
        "RENDER_GIT_COMMIT",
    ):
        value = os.getenv(key, "").strip()
        if value:
            return value[:8]
    return "unknown"

# 実行環境に応じてフォントを設定
if platform.system() == 'Windows':
    matplotlib.rcParams['font.family'] = 'MS Gothic'
elif platform.system() == 'Darwin':  # Macの場合
    matplotlib.rcParams['font.family'] = 'Hiragino Maru Gothic Pro'
else:  # Linux（Streamlit Cloud含む）
    matplotlib.rcParams['font.family'] = 'IPAexGothic'  # あるいは 'Noto Sans CJK JP'

# 警告メッセージを非表示にする
warnings.filterwarnings('ignore')
# ログレベルを設定してmatplotlibの警告を抑制
logging.getLogger('matplotlib').setLevel(logging.ERROR)

# Gitからバージョン情報を取得する関数
def get_git_revision():
    """Git のコミットハッシュを取得"""
    try:
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                               capture_output=True, text=True, cwd=get_project_root())
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return _get_static_git_rev_fallback()

def get_git_count():
    """Gitのコミット数を取得する"""
    try:
        return subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'], cwd=get_project_root()
        ).decode('ascii').strip()
    except Exception:
        return "0"  # Git情報が取得できない場合

def get_git_date():
    """Git の最終コミット日時を JST で取得"""
    try:
        # JST時間で取得を試行
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=format-local:%Y-%m-%d %H:%M'], 
                               capture_output=True, text=True, cwd=get_project_root())
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # フォールバック：UTC時間を取得してJSTに変換
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=iso'], 
                               capture_output=True, text=True, cwd=get_project_root())
        if result.returncode == 0:
            # 簡易的なUTC→JST変換（+9時間）
            import re
            from datetime import datetime as dt_class, timedelta
            match = re.match(r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}):\d{2}', result.stdout.strip())
            if match:
                date_part, time_part = match.groups()
                dt = dt_class.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
                dt_jst = dt + timedelta(hours=9)  # UTCからJSTに変換
                return dt_jst.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    
    # 最終フォールバック：現在のJST時間
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M")

def get_git_latest_commit_message():
    """最新のコミットメッセージを取得する"""
    try:
        return subprocess.check_output(
            ['git', 'log', '-1', '--pretty=%B'], cwd=get_project_root()
        ).decode('utf-8').strip()
    except Exception:
        return ""  # Git情報が取得できない場合は空文字列

def parse_version_from_commit_history():
    """コミット履歴を解析し、適切なバージョン番号を計算する"""
    try:
        latest_commit_message = get_git_latest_commit_message()
        commit_count = int(get_git_count())

        major = 1
        minor = commit_count // 100
        patch = commit_count % 100

        if re.search(r'^(major:|MAJOR:|!:)', latest_commit_message):
            major += 1
            minor = 0
            patch = 0
        elif re.search(r'^(feature:|feat:|FEATURE:)', latest_commit_message):
            minor += 1
            patch = 0
        elif re.search(r'^(fix:|bugfix:|FIX:)', latest_commit_message):
            patch += 1

        return f"{major}.{minor}.{patch}"
    except Exception:
        return "1.2.4"

def get_app_version():
    """アプリバージョンを取得（動的バージョン使用）"""
    try:
        project_root = get_project_root()
        branch_result = subprocess.run(
            ['git', 'branch', '--show-current'], capture_output=True, text=True, cwd=project_root
        )

        if branch_result.returncode != 0:
            static_version = _get_static_version_fallback()
            return static_version or "1.2.4"

        branch = branch_result.stdout.strip()
        base_version = parse_version_from_commit_history()

        if branch == "main" or not branch:
            return base_version
        if branch == "feature-branch":
            return f"{base_version}-dev"
        return f"{base_version}-{branch}"

    except Exception as e:
        print(f"Version calculation error: {e}")
        static_version = _get_static_version_fallback()
        return static_version or "1.2.4"

def get_app_last_update():
    """アプリの最終更新日を JST で動的に取得する"""
    try:
        return get_git_date()
    except Exception:
        # 現在のJST時間をフォールバック
        jst = pytz.timezone('Asia/Tokyo')
        return datetime.now(jst).strftime('%Y-%m-%d %H:%M')

# バージョン情報を動的に設定
APP_VERSION = get_app_version()
APP_LAST_UPDATE = get_app_last_update()


def resolve_main_render_mode() -> str:
    """メイン画面の描画モードを解決（safe / compat）"""
    explicit_mode = os.getenv("MAIN_RENDER_MODE", "").strip().lower()
    if explicit_mode in {"safe", "compat"}:
        return explicit_mode

    # 後方互換: MAIN_SAFE_MODE=true なら safe, それ以外は compat
    safe_mode_raw = os.getenv("MAIN_SAFE_MODE", "true")
    safe_mode_value = safe_mode_raw.strip().lower() == "true"
    return "safe" if safe_mode_value else "compat"


def _navigate(page: str) -> None:
    """画面遷移を統一する"""
    st.session_state.page = page
    st.rerun()


def _logout_user() -> None:
    """ログイン状態と一時データをクリアする"""
    st.session_state.logged_in = False
    st.session_state.admin_logged_in = False
    st.session_state.page = "login"
    st.session_state.pop("score_data", None)
    st.rerun()


def render_dashboard_shell() -> None:
    """ログイン後ホーム共通の視覚デザイン"""
    st.markdown(
        """
        <style>
          :root {
            --club-ink: #16332b;
            --club-muted: #6f817a;
            --club-green: #0e6b4f;
            --club-green-deep: #073d31;
            --club-mint: #e9f5ef;
            --club-line: #dce9e2;
            --club-cream: #fbfaf4;
            --club-gold: #d3aa4a;
          }
          .stApp { background: linear-gradient(180deg, #f7faf8 0, #ffffff 430px); }
          .block-container { max-width: 1180px; padding-top: 1.5rem; padding-bottom: 4rem; }
          .dashboard-hero {
            position: relative; overflow: hidden;
            padding: 2.4rem 2.5rem 2.25rem;
            margin: .25rem 0 1.25rem;
            border: 1px solid rgba(255,255,255,.15);
            border-radius: 28px;
            color: white;
            background:
              radial-gradient(circle at 90% 15%, rgba(255,255,255,.16) 0 90px, transparent 91px),
              radial-gradient(circle at 85% 80%, rgba(211,170,74,.18) 0 150px, transparent 151px),
              linear-gradient(125deg, #052f27 0%, #0c674c 58%, #17845f 100%);
            box-shadow: 0 22px 55px rgba(7, 61, 49, .20);
          }
          .dashboard-hero::after { content: "88"; position: absolute; right: 2rem; bottom: -2.5rem; color: rgba(255,255,255,.07); font-size: 9rem; line-height: 1; font-weight: 900; }
          .dashboard-eyebrow { color: #bcead7; font-size: .76rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
          .dashboard-hero h1 { margin: .45rem 0 0; font-size: clamp(2rem, 5vw, 3.25rem); line-height: 1.08; color: white; letter-spacing: -.035em; }
          .dashboard-hero p { max-width: 650px; margin: .8rem 0 0; color: #d9f3e8; font-size: 1rem; line-height: 1.75; }
          .dashboard-hero-badge { display: inline-block; margin-top: 1.2rem; padding: .42rem .75rem; border: 1px solid rgba(255,255,255,.22); border-radius: 999px; background: rgba(255,255,255,.10); color: #fff7dc; font-size: .78rem; font-weight: 700; }
          .dashboard-section-label { margin: 1.8rem 0 .75rem; color: var(--club-ink); font-size: 1.2rem; font-weight: 800; letter-spacing: -.01em; }
          .dashboard-section-label small { display: block; margin-top: .2rem; color: var(--club-muted); font-size: .78rem; font-weight: 500; letter-spacing: 0; }
          .dashboard-status-card {
            min-height: 98px; padding: .85rem .95rem;
            border: 1px solid var(--club-line); border-radius: 18px;
            background: rgba(255,255,255,.88); color: var(--club-ink);
            box-shadow: 0 8px 24px rgba(23, 72, 57, .055);
          }
          .dashboard-status-card .metric-icon { display: block; margin-bottom: .38rem; font-size: 1.05rem; }
          .dashboard-status-card strong { display: block; margin-top: .08rem; color: var(--club-green-deep); font-size: 1.28rem; letter-spacing: -.02em; }
          .dashboard-status-card span { color: var(--club-muted); font-size: .78rem; }
          .dashboard-notice { padding: 1.45rem 1.55rem; border: 1px solid #e9e3d1; border-radius: 22px; background: linear-gradient(135deg, #fffdf7, #fbf7e9); box-shadow: 0 10px 28px rgba(90,70,24,.06); }
          .dashboard-notice h3 { margin: 0; color: #43391e; font-size: 1.3rem; }
          .dashboard-notice p { margin: .65rem 0 0; color: #665f4d; line-height: 1.7; }
          .dashboard-footer { margin: 2.5rem 0 .5rem; padding-top: 1rem; border-top: 1px solid var(--club-line); text-align: center; color: #84968f; font-size: .78rem; }
          .dashboard-chart { padding: .75rem .9rem; border: 1px solid var(--club-line); border-radius: 16px; background: #fff; }
          .dashboard-chart-row { display: grid; grid-template-columns: minmax(105px, 24%) 1fr 42px; gap: .65rem; align-items: center; margin: .52rem 0; }
          .dashboard-chart-name { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; color: #235447; font-weight: 650; font-size: .9rem; }
          .dashboard-chart-track { height: 10px; overflow: hidden; border-radius: 999px; background: #e5f0eb; }
          .dashboard-chart-fill { height: 100%; min-width: 7px; border-radius: inherit; background: linear-gradient(90deg, var(--club-green), #36a77e); }
          .dashboard-chart-value { text-align: right; color: var(--club-green-deep); font-size: .84rem; font-weight: 800; }
          .dashboard-spotlight { min-height: 132px; padding: 1rem 1.1rem; border: 1px solid var(--club-line); border-radius: 18px; background: #fff; box-shadow: 0 8px 22px rgba(20,65,51,.06); }
          .dashboard-spotlight.gold { border-color: #eadcae; background: linear-gradient(135deg, #fffdf7, #fbf3d7); }
          .dashboard-spotlight .eyebrow { color: var(--club-muted); font-size: .75rem; font-weight: 800; letter-spacing: .09em; }
          .dashboard-spotlight strong { display: block; margin: .38rem 0 .18rem; color: var(--club-green-deep); font-size: 1.3rem; letter-spacing: -.02em; }
          .dashboard-spotlight.gold strong { color: #735a18; }
          .dashboard-spotlight p { margin: 0; color: #687b73; font-size: .8rem; line-height: 1.5; }
          .dashboard-podium { min-height: 96px; padding: .75rem; border: 1px solid var(--club-line); border-radius: 14px; background: #fff; text-align: center; }
          .dashboard-podium .medal { font-size: 1.35rem; }
          .dashboard-podium strong { display: block; margin: .28rem 0 .1rem; color: var(--club-ink); font-size: 1rem; }
          .dashboard-podium span { color: var(--club-muted); font-size: .8rem; }
          .dashboard-competition { min-height: 105px; padding: .8rem; border-left: 4px solid var(--club-green); border-radius: 0 14px 14px 0; background: #f7fbf9; }
          .dashboard-competition strong { display: block; margin: .3rem 0; color: var(--club-ink); font-size: .95rem; }
          .dashboard-competition span { color: var(--club-muted); font-size: .78rem; }
          div[data-testid="stButton"] > button { min-height: 3.15rem; border: 1px solid var(--club-line); border-radius: 14px; background: rgba(255,255,255,.92); color: var(--club-ink); font-weight: 700; box-shadow: 0 5px 16px rgba(20,65,51,.045); transition: all .16s ease; }
          div[data-testid="stButton"] > button:hover { border-color: #82b5a2; color: var(--club-green); transform: translateY(-1px); box-shadow: 0 9px 22px rgba(20,65,51,.10); }
          div[data-testid="stExpander"] { border-color: var(--club-line); border-radius: 14px; background: rgba(255,255,255,.72); }
          @media (max-width: 640px) {
            .block-container { padding: .8rem 1rem 3rem; }
            .dashboard-hero { padding: 1.65rem 1.35rem; border-radius: 22px; }
            .dashboard-hero::after { right: .5rem; font-size: 7rem; }
            .dashboard-status-card { min-height: 102px; margin-bottom: .45rem; }
            .dashboard-spotlight { min-height: 0; margin-bottom: .55rem; }
            .dashboard-chart-row { grid-template-columns: 88px 1fr 36px; gap: .45rem; }
          }
        </style>
        <div class="dashboard-hero">
          <div class="dashboard-eyebrow">Happakai Golf Society</div>
          <h1>いい仲間と、<br>いいゴルフを。</h1>
          <p>88会の開催案内から個人成績、歴代の競技結果まで。いつもの情報を、ひとつの場所で。</p>
          <div class="dashboard-hero-badge">⛳ 88会 メンバーズポータル</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_navigation() -> None:
    """主要機能へのショートカット"""
    st.markdown('<div class="dashboard-section-label">メニュー<small>見たい情報を選んでください</small></div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📈  個人成績を見る", key="dashboard_stats", use_container_width=True):
            _navigate("stats")
    with col2:
        if st.button("🏆  競技結果を見る", key="dashboard_results", use_container_width=True):
            _navigate("results")
    with col3:
        if st.button("⚙️  管理メニュー", key="dashboard_admin", use_container_width=True):
            st.session_state.admin_logged_in = False
            _navigate("admin")
    with col4:
        if st.button("↗  ログアウト", key="dashboard_logout", use_container_width=True):
            _logout_user()


def render_dashboard_status(
    scores_df: pd.DataFrame,
    players_df: pd.DataFrame,
    competitions_df: pd.DataFrame,
) -> None:
    """安全なHTMLカードでダッシュボードの概要を表示"""
    valid_scores = scores_df[
        (scores_df["合計スコア"] > 0)
        & (scores_df["アウトスコア"] > 0)
        & (scores_df["インスコア"] > 0)
    ]
    # 大会回数はスコア登録済み件数ではなく、通常コンペIDの最新回を使用する。
    # 100以上は特別・過去データ用IDのため、第◯回の回数には含めない。
    competition_round = 0
    if not competitions_df.empty and "competition_id" in competitions_df.columns:
        regular_ids = []
        for value in competitions_df["competition_id"].tolist():
            try:
                competition_id = int(value)
            except (TypeError, ValueError):
                continue
            if 0 < competition_id < 100:
                regular_ids.append(competition_id)
        if regular_ids:
            competition_round = max(regular_ids)
    latest_date = "データなし"
    if not valid_scores.empty and "日付" in valid_scores.columns:
        latest_values = valid_scores["日付"].dropna()
        if not latest_values.empty:
            latest_date = str(latest_values.max())

    st.markdown('<div class="dashboard-section-label">大会状況<small>88会の記録をひと目で確認</small></div>', unsafe_allow_html=True)
    cards = [
        ("👥", "登録プレイヤー", f"{len(players_df)} 名"),
        ("📝", "記録済みスコア", f"{len(valid_scores)} 件"),
        ("⛳", "開催コンペ", f"第{competition_round}回" if competition_round else "データなし"),
        ("📅", "最新記録", latest_date),
    ]
    columns = st.columns(4)
    for column, (icon, label, value) in zip(columns, cards):
        with column:
            st.markdown(
                f'<div class="dashboard-status-card"><span class="metric-icon">{icon}</span><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>',
                unsafe_allow_html=True,
            )

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
# .envファイルのパスをプロジェクトルートから解決
dotenv_path = os.path.join(get_project_root(), '.env')
load_dotenv(dotenv_path=dotenv_path, override=True)

# Supabase接続情報 - Streamlit secrets と環境変数の両方をサポート
def _get_secret_supabase(*keys: str) -> str:
    try:
        supabase_secrets = st.secrets.get("supabase", {})
        for key in keys:
            value = supabase_secrets.get(key, "")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""
    except Exception:
        return ""


def _get_secret_auth(*keys: str) -> str:
    try:
        auth_secrets = st.secrets.get("auth", {})
        for key in keys:
            value = auth_secrets.get(key, "")
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""
    except Exception:
        return ""


SUPABASE_URL = _get_secret_supabase("url") or os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    _get_secret_supabase("key", "anon_key", "anonKey")
    or os.getenv("SUPABASE_KEY", "").strip()
    or os.getenv("SUPABASE_ANON_KEY", "").strip()
)
SUPABASE_SERVICE_KEY = (
    _get_secret_supabase("service_key", "service_role_key", "serviceKey", "serviceRoleKey")
    or os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
)

# デバッグ: 環境変数の読み込み確認（開発時のみ）
if os.getenv("DEBUG_SUPABASE") == "true":
    st.write("DEBUG: SUPABASE_URL =", "SET" if SUPABASE_URL else "NOT SET")
    st.write("DEBUG: SUPABASE_KEY =", "SET" if SUPABASE_KEY else "NOT SET") 
    st.write("DEBUG: SUPABASE_SERVICE_KEY =", "SET" if SUPABASE_SERVICE_KEY else "NOT SET")

# 接続情報が不足している場合の対応
if not SUPABASE_URL or not SUPABASE_KEY:
    st.warning("""
    Supabase接続情報が見つかりません。以下のいずれかの方法で設定してください：
    
    1. ローカル開発環境: プロジェクトルートに `.env` ファイルを作成し、以下を設定
       ```
       SUPABASE_URL=あなたのSupabaseのURL
       SUPABASE_KEY=あなたのSupabaseのAPIキー
    SUPABASE_SERVICE_KEY=あなたのSupabaseのService Role Key（管理者モードで必要）
       ```
    
    2. Streamlit Cloud: `.streamlit/secrets.toml` ファイルを作成、または Streamlit Cloud の設定画面で以下を設定
       ```
       [supabase]
       url = "あなたのSupabaseのURL"
       key = "あなたのSupabaseのAPIキー"
    service_key = "あなたのSupabaseのService Role Key（管理者モードで必要）"
       ```
    
    3. その他のデプロイ環境: 環境変数 `SUPABASE_URL` / `SUPABASE_KEY`（または `SUPABASE_ANON_KEY`）/ `SUPABASE_SERVICE_KEY`（または `SUPABASE_SERVICE_ROLE_KEY`）を設定
    """)

# ログイン用のパスワード設定
USER_PASSWORD = (
    _get_secret_auth("user_password", "password")
    or os.getenv("USER_PASSWORD", "").strip()
)
ADMIN_PASSWORD = (
    _get_secret_auth("admin_password")
    or os.getenv("ADMIN_PASSWORD", "").strip()
)

if not USER_PASSWORD:
    logging.error("USER_PASSWORD is not configured. User login is disabled.")
if not ADMIN_PASSWORD:
    logging.error("ADMIN_PASSWORD is not configured. Administrator login is disabled.")

# エラーハンドリング用のヘルパー関数
def handle_error(error: Exception, context: str = "", show_details: bool = False):
    """統一されたエラーハンドリング"""
    error_message = f"エラーが発生しました"
    if context:
        error_message += f"（{context}）"
    
    st.error(error_message)
    
    if show_details or os.getenv("DEBUG_MODE") == "true":
        st.exception(error)
    
    # ログに記録（将来的にログファイルに保存）
    logging.error(f"{context}: {str(error)}")

def validate_score(score: int, field_name: str = "スコア") -> bool:
    """スコアの妥当性を検証"""
    if score < 0 or score > 200:
        st.error(f"{field_name}は0から200の範囲で入力してください。")
        return False
    return True

def safe_db_operation(operation, error_context: str = "データベース操作"):
    """データベース操作を安全に実行"""
    try:
        return operation(), None
    except Exception as e:
        handle_error(e, error_context)
        return None, e

# セッション状態を初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"  # デフォルト：ログイン画面

@st.cache_resource
def get_supabase_client():
    """Supabaseクライアントを取得（キャッシュ付き）"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            # 接続テスト
            test_response = supabase.table("players").select("count").limit(1).execute()
            return supabase
        except Exception as e:
            if attempt == max_retries - 1:
                st.error(f"Supabase接続エラー（{max_retries}回試行後）: {str(e)}")
                return None
            # リトライ前に少し待機
            import time
            time.sleep(0.5 * (attempt + 1))
    return None

@st.cache_resource
def get_supabase_admin_client() -> Optional[Client]:
    """管理者（サービスロール）用のSupabaseクライアントを取得（キャッシュ付き）"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        except Exception as e:
            if attempt == max_retries - 1:
                st.error(f"Supabase管理者クライアント接続エラー（{max_retries}回試行後）: {str(e)}")
                return None
            import time
            time.sleep(0.5 * (attempt + 1))
    return None

def fetch_scores():
    """スコアデータをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        # スコアデータを取得
        response = supabase.table("scores").select("*").execute()
        
        # レスポンスの検証
        if not response.data:
            st.warning("スコアデータが空です。データベースに値が存在しないか、RLS設定により取得できない可能性があります。")
            return pd.DataFrame()
        
        scores = response.data
        
        # プレイヤー情報を取得
        players_response = supabase.table("players").select("*").execute()
        
        # プレイヤーレスポンスの検証
        if not players_response.data:
            st.warning("プレイヤーデータが空です。データベースに値が存在しないか、RLS設定により取得できない可能性があります。")
            players = {}
        else:
            players = {
                player["id"]: player["name"]
                for player in players_response.data
                if isinstance(player, dict) and "id" in player and "name" in player
            }
        
        # スコアデータを整形
        scores_list = []
        for score in scores:
            if not isinstance(score, dict):
                continue  # scoreが辞書でない場合はスキップ

            # null/Noneチェックを追加
            out_score_val = score.get("out_score")
            out_score = int(out_score_val) if isinstance(out_score_val, (int, str)) and str(out_score_val).isdigit() else 0
            in_score_val = score.get("in_score")
            in_score = int(in_score_val) if isinstance(in_score_val, (int, str)) and str(in_score_val).isdigit() else 0
            
            # 合計スコアを計算（両方のスコアが有効な場合のみ）
            if out_score > 0 and in_score > 0:
                total_score = out_score + in_score
            else:
                total_score = None  # 無効な場合はNoneを設定
            
            score_dict = {
                "競技ID": score.get("competition_id"),
                "日付": score.get("date"),
                "コース": score.get("course"),
                "プレイヤー名": players.get(score.get("player_id"), "不明"),
                "アウトスコア": out_score,
                "インスコア": in_score,
                "合計スコア": total_score,
                "ハンディキャップ": score.get("handicap"),
                "ネットスコア": score.get("net_score"),
                "順位": score.get("ranking")
            }
            scores_list.append(score_dict)
        
        # データフレームに変換
        result_df = pd.DataFrame(scores_list)
        
        # debug用のprint文を削除
            
        return result_df
    except Exception as e:
        st.error(f"データ取得エラー詳細: {type(e).__name__} - {e}")
        return pd.DataFrame()

def fetch_players():
    """プレイヤーデータをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        # st.info("プレイヤーマスターデータを取得中...") - 表示を削除
        response = supabase.table("players").select("*").execute()
        
        # レスポンスの検証
        if not response.data:
            st.warning("プレイヤーマスターデータが空です。データベースに値が存在しないか、RLS設定により取得できない可能性があります。")
            return pd.DataFrame()
        
        # st.success(f"プレイヤーマスターデータ取得成功: {len(response.data)}件") - 表示を削除
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"プレイヤーデータ取得エラー詳細: {type(e).__name__} - {e}")
        return pd.DataFrame()

def fetch_competitions():
    """コンペデータをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("competitions").select("*").execute()
        
        # レスポンスの検証
        if not response.data:
            st.warning("コンペデータが空です。データベースに値が存在しないか、RLS設定により取得できない可能性があります。")
            return pd.DataFrame()
        
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"コンペデータ取得エラー詳細: {type(e).__name__} - {e}")
        return pd.DataFrame()

def display_aggregations(scores_df):
    st.subheader("データ分析")
    
    st.markdown("### 総合ランキング")
    if "プレイヤー名" in scores_df.columns and "合計スコア" in scores_df.columns:
        # データのフィルタリングを強化
        # 合計スコアが0または異常に低い値、または欠損値のデータを除外
        valid_scores_df = scores_df.dropna(subset=["合計スコア"])
        valid_scores_df = valid_scores_df[
            (valid_scores_df["合計スコア"] >= 50) &  # スコアの最小妥当値（通常は50以上が妥当）
            (valid_scores_df["アウトスコア"] > 0) & 
            (valid_scores_df["インスコア"] > 0)
        ]
        
        # 平均スコアの計算
        overall_ranking = valid_scores_df.groupby("プレイヤー名")["合計スコア"].mean().sort_values(ascending=True)
        
        # プレイヤー数に基づいてグラフの幅を動的に調整
        fig_width = max(10, len(overall_ranking) * 0.5)  # 最小幅は10インチ
        
        plt.figure(figsize=(fig_width, 8))
        ax = plt.gca()
        
        # 垂直棒グラフに変更（横棒ではなく縦棒）
        bars = ax.bar(overall_ranking.index, overall_ranking.values, color='skyblue')
        
        # グラフのタイトルと軸ラベルを設定
        plt.title("プレイヤーごとの平均合計スコア (低いほど良い)", fontsize=14, pad=20)
        plt.ylabel("平均合計スコア", fontsize=12)
        plt.xlabel("プレイヤー名", fontsize=12)
        
        # X軸（プレイヤー名）のフォントサイズと回転を調整
        plt.xticks(rotation=45, ha='right', fontsize=10)
        
        # Y軸（スコア）のフォントサイズと間隔を調整
        plt.yticks(fontsize=10)
        
        # 各バーにスコア値を表示
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, f'{height:.2f}',
                    ha='center', va='bottom', fontsize=9)
        
        # 表示範囲を調整（値のラベルが見切れないように）
        if len(overall_ranking) > 0:
            plt.ylim(0, max(overall_ranking.values) * 1.1)
        
        plt.tight_layout()
        st.pyplot(plt.gcf())
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
    st.pyplot(plt.gcf())

def _legacy_personal_stats_page():
    """個人成績ダッシュボード"""
    st.title("📊 個人成績ダッシュボード")
    
    # データ取得
    scores_df = fetch_scores()
    players_df = fetch_players()
    
    if scores_df.empty or players_df.empty:
        st.warning("データが取得できません。")
        if st.button("← メイン画面へ"):
            st.session_state.page = "main"
            st.rerun()
        return
    
    # プレイヤー選択（参加回数順にソート）
    player_counts = scores_df['プレイヤー名'].value_counts()
    players_list = player_counts.index.tolist()
    
    # セッションにプレイヤー名がない場合は最初のプレイヤー（参加回数最多）を設定
    if 'selected_player_for_stats' not in st.session_state:
        st.session_state.selected_player_for_stats = players_list[0] if players_list else None
    
    selected_player = st.selectbox(
        "プレイヤーを選択",
        players_list,
        index=players_list.index(st.session_state.selected_player_for_stats) if st.session_state.selected_player_for_stats in players_list else 0
    )
    
    st.session_state.selected_player_for_stats = selected_player
    
    # 選択されたプレイヤーのデータをフィルタリング
    player_data = scores_df[scores_df['プレイヤー名'] == selected_player].copy()
    
    if player_data.empty:
        st.info(f"{selected_player} のデータがありません。")
        if st.button("← メイン画面へ"):
            st.session_state.page = "main"
            st.rerun()
        return
    
    # 日付でソート
    player_data = player_data.sort_values(by='日付')  # type: ignore
    
    # === サマリー統計 ===
    st.markdown("---")
    st.subheader(f"🎯 {selected_player} の成績サマリー")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        participation_count = len(player_data)
        st.metric("参加回数", f"{participation_count}回")
    
    with col2:
        avg_net = player_data['ネットスコア'].mean()
        st.metric("平均ネット", f"{avg_net:.1f}")
    
    with col3:
        avg_gross = player_data['合計スコア'].mean()
        st.metric("平均グロス", f"{avg_gross:.1f}")
    
    with col4:
        best_net = player_data['ネットスコア'].min()
        st.metric("ベストネット", f"{best_net:.1f}")
    
    with col5:
        best_gross = player_data['合計スコア'].min()
        st.metric("ベストグロス", f"{best_gross:.0f}")
    
    # === 改善率 ===
    st.markdown("---")
    st.subheader("📈 スコア変化")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**前回比（グロス）**")
        if len(player_data) >= 2:
            latest_gross = player_data.iloc[-1]['合計スコア']
            previous_gross = player_data.iloc[-2]['合計スコア']
            gross_diff = latest_gross - previous_gross
            
            # ゴルフはスコアが低い方が良いので、マイナスが改善
            if gross_diff < 0:
                st.markdown(f"### :green[{gross_diff:.0f}打 改善 🎉]")
                st.caption(f"前回 {previous_gross:.0f} → 今回 {latest_gross:.0f}")
            elif gross_diff > 0:
                st.markdown(f"### :red[+{gross_diff:.0f}打 😞]")
                st.caption(f"前回 {previous_gross:.0f} → 今回 {latest_gross:.0f}")
            else:
                st.markdown(f"### 変化なし ±0")
                st.caption(f"前回 {previous_gross:.0f} → 今回 {latest_gross:.0f}")
        else:
            st.info("前回比較には2回以上の参加が必要です")
    
    with col2:
        st.markdown("**前年同月比（グロス）**")
        # 前年比（同月のデータと比較）
        if len(player_data) >= 2:
            latest_date = player_data.iloc[-1]['日付']
            current_year = latest_date[:4]
            current_month = latest_date[5:7]
            
            # 前年の同月データを取得
            previous_year = str(int(current_year) - 1)
            previous_year_data = player_data[
                (player_data['日付'].str[:4] == previous_year) &
                (player_data['日付'].str[5:7] == current_month)
            ]
            
            if not previous_year_data.empty:
                latest_gross = player_data.iloc[-1]['合計スコア']
                prev_year_gross = previous_year_data.iloc[-1]['合計スコア']
                year_diff = latest_gross - prev_year_gross

                # ゴルフはスコアが低い方が良いので、マイナスが改善
                if year_diff < 0:
                    st.markdown(f"### :green[{year_diff:.0f}打 改善 🎉]")
                    st.caption(f"前年 {prev_year_gross:.0f} → 今回 {latest_gross:.0f}")
                elif year_diff > 0:
                    st.markdown(f"### :red[+{year_diff:.0f}打 😞]")
                    st.caption(f"前年 {prev_year_gross:.0f} → 今回 {latest_gross:.0f}")
                else:
                    st.markdown(f"### 変化なし ±0")
                    st.caption(f"前年 {prev_year_gross:.0f} → 今回 {latest_gross:.0f}")
            else:
                st.info("前年同月のデータがありません")
        else:
            st.info("前年比較には複数年のデータが必要です")
    
    # === スコア推移グラフ ===
    st.markdown("---")
    st.subheader("📉 スコア推移")
    
    # データ検証：異常値チェック
    invalid_data = player_data[
        (player_data['ネットスコア'] <= 0) | 
        (player_data['合計スコア'] <= 0) |
        (player_data['ネットスコア'] > 200) |
        (player_data['合計スコア'] > 200)
    ]
    
    if not invalid_data.empty:
        st.warning(f"⚠️ 異常なスコアデータが{len(invalid_data)}件検出されました（スコア0または200超）")
        with st.expander("異常データの詳細を表示"):
            st.dataframe(invalid_data[['日付', 'コース', 'ネットスコア', '合計スコア', 'ハンディキャップ']])
    
    # 有効なデータのみでグラフ描画
    valid_data = player_data[
        (player_data['ネットスコア'] > 0) & 
        (player_data['合計スコア'] > 0) &
        (player_data['ネットスコア'] <= 200) &
        (player_data['合計スコア'] <= 200)
    ].copy()
    
    if len(valid_data) == 0:
        st.error("有効なスコアデータがありません。")
    else:
        # 折れ線グラフ
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # ネットスコアとグロススコアの推移
        ax.plot(range(len(valid_data)), valid_data['ネットスコア'], 
                marker='o', linestyle='-', linewidth=2, markersize=8, 
                label='ネットスコア', color='#1f77b4')
        ax.plot(range(len(valid_data)), valid_data['合計スコア'], 
                marker='s', linestyle='--', linewidth=2, markersize=6, 
                label='グロススコア', color='#ff7f0e', alpha=0.7)
        
        # 平均線を追加（有効なデータの平均）
        valid_avg_net = valid_data['ネットスコア'].mean()
        valid_avg_gross = valid_data['合計スコア'].mean()
        ax.axhline(y=valid_avg_net, color='#1f77b4', linestyle=':', alpha=0.5, label=f'平均ネット ({valid_avg_net:.1f})')
        ax.axhline(y=valid_avg_gross, color='#ff7f0e', linestyle=':', alpha=0.5, label=f'平均グロス ({valid_avg_gross:.1f})')
        
        # 日付ラベル
        date_labels = [d[:10] for d in valid_data['日付']]
        ax.set_xticks(range(len(valid_data)))
        ax.set_xticklabels(date_labels, rotation=45, ha='right')
        
        ax.set_xlabel("競技日", fontsize=12)
        ax.set_ylabel("スコア", fontsize=12)
        ax.set_title(f"{selected_player} のスコア推移", fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    # === ハンディキャップ履歴 ===
    st.markdown("---")
    st.subheader("🎯 ハンディキャップ履歴")
    
    if len(valid_data) == 0:
        st.error("有効なスコアデータがありません。")
    else:
        fig2, ax2 = plt.subplots(figsize=(12, 5))
        ax2.plot(range(len(valid_data)), valid_data['ハンディキャップ'], 
                marker='D', linestyle='-', linewidth=2, markersize=6, 
                color='#2ca02c')
        
        # 平均HC線
        avg_hc = valid_data['ハンディキャップ'].mean()
        ax2.axhline(y=avg_hc, color='#2ca02c', linestyle=':', alpha=0.5, label=f'平均HC ({avg_hc:.1f})')
        
        # 日付ラベル（valid_dataから取得）
        hc_date_labels = [d[:10] for d in valid_data['日付']]
        ax2.set_xticks(range(len(valid_data)))
        ax2.set_xticklabels(hc_date_labels, rotation=45, ha='right')
        ax2.set_xlabel("競技日", fontsize=12)
        ax2.set_ylabel("ハンディキャップ", fontsize=12)
        ax2.set_title(f"{selected_player} のハンディキャップ推移", fontsize=14, fontweight='bold')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig2)
    
    # === 最近5回の成績 ===
    st.markdown("---")
    st.subheader("📋 最近5回の成績")
    
    recent_5 = player_data.tail(5).copy()
    
    # 表示用にカラムを整理
    display_columns = ['日付', 'コース', '順位', 'ネットスコア', '合計スコア', 
                      'アウトスコア', 'インスコア', 'ハンディキャップ']
    
    recent_5_display = recent_5[display_columns].copy()
    recent_5_display.columns = ['日付', 'コース', '順位', 'ネット', 'グロス', 
                                'OUT', 'IN', 'HC']
    
    # 順位に応じて背景色を変更
    def highlight_rank(row):
        if row['順位'] == 1:
            return ['background-color: #FFD70033'] * len(row)
        elif row['順位'] == 2:
            return ['background-color: #C0C0C033'] * len(row)
        elif row['順位'] == 3:
            return ['background-color: #CD7F3233'] * len(row)
        return [''] * len(row)
    
    styled_recent = recent_5_display.style.apply(highlight_rank, axis=1).format({
        'ネット': '{:.1f}',
        'グロス': '{:.0f}',
        'OUT': '{:.0f}',
        'IN': '{:.0f}',
        'HC': '{:.1f}',
        '順位': '{:.0f}'
    })
    
    st.dataframe(styled_recent, use_container_width=True, hide_index=True)
    
    # === 詳細統計 ===
    st.markdown("---")
    st.subheader("📊 詳細統計")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🏆 入賞回数**")
        top3_count = len(player_data[player_data['順位'] <= 3])
        first_count = len(player_data[player_data['順位'] == 1])
        st.write(f"- 優勝: {first_count}回")
        st.write(f"- 3位以内: {top3_count}回")
        if participation_count > 0:
            st.write(f"- 入賞率: {(top3_count/participation_count*100):.1f}%")
    
    with col2:
        st.markdown("**📈 スコア分布**")
        st.write(f"- 最高ネット: {player_data['ネットスコア'].max():.1f}")
        st.write(f"- 最低ネット: {player_data['ネットスコア'].min():.1f}")
        st.write(f"- 標準偏差: {player_data['ネットスコア'].std():.2f}")
    
    with col3:
        st.markdown("**⛳ コース別平均**")
        course_avg = player_data.groupby('コース')['ネットスコア'].mean().sort_values()
        if len(course_avg) > 0:
            for course, avg in course_avg.head(3).items():
                st.write(f"- {course}: {avg:.1f}")
    
    # ナビゲーションボタン
    st.markdown("---")
    if st.button("← メイン画面へ", key="back_to_main_from_stats"):
        st.session_state.page = "main"
        st.rerun()


def personal_stats_page():
    """個人の記録を、通常コンペの有効スコアだけで見やすく表示する。"""
    scores_df = fetch_scores()
    if scores_df.empty:
        st.warning("個人成績データを取得できません。")
        return

    player_counts = scores_df["プレイヤー名"].dropna().value_counts()
    players_list = player_counts.index.tolist()
    if not players_list:
        st.info("表示できるプレイヤーがいません。")
        return

    if st.session_state.get("selected_player_for_stats") not in players_list:
        st.session_state.selected_player_for_stats = players_list[0]
    selected_player = st.selectbox(
        "プレイヤーを選択",
        players_list,
        index=players_list.index(st.session_state.selected_player_for_stats),
        key="selected_player_for_stats_selector",
    )
    st.session_state.selected_player_for_stats = selected_player

    all_player_data = scores_df[scores_df["プレイヤー名"] == selected_player].copy()
    player_data = _valid_dashboard_scores(scores_df)
    player_data = player_data[player_data["プレイヤー名"] == selected_player].copy()
    if player_data.empty:
        st.markdown(f'<div class="dashboard-hero"><div class="dashboard-eyebrow">PLAYER NOTE</div><h1>{html.escape(selected_player)}</h1><p>通常コンペの詳細スコアがまだ登録されていません。</p></div>', unsafe_allow_html=True)
        return

    player_data["_date"] = pd.to_datetime(player_data["日付"], errors="coerce")
    player_data = player_data.sort_values("_date")
    latest = player_data.iloc[-1]
    previous = player_data.iloc[-2] if len(player_data) >= 2 else None
    latest_gross = float(latest["_gross"])
    previous_gross = float(previous["_gross"]) if previous is not None else None
    gross_delta = latest_gross - previous_gross if previous_gross is not None else None
    regular_competitions = pd.to_numeric(all_player_data["競技ID"], errors="coerce")
    ranked_history = all_player_data[(regular_competitions > 0) & (regular_competitions < 100) & (regular_competitions != 41)]
    ranked_history_ranks = pd.to_numeric(ranked_history["順位"], errors="coerce")
    wins = int((ranked_history_ranks == 1).sum())
    top3 = int((ranked_history_ranks <= 3).sum())
    avg_net = pd.to_numeric(player_data["ネットスコア"], errors="coerce").mean()
    avg_gross = player_data["_gross"].mean()
    best_net_row = player_data.loc[pd.to_numeric(player_data["ネットスコア"], errors="coerce").idxmin()]
    best_gross_row = player_data.loc[player_data["_gross"].idxmin()]

    st.markdown(
        f'<div class="dashboard-hero"><div class="dashboard-eyebrow">PLAYER NOTE</div>'
        f'<h1>{html.escape(selected_player)} さんのゴルフノート</h1>'
        f'<p>通常コンペの詳細スコア {len(player_data)} 回分をもとにした個人成績です。</p></div>',
        unsafe_allow_html=True,
    )

    hero_columns = st.columns(2)
    latest_rank = _dashboard_text(latest.get("順位"))
    delta_label = "初回記録" if gross_delta is None else (f"前回比 {gross_delta:+.0f}打" if gross_delta else "前回比 ±0打")
    with hero_columns[0]:
        st.markdown(
            f'<div class="dashboard-spotlight"><div class="eyebrow">LATEST ROUND</div>'
            f'<strong>⛳ {_dashboard_text(latest.get("合計スコア"))}　<span style="font-size:1rem">{latest_rank}位</span></strong>'
            f'<p>{_dashboard_text(latest.get("日付"))} ・ {html.escape(_dashboard_text(latest.get("コース")))}<br>'
            f'NET {_dashboard_text(latest.get("ネットスコア"))} ・ {delta_label}</p></div>',
            unsafe_allow_html=True,
        )
    with hero_columns[1]:
        st.markdown(
            f'<div class="dashboard-spotlight gold"><div class="eyebrow">PERSONAL BEST</div>'
            f'<strong>⚡ GROSS {_dashboard_text(best_gross_row.get("合計スコア"))}</strong>'
            f'<p>{_dashboard_text(best_gross_row.get("日付"))} ・ {html.escape(_dashboard_text(best_gross_row.get("コース")))}<br>'
            f'ベストネット {_dashboard_text(best_net_row.get("ネットスコア"))}</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="dashboard-section-label">成績サマリー<small>有効スコアの通常コンペを集計</small></div>', unsafe_allow_html=True)
    metrics = [
        ("📝", "出場回数", f"{len(player_data)}回"),
        ("🏆", "優勝回数", f"{wins}回"),
        ("📈", "平均ネット", f"{avg_net:.1f}"),
        ("⛳", "平均グロス", f"{avg_gross:.1f}"),
    ]
    metric_columns = st.columns(4)
    for column, (icon, label, value) in zip(metric_columns, metrics):
        with column:
            st.markdown(f'<div class="dashboard-status-card"><span class="metric-icon">{icon}</span><span>{label}</span><strong>{value}</strong></div>', unsafe_allow_html=True)

    overview_tab, trend_tab, history_tab = st.tabs(["概要", "スコア推移", "成績履歴"])
    with overview_tab:
        overview_columns = st.columns(3)
        with overview_columns[0]:
            top3_rate = top3 / len(player_data) * 100
            st.markdown(f'<div class="dashboard-podium"><div class="medal">🏅</div><strong>入賞 {top3} 回</strong><span>3位以内率 {top3_rate:.1f}%</span></div>', unsafe_allow_html=True)
        with overview_columns[1]:
            st.markdown(f'<div class="dashboard-podium"><div class="medal">🎯</div><strong>NET {_dashboard_text(best_net_row.get("ネットスコア"))}</strong><span>自己ベストネット</span></div>', unsafe_allow_html=True)
        with overview_columns[2]:
            course_average = player_data.groupby("コース")["ネットスコア"].mean().sort_values()
            favourite_course = _dashboard_text(course_average.index[0]) if not course_average.empty else "－"
            favourite_average = _dashboard_text(course_average.iloc[0]) if not course_average.empty else "－"
            st.markdown(f'<div class="dashboard-podium"><div class="medal">🌿</div><strong>{html.escape(favourite_course)}</strong><span>平均ネット {favourite_average}</span></div>', unsafe_allow_html=True)

    with trend_tab:
        fig, ax = plt.subplots(figsize=(12, 5))
        x_values = range(len(player_data))
        net_scores = pd.to_numeric(player_data["ネットスコア"], errors="coerce")
        ax.plot(x_values, net_scores, marker="o", linewidth=2.2, label="ネット", color="#0e6b4f")
        ax.plot(x_values, player_data["_gross"], marker="s", linewidth=1.6, linestyle="--", label="グロス", color="#d3aa4a")
        ax.axhline(net_scores.mean(), color="#0e6b4f", linestyle=":", alpha=.55, label=f"平均ネット {net_scores.mean():.1f}")
        labels = [str(value)[:10] for value in player_data["日付"].tolist()]
        ax.set_xticks(list(x_values))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_ylabel("スコア")
        ax.grid(axis="y", alpha=.22)
        ax.legend()
        fig.tight_layout()
        st.pyplot(fig, width="stretch")

        handicap = pd.to_numeric(player_data["ハンディキャップ"], errors="coerce")
        if handicap.notna().any():
            fig_hc, ax_hc = plt.subplots(figsize=(12, 4))
            ax_hc.plot(x_values, handicap, marker="o", linewidth=2, color="#477fbb")
            ax_hc.set_xticks(list(x_values))
            ax_hc.set_xticklabels(labels, rotation=45, ha="right")
            ax_hc.set_ylabel("ハンディキャップ")
            ax_hc.grid(axis="y", alpha=.22)
            fig_hc.tight_layout()
            st.pyplot(fig_hc, width="stretch")

    with history_tab:
        history = player_data.sort_values("_date", ascending=False).head(10).copy()
        history = history[["日付", "コース", "順位", "ネットスコア", "合計スコア", "アウトスコア", "インスコア", "ハンディキャップ"]]
        history.columns = ["日付", "コース", "順位", "ネット", "グロス", "OUT", "IN", "HC"]
        render_html_table(history, max_rows=10)
        st.caption("直近10回の有効スコアを表示しています。")

    if st.button("← メイン画面へ", key="back_to_main_from_stats_modern"):
        st.session_state.page = "main"
        st.rerun()


def _legacy_competition_results_page():
    """競技結果一覧ページ"""
    st.title("🏆 競技結果一覧")
    
    # データ取得
    scores_df = fetch_scores()
    competitions_df = fetch_competitions()
    
    if scores_df.empty:
        st.warning("競技結果データがありません。")
        if st.button("← メイン画面へ"):
            st.session_state.page = "main"
            st.rerun()
        return
    
    # フィルター用のサイドバー
    st.sidebar.header("🔍 フィルター")
    
    # 年別フィルター
    available_years = sorted(scores_df['日付'].str[:4].unique(), reverse=True)
    selected_year = st.sidebar.selectbox(
        "年を選択",
        ["全て"] + available_years,
        index=0
    )
    
    # 月別フィルター
    if selected_year != "全て":
        filtered_by_year = scores_df[scores_df['日付'].str.startswith(selected_year)]
        available_months = sorted(filtered_by_year['日付'].str[5:7].unique())
        available_months = [m for m in available_months if m]  # 空文字列を除外
    else:
        available_months = sorted(scores_df['日付'].str[5:7].unique())
        available_months = [m for m in available_months if m]  # 空文字列を除外
    
    selected_month = st.sidebar.selectbox(
        "月を選択",
        ["全て"] + available_months,
        index=0
    )
    
    # コース別フィルター
    available_courses = sorted(scores_df['コース'].unique())
    selected_course = st.sidebar.selectbox(
        "コースを選択",
        ["全て"] + available_courses,
        index=0
    )
    
    # フィルタリング適用
    filtered_df = scores_df.copy()
    
    if selected_year != "全て":
        filtered_df = filtered_df[filtered_df['日付'].str.startswith(selected_year)]
    
    if selected_month != "全て":
        filtered_df = filtered_df[filtered_df['日付'].str[5:7] == selected_month]
    
    if selected_course != "全て":
        filtered_df = filtered_df[filtered_df['コース'] == selected_course]
    
    # 競技ごとにグループ化
    competitions = filtered_df.groupby('競技ID')
    
    if len(competitions) == 0:
        st.info("選択した条件に一致する競技結果がありません。")
    else:
        st.success(f"📊 {len(competitions)}件の競技結果が見つかりました")
        
        # 競技ごとに表示
        for comp_id, comp_data in competitions:
            comp_data = comp_data.sort_values('順位')
            
            # 競技情報を取得
            date = comp_data.iloc[0]['日付'] if '日付' in comp_data.columns else "不明"
            course = comp_data.iloc[0]['コース'] if 'コース' in comp_data.columns else "不明"
            
            # 展開可能なセクションで表示
            with st.expander(f"📅 競技ID: {comp_id} - {date} ({course})", expanded=False):
                # 表彰台表示（上位3名）
                st.markdown("### 🏅 表彰台")
                
                top_3 = comp_data.head(3)
                
                if len(top_3) >= 1:
                    cols = st.columns(len(top_3))

                    medals = ["🥇", "🥈", "🥉"]
                    colors = ["#FFD700", "#C0C0C0", "#CD7F32"]

                    for idx, (_, row) in enumerate(top_3.iterrows()):
                        with cols[idx]:
                            st.markdown(
                                f"""
                                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, {colors[idx]}22, {colors[idx]}11); border-radius: 10px; border: 2px solid {colors[idx]};">
                                    <div style="font-size: 48px;">{medals[idx]}</div>
                                    <div style="font-size: 20px; font-weight: bold; margin: 10px 0;">{row['プレイヤー名']}</div>
                                    <div style="font-size: 16px; color: #666;">ネット: <strong>{row['ネットスコア']:.1f}</strong></div>
                                    <div style="font-size: 14px; color: #888;">グロス: {row.get('合計スコア', 0):.0f}</div>
                                    <div style="font-size: 14px; color: #888;">HC: {row['ハンディキャップ']:.1f}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                
                st.markdown("---")
                
                # 全順位表
                st.markdown("### 📋 完全順位表")
                
                # 表示用データフレームを作成
                display_df = comp_data[[
                    '順位', 'プレイヤー名', '合計スコア', 
                    'アウトスコア', 'インスコア', 
                    'ハンディキャップ', 'ネットスコア'
                ]].copy()
                
                # カラム名を整形
                display_df.columns = [
                    '順位', 'プレイヤー名', 'グロス', 
                    'OUT', 'IN', 
                    'HC', 'ネット'
                ]
                
                # スタイル適用
                def highlight_top3(row):
                    if row['順位'] == 1:
                        return ['background-color: #FFD70033'] * len(row)
                    elif row['順位'] == 2:
                        return ['background-color: #C0C0C033'] * len(row)
                    elif row['順位'] == 3:
                        return ['background-color: #CD7F3233'] * len(row)
                    return [''] * len(row)
                
                styled_df = display_df.style.apply(highlight_top3, axis=1).format({
                    'グロス': '{:.0f}',
                    'OUT': '{:.0f}',
                    'IN': '{:.0f}',
                    'HC': '{:.1f}',
                    'ネット': '{:.1f}',
                    '順位': '{:.0f}'
                })
                
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # 統計情報
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("参加人数", f"{len(comp_data)}名")
                with col2:
                    st.metric("平均ネット", f"{comp_data['ネットスコア'].mean():.1f}")
                with col3:
                    st.metric("平均グロス", f"{comp_data['合計スコア'].mean():.1f}")
                with col4:
                    st.metric("平均HC", f"{comp_data['ハンディキャップ'].mean():.1f}")
    
    # ナビゲーションボタン
    st.markdown("---")
    if st.button("← メイン画面へ", key="back_to_main_from_results"):
        st.session_state.page = "main"
        st.rerun()


def competition_results_page():
    """競技を一つずつ選び、順位とスコアを見やすく確認する。"""
    scores_df = fetch_scores()
    if scores_df.empty:
        st.warning("競技結果データがありません。")
        return

    results = scores_df.copy()
    results["_competition_id"] = pd.to_numeric(results["競技ID"], errors="coerce")
    results["_date_text"] = results["日付"].fillna("").astype(str)
    results["_course_text"] = results["コース"].fillna("コース未設定").astype(str)

    filter_columns = st.columns([1, 1, 1.3])
    years = sorted([year for year in results["_date_text"].str[:4].unique() if year], reverse=True)
    with filter_columns[0]:
        selected_year = st.selectbox("開催年", ["すべて"] + years, key="results_year_filter")
    with filter_columns[1]:
        courses = sorted(results["_course_text"].unique().tolist())
        selected_course = st.selectbox("コース", ["すべて"] + courses, key="results_course_filter")
    with filter_columns[2]:
        include_archive = st.checkbox("特別・過去データも表示", value=False, key="results_include_archive")

    if not include_archive:
        results = results[
            (results["_competition_id"] > 0)
            & (results["_competition_id"] < 100)
            & (results["_competition_id"] != 41)
        ]
    if selected_year != "すべて":
        results = results[results["_date_text"].str.startswith(selected_year)]
    if selected_course != "すべて":
        results = results[results["_course_text"] == selected_course]

    if results.empty:
        st.info("選択した条件に一致する競技結果がありません。")
        return

    competition_index = (
        results.groupby("_competition_id", as_index=False)
        .agg({"_date_text": "max", "_course_text": "first"})
        .sort_values(["_date_text", "_competition_id"], ascending=False)
        .reset_index(drop=True)
    )
    selected_competition = st.selectbox(
        "競技を選択",
        competition_index.to_dict("records"),
        format_func=lambda item: f'第{int(item["_competition_id"])}回　{item["_date_text"]}　{item["_course_text"]}',
        key="results_competition_selector",
    )
    competition_id = selected_competition["_competition_id"]
    competition_rows = results[results["_competition_id"] == competition_id].copy()
    rankings = pd.to_numeric(competition_rows["順位"], errors="coerce")
    competition_rows["_ranking"] = rankings
    competition_rows = competition_rows.sort_values(["_ranking", "プレイヤー名"], na_position="last")
    detailed_rows = _valid_dashboard_scores(competition_rows)

    participants = len(competition_rows)
    valid_participants = len(detailed_rows)
    average_net = pd.to_numeric(detailed_rows.get("ネットスコア"), errors="coerce").mean() if not detailed_rows.empty else None
    average_gross = detailed_rows["_gross"].mean() if not detailed_rows.empty else None
    st.markdown(
        f'<div class="dashboard-hero"><div class="dashboard-eyebrow">COMPETITION RESULT</div>'
        f'<h1>第{int(competition_id)}回　競技結果</h1>'
        f'<p>{_dashboard_text(selected_competition["_date_text"])} ・ {html.escape(selected_competition["_course_text"])}<br>'
        f'順位登録 {participants} 名 / 詳細スコア登録 {valid_participants} 名</p></div>',
        unsafe_allow_html=True,
    )

    summary_cards = [
        ("👥", "順位登録人数", f"{participants}名"),
        ("📊", "平均ネット", f"{average_net:.1f}" if pd.notna(average_net) else "－"),
        ("⛳", "平均グロス", f"{average_gross:.1f}" if pd.notna(average_gross) else "－"),
        ("📝", "詳細スコア", f"{valid_participants}名"),
    ]
    summary_columns = st.columns(4)
    for column, (icon, label, value) in zip(summary_columns, summary_cards):
        with column:
            st.markdown(f'<div class="dashboard-status-card"><span class="metric-icon">{icon}</span><span>{label}</span><strong>{value}</strong></div>', unsafe_allow_html=True)

    st.markdown('<div class="dashboard-section-label">表彰台<small>順位が登録されている上位3名</small></div>', unsafe_allow_html=True)
    podium_rows = competition_rows[competition_rows["_ranking"].notna()].head(3)
    podium_columns = st.columns(3)
    medals = ("🥇", "🥈", "🥉")
    for index, column in enumerate(podium_columns):
        with column:
            if index < len(podium_rows):
                row = podium_rows.iloc[index]
                name = html.escape(_dashboard_text(row.get("プレイヤー名")))
                net = _dashboard_text(row.get("ネットスコア"))
                gross = _dashboard_text(row.get("合計スコア"))
                st.markdown(f'<div class="dashboard-podium"><div class="medal">{medals[index]}</div><strong>{name} さん</strong><span>NET {net} ・ GROSS {gross}</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="dashboard-podium"><div class="medal">⛳</div><strong>順位未登録</strong><span>結果を入力すると表示されます</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="dashboard-section-label">完全順位表<small>詳細スコア未登録の順位記録も含みます</small></div>', unsafe_allow_html=True)
    result_columns = ["順位", "プレイヤー名", "合計スコア", "アウトスコア", "インスコア", "ハンディキャップ", "ネットスコア"]
    result_table = competition_rows[result_columns].copy()
    result_table.columns = ["順位", "プレイヤー名", "グロス", "OUT", "IN", "HC", "ネット"]
    render_html_table(result_table, max_rows=200)

    if not detailed_rows.empty:
        st.caption("平均値は、OUT/INが入力された詳細スコアのみで計算しています。")
    elif not competition_rows.empty:
        st.caption("この競技には詳細スコアが登録されていないため、平均スコアは表示していません。")

    if st.button("← メイン画面へ", key="back_to_main_from_results_modern"):
        st.session_state.page = "main"
        st.rerun()


def get_winner_count_ranking(scores_df: pd.DataFrame) -> pd.DataFrame:
    """通常コンペの順位1位記録から優勝回数を集計する。"""
    required_columns = {"競技ID", "順位", "プレイヤー名"}
    if scores_df.empty or not required_columns.issubset(scores_df.columns):
        return pd.DataFrame(columns=["プレイヤー名", "優勝回数"])

    competition_ids = pd.to_numeric(scores_df["競技ID"], errors="coerce")
    rankings = pd.to_numeric(scores_df["順位"], errors="coerce")
    # 過去データには詳細スコアが未入力でも順位が登録された回があるため、
    # 優勝回数はスコアの有無ではなく順位のみを正とする。
    # 第41回はテスト用データのため、ベストスコアと同様に集計対象外とする。
    valid_scores = scores_df[
        (competition_ids > 0)
        & (competition_ids < 100)
        & (competition_ids != 41)
        & (rankings == 1)
        & scores_df["プレイヤー名"].notna()
    ]
    return (
        valid_scores.groupby("プレイヤー名")
        .size()
        .reset_index(name="優勝回数")
        .sort_values(by=["優勝回数", "プレイヤー名"], ascending=[False, True])
        .reset_index(drop=True)
    )


def display_winner_count_ranking(scores_df):
    st.subheader("優勝回数ランキング")

    ranking_type = st.radio("ランキングの種類を選択してください:", ["トータルランキング", "年度ランキング"])

    if ranking_type == "年度ランキング":
        available_years = scores_df['日付'].str[:4].unique()
        year = st.selectbox("表示する年度を選択してください:", sorted(available_years))
        scores_df = scores_df[scores_df['日付'].str.startswith(year)]

    rank_one_winners = get_winner_count_ranking(scores_df)

    render_html_table(rank_one_winners, max_rows=200)
    st.caption("通常コンペ（ID 1〜99・第41回を除く）の順位1位記録を集計しています。")


def render_html_table(df: pd.DataFrame, max_rows: int = 200) -> None:
    """ブラウザ互換性重視のシンプルなHTMLテーブル描画"""
    if df.empty:
        st.info("表示するデータがありません。")
        return

    view_df = df.head(max_rows).reset_index(drop=True)

    headers = "".join(
        f"<th style='padding:8px;border:1px solid #ddd;background:#f6f8fa;text-align:left;'>{html.escape(str(col))}</th>"
        for col in view_df.columns
    )

    body_rows = []
    for _, row in view_df.iterrows():
        cells = []
        for value in row.tolist():
            text = "" if pd.isna(value) else str(value)
            cells.append(f"<td style='padding:8px;border:1px solid #ddd;'>{html.escape(text)}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    table_html = f"""
    <div style='overflow-x:auto;'>
      <table style='border-collapse:collapse;width:100%;font-size:14px;'>
        <thead><tr>{headers}</tr></thead>
        <tbody>{''.join(body_rows)}</tbody>
      </table>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)

def sanitize_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """表示用に不要なインデックス由来カラムを除去"""
    drop_cols = []
    for col in df.columns:
        col_str = str(col).strip().lower()
        if col_str in ("", "index", "unnamed: 0") or col_str.startswith("unnamed"):
            drop_cols.append(col)
    if drop_cols:
        return df.drop(columns=drop_cols, errors="ignore")
    return df


def _valid_dashboard_scores(scores_df: pd.DataFrame) -> pd.DataFrame:
    """グロス・出場回数表示に使える、詳細スコア登録済みの通常コンペを返す。"""
    required_columns = {"競技ID", "アウトスコア", "インスコア", "合計スコア", "プレイヤー名"}
    if scores_df.empty or not required_columns.issubset(scores_df.columns):
        return pd.DataFrame()

    valid_scores = scores_df.copy()
    valid_scores["_competition_id"] = pd.to_numeric(valid_scores["競技ID"], errors="coerce")
    valid_scores["_gross"] = pd.to_numeric(valid_scores["合計スコア"], errors="coerce")
    valid_scores["_out"] = pd.to_numeric(valid_scores["アウトスコア"], errors="coerce")
    valid_scores["_in"] = pd.to_numeric(valid_scores["インスコア"], errors="coerce")
    return valid_scores[
        (valid_scores["_competition_id"] > 0)
        & (valid_scores["_competition_id"] < 100)
        & (valid_scores["_competition_id"] != 41)
        & (valid_scores["_out"] > 0)
        & (valid_scores["_in"] > 0)
        & (valid_scores["_gross"] > 0)
        & valid_scores["プレイヤー名"].notna()
    ].copy()


def get_best_gross_ranking(valid_scores: pd.DataFrame, unique_players: bool = False) -> pd.DataFrame:
    """有効な詳細スコアからベスグロ上位10件を返す。"""
    if valid_scores.empty:
        return pd.DataFrame()

    ranking = valid_scores.sort_values(
        ["_gross", "日付", "_competition_id", "プレイヤー名"],
        ascending=[True, False, False, True],
        na_position="last",
    ).copy()
    if unique_players:
        # 同スコアならより新しい記録を採用する（上の並び順を維持）。
        ranking = ranking.drop_duplicates(subset=["プレイヤー名"], keep="first")
    return ranking.head(10).reset_index(drop=True)


def _dashboard_text(value: Any, fallback: str = "－") -> str:
    if pd.isna(value) or value is None or str(value).strip() == "":
        return fallback
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def render_dashboard_highlights(scores_df: pd.DataFrame) -> None:
    """トップページ用の主要記録・ランキングを表示する。"""
    valid_scores = _valid_dashboard_scores(scores_df)
    if valid_scores.empty:
        return

    st.markdown('<div class="dashboard-section-label">88会 ハイライト<small>記録から見る、みんなのゴルフ</small></div>', unsafe_allow_html=True)

    latest_scores = valid_scores.sort_values(["日付", "_competition_id"], ascending=False)
    latest_competition_id = latest_scores.iloc[0]["_competition_id"]
    latest_competition = valid_scores[valid_scores["_competition_id"] == latest_competition_id]
    latest_date = _dashboard_text(latest_competition.iloc[0].get("日付"))
    latest_course = html.escape(_dashboard_text(latest_competition.iloc[0].get("コース")))
    latest_ranking = pd.to_numeric(latest_competition.get("順位"), errors="coerce")
    latest_winners = latest_competition[latest_ranking == 1]
    if latest_winners.empty:
        winner_name = "順位未登録"
        winner_detail = "最新コンペの順位を登録すると表示されます"
    else:
        winner = latest_winners.sort_values("ネットスコア", na_position="last").iloc[0]
        winner_name = html.escape(_dashboard_text(winner.get("プレイヤー名")))
        winner_detail = f'NET {_dashboard_text(winner.get("ネットスコア"))} / GROSS {_dashboard_text(winner.get("合計スコア"))}'

    best_gross = valid_scores.sort_values("_gross", ascending=True).iloc[0]
    best_name = html.escape(_dashboard_text(best_gross.get("プレイヤー名")))
    best_detail = (
        f'{_dashboard_text(best_gross.get("日付"))} ・ '
        f'{html.escape(_dashboard_text(best_gross.get("コース")))}'
    )

    spotlight_columns = st.columns(2)
    with spotlight_columns[0]:
        st.markdown(
            f'<div class="dashboard-spotlight"><div class="eyebrow">LATEST CHAMPION</div>'
            f'<strong>🏆 {winner_name}</strong><p>第{int(latest_competition_id)}回 ・ {latest_date} ・ {latest_course}<br>{winner_detail}</p></div>',
            unsafe_allow_html=True,
        )
    with spotlight_columns[1]:
        st.markdown(
            f'<div class="dashboard-spotlight gold"><div class="eyebrow">BEST GROSS</div>'
            f'<strong>⚡ {best_name}　{_dashboard_text(best_gross.get("合計スコア"))}</strong>'
            f'<p>{best_detail}<br>OUT {_dashboard_text(best_gross.get("アウトスコア"))} / IN {_dashboard_text(best_gross.get("インスコア"))}</p></div>',
            unsafe_allow_html=True,
        )

    winners = get_winner_count_ranking(scores_df).head(3)
    appearances = (
        valid_scores.groupby("プレイヤー名")["_competition_id"]
        .nunique()
        .sort_values(ascending=False)
        .head(5)
    )
    st.markdown('<div class="dashboard-section-label">歴代ランキング<small>優勝と出場の記録</small></div>', unsafe_allow_html=True)
    podium_columns = st.columns(3)
    medals = ("🥇", "🥈", "🥉")
    for index, column in enumerate(podium_columns):
        with column:
            if index < len(winners):
                row = winners.iloc[index]
                name = html.escape(_dashboard_text(row["プレイヤー名"]))
                wins = _dashboard_text(row["優勝回数"])
                st.markdown(f'<div class="dashboard-podium"><div class="medal">{medals[index]}</div><strong>{name}</strong><span>優勝 {wins} 回</span></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="dashboard-podium"><div class="medal">⛳</div><strong>記録なし</strong><span>優勝記録を待っています</span></div>', unsafe_allow_html=True)

    if not appearances.empty:
        appearance_rows = "".join(
            f'<div class="dashboard-chart-row"><div class="dashboard-chart-name">{rank}. {html.escape(_dashboard_text(name))}</div>'
            f'<div class="dashboard-chart-track"><div class="dashboard-chart-fill" style="width:{max(8, round(count / appearances.iloc[0] * 100))}%"></div></div>'
            f'<div class="dashboard-chart-value">{int(count)}回</div></div>'
            for rank, (name, count) in enumerate(appearances.items(), start=1)
        )
        st.markdown('<div class="dashboard-section-label">出場回数ランキング<small>詳細スコアが登録された通常コンペを集計</small></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="dashboard-chart">{appearance_rows}</div>', unsafe_allow_html=True)

    st.markdown('<div class="dashboard-section-label">ベスグロランキング<small>詳細スコアが登録された通常コンペを集計</small></div>', unsafe_allow_html=True)
    gross_mode = st.radio(
        "表示方法",
        ("純粋なトップ10", "ユニークなトップ10"),
        horizontal=True,
        key="dashboard_best_gross_mode",
        label_visibility="collapsed",
    )
    best_gross_rows = get_best_gross_ranking(
        valid_scores,
        unique_players=(gross_mode == "ユニークなトップ10"),
    )
    gross_ranking_rows = "".join(
        f'<div class="dashboard-chart-row"><div class="dashboard-chart-name">{rank}. {html.escape(_dashboard_text(row.get("プレイヤー名")))}</div>'
        f'<div class="dashboard-chart-track"><div class="dashboard-chart-fill" style="width:{max(8, round(float(row["_gross"]) / float(best_gross_rows["_gross"].max()) * 100))}%"></div></div>'
        f'<div class="dashboard-chart-value">{_dashboard_text(row.get("合計スコア"))}</div></div>'
        for rank, (_, row) in enumerate(best_gross_rows.iterrows(), start=1)
    )
    if gross_ranking_rows:
        st.markdown(f'<div class="dashboard-chart">{gross_ranking_rows}</div>', unsafe_allow_html=True)

    recent_competitions = (
        valid_scores.groupby("_competition_id", as_index=False)
        .agg({"日付": "max", "コース": "first"})
        .sort_values(["日付", "_competition_id"], ascending=False)
        .head(3)
    )
    st.markdown('<div class="dashboard-section-label">最近のコンペ<small>直近3回の開催記録</small></div>', unsafe_allow_html=True)
    recent_columns = st.columns(3)
    for index, (_, competition) in enumerate(recent_competitions.iterrows()):
        competition_id = competition["_competition_id"]
        rows = valid_scores[valid_scores["_competition_id"] == competition_id]
        rankings = pd.to_numeric(rows.get("順位"), errors="coerce")
        winner_rows = rows[rankings == 1]
        winner = html.escape(_dashboard_text(winner_rows.iloc[0].get("プレイヤー名"))) if not winner_rows.empty else "順位未登録"
        with recent_columns[index]:
            st.markdown(
                f'<div class="dashboard-competition"><span>第{int(competition_id)}回 ・ {_dashboard_text(competition.get("日付"))}</span>'
                f'<strong>{html.escape(_dashboard_text(competition.get("コース")))}</strong><span>🏆 {winner}</span></div>',
                unsafe_allow_html=True,
            )


def render_main_safe_mode(scores_df: pd.DataFrame) -> None:
    """DataFrame/グラフを使わずに、カードUIで主要情報を表示する"""
    # 優勝回数ランキング（HTMLカード表示）
    st.markdown('<div class="dashboard-section-label">優勝回数ランキング<small>歴代チャンピオンの記録</small></div>', unsafe_allow_html=True)
    rank_one_winners = get_winner_count_ranking(scores_df).head(20)
    if rank_one_winners.empty:
        st.caption("ランキング対象のデータがありません。")
    else:
        max_wins = max(int(value) for value in rank_one_winners["優勝回数"].tolist())
        chart_rows = []
        for rank, (_, row) in enumerate(rank_one_winners.head(5).iterrows(), start=1):
            name = html.escape(str(row["プレイヤー名"]))
            wins = int(row["優勝回数"])
            width = max(8, round(wins / max_wins * 100))
            chart_rows.append(
                f'<div class="dashboard-chart-row"><div class="dashboard-chart-name">{rank}. {name}</div>'
                f'<div class="dashboard-chart-track"><div class="dashboard-chart-fill" style="width:{width}%"></div></div>'
                f'<div class="dashboard-chart-value">{wins}回</div></div>'
            )
        st.markdown(f'<div class="dashboard-chart">{"".join(chart_rows)}</div>', unsafe_allow_html=True)

        rank_columns = st.columns(2)
        for idx, (_, row) in enumerate(rank_one_winners.iterrows()):
            medal = ("🥇", "🥈", "🥉")[idx] if idx < 3 else f"{idx + 1}位"
            name = html.escape(str(row["プレイヤー名"]))
            wins = int(row["優勝回数"])
            with rank_columns[idx % 2]:
                st.markdown(
                    f'<div class="dashboard-status-card"><span>{medal}</span><strong>{name}</strong><span>優勝 {wins} 回</span></div>',
                    unsafe_allow_html=True,
                )

    # 過去データ（最新12件をカード表示）
    st.markdown('<div class="dashboard-section-label">最近の記録<small>直近のスコアを12件表示</small></div>', unsafe_allow_html=True)
    past_data_df = scores_df.copy()
    past_data_df = past_data_df[
        (past_data_df["合計スコア"] > 0)
        & (past_data_df["アウトスコア"] > 0)
        & (past_data_df["インスコア"] > 0)
    ]
    past_data_df = past_data_df.sort_values(by=["日付", "順位"], ascending=[False, True])
    preferred_cols = [
        "順位", "競技ID", "日付", "コース", "プレイヤー名",
        "アウトスコア", "インスコア", "合計スコア", "ハンディキャップ", "ネットスコア",
    ]
    existing_cols = [col for col in preferred_cols if col in past_data_df.columns]
    past_data_df = past_data_df[existing_cols].head(12).reset_index(drop=True)
    past_data_df = sanitize_display_df(past_data_df)
    if past_data_df.empty:
        st.caption("表示できる過去データがありません。")
        return

    def format_number(value: Any) -> str:
        if pd.isna(value):
            return "-"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    record_columns = st.columns(2)
    for idx, (_, row) in enumerate(past_data_df.iterrows()):
        date = html.escape(str(row.get("日付", "")))
        course = html.escape(str(row.get("コース", "")))
        player = html.escape(str(row.get("プレイヤー名", "")))
        ranking = format_number(row.get("順位", "-"))
        total = format_number(row.get("合計スコア", "-"))
        out_score = format_number(row.get("アウトスコア", "-"))
        in_score = format_number(row.get("インスコア", "-"))
        with record_columns[idx % 2]:
            st.markdown(
                f"""
                <div class="dashboard-status-card" style="margin-bottom:.65rem;">
                  <span>{date}　{course}</span>
                  <strong>{player}</strong>
                  <span>{ranking}位 ・ TOTAL {total}　（OUT {out_score} / IN {in_score}）</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


RESTORE_TABLES = ["competitions", "players", "participants", "scores", "announcements"]


def _resolve_backup_dir() -> str:
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backup'))
    if not os.path.exists(backup_dir):
        parent_backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backup'))
        if os.path.exists(parent_backup_dir):
            return parent_backup_dir
        os.makedirs(backup_dir)
    return backup_dir


def _fetch_backup_payload(supabase: Client) -> Dict[str, Any]:
    competitions_response = supabase.table("competitions").select("*").execute()
    players_response = supabase.table("players").select("*").execute()
    participants_response = supabase.table("participants").select("*").execute()
    scores_response = supabase.table("scores").select("*").execute()
    announcements_response = supabase.table("announcements").select("*").execute()

    return {
        "competitions": competitions_response.data or [],
        "players": players_response.data or [],
        "participants": participants_response.data or [],
        "scores": scores_response.data or [],
        "announcements": announcements_response.data or [],
    }


def _collect_table_counts(supabase: Client) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for table in RESTORE_TABLES:
        primary_key = "competition_id" if table == "competitions" else "id"
        response = supabase.table(table).select(primary_key, count="exact").limit(1).execute()  # type: ignore[arg-type]
        counts[table] = int(response.count or 0)
    return counts


def _save_pre_restore_snapshot(supabase: Client) -> str:
    backup_dir = _resolve_backup_dir()
    snapshot_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    snapshot_payload = _fetch_backup_payload(supabase)
    snapshot_payload["backup_date"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    snapshot_payload["backup_type"] = "pre_restore"
    snapshot_file = os.path.join(backup_dir, f"pre_restore_{snapshot_id}.json")

    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(snapshot_payload, f, ensure_ascii=False, indent=2)

    # 自動保持ポリシー（既定30日）で古いpre_restoreを整理
    retention_days = _get_pre_restore_retention_days()
    try:
        deleted_files = _cleanup_old_pre_restore_snapshots(backup_dir, retention_days)
        if deleted_files:
            _append_snapshot_cleanup_log("自動保持整理", deleted_files, "system-auto")
            st.info(f"自動保持ポリシーにより古いスナップショットを {len(deleted_files)} 件削除しました。")
    except Exception:
        pass

    return snapshot_file


def _get_pre_restore_retention_days() -> int:
    raw_value = os.getenv("PRE_RESTORE_RETENTION_DAYS", "30").strip()
    try:
        days = int(raw_value)
        return max(1, days)
    except Exception:
        return 30


def _cleanup_old_pre_restore_snapshots(backup_dir: str, retention_days: int) -> List[str]:
    cutoff_ts = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
    deleted_files: List[str] = []
    for file_name in os.listdir(backup_dir):
        if not (file_name.startswith("pre_restore_") and file_name.endswith(".json")):
            continue
        file_path = os.path.join(backup_dir, file_name)
        if not os.path.isfile(file_path):
            continue
        if os.path.getmtime(file_path) < cutoff_ts:
            os.remove(file_path)
            deleted_files.append(file_name)
    return deleted_files


def _get_snapshot_cleanup_log_path() -> str:
    return os.path.join(_resolve_backup_dir(), "snapshot_cleanup_log.json")


def _get_restore_report_log_path() -> str:
    return os.path.join(_resolve_backup_dir(), "restore_report_log.json")


def _get_snapshot_cleanup_log_retention_days() -> int:
    raw_value = os.getenv("SNAPSHOT_CLEANUP_LOG_RETENTION_DAYS", "90").strip()
    try:
        days = int(raw_value)
        return max(1, days)
    except Exception:
        return 90


def _get_restore_report_log_retention_days() -> int:
    raw_value = os.getenv("RESTORE_REPORT_LOG_RETENTION_DAYS", "180").strip()
    try:
        days = int(raw_value)
        return max(1, days)
    except Exception:
        return 180


def _prune_log_entries_by_retention(logs: List[Dict[str, Any]], retention_days: int) -> List[Dict[str, Any]]:
    cutoff_ts = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
    pruned: List[Dict[str, Any]] = []
    for item in logs:
        if not isinstance(item, dict):
            continue
        dt_str = item.get("実行日時")
        if not isinstance(dt_str, str):
            continue
        try:
            ts = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').timestamp()
        except Exception:
            continue
        if ts >= cutoff_ts:
            pruned.append(item)
    return pruned


def _load_snapshot_cleanup_logs() -> List[Dict[str, Any]]:
    log_path = _get_snapshot_cleanup_log_path()
    if not os.path.exists(log_path):
        return []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            logs = [item for item in data if isinstance(item, dict)]
            logs = _prune_log_entries_by_retention(logs, _get_snapshot_cleanup_log_retention_days())
            if len(logs) > 200:
                logs = logs[-200:]
            return logs
    except Exception:
        return []
    return []


def _save_snapshot_cleanup_logs(logs: List[Dict[str, Any]]) -> None:
    logs = _prune_log_entries_by_retention(logs, _get_snapshot_cleanup_log_retention_days())
    if len(logs) > 200:
        logs = logs[-200:]
    log_path = _get_snapshot_cleanup_log_path()
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def _load_restore_report_logs() -> List[Dict[str, Any]]:
    log_path = _get_restore_report_log_path()
    if not os.path.exists(log_path):
        return []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            logs = [item for item in data if isinstance(item, dict)]
            logs = _prune_log_entries_by_retention(logs, _get_restore_report_log_retention_days())
            return logs[-1000:] if len(logs) > 1000 else logs
    except Exception:
        return []
    return []


def _save_restore_report_logs(logs: List[Dict[str, Any]]) -> None:
    logs = _prune_log_entries_by_retention(logs, _get_restore_report_log_retention_days())
    if len(logs) > 1000:
        logs = logs[-1000:]
    log_path = _get_restore_report_log_path()
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def _append_restore_report_log(report_rows: List[Dict[str, Any]]) -> None:
    logs = _load_restore_report_logs()
    logs.extend(report_rows)
    _save_restore_report_logs(logs)


def _append_snapshot_cleanup_log(operation: str, affected_files: List[str], operator_name: str = "") -> None:
    logs = st.session_state.get("snapshot_cleanup_logs")
    if not isinstance(logs, list):
        logs = _load_snapshot_cleanup_logs()
    logs.append(
        {
            "実行日時": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "作業者": operator_name.strip() or "未入力",
            "操作": operation,
            "対象件数": len(affected_files),
            "対象ファイル": "\n".join(affected_files) if affected_files else "(なし)",
        }
    )
    # メモリ肥大化を防ぐため最新200件に制限
    if len(logs) > 200:
        logs = logs[-200:]
    st.session_state["snapshot_cleanup_logs"] = logs
    _save_snapshot_cleanup_logs(logs)


def _render_snapshot_cleanup_log_download() -> None:
    logs = st.session_state.get("snapshot_cleanup_logs")
    if not isinstance(logs, list):
        logs = _load_snapshot_cleanup_logs()
        st.session_state["snapshot_cleanup_logs"] = logs
    if not logs:
        return
    st.write("### スナップショット整理ログ")
    log_df = pd.DataFrame(logs)
    st.dataframe(log_df.tail(20), use_container_width=True, hide_index=True)
    log_ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    st.download_button(
        label="整理ログをCSVダウンロード",
        data=log_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"snapshot_cleanup_log_{log_ts}.csv",
        mime="text/csv",
        key=f"snapshot_cleanup_log_csv_{log_ts}",
    )


def _show_restore_count_report(
    before_counts: Dict[str, int],
    expected_counts: Dict[str, int],
    after_counts: Dict[str, int],
    restore_source: str,
    backup_identifier: str,
    operator_name: str,
) -> None:
    report_rows = []
    executed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for table in RESTORE_TABLES:
        expected = expected_counts.get(table, 0)
        after = after_counts.get(table, 0)
        delta = after - expected
        status = "OK" if after == expected else "MISMATCH"
        report_rows.append({
            "実行元": restore_source,
            "バックアップ識別子": backup_identifier,
            "実行者": operator_name or "未入力",
            "実行日時": executed_at,
            "テーブル": table,
            "復元前": before_counts.get(table, 0),
            "期待件数": expected,
            "復元後": after,
            "差分": delta,
            "結果": status,
        })

    report_df = pd.DataFrame(report_rows)
    _append_restore_report_log(report_rows)
    st.write("### 復元件数レポート")
    st.dataframe(report_df, use_container_width=True, hide_index=True)
    report_ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    st.download_button(
        label="復元レポートをCSVダウンロード",
        data=report_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"restore_report_{report_ts}.csv",
        mime="text/csv",
        key=f"restore_report_csv_{report_ts}",
    )
    if any(row["結果"] == "MISMATCH" for row in report_rows):
        st.warning("一部テーブルで期待件数との差分があります。pre_restore スナップショットを使って確認してください。")
    else:
        st.success("全テーブルで期待件数どおりに復元されました。")

    with st.expander("復元レポート履歴（永続ログ）", expanded=False):
        history_logs = _load_restore_report_logs()
        if history_logs:
            history_df = pd.DataFrame(history_logs)
            st.dataframe(history_df.tail(50), use_container_width=True, hide_index=True)
            history_ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            st.download_button(
                label="復元レポート履歴をCSVダウンロード",
                data=history_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"restore_report_history_{history_ts}.csv",
                mime="text/csv",
                key=f"restore_report_history_csv_{history_ts}",
            )
        else:
            st.info("復元レポート履歴はまだありません。")


def _expected_counts_from_backup(backup_data: Dict[str, Any]) -> Dict[str, int]:
    return {
        table: len(backup_data.get(table, [])) if isinstance(backup_data.get(table, []), list) else 0
        for table in RESTORE_TABLES
    }


def _show_expected_restore_counts(expected_counts: Dict[str, int], title: str) -> None:
    st.write(title)
    preview_df = pd.DataFrame(
        [{"テーブル": table, "復元予定件数": expected_counts.get(table, 0)} for table in RESTORE_TABLES]
    )
    st.dataframe(preview_df, use_container_width=True, hide_index=True)


def _render_pre_restore_snapshot_manager() -> None:
    backup_dir = _resolve_backup_dir()
    retention_days = _get_pre_restore_retention_days()
    snapshot_files = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith("pre_restore_") and f.endswith(".json")],
        reverse=True,
    )

    with st.expander("pre_restore スナップショット一覧", expanded=False):
        st.caption(f"自動保持ポリシー: {retention_days}日（環境変数 PRE_RESTORE_RETENTION_DAYS で変更可能）")
        cleanup_operator = st.text_input("整理作業者名（任意）", key="snapshot_cleanup_operator")

        if not snapshot_files:
            st.info("pre_restore スナップショットはまだありません。")
            _render_snapshot_cleanup_log_download()
            return

        selected_snapshot = st.selectbox(
            "確認するスナップショットを選択",
            snapshot_files,
            key="pre_restore_snapshot_select",
        )
        snapshot_path = os.path.join(backup_dir, selected_snapshot)
        modified_at = datetime.fromtimestamp(os.path.getmtime(snapshot_path)).strftime('%Y-%m-%d %H:%M:%S')
        st.caption(f"更新日時: {modified_at}")

        col1, col2 = st.columns(2)
        with col1:
            delete_selected_confirm = st.checkbox(
                "選択スナップショットを削除する",
                key=f"confirm_delete_snapshot_{selected_snapshot}",
            )
            if st.button(
                "選択スナップショット削除",
                key=f"delete_snapshot_btn_{selected_snapshot}",
                disabled=not delete_selected_confirm,
            ):
                try:
                    os.remove(snapshot_path)
                    _append_snapshot_cleanup_log("選択削除", [selected_snapshot], cleanup_operator)
                    st.success(f"削除しました: {selected_snapshot}")
                    st.rerun()
                except Exception as delete_error:
                    st.error(f"削除に失敗しました: {delete_error}")

        with col2:
            retain_count = st.number_input(
                "保持する最新件数",
                min_value=1,
                max_value=max(1, len(snapshot_files)),
                value=min(20, max(1, len(snapshot_files))),
                step=1,
                key="snapshot_retain_count",
            )
            planned_delete_count = max(0, len(snapshot_files) - int(retain_count))
            st.caption(f"世代整理の対象: {planned_delete_count}件")
            cleanup_confirm = st.checkbox(
                "古いスナップショットを一括削除する",
                key="confirm_cleanup_snapshots",
            )
            if st.button(
                "世代整理を実行",
                key="cleanup_snapshots_btn",
                disabled=not cleanup_confirm,
            ):
                try:
                    to_delete = snapshot_files[int(retain_count):]
                    deleted_count = 0
                    for name in to_delete:
                        path = os.path.join(backup_dir, name)
                        if os.path.exists(path):
                            os.remove(path)
                            deleted_count += 1
                    _append_snapshot_cleanup_log("世代整理", to_delete, cleanup_operator)
                    st.success(f"世代整理が完了しました（削除: {deleted_count}件 / 保持: {retain_count}件）")
                    st.rerun()
                except Exception as cleanup_error:
                    st.error(f"世代整理に失敗しました: {cleanup_error}")

        try:
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
            backup_date = snapshot_data.get("backup_date", "unknown") if isinstance(snapshot_data, dict) else "unknown"
            backup_type = snapshot_data.get("backup_type", "unknown") if isinstance(snapshot_data, dict) else "unknown"
            st.write(f"バックアップ日時: {backup_date}")
            st.write(f"種別: {backup_type}")

            if isinstance(snapshot_data, dict):
                _show_expected_restore_counts(_expected_counts_from_backup(snapshot_data), "### スナップショット内テーブル件数")

            st.download_button(
                label="選択スナップショットをダウンロード",
                data=json.dumps(snapshot_data, ensure_ascii=False, indent=2).encode("utf-8"),
                file_name=selected_snapshot,
                mime="application/json",
                key=f"download_snapshot_{selected_snapshot}",
            )
        except Exception as snapshot_error:
            st.error(f"スナップショットの読み込みに失敗しました: {snapshot_error}")

        _render_snapshot_cleanup_log_download()


def _execute_restore_with_guard(
    backup_data: Dict[str, Any],
    supabase: Client,
    source_label: str,
    backup_identifier: str,
    operator_name: str,
) -> None:
    pre_snapshot_file = _save_pre_restore_snapshot(supabase)
    before_counts = _collect_table_counts(supabase)
    expected_counts = {table: len(backup_data.get(table, [])) for table in RESTORE_TABLES}

    try:
        perform_restore(backup_data, supabase)
        after_counts = _collect_table_counts(supabase)
        st.success(f"{source_label}からデータベースがリストアされました")
        st.info(f"リストア前スナップショットを保存しました: {pre_snapshot_file}")
        _show_restore_count_report(
            before_counts,
            expected_counts,
            after_counts,
            restore_source=source_label,
            backup_identifier=backup_identifier,
            operator_name=operator_name,
        )
    except Exception as restore_error:
        st.error(f"リストアに失敗したため、自動ロールバックを実行します: {restore_error}")
        try:
            with open(pre_snapshot_file, 'r', encoding='utf-8') as f:
                rollback_payload = json.load(f)
            if not isinstance(rollback_payload, dict):
                raise ValueError("ロールバックスナップショットの形式が不正です。")
            perform_restore(rollback_payload, supabase)
            st.warning("自動ロールバックにより、リストア開始前の状態へ戻しました。")
            after_rollback_counts = _collect_table_counts(supabase)
            _show_restore_count_report(
                before_counts,
                before_counts,
                after_rollback_counts,
                restore_source=f"{source_label}-rollback",
                backup_identifier=pre_snapshot_file,
                operator_name=operator_name,
            )
        except Exception as rollback_error:
            st.error(f"自動ロールバックにも失敗しました: {rollback_error}")
            st.error(f"手動復旧に備えてスナップショットを確認してください: {pre_snapshot_file}")
            raise


def backup_database(supabase: Optional[Client] = None):
    """Supabaseからデータをバックアップする（JSONファイルとして保存、およびbackupsテーブルに保存）"""
    if supabase is None:
        supabase = get_supabase_admin_client()
    if not supabase:
        st.error("バックアップ用クライアントの初期化に失敗しました。")
        return
    
    backup_dir = _resolve_backup_dir()
    
    try:
        # バックアップデータを準備
        backup_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        backup_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        backup_data = _fetch_backup_payload(supabase)
        backup_data["backup_date"] = backup_date
        
        # JSONファイルとして保存
        backup_file = os.path.join(backup_dir, f"backup_{backup_id}.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        # Supabaseのbackupsテーブルにもバックアップデータを保存
        try:
            # backupsテーブルが存在しない場合は作成する（初回のみ）
            # このコードはテーブルがすでに存在する場合エラーになるが、try-exceptで処理される
            insert_response = supabase.table("backups").insert({
                "backup_id": backup_id,
                "backup_date": backup_date,
                "data": backup_data
            }).execute()
            st.success("Supabaseバックアップテーブルにバックアップを保存しました")
        except Exception as e:
            st.warning(f"backupsテーブルへの保存に失敗しました（テーブルが存在しない可能性があります）: {e}")
            st.info("backupsテーブルを作成・設定します...")
            
            # 最新のSupabaseクライアントでは直接SQLクエリを実行する方法が変更されている
            # 管理者画面でテーブルを作成するように促す
            st.warning("以下のSQLクエリをSupabaseの管理画面で実行してbackupsテーブルを正しく設定してください:")
            st.code("""
-- テーブルの作成（既に存在する場合はスキップされます）
CREATE TABLE IF NOT EXISTS backups (
    id serial PRIMARY KEY,
    backup_id text NOT NULL,
    backup_date text NOT NULL,
    data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- RLSを有効化
ALTER TABLE backups ENABLE ROW LEVEL SECURITY;

-- 不要な公開権限は付与しない
REVOKE ALL ON TABLE backups FROM anon;
REVOKE ALL ON TABLE backups FROM authenticated;

-- サーバー側（Service Role Key）でのみ運用する場合、ポリシー追加は不要
            """, language="sql")
            
            # 情報メッセージを表示
            st.info("ローカルJSONバックアップのみ作成しました。Supabaseテーブルへのバックアップは次回成功します。")
            st.info("RLSポリシーの変更後は、アプリを再起動してください。")
        
        st.success(f"バックアップが作成されました: {backup_file}")
        
    except Exception as e:
        st.error(f"バックアップ中にエラーが発生しました: {e}")
        import traceback
        st.error(traceback.format_exc())

def restore_database(supabase: Optional[Client] = None):
    """JSONバックアップファイルまたはSupabaseのbackupsテーブルからデータをリストアする"""
    if supabase is None:
        supabase = get_supabase_admin_client()
    if not supabase:
        st.error("リストア用クライアントの初期化に失敗しました。")
        return
    
    # リストア方法の選択
    st.subheader("データベースのリストア")
    restore_method = st.radio(
        "リストア方法を選択してください:",
        ["ローカルJSONファイルから", "Supabaseバックアップテーブルから"]
    )
    operator_name = st.text_input("実行者名（任意）", key="restore_operator_name")
    _render_pre_restore_snapshot_manager()
    
    if restore_method == "ローカルJSONファイルから":
        # 既存の実装：ローカルJSONファイルからのリストア
        backup_dir = _resolve_backup_dir()
        
        # JSONバックアップファイルを検索
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
        if not backup_files:
            st.warning("バックアップファイルが見つかりません。")
            return
        
        selected_backup = st.selectbox("リストアするバックアップファイルを選択してください", backup_files)

        backup_data: Optional[Dict[str, Any]] = None
        try:
            backup_file_path = os.path.join(backup_dir, selected_backup)
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            if not isinstance(loaded_data, dict):
                raise ValueError("バックアップファイルの形式が不正です。")
            backup_data = loaded_data
            _show_expected_restore_counts(
                _expected_counts_from_backup(backup_data),
                "### 復元予定件数（ローカルバックアップ）",
            )
        except Exception as preview_error:
            st.error(f"バックアップ内容の事前確認に失敗しました: {preview_error}")

        confirm_local_restore = st.checkbox(
            "上記件数を確認し、ローカルバックアップから復元を実行する",
            key=f"confirm_local_restore_{selected_backup}",
        )
        confirm_local_final = st.checkbox(
            "最終確認: 現在のデータを上書きすることを理解した上で実行する",
            key=f"confirm_local_final_{selected_backup}",
        )

        if st.button(
            "リストア実行",
            key="execute_local_restore",
            disabled=(not confirm_local_restore or not confirm_local_final or backup_data is None),
        ):
            try:
                if backup_data is None:
                    raise ValueError("バックアップデータが読み込まれていません。")

                _execute_restore_with_guard(
                    backup_data,
                    supabase,
                    source_label="ローカルバックアップ",
                    backup_identifier=selected_backup,
                    operator_name=operator_name,
                )
            except Exception as e:
                st.error(f"リストア中にエラーが発生しました: {e}")
                import traceback
                st.error(traceback.format_exc())
    
    else:  # Supabaseバックアップテーブルから
        try:
            # backupsテーブルが存在するか確認
            st.info("Supabaseのバックアップデータを確認しています...")
            
            # バックアップの存在確認
            try:
                # テーブルの構造に関係なく、まずバックアップの存在確認のみ実行
                count_response = supabase.table("backups").select("*", count="exact").execute() # type: ignore
                
                # バックアップカウント表示（デバッグ用）
                backup_count = count_response.count
                
                st.success(f"バックアップが見つかりました: {backup_count}件")
                
                # backupsテーブルからバックアップ一覧を取得
                response = supabase.table("backups").select("id, backup_id, backup_date").order('backup_date', desc=True).execute()
                backups = response.data
                
                if not backups:
                    st.warning("Supabaseバックアップテーブルにバックアップが見つかりません。")
                    st.info("先にバックアップを実行するか、Supabase管理画面でbackupsテーブルが正しく設定されているか確認してください。")
                    
                    # テーブル構造の確認を試みる
                    try:
                        # テーブル構造の表示
                        st.info("バックアップテーブルの構造を確認します...")
                        columns_response = supabase.table("backups").select("*").limit(1).execute()
                        if columns_response.data:
                            st.info(f"テーブル構造: {list(columns_response.data[0].keys())}")
                        else:
                            st.info("テーブルは存在しますが、データがありません。")
                    except Exception as column_error:
                        st.error(f"テーブル構造の確認に失敗しました: {column_error}")
                    
                    return
                
                # バックアップ選択用のオプションリストを作成
                backup_options = [f"{b.get('backup_id', b.get('id', 'unknown'))} ({b.get('backup_date', 'unknown date')})" for b in backups]
                selected_backup_option = st.selectbox("リストアするバックアップを選択してください", backup_options)

                selected_id = selected_backup_option.split(" ")[0]
                field_name = "backup_id" if any(b.get('backup_id') == selected_id for b in backups) else "id"
                backup_response = supabase.table("backups").select("*").eq(field_name, selected_id).execute()

                selected_backup_data: Optional[Dict[str, Any]] = None
                if not backup_response.data:
                    st.error("選択されたバックアップが見つかりません。")
                elif "data" not in backup_response.data[0]:
                    st.error(f"バックアップデータの形式が不正です。フィールド: {list(backup_response.data[0].keys())}")
                    st.info("バックアップデータの構造:")
                    st.json(backup_response.data[0])
                else:
                    candidate_data = backup_response.data[0]["data"]
                    if not isinstance(candidate_data, dict):
                        st.error("Supabaseバックアップデータの形式が不正です。")
                    else:
                        selected_backup_data = candidate_data
                        _show_expected_restore_counts(
                            _expected_counts_from_backup(selected_backup_data),
                            "### 復元予定件数（Supabaseバックアップ）",
                        )

                confirm_remote_restore = st.checkbox(
                    "上記件数を確認し、Supabaseバックアップから復元を実行する",
                    key=f"confirm_remote_restore_{selected_id}",
                )
                confirm_remote_final = st.checkbox(
                    "最終確認: 現在のデータを上書きすることを理解した上で実行する",
                    key=f"confirm_remote_final_{selected_id}",
                )

                if st.button(
                    "リストア実行",
                    key="execute_remote_restore",
                    disabled=(not confirm_remote_restore or not confirm_remote_final or selected_backup_data is None),
                ):
                    # 選択されたバックアップのIDを取得
                    if selected_backup_data is None:
                        st.error("選択されたバックアップデータが読み込めませんでした。")
                    else:
                        st.info("リストア処理を開始します...")
                        _execute_restore_with_guard(
                            selected_backup_data,
                            supabase,
                            source_label="Supabaseバックアップ",
                            backup_identifier=selected_backup_option,
                            operator_name=operator_name,
                        )
            
            except Exception as table_error:
                # バックアップテーブルが存在しない場合やアクセス権限がない場合
                st.warning("Supabaseバックアップテーブルにアクセスできないか、テーブルが存在しません。")
                st.error(f"エラー詳細: {table_error}")
                st.info("以下のSQLクエリをSupabaseの管理画面で実行してbackupsテーブルを作成してください:")
                st.code("""
-- テーブルの作成
CREATE TABLE IF NOT EXISTS backups (
    id serial PRIMARY KEY,
    backup_id text NOT NULL,
    backup_date text NOT NULL,
    data jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- RLSを有効化
ALTER TABLE backups ENABLE ROW LEVEL SECURITY;

-- 不要な公開権限は付与しない
REVOKE ALL ON TABLE backups FROM anon;
REVOKE ALL ON TABLE backups FROM authenticated;

-- サーバー側（Service Role Key）でのみ運用する場合、ポリシー追加は不要
                """, language="sql")
        
        except Exception as e:
            st.error(f"Supabaseバックアップからのリストア中にエラーが発生しました: {e}")
            import traceback
            st.error(traceback.format_exc())

def perform_restore(backup_data, supabase: Client):
    """サーバー側RPCで、全テーブルを単一トランザクション内に復元する。"""
    if not isinstance(backup_data, dict):
        raise ValueError("バックアップデータ形式が不正です。JSONオブジェクトではありません。")

    for table in RESTORE_TABLES:
        rows = backup_data.get(table, [])
        if not isinstance(rows, list):
            raise ValueError(f"バックアップデータ形式が不正です。{table} が配列ではありません。")

    supabase.rpc("restore_golf_database", {"backup_data": backup_data}).execute()

def login_page():
    st.title("88会ログイン")
    
    # ログイン画面に画像を表示
    image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', '01205972-9563-43D7-B862-5B2B8DECF9FA.png')
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    
    if not USER_PASSWORD:
        st.error("利用者パスワードが設定されていないため、ログインできません。管理者に連絡してください。")
        return

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
    
    if not ADMIN_PASSWORD:
        st.error("管理者パスワードが設定されていないため、管理機能は無効です。")
        return

    password = st.text_input("管理者パスワードを入力してください", type="password", key="admin_password_input")
    if st.button("ログイン", key="admin_login_button"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.session_state.page = "admin"
            st.rerun()
        else:
            st.error("パスワードが間違っています")


def render_dashboard_announcement(announcement: Dict[str, Any]) -> None:
    """次回案内をホーム用のカードとして表示する。"""
    title = html.escape(str(announcement.get("title") or "次回コンペのお知らせ"))
    content = html.escape(str(announcement.get("content") or "")).replace("\n", "<br>")
    info = announcement.get("tournament_info") or {}
    if isinstance(info, str):
        try:
            info = json.loads(info)
        except (TypeError, json.JSONDecodeError):
            info = {}
    if not isinstance(info, dict):
        info = {}

    detail_items = []
    details = [
        ("📅", "開催日", " ".join(filter(None, [str(info.get("date") or ""), str(info.get("start_time") or "")] ))),
        ("⛳", "コース", str(info.get("course_name") or "")),
        ("🕗", "集合", str(info.get("meeting_time") or "")),
        ("👥", "組数", f'{info.get("groups")}組' if info.get("groups") else ""),
    ]
    for icon, label, value in details:
        if value.strip():
            detail_items.append(
                f'<div style="padding:.7rem .8rem;border-radius:12px;background:rgba(255,255,255,.68);">'
                f'<span style="font-size:.74rem;color:#81775d;">{icon} {label}</span>'
                f'<strong style="display:block;margin-top:.15rem;color:#43391e;font-size:.9rem;">{html.escape(value)}</strong></div>'
            )

    details_html = ""
    if detail_items:
        details_html = (
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:.55rem;margin-top:1rem;">'
            + "".join(detail_items)
            + "</div>"
        )
    content_html = f"<p>{content}</p>" if content else ""
    st.markdown(
        f'<div class="dashboard-section-label">次回のご案内<small>開催情報と幹事からのお知らせ</small></div>'
        f'<div class="dashboard-notice"><h3>🏌️ {title}</h3>{content_html}{details_html}</div>',
        unsafe_allow_html=True,
    )
    if announcement.get("image_url"):
        try:
            st.image(announcement["image_url"], use_container_width=True)
        except Exception:
            pass


def get_default_dashboard_announcement() -> Dict[str, Any]:
    return {
        "title": "第52回 88会ゴルフコンペのご案内",
        "content": "次回の開催場所は、前回同様に本千葉カントリークラブとなりました。",
        "tournament_info": {
            "date": "12月6日",
            "start_time": "9:07スタート",
            "course_name": "本千葉カントリークラブ",
            "meeting_time": "8:30",
            "groups": 3,
        },
    }


def main_app():
    render_dashboard_shell()
    render_dashboard_navigation()
    
    # お知らせをデータベースから取得して表示
    try:
        supabase_client = get_supabase_client()
        announcements_response = None
        
        if supabase_client:
            announcements_response = supabase_client.table("announcements").select("*").eq("is_active", True).order("display_order", desc=True).limit(1).execute()
        
        if announcements_response and announcements_response.data and len(announcements_response.data) > 0:
            announcement = announcements_response.data[0]
            render_dashboard_announcement(announcement)
        else:
            # デフォルトのお知らせ（データベースにデータがない場合）
            render_dashboard_announcement(get_default_dashboard_announcement())
    except Exception:
        # エラー時はデフォルトのお知らせを表示
        render_dashboard_announcement(get_default_dashboard_announcement())
    
    # Supabaseからデータを取得
    scores_df = fetch_scores()
    players_df = fetch_players()
    competitions_df = fetch_competitions()
    
    if not scores_df.empty and not players_df.empty:
        render_dashboard_status(scores_df, players_df, competitions_df)
        render_dashboard_highlights(scores_df)
        # 最終切り分け用: safe モードでは最小表示のみ行う
        render_mode = resolve_main_render_mode()
        if render_mode == "safe":
            render_main_safe_mode(scores_df)
            st.markdown('<div class="dashboard-footer">88会ゴルフコンペ・スコア管理システム</div>', unsafe_allow_html=True)
            return

        # 一部環境でフロント側の module script 読み込みに失敗するため、
        # メイン画面のグラフ描画は一時的に停止（ランキング表とデータ表は表示継続）
        st.info("互換性モード: グラフ表示を一時停止しています。")
        display_winner_count_ranking(scores_df)
        
        # 過去データを準備（表示不整合を避けるため有効データのみ、index列は表示しない）
        past_data_df = scores_df.copy()
        past_data_df = past_data_df[
            (past_data_df["合計スコア"] > 0)
            & (past_data_df["アウトスコア"] > 0)
            & (past_data_df["インスコア"] > 0)
        ]
        past_data_df = past_data_df.sort_values(by=["日付", "順位"], ascending=[False, True])
        preferred_cols = [
            "順位", "競技ID", "日付", "コース", "プレイヤー名",
            "アウトスコア", "インスコア", "合計スコア", "ハンディキャップ", "ネットスコア",
        ]
        existing_cols = [col for col in preferred_cols if col in past_data_df.columns]
        past_data_df = past_data_df[existing_cols].reset_index(drop=True)
        past_data_df = sanitize_display_df(past_data_df)
        
        st.subheader("過去データ")
        # Streamlit DataFrameのブラウザ互換問題回避のため、静的テーブル表示に変換
        past_display_df = past_data_df.copy()
        format_cols = {
            "ハンディキャップ": "{:.2f}",
            "ネットスコア": "{:.2f}",
            "アウトスコア": "{:.0f}",
            "インスコア": "{:.0f}",
            "合計スコア": "{:.0f}",
            "順位": "{:.0f}",
            "競技ID": "{:.0f}",
        }
        for col, fmt in format_cols.items():
            if col in past_display_df.columns:
                past_display_df[col] = past_display_df[col].map(lambda x: fmt.format(x) if pd.notna(x) else "")
        render_html_table(past_display_df, max_rows=200)
        
        # ベストグロススコアトップ10を準備
        st.subheader("ベストグロススコアトップ10")
        
        # 表示方法の選択（ユニークユーザーか純粋なトップ10か）
        display_mode = st.radio(
            "表示方法を選択してください：",
            ["ユニークユーザー（各プレイヤーの最高スコアのみ表示）", "純粋なトップ10（同じプレイヤーが複数回登場する可能性あり）"],
            key="best_score_display_mode"
        )
        
        # 競技IDが41でないデータのみを対象にする
        filtered_scores_df = scores_df[scores_df["競技ID"] != 41]
        
        # 競技IDが100未満のデータのみを対象にする（要件に基づく）
        filtered_scores_df = filtered_scores_df[filtered_scores_df["競技ID"] < 100]
        
        # 合計スコアが0または欠損値のデータを除外する
        filtered_scores_df = filtered_scores_df[
            (filtered_scores_df["合計スコア"] > 0) & 
            (~filtered_scores_df["合計スコア"].isna()) &
            (filtered_scores_df["アウトスコア"] > 0) & 
            (~filtered_scores_df["アウトスコア"].isna()) &
            (filtered_scores_df["インスコア"] > 0) & 
            (~filtered_scores_df["インスコア"].isna())
        ]
        
        # 合計スコアが0以上のデータのみを対象にする（不正なデータの除外）
        filtered_scores_df = filtered_scores_df[filtered_scores_df["合計スコア"] > 0]
        
        # 表示方法に応じたデータ処理
        if display_mode.startswith("ユニークユーザー"):
            # 各プレイヤーのベストスコア（最小の合計スコア）を取得
            best_player_scores = filtered_scores_df.groupby("プレイヤー名")["合計スコア"].min().reset_index()
            
            # プレイヤーごとのベストスコアを合計スコアでソート（昇順）し、トップ10を取得
            best_gross_scores = best_player_scores.sort_values(by="合計スコア").head(10).reset_index(drop=True)
            
            # 各ベストスコアの詳細情報を取得
            best_scores_with_details = []
            for _, row in best_gross_scores.iterrows():
                player_name = row["プレイヤー名"]
                best_score = row["合計スコア"]
                
                # 該当プレイヤーの該当スコアの詳細データを検索（最初の一致を使用）
                player_best_score_records = filtered_scores_df[
                    (filtered_scores_df["プレイヤー名"] == player_name) & 
                    (filtered_scores_df["合計スコア"] == best_score)
                ]
                
                if not player_best_score_records.empty:
                    best_scores_with_details.append(player_best_score_records.iloc[0].to_dict())
            
            # データフレームに変換し、インデックスを1から始める連番に設定
            if best_scores_with_details:
                best_gross_scores_detailed = pd.DataFrame(best_scores_with_details).reset_index(drop=True)
                best_gross_scores_detailed.index += 1
                best_gross_scores_detailed.index.name = '順位'
            else:
                best_gross_scores_detailed = pd.DataFrame()
        else:
            # 純粋なトップ10（同じプレイヤーが複数回登場する可能性あり）
            # 合計スコアで昇順ソートし、純粋にトップ10のスコアを取得
            best_gross_scores_detailed = filtered_scores_df.sort_values(by="合計スコア").head(10).reset_index(drop=True)
            best_gross_scores_detailed.index += 1
            best_gross_scores_detailed.index.name = '順位'
        
        # 結果の表示
        if not best_gross_scores_detailed.empty:
            best_display_df = sanitize_display_df(best_gross_scores_detailed.copy())
            format_cols = {
                "ハンディキャップ": "{:.2f}",
                "ネットスコア": "{:.2f}",
                "アウトスコア": "{:.0f}",
                "インスコア": "{:.0f}",
                "合計スコア": "{:.0f}",
                "順位": "{:.0f}",
                "競技ID": "{:.0f}",
            }
            for col, fmt in format_cols.items():
                if col in best_display_df.columns:
                    best_display_df[col] = best_display_df[col].map(lambda x: fmt.format(x) if pd.notna(x) else "")
            render_html_table(best_display_df, max_rows=200)
        else:
            st.warning("有効なスコアデータが見つかりませんでした。")
        
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
    
    st.markdown("---")
    st.caption("88会ゴルフコンペ・スコア管理システム")

def render_admin_shared_styles() -> None:
    """管理画面へ直接アクセスした場合にも共通カードスタイルを適用する。"""
    st.markdown(
        """
        <style>
          .dashboard-hero { padding: 2rem 2.2rem; margin: .3rem 0 1rem; border-radius: 24px; color: #fff; background: linear-gradient(125deg, #052f27, #0c674c 58%, #17845f); box-shadow: 0 18px 42px rgba(7,61,49,.18); }
          .dashboard-eyebrow { color: #bcead7; font-size: .76rem; font-weight: 800; letter-spacing: .14em; }
          .dashboard-hero h1 { margin: .4rem 0 0; color: #fff; font-size: 2.25rem; }
          .dashboard-hero p { margin: .65rem 0 0; color: #d9f3e8; }
          .dashboard-section-label { margin: 1.4rem 0 .65rem; color: #16332b; font-size: 1.15rem; font-weight: 800; }
          .dashboard-section-label small { display:block; margin-top:.18rem; color:#6f817a; font-size:.78rem; font-weight:500; }
          div[data-testid="stButton"] > button { min-height: 2.8rem; border-radius: 12px; font-weight: 700; }
          @media (max-width:640px) { .dashboard-hero { padding: 1.45rem 1.25rem; } .dashboard-hero h1 { font-size: 1.75rem; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def admin_app():
    """必要な機能だけを読み込む、運営者向けの管理画面。"""
    render_admin_shared_styles()
    st.markdown(
        '<div class="dashboard-hero"><div class="dashboard-eyebrow">ADMIN CONSOLE</div>'
        '<h1>88会 運営メニュー</h1><p>お知らせ、コンペ、スコア、メンバー情報をここから管理します。</p></div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("← メイン画面へ", key="admin_to_main", type="primary"):
            st.session_state.page = "main"
            st.rerun()
    with col2:
        if st.button("ログアウト", key="admin_logout", type="secondary"):
            # セッション状態を全てクリア
            st.session_state.logged_in = False
            st.session_state.admin_logged_in = False
            st.session_state.page = "login"
            st.rerun()
    
    supabase_admin = get_supabase_admin_client()
    if not supabase_admin:
        st.error("管理者用クライアントの初期化に失敗しました。設定を確認してください。")
        st.info("💡 ヒント: 環境変数 SUPABASE_SERVICE_KEY が正しく設定されているか確認してください。")
        return

    admin_sections = {
        "📢 お知らせ・次回案内": "ホームに表示する案内を作成・編集します。",
        "🏆 コンペ・参加者": "コンペの作成、編集、参加者登録を行います。",
        "✍️ スコア入力": "開催済みコンペのスコアと順位を入力します。",
        "👤 プレイヤー管理": "プレイヤーの追加・編集・削除を行います。",
        "💾 バックアップ": "現在のデータをバックアップとして保存します。",
        "⚠️ リストア（危険な操作）": "バックアップから全データを復元します。現在のデータは置き換わります。",
    }
    st.markdown('<div class="dashboard-section-label">管理する内容を選択<small>選んだ機能だけを読み込みます</small></div>', unsafe_allow_html=True)
    selected_section = st.selectbox(
        "管理メニュー",
        list(admin_sections.keys()),
        label_visibility="collapsed",
        key="admin_section_selector",
    )
    st.caption(admin_sections[selected_section])

    if selected_section == "📢 お知らせ・次回案内":
        announcement_management_tab(supabase_admin)
    elif selected_section == "🏆 コンペ・参加者":
        competition_management_tab(supabase_admin)
    elif selected_section == "✍️ スコア入力":
        score_entry_tab(supabase_admin)
    elif selected_section == "👤 プレイヤー管理":
        player_management_tab(supabase_admin)
    elif selected_section == "💾 バックアップ":
        st.subheader("データベースのバックアップ")
        st.info("バックアップは現在のデータを変更せず、復元用の記録を保存します。")
        confirm_backup = st.checkbox("バックアップを実行することを確認しました。", key="confirm_backup")
        if st.button("バックアップを実行", key="backup_button", disabled=not confirm_backup):
            backup_database(supabase_admin)
    else:
        st.error("この操作は、現在のデータをバックアップの内容で置き換えます。")
        st.subheader("データベースのリストア")
        restore_database(supabase_admin)


def login_app():
    """ログイン画面"""
    st.title("ログイン")
    
    if not USER_PASSWORD:
        st.error("利用者パスワードが設定されていないため、ログインできません。")
        return

    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == USER_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.page = "main"
            st.rerun()  # ページを強制的に再読み込み
        else:
            st.error("パスワードが間違っています")

# ページ表示（ルーティング）
page = st.session_state.get("page", "login")

if page == "login":
    login_page()
elif page == "main":
    if not st.session_state.get("logged_in", False):
        st.session_state.page = "login"
        st.rerun()
    main_app()
elif page == "stats":
    if not st.session_state.get("logged_in", False):
        st.session_state.page = "login"
        st.rerun()
    personal_stats_page()
elif page == "results":
    if not st.session_state.get("logged_in", False):
        st.session_state.page = "login"
        st.rerun()
    competition_results_page()
elif page == "admin":
    if not st.session_state.get("admin_logged_in", False):
        admin_login_page()
    else:
        admin_app()
else:
    st.session_state.page = "login"
    st.rerun()

# # CSS調整（縦配置用） - ページ表示の後に配置
# st.markdown("""
# <style>
#     .vertical-footer {
#         position: fixed;
#         bottom: 10px;
#         right: 10px;
#         background-color: rgba(255, 255, 255, 0.8);
#         padding: 10px;
#         border-radius: 5px;
#         box-shadow: 0 0 5px rgba(0,0,0,0.1);
#         z-index: 999;
#         text-align: right;
#         line-height: 1.5;
#     }
#     .footer-item {
#         font-size: 0.75rem;
#         color: #666;
#         display: block;
#     }
# </style>
# """, unsafe_allow_html=True)

# # フッターを右下に縦に配置
# try:
#     app_version = get_app_version()
#     git_rev = get_git_revision()
#     git_date = get_git_date()
# except Exception:
#     app_version = "1.2.4"
#     git_rev = "unknown"
#     git_date = "unknown"

# st.markdown(f"""
# <div class="vertical-footer">
#     <span class="footer-item">Ver {app_version} ({git_rev})</span>
#     <span class="footer-item">最終更新: {git_date}</span>
# </div>
# """, unsafe_allow_html=True)
