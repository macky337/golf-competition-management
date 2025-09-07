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


バージョン表示を追加した
"""

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
from supabase import create_client
from dotenv import load_dotenv
import subprocess
import warnings
import logging
import japanize_matplotlib
import re
import traceback

import matplotlib
import platform

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
    """現在のGitリビジョン（コミットハッシュ）を取得する"""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "dev"  # Git情報が取得できない場合

def get_git_count():
    """Gitのコミット数を取得する"""
    try:
        return subprocess.check_output(['git', 'rev-list', '--count', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "0"  # Git情報が取得できない場合

def get_git_date():
    """最新コミットの日付を取得する"""
    try:
        return subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short']).decode('ascii').strip()
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')  # Git情報が取得できない場合は現在日付

def get_git_latest_commit_message():
    """最新のコミットメッセージを取得する"""
    try:
        return subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip()
    except Exception:
        return ""  # Git情報が取得できない場合は空文字列

def parse_version_from_commit_history():
    """コミット履歴を解析して、適切なバージョン番号を生成する"""
    try:
        # 最新50コミットを取得
        import subprocess
        result = subprocess.run(['git', 'log', '--oneline', '-50'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode != 0:
            # Gitコマンドが失敗した場合、環境変数から取得を試す
            env_version = os.environ.get('APP_VERSION')
            if env_version:
                return env_version
            # 最後の手段として、固定バージョンを返す
            return '1.15.15'  # 最後に確認できた正確なバージョン
        
        commits = result.stdout.strip().split('\n')
        
        major = 1
        minor = 0
        patch = 0
        
        for commit in commits:
            commit_lower = commit.lower()
            
            # メジャーバージョンアップのキーワード
            if 'major:' in commit_lower or 'breaking:' in commit_lower:
                major += 1
                minor = 0
                patch = 0
            # マイナーバージョンアップのキーワード
            elif 'feature:' in commit_lower or 'feat:' in commit_lower:
                minor += 1
                patch = 0
            # パッチバージョンアップのキーワード
            elif 'fix:' in commit_lower or 'patch:' in commit_lower or 'bug:' in commit_lower:
                patch += 1
            else:
                # その他のコミットもpatchとしてカウント
                patch += 1
        
        return f'{major}.{minor}.{patch}'
    
    except Exception as e:
        # 例外が発生した場合も環境変数から取得を試す
        env_version = os.environ.get('APP_VERSION')
        if env_version:
            return env_version
        # Git情報が取得できない場合は最後に確認できたバージョン
        return '1.15.15'

def get_app_version():
    """アプリのバージョンを動的に取得する"""
    try:
        # セッションステートにバージョンをキャッシュ
        if 'app_version' not in st.session_state:
            st.session_state.app_version = parse_version_from_commit_history()
        return st.session_state.app_version
    except Exception:
        # 環境変数から取得を試す
        env_version = os.environ.get('APP_VERSION')
        if env_version:
            return env_version
        return "1.15.15"  # 最後に確認できた正確なバージョン

def get_app_last_update():
    """アプリの最終更新日を動的に取得する"""
    try:
        return get_git_date()
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')  # 現在の日付

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
load_dotenv()

# Supabase接続情報 - Streamlit secretsと環境変数の両方をサポート
try:
    # まずStreamlit secretsを試す
    SUPABASE_URL = st.secrets.get("supabase", {}).get("url", "")
    SUPABASE_KEY = st.secrets.get("supabase", {}).get("key", "")
except Exception:
    # 次に環境変数を試す
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# 接続情報が不足している場合の対応
if not SUPABASE_URL or not SUPABASE_KEY:
    st.warning("""
    Supabase接続情報が見つかりません。以下のいずれかの方法で設定してください：
    
    1. ローカル開発環境: プロジェクトルートに `.env` ファイルを作成し、以下を設定
       ```
       SUPABASE_URL=あなたのSupabaseのURL
       SUPABASE_KEY=あなたのSupabaseのAPIキー
       ```
    
    2. Streamlit Cloud: `.streamlit/secrets.toml` ファイルを作成、または Streamlit Cloud の設定画面で以下を設定
       ```
       [supabase]
       url = "あなたのSupabaseのURL"
       key = "あなたのSupabaseのAPIキー"
       ```
    
    3. その他のデプロイ環境: 環境変数 `SUPABASE_URL` および `SUPABASE_KEY` を設定
    """)

# ログイン用のパスワード設定
USER_PASSWORD = "88"
ADMIN_PASSWORD = "admin88"

# 次回開催告知情報
NEXT_TOURNAMENT_INFO = {
    "tournament_number": "第51回",
    "event_name": "88会",
    "date": "2025年9月6日（土）",
    "course": "未定",
    "course_note": "※千葉県のゴルフ場の予定",
    "start_time": "未定（早い時間のスタート予定）",
    "groups": "4組",
    "briefing_time": "未定",
    "cost": "未定",
    "organizers": "福澤・関野"
}

# セッション状態を初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"  # デフォルト：ログイン画面

def display_next_tournament_announcement():
    """次回開催のお知らせを表示"""
    st.markdown("---")
    
    # 告知ヘッダーをカラフルに
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #1f4e79, #2980b9);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
    ">
        <h2 style="color: white; margin: 0; font-weight: bold;">
            🏌️ 次回開催のお知らせ 🏌️
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # 開催情報を見やすく表示
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div style="
            background-color: #f8f9fa;
            border-left: 5px solid #28a745;
            padding: 20px;
            border-radius: 5px;
            margin: 10px 0;
        ">
            <h3 style="color: #28a745; margin-top: 0;">
                {NEXT_TOURNAMENT_INFO['tournament_number']} {NEXT_TOURNAMENT_INFO['event_name']}
            </h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #495057; width: 25%;">📅 開催日：</td>
                    <td style="padding: 8px 0; color: #212529;">{NEXT_TOURNAMENT_INFO['date']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #495057;">🏌️ コース：</td>
                    <td style="padding: 8px 0; color: #212529;">
                        {NEXT_TOURNAMENT_INFO['course']}<br>
                        <small style="color: #6c757d;">{NEXT_TOURNAMENT_INFO['course_note']}</small>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #495057;">⏰ スタート時間：</td>
                    <td style="padding: 8px 0; color: #212529;">{NEXT_TOURNAMENT_INFO['start_time']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #495057;">👥 組数：</td>
                    <td style="padding: 8px 0; color: #212529;">{NEXT_TOURNAMENT_INFO['groups']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #495057;">📋 朝礼時間：</td>
                    <td style="padding: 8px 0; color: #212529;">{NEXT_TOURNAMENT_INFO['briefing_time']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #495057;">💰 費用：</td>
                    <td style="padding: 8px 0; color: #212529;">{NEXT_TOURNAMENT_INFO['cost']}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold; color: #495057;">👔 幹事：</td>
                    <td style="padding: 8px 0; color: #212529; font-weight: bold;">{NEXT_TOURNAMENT_INFO['organizers']}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    
    # 注意事項・お願い
    st.info("📝 詳細が決まり次第、改めてご連絡いたします。皆様のご参加をお待ちしております！")
    
    st.markdown("---")

# Supabase接続情報が設定されているか確認
if not SUPABASE_URL or not SUPABASE_KEY:
    st.warning("""
    Supabase接続情報が見つかりません。以下のいずれかの方法で設定してください：
    
    1. ローカル開発環境: プロジェクトルートに `.env` ファイルを作成し、以下を設定
       ```
       SUPABASE_URL=あなたのSupabaseのURL
       SUPABASE_KEY=あなたのSupabaseのAPIキー
       ```
    
    2. Streamlit Cloud: `.streamlit/secrets.toml` ファイルを作成、または Streamlit Cloud の設定画面で以下を設定
       ```
       [supabase]
       url = "あなたのSupabaseのURL"
       key = "あなたのSupabaseのAPIキー"
       ```
    
    3. その他のデプロイ環境: 環境変数 `SUPABASE_URL` および `SUPABASE_KEY` を設定
    """)

# ログイン用のパスワード設定
USER_PASSWORD = "88"
ADMIN_PASSWORD = "admin88"

# 次回開催告知情報
NEXT_TOURNAMENT_INFO = {
    "tournament_number": "第51回",
    "event_name": "88会",
    "date": "2025年9月6日（土）",
    "course": "未定",
    "course_note": "※千葉県のゴルフ場の予定",
    "start_time": "未定（早い時間のスタート予定）",
    "groups": "4組",
    "briefing_time": "未定",
    "cost": "未定",
    "organizers": "福澤・関野"
}

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
            players = {player["id"]: player["name"] for player in players_response.data}
        
        # スコアデータを整形
        scores_list = []
        for score in scores:
            # null/Noneチェックを追加
            out_score = score["out_score"] if score["out_score"] is not None else 0
            in_score = score["in_score"] if score["in_score"] is not None else 0
            
            # 合計スコアを計算（両方のスコアが有効な場合のみ）
            if out_score > 0 and in_score > 0:
                total_score = out_score + in_score
            else:
                total_score = None  # 無効な場合はNoneを設定
            
            score_dict = {
                "競技ID": score["competition_id"],
                "日付": score["date"],
                "コース": score["course"],
                "プレイヤー名": players.get(score["player_id"], "不明"),
                "アウトスコア": out_score,
                "インスコア": in_score,
                "合計スコア": total_score,
                "ハンディキャップ": score["handicap"],
                "ネットスコア": score["net_score"],
                "順位": score["ranking"]
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
                count_response = supabase.table("backups").select("count", count="exact").execute()
                
                # バックアップカウント表示（デバッグ用）
                if hasattr(count_response, 'count') and count_response.count is not None:
                    backup_count = count_response.count
                elif 'count' in count_response.data and count_response.data['count'] is not None:
                    backup_count = count_response.data['count']
                else:
                    backup_count = len(count_response.data)
                
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
    
    # タイトルの下に画像を追加
    try:
        # 環境に依存しない正確なパスの取得
        image_file = "2025-04-13 172536.png"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        image_path = os.path.join(project_root, "image", image_file)
        
        # 画像ファイルが存在するか確認
        if os.path.exists(image_path):
            st.image(image_path, use_container_width=True)
            st.markdown("### 第50回記念大会 (2025年4月12日)")
        else:
            # 代替画像を試す
            alt_image_file = "01205972-9563-43D7-B862-5B2B8DECF9FA.png"
            alt_image_path = os.path.join(project_root, "image", alt_image_file)
            
            if os.path.exists(alt_image_path):
                st.image(alt_image_path, use_container_width=True)
            
            st.markdown("### 第50回記念大会 (2025年4月13日)")
            st.info(f"目的の画像が見つかりません。パス: {image_path}")
    except Exception as e:
        st.error(f"画像表示エラー: {e}")
        st.markdown("### 第50回記念大会 (2025年4月13日)")
    
    # 次回開催告知を表示
    display_next_tournament_announcement()
    
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
                height=None, 
                use_container_width=True
            )
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
    
    if st.button("設定画面へ"):
        st.session_state.page = "admin"
        st.rerun()  # ページを強制的に再読み込み
    
    if st.button("ログアウト"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()  # ページを強制的に再読み込み

def admin_app():
    st.title("管理者設定画面")
    
    # タブを追加してUIを整理
    tabs = st.tabs(["バックアップ", "リストア", "スコア入力", "コンペ設定", "プレイヤー管理", "その他"])
    
    with tabs[0]:
        st.subheader("データベースのバックアップ")
        if st.button("データベースをバックアップ"):
            backup_database()
    
    with tabs[1]:
        # リストアセクションはタブに移動
        restore_database()
    
    with tabs[2]:
        st.subheader("スコア入力")
        st.write("コンペ結果のスコアを入力します。")
        
        # スコア入力機能を直接埋め込み
        score_entry_tab()
    
    with tabs[3]:
        st.subheader("コンペ設定")
        st.write("コンペの開催日、ゴルフ場、参加メンバーを登録します。")
        
        # コンペ設定機能を直接埋め込み
        competition_setup_tab()
    
    with tabs[4]:
        st.subheader("プレイヤー管理")
        st.write("プレイヤーの追加、編集、削除を行います。")
        
        # プレイヤー管理機能を直接埋め込み
        player_management_tab()
    
    with tabs[5]:
        st.subheader("その他の設定")
        # 将来的に追加される可能性のある設定用のスペース
    with tabs[5]:
        st.subheader("システム情報")
        
        # バージョン情報表示
        st.write("**バージョン情報**")
        current_version = get_app_version()
        st.info(f"現在のバージョン: {current_version}")
        
        # バージョン情報の更新ボタン
        if st.button("バージョン情報を更新"):
            if 'app_version' in st.session_state:
                del st.session_state.app_version
            st.success("バージョン情報を更新しました")
            st.rerun()
    
    # ナビゲーションボタン
    col1, col2 = st.columns(2)
    with col1:
        if st.button("本体画面へ"):
            st.session_state.page = "main"
            st.rerun()  # ページを強制的に再読み込み
    
    with col2:
        if st.button("ログアウト"):
            st.session_state.admin_logged_in = False
            st.session_state.page = "login"
            st.rerun()  # ページを強制的に再読み込み

# コンペ設定タブの機能
def competition_setup_tab():
    # 以下に元々のcompetition_setup.pyの機能を組み込みます
    # セッション状態の初期化
    if "edit_mode_competition" not in st.session_state:
        st.session_state.edit_mode_competition = False
    if "selected_competition" not in st.session_state:
        st.session_state.selected_competition = None
    if "participants" not in st.session_state:
        st.session_state.participants = []
    
    # データの取得
    competitions_df = fetch_competitions()
    players_df = fetch_players()
    
    if competitions_df.empty or players_df.empty:
        st.error("コンペまたはプレイヤーのデータが取得できませんでした。")
        if st.button("再試行", key="retry_competition"):
            st.rerun()
        return
    
    # タブを設定
    setup_tab1, setup_tab2 = st.tabs(["コンペ登録", "コンペ一覧"])
    
    with setup_tab1:
        st.subheader("新規コンペ登録")
        
        # 編集モードの場合は既存のコンペ情報をロード
        competition_data = {}
        
        if st.session_state.edit_mode_competition and st.session_state.selected_competition:
            competition_id = st.session_state.selected_competition
            competition_info = competitions_df[competitions_df["competition_id"] == competition_id]
            
            if not competition_info.empty:
                competition_data = {
                    "competition_id": int(competition_id),
                    "date": competition_info.iloc[0]["date"],
                    "course": competition_info.iloc[0]["course"],
                    "is_reference": int(competition_id) >= 100
                }
                
                # 参加者情報をロード
                st.session_state.participants = fetch_participants(competition_id)
            
            st.info(f"コンペID: {competition_id} の編集モードです")
        
        # コンペ情報入力欄
        col1, col2 = st.columns(2)
        
        with col1:
            date_input = st.text_input(
                "開催日 (YYYY-MM-DD)",
                value=competition_data.get("date", datetime.now().strftime('%Y-%m-%d')),
                key="competition_date"
            )
        
        with col2:
            course_input = st.text_input(
                "ゴルフ場名",
                value=competition_data.get("course", ""),
                key="competition_course"
            )
        
        # 参考大会フラグ
        is_reference = st.checkbox(
            "参考大会（集計対象外）",
            value=competition_data.get("is_reference", False),
            help="チェックすると、このコンペは参考大会（集計対象外）となり、コンペIDは100以上になります。",
            key="is_reference"
        )
        
        # プレイヤー選択
        st.subheader("参加プレイヤー選択")
        
        # プレイヤーデータをID->名前の辞書に変換
        players_dict = dict(zip(players_df["id"], players_df["name"]))
        
        # 選択されたプレイヤー
        selected_players = []
        
        # 全選択/全解除ボタン
        col1, col2 = st.columns(2)
        with col1:
            if st.button("全プレイヤーを選択", key="select_all_players"):
                st.session_state.participants = list(players_dict.keys())
                st.rerun()
        
        with col2:
            if st.button("全選択解除", key="deselect_all_players"):
                st.session_state.participants = []
                st.rerun()
        
        # プレイヤーリストを表示（グリッド形式）
        st.write("参加プレイヤーにチェックを入れてください:")
        
        # プレイヤーをグループで表示するための準備
        player_items = list(players_dict.items())
        num_cols = 3  # 一行に表示する列数
        
        # プレイヤー選択チェックボックスをグリッド表示
        for i in range(0, len(player_items), num_cols):
            cols = st.columns(num_cols)
            for j in range(num_cols):
                idx = i + j
                if idx < len(player_items):
                    player_id, player_name = player_items[idx]
                    with cols[j]:
                        checked = st.checkbox(
                            player_name,
                            value=player_id in st.session_state.participants,
                            key=f"player_competition_{player_id}"
                        )
                        if checked and player_id not in selected_players:
                            selected_players.append(player_id)
        
        # 選択されたプレイヤーを更新
        if selected_players:
            st.session_state.participants = selected_players
        
        # 登録ボタン
        if st.button("コンペ情報を保存", key="save_competition"):
            # 入力検証
            if not date_input:
                st.error("開催日を入力してください")
            elif not course_input:
                st.error("ゴルフ場名を入力してください")
            elif not st.session_state.participants:
                st.warning("参加プレイヤーが選択されていません。このまま保存しますか？")
                if st.button("はい、保存します", key="confirm_save_no_players"):
                    competition_data = {
                        "date": date_input,
                        "course": course_input,
                        "is_reference": is_reference
                    }
                    
                    if st.session_state.edit_mode_competition and st.session_state.selected_competition:
                        competition_data["competition_id"] = st.session_state.selected_competition
                    
                    success, message = save_competition(competition_data, st.session_state.participants)
                    
                    if success:
                        st.success(message)
                        # 編集モードをリセット
                        st.session_state.edit_mode_competition = False
                        st.session_state.selected_competition = None
                        st.session_state.participants = []
                        st.rerun()
                    else:
                        st.error(message)
            else:
                # コンペデータの準備
                competition_data = {
                    "date": date_input,
                    "course": course_input,
                    "is_reference": is_reference
                }
                
                if st.session_state.edit_mode_competition and st.session_state.selected_competition:
                    competition_data["competition_id"] = st.session_state.selected_competition
                
                success, message = save_competition(competition_data, st.session_state.participants)
                
                if success:
                    st.success(message)
                    # 編集モードをリセット
                    st.session_state.edit_mode_competition = False
                    st.session_state.selected_competition = None
                    st.session_state.participants = []
                    st.rerun()
                else:
                    st.error(message)
        
        # キャンセルボタン（編集モードの場合のみ表示）
        if st.session_state.edit_mode_competition:
            if st.button("編集をキャンセル", key="cancel_competition_edit"):
                st.session_state.edit_mode_competition = False
                st.session_state.selected_competition = None
                st.session_state.participants = []
                st.rerun()
    
    with setup_tab2:
        st.subheader("コンペ一覧")
        
        # 削除確認用のセッション状態
        if "delete_confirm_competition" not in st.session_state:
            st.session_state.delete_confirm_competition = None
        if "delete_message_competition" not in st.session_state:
            st.session_state.delete_message_competition = ""
        
        # 前回の削除操作の結果を表示
        if st.session_state.delete_message_competition:
            st.success(st.session_state.delete_message_competition)
            # メッセージをクリア
            st.session_state.delete_message_competition = ""
        
        # コンペ一覧の表示
        if not competitions_df.empty:
            # IDでソート
            competitions_df = competitions_df.sort_values(by="competition_id", ascending=False)
            
            # 対象大会と参考大会を分けて表示
            st.write("### 対象大会（ID < 100）")
            target_competitions = competitions_df[competitions_df["competition_id"] < 100]
            
            if not target_competitions.empty:
                for _, comp in target_competitions.iterrows():
                    comp_id = comp["competition_id"]
                    date = comp["date"]
                    course = comp["course"]
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"ID: {comp_id} - {date} {course}")
                    
                    with col2:
                        if st.button("編集", key=f"edit_competition_{comp_id}"):
                            st.session_state.edit_mode_competition = True
                            st.session_state.selected_competition = comp_id
                            st.rerun()
                    
                    with col3:
                        # 削除ボタン
                        if st.session_state.delete_confirm_competition == comp_id:
                            # 削除確認中
                            if st.button("はい、削除します", key=f"confirm_yes_competition_{comp_id}"):
                                success, message = delete_competition(comp_id)
                                if success:
                                    st.session_state.delete_message_competition = message
                                    st.session_state.delete_confirm_competition = None
                                    st.rerun()
                                else:
                                    st.error(message)
                            if st.button("キャンセル", key=f"confirm_no_competition_{comp_id}"):
                                st.session_state.delete_confirm_competition = None
                                st.rerun()
                        else:
                            # 削除ボタン（確認前）
                            if st.button("削除", key=f"delete_competition_{comp_id}"):
                                st.session_state.delete_confirm_competition = comp_id
                                st.rerun()
            else:
                st.info("対象大会のデータがありません")
            
            st.write("### 参考大会（ID >= 100）")
            reference_competitions = competitions_df[competitions_df["competition_id"] >= 100]
            
            if not reference_competitions.empty:
                for _, comp in reference_competitions.iterrows():
                    comp_id = comp["competition_id"]
                    date = comp["date"]
                    course = comp["course"]
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"ID: {comp_id} - {date} {course}")
                    
                    with col2:
                        if st.button("編集", key=f"edit_reference_{comp_id}"):
                            st.session_state.edit_mode_competition = True
                            st.session_state.selected_competition = comp_id
                            st.rerun()
                    
                    with col3:
                        # 削除ボタン
                        if st.session_state.delete_confirm_competition == comp_id:
                            # 削除確認中
                            if st.button("はい、削除します", key=f"confirm_yes_reference_{comp_id}"):
                                success, message = delete_competition(comp_id)
                                if success:
                                    st.session_state.delete_message_competition = message
                                    st.session_state.delete_confirm_competition = None
                                    st.rerun()
                                else:
                                    st.error(message)
                            if st.button("キャンセル", key=f"confirm_no_reference_{comp_id}"):
                                st.session_state.delete_confirm_competition = None
                                st.rerun()
                        else:
                            # 削除ボタン（確認前）
                            if st.button("削除", key=f"delete_reference_{comp_id}"):
                                st.session_state.delete_confirm_competition = comp_id
                                st.rerun()
            else:
                st.info("参考大会のデータがありません")
        else:
            st.info("コンペデータがありません")

def fetch_participants(competition_id):
    """参加者データをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    try:
        # participantsテーブルから該当コンペの参加者を取得
        response = supabase.table("participants").select("*").eq("competition_id", competition_id).execute()
        
        if not response.data:
            return []
        
        # participantsテーブルからplayer_idのリストを作成
        return [participant["player_id"] for participant in response.data]
    except Exception as e:
        st.error(f"参加者データ取得エラー: {e}")
        return []

