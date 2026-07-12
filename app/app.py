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
    session_override = st.session_state.get("main_render_mode_override", "")
    if isinstance(session_override, str):
        session_override = session_override.strip().lower()
        if session_override in {"safe", "compat"}:
            return session_override

    explicit_mode = os.getenv("MAIN_RENDER_MODE", "").strip().lower()
    if explicit_mode in {"safe", "compat"}:
        return explicit_mode

    # 後方互換: MAIN_SAFE_MODE=true なら safe, それ以外は compat
    safe_mode_raw = os.getenv("MAIN_SAFE_MODE", "true")
    safe_mode_value = safe_mode_raw.strip().lower() == "true"
    return "safe" if safe_mode_value else "compat"


def render_deploy_fingerprint() -> None:
    """デプロイ反映確認用の識別子を表示"""
    git_rev = get_git_revision()
    deploy_branch = (
        os.getenv("RAILWAY_GIT_BRANCH", "").strip()
        or os.getenv("VERCEL_GIT_COMMIT_REF", "").strip()
        or os.getenv("GITHUB_REF_NAME", "").strip()
        or "unknown"
    )
    render_mode = resolve_main_render_mode()
    session_override = st.session_state.get("main_render_mode_override", "")
    override_label = ""
    if isinstance(session_override, str) and session_override.strip().lower() in {"safe", "compat"}:
        override_label = f" | SESSION_OVERRIDE={session_override.strip().lower()}"
    st.caption(
        f"Build: v{APP_VERSION} | rev: {git_rev} | branch: {deploy_branch} | updated: {APP_LAST_UPDATE} | MAIN_RENDER_MODE={render_mode}{override_label}"
    )


def render_main_mode_switch_controls() -> None:
    """運用中の段階復旧用に表示モードをセッション単位で切替"""
    current_mode = resolve_main_render_mode()
    st.caption("表示モード切替（このブラウザセッションのみ）")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("safe表示", key="switch_mode_safe", use_container_width=True):
            st.session_state["main_render_mode_override"] = "safe"
            st.rerun()
    with col2:
        if st.button("compat表示", key="switch_mode_compat", use_container_width=True):
            st.session_state["main_render_mode_override"] = "compat"
            st.rerun()
    with col3:
        if st.button("環境設定に戻す", key="switch_mode_env", use_container_width=True):
            st.session_state.pop("main_render_mode_override", None)
            st.rerun()
    st.caption(f"現在モード: {current_mode}")


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
    st.session_state.pop("main_render_mode_override", None)
    st.rerun()


