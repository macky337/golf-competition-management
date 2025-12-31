# -*- coding: utf-8 -*-
import platform


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
from typing import Optional
import re

# 他のモジュールをインポート
from announcement_management import announcement_management_tab
# プレースホルダーとして他の管理モジュールもインポート
# from player_management import player_management_tab
# from competition_management import competition_management_tab
# from score_entry import score_entry_tab


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
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"

def get_git_count():
    """Gitのコミット数を取得する"""
    try:
        return subprocess.check_output(['git', 'rev-list', '--count', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "0"  # Git情報が取得できない場合

def get_git_date():
    """Git の最終コミット日時を JST で取得"""
    try:
        # JST時間で取得を試行
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=format-local:%Y-%m-%d %H:%M'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # フォールバック：UTC時間を取得してJSTに変換
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=iso'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            # 簡易的なUTC→JST変換（+9時間）
            import re
            from datetime import datetime, timedelta
            match = re.match(r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}):\d{2}', result.stdout.strip())
            if match:
                date_part, time_part = match.groups()
                dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
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
        return subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip()
    except Exception:
        return ""  # Git情報が取得できない場合は空文字列

def parse_version_from_commit_history():
    """コミット履歴を解析し、適切なバージョン番号を計算する"""
    major = 1
    minor = 0
    patch = 0
    
    try:
        # 最新のコミットメッセージを取得
        latest_commit_message = get_git_latest_commit_message()
        
        # コミットメッセージに基づいてバージョンタイプを判断
        if re.search(r'^(major:|MAJOR:|!:)', latest_commit_message):
            # メジャーバージョンアップ
            major = 2  # 次のメジャーバージョン
            minor = 0
            patch = 0
        elif re.search(r'^(feature:|feat:|FEATURE:)', latest_commit_message):
            # マイナーバージョンアップ
            minor = 1
            patch = 0
        elif re.search(r'^(fix:|bugfix:|FIX:)', latest_commit_message):
            # パッチバージョンアップ
            patch = 1
        else:
            # コミット数を基にしたバージョン番号計算
            count = int(get_git_count())
            # より現実的なバージョン管理
            major = 1
            minor = count // 100  # 100コミットごとにマイナーバージョンアップ
            patch = count % 100   # パッチバージョンは100未満
            
        return f"{major}.{minor}.{patch}"
    except Exception:
        # デフォルトバージョン
        return "1.2.4"

def get_app_version():
    """アプリバージョンを取得（動的バージョン使用）"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            branch = result.stdout.strip()
            base_version = parse_version_from_commit_history()
            
            if branch == "main":
                return base_version  # メインブランチは動的バージョン
            elif branch == "feature-branch":
                return f"{base_version}-dev"  # 開発ブランチ
            else:
                return f"{base_version}-{branch}"  # 機能ブランチ
    except Exception:
        pass
    return "1.2.4-dev"

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
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

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
    # デバッグ情報は本番環境では非表示にする
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Supabase接続情報が設定されていません。.streamlit/secrets.tomlまたは.envファイルを確認してください。")
        return None
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # 接続テスト（静かに実行、成功メッセージは表示しない）
        test_response = supabase.table("players").select("count").limit(1).execute()
        return supabase
    except Exception as e:
        st.error(f"Supabase接続エラー: {e}")
        return None

def get_supabase_admin_client() -> Optional[Client]:
    """管理者（サービスロール）用のSupabaseクライアントを取得"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        st.error(
            "SupabaseのURLまたはサービスキーが設定されていません。\n"
            "管理者モードには Service Role Key が必要です（例: `SUPABASE_SERVICE_KEY` または `SUPABASE_SERVICE_ROLE_KEY`、"
            "または `.streamlit/secrets.toml` の `[supabase] service_key`）。"
        )
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        st.error(f"Supabase管理者クライアント接続エラー: {e}")
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
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    st.pyplot(fig)


def backup_database():
    """Supabaseからデータをバックアップする（JSONファイルとして保存、およびbackupsテーブルに保存）"""
    supabase = get_supabase_client()
    if not supabase:
        return
    
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backup'))
    if not os.path.exists(backup_dir):
        # 一つ上の階層のbackupディレクトリを試す
        parent_backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backup'))
        if (os.path.exists(parent_backup_dir)):
            backup_dir = parent_backup_dir
        else:
            os.makedirs(backup_dir)
            st.info(f"バックアップディレクトリを作成しました: {backup_dir}")
    
    try:
        # 各テーブルのデータを取得
        competitions_response = supabase.table("competitions").select("*").execute()
        players_response = supabase.table("players").select("*").execute()
        scores_response = supabase.table("scores").select("*").execute()
        
        # バックアップデータを準備
        backup_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        backup_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_data = {
            "competitions": competitions_response.data,
            "players": players_response.data,
            "scores": scores_response.data,
            "backup_date": backup_date
        }
        
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

-- 既存のポリシーがある場合は削除
DROP POLICY IF EXISTS "管理者のみbackupsテーブルにアクセス可能" ON backups;