def save_competition(competition_data, participants_data):
    """コンペデータをSupabaseに保存"""
    supabase = get_supabase_client()
    if not supabase:
        return False, "Supabaseに接続できません"
    
    try:
        # 既存のコンペか新規コンペかを確認
        is_new = "competition_id" not in competition_data or competition_data["competition_id"] is None
        
        if is_new:
            # 新規コンペの場合はcompetition_idを自動設定
            # 既存のcompetition_idの最大値を取得して+1
            response = supabase.table("competitions").select("competition_id").execute()
            existing_ids = [record.get("competition_id", 0) for record in response.data]
            next_id = max(existing_ids) + 1 if existing_ids else 1
            
            # 参考大会フラグに基づいてIDを調整
            is_reference = competition_data.get("is_reference", False)
            if is_reference and next_id < 100:
                next_id = 100  # 参考大会は100以上のIDを使用
            elif not is_reference and next_id >= 100:
                # 対象大会の場合は100未満のIDにする
                # 既存の対象大会の最大IDを取得
                target_response = supabase.table("competitions").select("competition_id").lt("competition_id", 100).execute()
                target_ids = [record.get("competition_id", 0) for record in target_response.data]
                next_id = max(target_ids) + 1 if target_ids else 1
            
            competition_data["competition_id"] = next_id
            
            # competitionsテーブルに挿入
            insert_response = supabase.table("competitions").insert({
                "competition_id": next_id,
                "date": competition_data["date"],
                "course": competition_data["course"]
            }).execute()
            
            competition_id = next_id
            
        else:
            # 既存のコンペを更新
            competition_id = competition_data["competition_id"]
            update_response = supabase.table("competitions").update({
                "date": competition_data["date"],
                "course": competition_data["course"]
            }).eq("competition_id", competition_id).execute()
            
            # 既存の参加者データを削除
            delete_response = supabase.table("participants").delete().eq("competition_id", competition_id).execute()
        
        # 参加者データを登録
        if participants_data:
            participants_records = []
            for player_id in participants_data:
                participants_records.append({
                    "competition_id": competition_id,
                    "player_id": player_id
                })
            
            if participants_records:
                participants_response = supabase.table("participants").insert(participants_records).execute()
        
        return True, f"コンペデータを{'登録' if is_new else '更新'}しました。コンペID: {competition_id}"
    
    except Exception as e:
        st.error(traceback.format_exc())
        return False, f"データ保存エラー: {e}"