def render_dashboard_shell() -> None:
    """ログイン後ホーム共通の視覚デザイン"""
    st.markdown(
        """
        <style>
          .dashboard-hero {
            padding: 1.6rem 1.7rem;
            margin: .4rem 0 1rem;
            border-radius: 18px;
            color: white;
            background: linear-gradient(120deg, #0b5542 0%, #087f5b 55%, #13a36f 100%);
            box-shadow: 0 10px 26px rgba(8, 127, 91, .20);
          }
          .dashboard-hero h1 { margin: 0; font-size: 2rem; color: white; }
          .dashboard-hero p { margin: .45rem 0 0; color: #e4fff2; font-size: 1rem; }
          .dashboard-section-label { margin: 1.4rem 0 .5rem; font-weight: 700; color: #155e4a; }
          .dashboard-status-card {
            border: 1px solid #dcece5; border-radius: 12px; padding: .85rem 1rem;
            background: #f7fcf9; color: #245447; min-height: 88px;
          }
          .dashboard-status-card strong { display: block; color: #0b5542; font-size: 1.3rem; margin-top: .18rem; }
          .dashboard-status-card span { color: #638277; font-size: .82rem; }
          div[data-testid="stButton"] > button { border-radius: 10px; min-height: 2.65rem; font-weight: 600; }
        </style>
        <div class="dashboard-hero">
          <h1>88会 ゴルフコンペ</h1>
          <p>ようこそ。大会のお知らせ、成績、競技結果をここから確認できます。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_navigation() -> None:
    """主要機能へのショートカット"""
    st.markdown('<div class="dashboard-section-label">メニュー</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📊 個人成績", key="dashboard_stats", use_container_width=True):
            _navigate("stats")
    with col2:
        if st.button("🏆 競技結果", key="dashboard_results", use_container_width=True):
            _navigate("results")
    with col3:
        if st.button("⚙️ 管理", key="dashboard_admin", use_container_width=True):
            st.session_state.admin_logged_in = False
            _navigate("admin")
    with col4:
        if st.button("🚪 ログアウト", key="dashboard_logout", use_container_width=True):
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
        competition_ids = pd.to_numeric(competitions_df["competition_id"], errors="coerce")
        regular_ids = competition_ids[(competition_ids > 0) & (competition_ids < 100)]
        if not regular_ids.empty:
            competition_round = int(regular_ids.max())
    latest_date = "データなし"
    if not valid_scores.empty and "日付" in valid_scores.columns:
        latest_values = valid_scores["日付"].dropna()
        if not latest_values.empty:
            latest_date = str(latest_values.max())

    st.markdown('<div class="dashboard-section-label">大会状況</div>', unsafe_allow_html=True)
    cards = [
        ("登録プレイヤー", f"{len(players_df)} 名"),
        ("記録済みスコア", f"{len(valid_scores)} 件"),
        ("開催コンペ", f"第{competition_round}回" if competition_round else "データなし"),
        ("最新記録", latest_date),
    ]
    columns = st.columns(4)
    for column, (label, value) in zip(columns, cards):
        with column:
            st.markdown(
                f'<div class="dashboard-status-card"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>',
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
    st.write("DEBUG: from secrets =", _get_secret_supabase("service_key"))
    st.write("DEBUG: from env =", os.getenv("SUPABASE_SERVICE_KEY", "NOT SET"))

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
    or "88"
)
ADMIN_PASSWORD = (
    _get_secret_auth("admin_password")
    or os.getenv("ADMIN_PASSWORD", "").strip()
    or "admin88"
)

if USER_PASSWORD == "88" or ADMIN_PASSWORD == "admin88":
    logging.warning("Default passwords are in use. Set USER_PASSWORD and ADMIN_PASSWORD in secrets or env.")

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

def personal_stats_page():
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

def competition_results_page():
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

def display_winner_count_ranking(scores_df):
    st.subheader("優勝回数ランキング")

    ranking_type = st.radio("ランキングの種類を選択してください:", ["トータルランキング", "年度ランキング"])

    if ranking_type == "年度ランキング":
        available_years = scores_df['日付'].str[:4].unique()
        year = st.selectbox("表示する年度を選択してください:", sorted(available_years))
        scores_df = scores_df[scores_df['日付'].str.startswith(year)]

    rank_one_winners = scores_df[scores_df['順位'] == 1].groupby('プレイヤー名').size().reset_index(name='優勝回数')
    rank_one_winners = rank_one_winners.sort_values(by='優勝回数', ascending=False).reset_index(drop=True)

    render_html_table(rank_one_winners, max_rows=200)
    st.caption("※ 現在は互換性優先のためグラフ表示を一時停止しています。")


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
def render_main_safe_mode(scores_df: pd.DataFrame) -> None:
    """DataFrame/グラフを使わずに、カードUIで主要情報を表示する"""
    st.info("安定表示モードです。グラフは停止していますが、最新の成績とランキングを確認できます。")

    # 優勝回数ランキング（HTMLカード表示）
    st.subheader("🏆 優勝回数ランキング")
    rank_one_winners = (
        scores_df[scores_df['順位'] == 1]
        .groupby('プレイヤー名')
        .size()
        .reset_index(name='優勝回数')
        .sort_values(by='優勝回数', ascending=False)
        .head(20)
    )
    if rank_one_winners.empty:
        st.caption("ランキング対象のデータがありません。")
    else:
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
    st.subheader("🗓️ 最近の記録")
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

    for _, row in past_data_df.iterrows():
        date = html.escape(str(row.get("日付", "")))
        course = html.escape(str(row.get("コース", "")))
        player = html.escape(str(row.get("プレイヤー名", "")))
        ranking = format_number(row.get("順位", "-"))
        total = format_number(row.get("合計スコア", "-"))
        out_score = format_number(row.get("アウトスコア", "-"))
        in_score = format_number(row.get("インスコア", "-"))
        st.markdown(
            f"""
            <div class="dashboard-status-card" style="margin-bottom:.5rem;">
              <span>{date}　{course}</span>
              <strong>{player}　{ranking}位　{total}</strong>
              <span>OUT {out_score}　/　IN {in_score}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.caption("最新12件を表示しています。全件は「競技結果」から確認できます。")


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
        response = supabase.table(table).select("id", count="exact").limit(1).execute()  # type: ignore[arg-type]
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
    """実際のリストア処理を実行する共通関数"""
    competitions = backup_data.get("competitions", []) if isinstance(backup_data, dict) else []
    players = backup_data.get("players", []) if isinstance(backup_data, dict) else []
    participants = backup_data.get("participants", []) if isinstance(backup_data, dict) else []
    scores = backup_data.get("scores", []) if isinstance(backup_data, dict) else []
    announcements = backup_data.get("announcements", []) if isinstance(backup_data, dict) else []

    if not isinstance(competitions, list) or not isinstance(players, list):
        raise ValueError("バックアップデータ形式が不正です。competitions / players が配列ではありません。")

    # 子テーブルから削除して外部キー制約を回避
    supabase.table("scores").delete().gt("id", 0).execute()
    supabase.table("participants").delete().gt("id", 0).execute()
    supabase.table("announcements").delete().gt("id", 0).execute()
    supabase.table("competitions").delete().gt("id", 0).execute()
    supabase.table("players").delete().gt("id", 0).execute()

    # 親テーブル -> 関連テーブルの順で復元
    if competitions:
        supabase.table("competitions").insert(competitions).execute()
    if players:
        supabase.table("players").insert(players).execute()
    if announcements:
        supabase.table("announcements").insert(announcements).execute()
    if participants:
        supabase.table("participants").insert(participants).execute()

    # スコアデータは量が多い可能性があるのでチャンクに分ける
    if scores:
        chunk_size = 100
        for i in range(0, len(scores), chunk_size):
            chunk = scores[i:i+chunk_size]
            supabase.table("scores").insert(chunk).execute()

def login_page():
    st.title("88会ログイン")
    
    # ログイン画面に画像を表示
    image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', '01205972-9563-43D7-B862-5B2B8DECF9FA.png')
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    
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
    
    password = st.text_input("管理者パスワードを入力してください", type="password", key="admin_password_input")
    if st.button("ログイン", key="admin_login_button"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.session_state.page = "admin"
            st.rerun()
        else:
            st.error("パスワードが間違っています")

def main_app():
    render_dashboard_shell()
    render_deploy_fingerprint()
    render_dashboard_navigation()
    render_main_mode_switch_controls()
    
    # お知らせをデータベースから取得して表示
    try:
        supabase_client = get_supabase_client()
        announcements_response = None
        
        if supabase_client:
            announcements_response = supabase_client.table("announcements").select("*").eq("is_active", True).order("display_order", desc=True).limit(1).execute()
        
        if announcements_response and announcements_response.data and len(announcements_response.data) > 0:
            announcement = announcements_response.data[0]
            
            # タイトル表示
            st.markdown(f"### 🏌️ {announcement.get('title', 'お知らせ')}")
            
            # 画像があれば表示
            if announcement.get('image_url'):
                try:
                    st.image(announcement.get('image_url'), use_container_width=True)
                except:
                    pass
            
            # 本文表示
            if announcement.get('content'):
                st.info(announcement.get('content'))
            
            # 大会情報があれば整形して表示
            if announcement.get('tournament_info'):
                info = announcement.get('tournament_info')
                if isinstance(info, str):
                    info = json.loads(info)
                
                info_text = f"\n**【第{info.get('tournament_number', '')}回　88会】**\n"
                if info.get('date'):
                    info_text += f"📅 **開催日**: {info.get('date')} {info.get('start_time', '')}スタート\n"
                if info.get('course_name'):
                    info_text += f"⛳ **コース**: {info.get('course_name')}\n"
                if info.get('course_url'):
                    info_text += f"🔗 **HP**: {info.get('course_url')}\n"
                if info.get('address'):
                    info_text += f"📍 **住所**: {info.get('address')}\n"
                if info.get('phone'):
                    info_text += f"📞 **TEL**: {info.get('phone')}\n"
                if info.get('groups'):
                    info_text += f"👥 **組数**: {info.get('groups')}組\n"
                if info.get('meeting_time'):
                    info_text += f"🕗 **集合時間**: {info.get('meeting_time')}\n"
                if info.get('fee'):
                    info_text += f"💰 **費用**: {info.get('fee')}\n"
                if info.get('organizers'):
                    info_text += f"👔 **幹事**: {info.get('organizers')}\n"
                
                st.markdown(info_text)
        else:
            # デフォルトのお知らせ（データベースにデータがない場合）
            st.markdown("### 🏌️ 第52回88会ゴルフコンペのご案内")
            st.info("""
次回の開催場所は前回同様本千葉カントリーとなりました。

**【52回　88会】**  
📅 **開催日**: 12月6日　9:07スタート  
⛳ **コース**: 本千葉カントリークラブ  
🔗 **HP**: https://www.honchiba-cc.co.jp/  
📍 **住所**: 千葉市緑区大金沢町311  
📞 **TEL**: 043-292-0191  
👥 **組数**: 3組  
🕗 **集合時間**: 8:30  
💰 **費用**: 18,000+昼食（少し引いてくれるかも）  
👔 **幹事**: 吉井.福澤
    """)
    except Exception as e:
        # エラー時はデフォルトのお知らせを表示
        st.markdown("### 🏌️ 第52回88会ゴルフコンペのご案内")
        st.info("""
次回の開催場所は前回同様本千葉カントリーとなりました。

**【52回　88会】**  
📅 **開催日**: 12月6日　9:07スタート  
⛳ **コース**: 本千葉カントリークラブ  
🔗 **HP**: https://www.honchiba-cc.co.jp/  
📍 **住所**: 千葉市緑区大金沢町311  
📞 **TEL**: 043-292-0191  
👥 **組数**: 3組  
🕗 **集合時間**: 8:30  
💰 **費用**: 18,000+昼食（少し引いてくれるかも）  
👔 **幹事**: 吉井.福澤
    """)
    
    # Supabaseからデータを取得
    scores_df = fetch_scores()
    players_df = fetch_players()
    competitions_df = fetch_competitions()
    
    if not scores_df.empty and not players_df.empty:
        render_dashboard_status(scores_df, players_df, competitions_df)
        st.markdown('<div class="dashboard-section-label">成績ダイジェスト</div>', unsafe_allow_html=True)
        # 最終切り分け用: safe モードでは最小表示のみ行う
        render_mode = resolve_main_render_mode()
        if render_mode == "safe":
            render_main_safe_mode(scores_df)
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

def admin_app():
    """管理者向けアプリ"""
    st.title("ゴルフコンペ管理 - 管理者モード")
    
    # 上部にナビゲーションボタンを配置
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
    
    st.markdown("---")

    supabase_admin = get_supabase_admin_client()
    if not supabase_admin:
        st.error("管理者用クライアントの初期化に失敗しました。設定を確認してください。")
        st.info("💡 ヒント: 環境変数 SUPABASE_SERVICE_KEY が正しく設定されているか確認してください。")
        return

    tab_titles = ["お知らせ管理", "プレイヤー管理", "コンペ設定", "スコア入力", "バックアップ", "リストア"]
    tabs = st.tabs(tab_titles)

    with tabs[0]:
        announcement_management_tab(supabase_admin)

    with tabs[1]:
        player_management_tab(supabase_admin)

    with tabs[2]:
        competition_management_tab(supabase_admin)

    with tabs[3]:
        score_entry_tab()

    with tabs[4]:
        st.subheader("データベースのバックアップ")
        if st.button("バックアップを実行", key="backup_button"):
            backup_database(supabase_admin)

    with tabs[5]:
        st.subheader("データベースのリストア")
        restore_database(supabase_admin)


def login_app():
    """ログイン画面"""
    st.title("ログイン")
    
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