-- すべてのユーザーがアクセスできるポリシーを作成
-- auth.roleの制限を使わず、すべての操作を許可
CREATE POLICY "backupsテーブルへのフルアクセス" ON backups
    FOR ALL
    USING (true)
    WITH CHECK (true);
            """, language="sql")
            
            # 情報メッセージを表示
            st.info("ローカルJSONバックアップのみ作成しました。Supabaseテーブルへのバックアップは次回成功します。")
            st.info("RLSポリシーの変更後は、アプリを再起動してください。")
        
        st.success(f"バックアップが作成されました: {backup_file}")
        
    except Exception as e:
        st.error(f"バックアップ中にエラーが発生しました: {e}")
        import traceback
        st.error(traceback.format_exc())

def restore_database():
    """JSONバックアップファイルまたはSupabaseのbackupsテーブルからデータをリストアする"""
    supabase = get_supabase_client()
    if not supabase:
        return
    
    # リストア方法の選択
    st.subheader("データベースのリストア")
    restore_method = st.radio(
        "リストア方法を選択してください:",
        ["ローカルJSONファイルから", "Supabaseバックアップテーブルから"]
    )
    
    if restore_method == "ローカルJSONファイルから":
        # 既存の実装：ローカルJSONファイルからのリストア
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
                
                # リストア処理を実行
                perform_restore(backup_data)
                
                st.success(f"データベースがリストアされました: {selected_backup}")
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
                
                if st.button("リストア実行"):
                    # 選択されたバックアップのIDを取得
                    selected_id = selected_backup_option.split(" ")[0]
                    
                    # backup_idかidかを判断
                    field_name = "backup_id" if any(b.get('backup_id') == selected_id for b in backups) else "id"
                    
                    # 選択されたバックアップのデータを取得
                    backup_response = supabase.table("backups").select("*").eq(field_name, selected_id).execute()
                    
                    if not backup_response.data:
                        st.error("選択されたバックアップが見つかりません。")
                        return
                    
                    # dataフィールドを取得
                    if "data" in backup_response.data[0]:
                        backup_data = backup_response.data[0]["data"]
                        
                        # リストア処理を実行
                        st.info("リストア処理を開始します...")
                        perform_restore(backup_data)
                        
                        st.success(f"Supabaseバックアップテーブルからデータがリストアされました: {selected_backup_option}")
                    else:
                        st.error(f"バックアップデータの形式が不正です。フィールド: {list(backup_response.data[0].keys())}")
                        
                        # バックアップデータの構造を表示（デバッグ用）
                        st.info("バックアップデータの構造:")
                        st.json(backup_response.data[0])
            
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

-- 既存のポリシーがある場合は削除
DROP POLICY IF EXISTS "管理者のみbackupsテーブルにアクセス可能" ON backups;

-- 管理者のみがアクセスできるポリシーを作成
CREATE POLICY "管理者のみbackupsテーブルにアクセス可能" ON backups
    USING (true);  -- すべてのユーザーがアクセス可能に変更
                """, language="sql")
        
        except Exception as e:
            st.error(f"Supabaseバックアップからのリストア中にエラーが発生しました: {e}")
            import traceback
            st.error(traceback.format_exc())

def perform_restore(backup_data):
    """実際のリストア処理を実行する共通関数"""
    supabase = get_supabase_client()
    if not supabase:
        return
    
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
            use_container_width=True
        )
        
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
            # ベストグロススコアトップ10のフォーマットを適用
            st.dataframe(
                best_gross_scores_detailed.style.format({
                    "ハンディキャップ": "{:.2f}",
                    "ネットスコア": "{:.2f}",
                    "アウトスコア": "{:.0f}",
                    "インスコア": "{:.0f}",
                    "合計スコア": "{:.0f}",
                    "順位": "{:.0f}",
                    "競技ID": "{:.0f}"
                }), 
                use_container_width=True
            )
        else:
            st.warning("有効なスコアデータが見つかりませんでした。")
        
        # 最終更新日時を表示
        st.subheader("最終更新日時")
        jst = pytz.timezone('Asia/Tokyo')
        # st.write(datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S"))
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
    """管理者向けアプリ"""
    st.title("ゴルフコンペ管理 - 管理者モード")

    supabase_admin = get_supabase_admin_client()
    if not supabase_admin:
        st.error("管理者用クライアントの初期化に失敗しました。設定を確認してください。")
        return

    tab_titles = ["お知らせ管理", "プレイヤー管理", "コンペ設定", "スコア入力", "バックアップ", "リストア"]
    tabs = st.tabs(tab_titles)

    with tabs[0]:
        announcement_management_tab(supabase_admin)

    with tabs[1]:
        st.subheader("プレイヤー管理")
        st.write("（この機能は現在開発中です）")
        # player_management_tab(supabase_admin)

    with tabs[2]:
        st.subheader("コンペ設定")
        st.write("（この機能は現在開発中です）")
        # competition_management_tab(supabase_admin)

    with tabs[3]:
        st.subheader("スコア入力")
        st.write("（この機能は現在開発中です）")
        # score_entry_tab(supabase_admin)

    with tabs[4]:
        st.subheader("データベースのバックアップ")
        if st.button("バックアップを実行"):
            backup_database()

    with tabs[5]:
        st.subheader("データベースのリストア")
        restore_database()


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
app_version = get_app_version()
git_rev = get_git_revision()
git_date = get_git_date()

st.markdown(f"""
<div class="vertical-footer">
    <span class="footer-item">Ver {app_version} ({git_rev})</span>
    <span class="footer-item">最終更新: {git_date}</span>
</div>
""", unsafe_allow_html=True)

# ページ表示（ルーティング）
page = st.session_state.get("page", "login")

if page == "login":
    login_page()
elif page == "main":
    if not st.session_state.get("logged_in", False):
        st.session_state.page = "login"
        st.rerun()
    main_app()
elif page == "admin":
    if not st.session_state.get("admin_logged_in", False):
        admin_login_page()
    else:
        admin_app()
else:
    st.session_state.page = "login"
    st.rerun()