def delete_competition(competition_id):
    """コンペデータをSupabaseから削除"""
    supabase = get_supabase_client()
    if not supabase:
        return False, "Supabaseに接続できません"
    
    try:
        # 参加者データを削除
        participants_delete = supabase.table("participants").delete().eq("competition_id", competition_id).execute()
        
        # スコアデータを削除
        scores_delete = supabase.table("scores").delete().eq("competition_id", competition_id).execute()
        
        # コンペデータを削除
        competitions_delete = supabase.table("competitions").delete().eq("competition_id", competition_id).execute()
        
        return True, f"コンペID:{competition_id}のデータを削除しました"
    
    except Exception as e:
        return False, f"データ削除エラー: {e}"

# プレイヤー管理タブの機能
def player_management_tab():
    # プレイヤー管理機能をここに実装
    if "edit_mode_player" not in st.session_state:
        st.session_state.edit_mode_player = False
    if "selected_player" not in st.session_state:
        st.session_state.selected_player = None
        
    # プレイヤーデータを取得
    players_df = fetch_players()
    
    if players_df.empty:
        st.error("プレイヤーデータの取得に失敗しました。")
        return
        
    # タブを設定
    player_tab1, player_tab2 = st.tabs(["プレイヤー登録", "プレイヤー一覧"])
    
    with player_tab1:
        st.subheader("新規プレイヤー登録")
        
        player_data = {}
        
        # 編集モードの場合は既存のプレイヤー情報をロード
        if st.session_state.edit_mode_player and st.session_state.selected_player:
            player_id = st.session_state.selected_player
            player_info = players_df[players_df["id"] == player_id]
            
            if not player_info.empty:
                player_data = {
                    "id": player_id,
                    "name": player_info.iloc[0]["name"],
                    "handicap": player_info.iloc[0]["handicap"] if "handicap" in player_info.columns else 0,
                    "active": player_info.iloc[0]["active"] if "active" in player_info.columns else True
                }
            
            st.info(f"プレイヤーID: {player_id} の編集モードです")
            
        # プレイヤー情報入力欄
        name_input = st.text_input(
            "名前",
            value=player_data.get("name", ""),
            key="player_name"
        )
        
        handicap_input = st.number_input(
            "ハンディキャップ",
            value=float(player_data.get("handicap", 0.0)),
            format="%.1f",
            step=0.1,
            key="player_handicap"
        )
        
        is_active = st.checkbox(
            "アクティブ",
            value=player_data.get("active", True),
            help="チェックを外すと非アクティブ（引退など）になります",
            key="player_is_active"
        )
        
        # 登録・更新ボタン
        if st.button("プレイヤー情報を保存", key="save_player"):
            if not name_input:
                st.error("名前を入力してください")
            else:
                # プレイヤーデータの準備
                updated_player_data = {
                    "name": name_input,
                    "handicap": handicap_input,
                    "active": is_active
                }
                
                if st.session_state.edit_mode_player and st.session_state.selected_player:
                    updated_player_data["id"] = st.session_state.selected_player
                    
                # プレイヤーデータを保存
                success, message = save_player(updated_player_data)
                
                if success:
                    st.success(message)
                    # 編集モードをリセット
                    st.session_state.edit_mode_player = False
                    st.session_state.selected_player = None
                    st.rerun()
                else:
                    st.error(message)
                    
        # キャンセルボタン（編集モード時のみ表示）
        if st.session_state.edit_mode_player:
            if st.button("編集をキャンセル", key="cancel_player_edit"):
                st.session_state.edit_mode_player = False
                st.session_state.selected_player = None
                st.rerun()
    
    with player_tab2:
        st.subheader("プレイヤー一覧")
        
        # 削除確認用のセッション状態
        if "delete_confirm_player" not in st.session_state:
            st.session_state.delete_confirm_player = None
        if "delete_message_player" not in st.session_state:
            st.session_state.delete_message_player = ""
            
        # 前回の削除操作結果を表示
        if st.session_state.delete_message_player:
            st.success(st.session_state.delete_message_player)
            st.session_state.delete_message_player = ""
            
        # プレイヤー一覧表示
        if not players_df.empty:
            # 表示用にプレイヤーをソート
            players_df = players_df.sort_values(by="name")
            
            for _, player in players_df.iterrows():
                player_id = player["id"]
                name = player["name"]
                handicap = player["handicap"] if "handicap" in player.index else 0.0
                active_status = player["active"] if "active" in player.index else True
                
                # アクティブ状態によって行の色を変える
                row_color = "" if active_status else "color: gray;"
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    display_name = name
                    if not active_status:
                        display_name += "（非アクティブ）"
                    st.markdown(f"<span style='{row_color}'>{display_name}</span>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"<span style='{row_color}'>HCP: {handicap:.1f}</span>", unsafe_allow_html=True)
                
                with col3:
                    if st.button("編集", key=f"edit_player_{player_id}"):
                        st.session_state.edit_mode_player = True
                        st.session_state.selected_player = player_id
                        st.rerun()
                
                with col4:
                    # 削除ボタン
                    if st.session_state.delete_confirm_player == player_id:
                        # 削除確認中
                        col4a, col4b = st.columns(2)
                        with col4a:
                            if st.button("はい", key=f"confirm_yes_player_{player_id}"):
                                success, message = delete_player(player_id)
                                if success:
                                    st.session_state.delete_message_player = message
                                    st.session_state.delete_confirm_player = None
                                    st.rerun()
                                else:
                                    st.error(message)
                        with col4b:
                            if st.button("いいえ", key=f"confirm_no_player_{player_id}"):
                                st.session_state.delete_confirm_player = None
                                st.rerun()
                    else:
                        # 削除ボタン（確認前）
                        if st.button("削除", key=f"delete_player_{player_id}"):
                            st.session_state.delete_confirm_player = player_id
                            st.rerun()
            else:
                st.info("条件に合うプレイヤーはいません")
        else:
            st.info("プレイヤーデータがありません")

def save_player(player_data):
    """プレイヤーデータをSupabaseに保存"""
    supabase = get_supabase_client()
    if not supabase:
        return False, "Supabaseに接続できません"
    
    try:
        # 既存のプレイヤーか新規プレイヤーかを確認
        is_new = "id" not in player_data or player_data["id"] is None
        
        if is_new:
            # 新規プレイヤーの場合はinsert
            insert_response = supabase.table("players").insert({
                "name": player_data["name"],
                "handicap": player_data["handicap"],
                "active": player_data["active"]
            }).execute()
            
            return True, f"プレイヤー「{player_data['name']}」を登録しました"
        else:
            # 既存のプレイヤーを更新
            player_id = player_data["id"]
            update_response = supabase.table("players").update({
                "name": player_data["name"],
                "handicap": player_data["handicap"],
                "active": player_data["active"]
            }).eq("id", player_id).execute()
            
            return True, f"プレイヤー「{player_data['name']}」を更新しました"
    
    except Exception as e:
        import traceback
        st.error(traceback.format_exc())
        return False, f"データ保存エラー: {e}"

def delete_player(player_id):
    """プレイヤーデータをSupabaseから削除"""
    supabase = get_supabase_client()
    if not supabase:
        return False, "Supabaseに接続できません"
    
    try:
        # プレイヤー名を取得（削除メッセージ用）
        player_response = supabase.table("players").select("name").eq("id", player_id).execute()
        player_name = player_response.data[0]["name"] if player_response.data else "不明"
        
        # プレイヤーが参加しているコンペをチェック
        participants_response = supabase.table("participants").select("*").eq("player_id", player_id).execute()
        
        if participants_response.data:
            # 参加しているコンペがある場合は物理削除せずに非アクティブにする
            update_response = supabase.table("players").update({
                "active": False
            }).eq("id", player_id).execute()
            
            return True, f"プレイヤー「{player_name}」を非アクティブに設定しました（コンペ参加データがあるため）"
        else:
            # コンペ参加データがない場合は物理削除
            delete_response = supabase.table("players").delete().eq("id", player_id).execute()
            
            return True, f"プレイヤー「{player_name}」を削除しました"
    
    except Exception as e:
        return False, f"データ削除エラー: {e}"

# スコア入力タブの機能
def score_entry_tab():
    # スコア入力画面のメイン機能をここに実装
    st.write("コンペ結果のスコアデータを入力します。")
    
    # 必要なセッション状態の初期化
    if "selected_competition_for_score" not in st.session_state:
        st.session_state.selected_competition_for_score = None
    if "scores_data" not in st.session_state:
        st.session_state.scores_data = {}
    
    # コンペデータを取得
    competitions_df = fetch_competitions()
    
    if competitions_df.empty:
        st.error("コンペデータの取得に失敗しました。")
        return
    
    # 最新のコンペを上に表示するソート
    competitions_df = competitions_df.sort_values(by="competition_id", ascending=False)
    
    # コンペ選択オプション
    competition_options = [f"ID:{row['competition_id']} - {row['date']} {row['course']}" for _, row in competitions_df.iterrows()]
    selected_option = st.selectbox(
        "スコア入力するコンペを選択してください", 
        competition_options,
        key="score_competition_select"
    )
    
    if selected_option:
        # 選択されたコンペIDを抽出
        competition_id = int(selected_option.split(" - ")[0].replace("ID:", ""))
        st.session_state.selected_competition_for_score = competition_id
        
        # 選択されたコンペの情報を表示
        competition_info = competitions_df[competitions_df["competition_id"] == competition_id].iloc[0]
        st.write(f"コンペ日付: {competition_info['date']}")
        st.write(f"ゴルフ場: {competition_info['course']}")
        
        # 参加者データを取得
        participants = fetch_participants(competition_id)
        if not participants:
            st.warning("このコンペには参加者が登録されていません。先にコンペ設定で参加者を登録してください。")
            return
        
        # プレイヤーデータを取得してIDから名前へのマッピングを作成
        players_df = fetch_players()
        players_dict = dict(zip(players_df["id"], players_df["name"]))
        
        # 既存のスコアデータを取得
        existing_scores = fetch_competition_scores(competition_id)
        
        # スコア入力フォームを表示
        st.subheader("スコア入力")
        
        # 参加者ごとのスコア入力欄
        score_data = {}
        
        for player_id in participants:
            if player_id in players_dict:
                player_name = players_dict[player_id]
                
                # このプレイヤーの既存スコアがあれば取得
                player_existing_score = existing_scores[existing_scores["player_id"] == player_id] if not existing_scores.empty else pd.DataFrame()
                
                st.write(f"### {player_name}")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    out_score = st.number_input(
                        "アウトスコア",
                        min_value=0,
                        value=int(player_existing_score["out_score"].iloc[0]) if not player_existing_score.empty and "out_score" in player_existing_score.columns else 0,
                        key=f"out_score_{player_id}"
                    )
                
                with col2:
                    in_score = st.number_input(
                        "インスコア",
                        min_value=0,
                        value=int(player_existing_score["in_score"].iloc[0]) if not player_existing_score.empty and "in_score" in player_existing_score.columns else 0,
                        key=f"in_score_{player_id}"
                    )
                
                with col3:
                    total_score = out_score + in_score if out_score > 0 and in_score > 0 else None
                    st.write(f"合計スコア: {total_score if total_score else '未入力'}")
                
                with col4:
                    handicap = st.number_input(
                        "ハンディキャップ",
                        min_value=0.0,
                        max_value=50.0,
                        value=float(player_existing_score["handicap"].iloc[0]) if not player_existing_score.empty and "handicap" in player_existing_score.columns else float(players_df[players_df["id"] == player_id]["handicap"].iloc[0]) if "handicap" in players_df.columns else 0.0,
                        format="%.1f",
                        step=0.1,
                        key=f"handicap_{player_id}"
                    )
                
                # ネットスコアの計算
                if total_score:
                    net_score = total_score - handicap
                    st.write(f"ネットスコア: {net_score:.1f}")
                
                # スコアデータを辞書に格納
                score_data[player_id] = {
                    "out_score": out_score,
                    "in_score": in_score,
                    "total_score": total_score,
                    "handicap": handicap,
                    "net_score": net_score if total_score else None
                }
        
        # スコアデータをセッションに保存
        st.session_state.scores_data = score_data
        
        # スコア保存ボタン
        if st.button("スコアデータを保存", key="save_scores"):
            if score_data:
                success, message = save_scores(competition_id, score_data)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("保存するスコアデータがありません")

def fetch_competition_scores(competition_id):
    """指定されたコンペのスコアデータを取得"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        # スコアテーブルから指定コンペのスコアを取得
        response = supabase.table("scores").select("*").eq("competition_id", competition_id).execute()
        
        if not response.data:
            return pd.DataFrame()
        
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"スコアデータ取得エラー: {e}")
        return pd.DataFrame()

def save_scores(competition_id, scores_data):
    """スコアデータを保存"""
    supabase = get_supabase_client()
    if not supabase:
        return False, "Supabaseに接続できません"
    
    try:
        # まず有効なネットスコアのプレイヤーを抽出してランキングを計算
        valid_players = []
        for player_id, score in scores_data.items():
            if score["net_score"] is not None:
                valid_players.append({
                    "player_id": player_id,
                    "net_score": score["net_score"]
                })
        
        # ネットスコア順にソートして順位を付ける
        if valid_players:
            sorted_players = sorted(valid_players, key=lambda x: x["net_score"])
            rank = 1
            
            for idx, player in enumerate(sorted_players):
                player["ranking"] = rank
                
                # 同スコアなら同順位
                if idx + 1 < len(sorted_players) and player["net_score"] == sorted_players[idx + 1]["net_score"]:
                    pass  # 次のプレイヤーも同じランキング
                else:
                    rank = idx + 2  # 次の順位へ
        
        # 既存のスコアを削除
        delete_response = supabase.table("scores").delete().eq("competition_id", competition_id).execute()
        
        # 新しいスコアデータを登録
        scores_records = []
        
        for player_id, score in scores_data.items():
            # ランキングを取得
            ranking = next((p["ranking"] for p in valid_players if p["player_id"] == player_id), None)
            
            # 必須フィールドの検証
            if not player_id:
                st.error(f"プレイヤーIDが不正です: {player_id}")
                continue
                
            if not competition_id:
                st.error(f"コンペIDが不正です: {competition_id}")
                continue
            
            # scoreレコードを作成（idフィールドは明示的に除外）
            score_record = {
                "competition_id": int(competition_id),
                "player_id": int(player_id),
                "out_score": int(score["out_score"]) if score["out_score"] else None,
                "in_score": int(score["in_score"]) if score["in_score"] else None,
                "handicap": float(score["handicap"]) if score["handicap"] is not None else 0.0,
                "net_score": float(score["net_score"]) if score["net_score"] is not None else None,
                "ranking": int(ranking) if ranking is not None else None
            }
            
            # コンペの日付とコース名をscoreレコードに追加
            competition_info = fetch_competition_info(competition_id)
            if competition_info:
                score_record["date"] = competition_info.get("date", "")
                score_record["course"] = competition_info.get("course", "")
            
            # NULLフィールドのチェック（デバッグ用）
            null_fields = [k for k, v in score_record.items() if v is None]
            if null_fields:
                st.info(f"プレイヤー{player_id}のNULLフィールド: {null_fields}")
            
            scores_records.append(score_record)
        
        if scores_records:
            try:
                # デバッグ情報: 挿入しようとするレコードの最初の1件をログ出力
                st.info(f"挿入予定レコード数: {len(scores_records)}")
                # 最初のレコードの構造を表示（デバッグ用）
                sample_record = scores_records[0]
                st.info(f"サンプルレコード構造: {list(sample_record.keys())}")
                
                # まず1件ずつ挿入を試行（エラー特定のため）
                if len(scores_records) == 1:
                    # 1件のみの場合は直接挿入
                    insert_response = supabase.table("scores").insert(scores_records[0]).execute()
                else:
                    # 複数件の場合は一括挿入を試行、失敗したら1件ずつ
                    try:
                        insert_response = supabase.table("scores").insert(scores_records).execute()
                    except Exception as bulk_error:
                        st.warning(f"一括挿入に失敗: {bulk_error}")
                        st.info("1件ずつ挿入を試行します...")
                        
                        # 1件ずつ挿入
                        successful_inserts = 0
                        for i, record in enumerate(scores_records):
                            try:
                                single_response = supabase.table("scores").insert(record).execute()
                                successful_inserts += 1
                            except Exception as single_error:
                                st.error(f"レコード{i+1}の挿入に失敗: {single_error}")
                                st.error(f"問題のレコード: {record}")
                        
                        if successful_inserts > 0:
                            return True, f"部分的に成功: {successful_inserts}/{len(scores_records)}件のスコアデータを保存しました"
                        else:
                            return False, "すべてのレコードの挿入に失敗しました"
                
                # 挿入成功時のレスポンスを確認
                if insert_response.data:
                    st.success(f"挿入成功: {len(insert_response.data)}件")
                    return True, f"スコアデータを保存しました。有効なスコア: {len(valid_players)}件"
                else:
                    st.warning("挿入レスポンスのデータが空です")
                    return False, "データの保存に失敗しました（レスポンスが空）"
                
            except Exception as insert_error:
                st.error(f"挿入エラー詳細: {insert_error}")
                
                # Supabaseのエラーメッセージを解析
                if "null value in column" in str(insert_error):
                    st.error("NULL制約違反が発生しました。Supabaseのscoresテーブルの構造を確認してください。")
                    st.info("修正方法: fix_scores_table.sql を Supabase管理画面で実行してください。")
                elif "relation" in str(insert_error) and "does not exist" in str(insert_error):
                    st.error("テーブルまたはシーケンスが存在しません。")
                    st.info("修正方法: fix_scores_table.sql を Supabase管理画面で実行してください。")
                
                # 挿入するレコードの詳細を表示
                for i, record in enumerate(scores_records[:2]):  # 最大2件表示
                    st.error(f"レコード{i+1}: {record}")
                
                return False, f"データ保存エラー: {insert_error}"
        else:
            return False, "保存するスコアデータがありません"
    
    except Exception as e:
        import traceback
        st.error(traceback.format_exc())
        return False, f"データ保存エラー: {e}"

def fetch_competition_info(competition_id):
    """コンペ情報を取得"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        response = supabase.table("competitions").select("*").eq("competition_id", competition_id).execute()
        
        if not response.data:
            return None
        
        return response.data[0]
    except Exception:
        return None

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
        background-color: transparent;
        padding: 10px;
        border-radius: 5px;
        # box-shadow: 0 0 5px rgba(0,0,0,0.1);
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
def display_footer():
    connection_status = get_supabase_status()
    git_rev = get_git_revision()
    git_date = get_git_date()
    current_version = get_app_version()  # キャッシュされたバージョンを取得

    st.markdown(f"""
    <div class="vertical-footer">
        <span class="footer-item">Ver {current_version} ({git_rev})</span>
        <span class="footer-item">最終更新: {git_date}</span>
        <span class="footer-item">Supabase: {connection_status}</span>
    </div>
    """, unsafe_allow_html=True)

def page_router():
    if st.session_state.page == "main":
        if st.session_state.logged_in:
            main_app()
        else:
            login_page()
            display_footer() # ログイン前画面でのみフッター表示
    elif st.session_state.page == "admin":
        if st.session_state.admin_logged_in:
            admin_app()
        else:
            admin_login_page()
            display_footer() # 管理者ログイン前画面でのみフッター表示
    else:
        login_page()
        display_footer() # ログイン前画面でのみフッター表示

# アプリの起動
if not st.session_state.logged_in and not st.session_state.admin_logged_in:
    st.session_state.page = "login"

page_router()





