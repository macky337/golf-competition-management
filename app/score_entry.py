"""
88会ゴルフコンペ・スコア入力システム (Supabase版)

このスクリプトは、88会ゴルフコンペのスコアを入力するためのStreamlitアプリケーションです。
コンペ終了後、各参加者のスコアを入力し、データベースに登録することができます。
また、ネットスコアに基づいた順位付けも自動で行います。

機能:
- コンペ選択と参加メンバーの表示
- スコア入力（OUT/INスコア、ハンディキャップ）
- グロススコア・ネットスコアの自動計算
- 順位の自動計算
- スコアの登録と更新

使用方法:
1. 入力対象のコンペを選択します
2. 各プレイヤーのスコア情報を入力します
3. 「登録」ボタンをクリックしてデータをSupabaseに保存します
"""

import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client
import datetime
import pytz
import matplotlib
import platform

# 環境に応じたフォント設定
if platform.system() == 'Windows':
    matplotlib.rcParams['font.family'] = 'MS Gothic'
elif platform.system() == 'Darwin':  # Macの場合
    matplotlib.rcParams['font.family'] = 'Hiragino Maru Gothic Pro'
else:  # Linux（Streamlit Cloud含む）
    matplotlib.rcParams['font.family'] = 'IPAexGothic'

# 環境変数の読み込み
load_dotenv()

# Supabase接続情報の取得
try:
    # まずStreamlit secretsを試す
    SUPABASE_URL = st.secrets.get("supabase", {}).get("url", "")
    SUPABASE_KEY = st.secrets.get("supabase", {}).get("key", "")
except Exception:
    # 次に環境変数を試す
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ログイン用のパスワード設定
USER_PASSWORD = "88"
ADMIN_PASSWORD = "admin88"

# セッション状態の初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"  # デフォルト：ログイン画面
if "selected_competition" not in st.session_state:
    st.session_state.selected_competition = None
if "participants" not in st.session_state:
    st.session_state.participants = []
if "score_data" not in st.session_state:
    st.session_state.score_data = {}

def get_supabase_client():
    """Supabaseクライアントを取得"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Supabase接続情報が設定されていません。.streamlit/secrets.tomlまたは.envファイルを確認してください。")
        return None
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # 接続テスト
        test_response = supabase.table("players").select("count").limit(1).execute()
        return supabase
    except Exception as e:
        st.error(f"Supabase接続エラー: {e}")
        return None

def fetch_competitions():
    """コンペデータをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("competitions").select("*").order('date', desc=True).execute()
        
        if not response.data:
            st.warning("コンペデータが見つかりません。")
            return pd.DataFrame()
        
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"コンペデータ取得エラー: {e}")
        return pd.DataFrame()

def fetch_players():
    """プレイヤーデータをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("players").select("*").order('name').execute()
        
        if not response.data:
            st.warning("プレイヤーデータが見つかりません。")
            return pd.DataFrame()
        
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"プレイヤーデータ取得エラー: {e}")
        return pd.DataFrame()

def fetch_participants(competition_id):
    """参加者データをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    try:
        # participantsテーブルから該当コンペの参加者を取得
        response = supabase.table("participants").select("*").eq("competition_id", competition_id).execute()
        
        if not response.data:
            # participantsテーブルにデータがない場合は、scoresテーブルから参加者を推定
            scores_response = supabase.table("scores").select("player_id").eq("competition_id", competition_id).execute()
            if scores_response.data:
                player_ids = [score["player_id"] for score in scores_response.data]
                # 重複を削除
                player_ids = list(set(player_ids))
                return player_ids
            else:
                return []
        
        # participantsテーブルからplayer_idのリストを作成
        return [participant["player_id"] for participant in response.data]
    except Exception as e:
        st.error(f"参加者データ取得エラー: {e}")
        return []

def fetch_existing_scores(competition_id):
    """既存のスコアデータをSupabaseから取得"""
    supabase = get_supabase_client()
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("scores").select("*").eq("competition_id", competition_id).execute()
        
        if not response.data:
            return pd.DataFrame()
        
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"スコアデータ取得エラー: {e}")
        return pd.DataFrame()

def calculate_rankings(scores_data):
    """ネットスコアに基づいて順位を計算"""
    if not scores_data:
        return {}
    
    # スコアデータをネットスコアでソート
    sorted_scores = sorted(
        scores_data.items(),
        key=lambda x: (x[1].get("net_score", float('inf')), x[1].get("handicap", 0))
    )
    
    # 順位を割り当て
    rankings = {}
    for i, (player_id, _) in enumerate(sorted_scores):
        rankings[player_id] = i + 1
    
    return rankings

def save_scores(competition_id, scores_data, players_data):
    """スコアデータをSupabaseに保存"""
    supabase = get_supabase_client()
    if not supabase:
        return False
    
    try:
        # 既存のスコアを削除
        supabase.table("scores").delete().eq("competition_id", competition_id).execute()
        
        # データ登録用の辞書のリストを作成
        records_to_insert = []
        competition_info = st.session_state.competitions[
            st.session_state.competitions["competition_id"] == competition_id
        ]
        
        if competition_info.empty:
            st.error("コンペ情報が見つかりません。")
            return False
        
        date = competition_info.iloc[0]["date"]
        course = competition_info.iloc[0]["course"]
        
        # 順位を計算
        rankings = calculate_rankings(scores_data)
        
        for player_id, score_info in scores_data.items():
            if score_info.get("out_score") is not None and score_info.get("in_score") is not None:
                record = {
                    "competition_id": competition_id,
                    "player_id": player_id,
                    "date": date,
                    "course": course,
                    "out_score": score_info.get("out_score"),
                    "in_score": score_info.get("in_score"),
                    "handicap": score_info.get("handicap", 0),
                    "net_score": score_info.get("net_score", 0),
                    "ranking": rankings.get(player_id, 0)
                }
                records_to_insert.append(record)
        
        # データを登録
        if records_to_insert:
            response = supabase.table("scores").insert(records_to_insert).execute()
            return True
        else:
            st.warning("登録するスコアデータがありません。")
            return False
        
    except Exception as e:
        st.error(f"スコア登録エラー: {e}")
        import traceback
        st.error(traceback.format_exc())
        return False

def login_page():
    st.title("88会ゴルフコンペ・スコア入力")
    
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
        elif password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.session_state.page = "main"
            st.rerun()
        else:
            st.error("パスワードが間違っています")

def score_entry_page():
    st.title("88会ゴルフコンペ・スコア入力")
    
    if "competitions" not in st.session_state:
        st.session_state.competitions = fetch_competitions()
    
    if "players" not in st.session_state:
        st.session_state.players = fetch_players()
    
    if st.session_state.competitions.empty or st.session_state.players.empty:
        st.error("コンペまたはプレイヤーのデータが取得できませんでした。")
        if st.button("再試行"):
            st.session_state.competitions = fetch_competitions()
            st.session_state.players = fetch_players()
            st.rerun()
        return
    
    # コンペ選択
    competition_options = [
        f"{row['competition_id']} - {row['date']} {row['course']}" 
        for _, row in st.session_state.competitions.iterrows()
    ]
    
    competition_selection = st.selectbox(
        "スコアを入力するコンペを選択してください",
        competition_options
    )
    
    if competition_selection:
        # コンペIDを抽出
        competition_id = int(competition_selection.split(" - ")[0])
        
        if st.session_state.selected_competition != competition_id:
            st.session_state.selected_competition = competition_id
            # 参加者を取得
            st.session_state.participants = fetch_participants(competition_id)
            # 既存のスコアを取得
            existing_scores = fetch_existing_scores(competition_id)
            
            # スコアデータの初期化
            st.session_state.score_data = {}
            
            # 既存のスコアデータがあれば設定
            if not existing_scores.empty:
                for _, score in existing_scores.iterrows():
                    player_id = score["player_id"]
                    st.session_state.score_data[player_id] = {
                        "out_score": score["out_score"],
                        "in_score": score["in_score"],
                        "handicap": score["handicap"],
                        "net_score": score["net_score"]
                    }
            
            st.rerun()
        
        # プレイヤーデータをID->名前の辞書に変換
        players_dict = dict(zip(st.session_state.players["id"], st.session_state.players["name"]))
        
        if not st.session_state.participants:
            # 参加者が登録されていない場合、全プレイヤーから選択できるようにする
            st.warning("このコンペの参加者情報が登録されていません。全プレイヤーから選択できます。")
            with st.expander("参加者を選択"):
                selected_players = []
                for player_id, player_name in players_dict.items():
                    if st.checkbox(player_name, key=f"player_{player_id}"):
                        selected_players.append(player_id)
                
                if st.button("参加者を確定"):
                    st.session_state.participants = selected_players
                    st.rerun()
        else:
            # スコア入力フォームの表示
            st.subheader("スコア入力")
            
            with st.form("score_entry_form"):
                scores_changed = False
                
                # 各プレイヤーのスコア入力欄を表示
                for player_id in st.session_state.participants:
                    player_name = players_dict.get(player_id, f"不明なプレイヤー({player_id})")
                    
                    with st.expander(f"{player_name} のスコア", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        
                        # 既存の値を取得
                        existing_data = st.session_state.score_data.get(player_id, {})
                        
                        with col1:
                            out_score = st.number_input(
                                "OUTスコア",
                                min_value=0.0,
                                max_value=100.0,
                                value=existing_data.get("out_score", 0.0),
                                step=1.0,
                                format="%.1f",
                                key=f"out_{player_id}"
                            )
                        
                        with col2:
                            in_score = st.number_input(
                                "INスコア",
                                min_value=0.0,
                                max_value=100.0,
                                value=existing_data.get("in_score", 0.0),
                                step=1.0,
                                format="%.1f",
                                key=f"in_{player_id}"
                            )
                        
                        with col3:
                            handicap = st.number_input(
                                "ハンディキャップ",
                                min_value=0.0,
                                max_value=50.0,
                                value=existing_data.get("handicap", 0.0),
                                step=0.1,
                                format="%.1f",
                                key=f"hcp_{player_id}"
                            )
                        
                        # グロススコアとネットスコアを計算
                        if out_score > 0 and in_score > 0:
                            gross_score = out_score + in_score
                            net_score = gross_score - handicap
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"グロススコア: {gross_score:.1f}")
                            with col2:
                                st.info(f"ネットスコア: {net_score:.1f}")
                            
                            # スコアデータを更新
                            st.session_state.score_data[player_id] = {
                                "out_score": out_score,
                                "in_score": in_score,
                                "handicap": handicap,
                                "gross_score": gross_score,
                                "net_score": net_score
                            }
                            scores_changed = True
                
                # 登録ボタン
                submit_button = st.form_submit_button("スコアを登録")
                
                if submit_button:
                    # スコアに基づいて順位を計算し、データを保存
                    if save_scores(competition_id, st.session_state.score_data, st.session_state.players):
                        st.success("スコアが正常に登録されました！")
                        # 最新のデータを再取得
                        existing_scores = fetch_existing_scores(competition_id)
                        st.session_state.score_data = {}
                        if not existing_scores.empty:
                            for _, score in existing_scores.iterrows():
                                player_id = score["player_id"]
                                st.session_state.score_data[player_id] = {
                                    "out_score": score["out_score"],
                                    "in_score": score["in_score"],
                                    "handicap": score["handicap"],
                                    "net_score": score["net_score"]
                                }
                    else:
                        st.error("スコア登録に失敗しました。もう一度お試しください。")
            
            # 現在の順位を表示
            if st.session_state.score_data:
                st.subheader("現在の順位")
                
                # 有効なスコアデータ（OUT/INスコアが入力されている）のみ抽出
                valid_scores = {
                    player_id: data for player_id, data in st.session_state.score_data.items()
                    if data.get("out_score", 0) > 0 and data.get("in_score", 0) > 0
                }
                
                if valid_scores:
                    # 順位を計算
                    rankings = calculate_rankings(valid_scores)
                    
                    # 表示用データを作成
                    ranking_data = []
                    for player_id, rank in sorted(rankings.items(), key=lambda x: x[1]):
                        player_name = players_dict.get(player_id, f"不明なプレイヤー({player_id})")
                        score_info = valid_scores[player_id]
                        
                        ranking_data.append({
                            "順位": rank,
                            "プレイヤー名": player_name,
                            "OUTスコア": score_info["out_score"],
                            "INスコア": score_info["in_score"],
                            "グロススコア": score_info["gross_score"],
                            "ハンディキャップ": score_info["handicap"],
                            "ネットスコア": score_info["net_score"]
                        })
                    
                    # DataFrameに変換して表示
                    ranking_df = pd.DataFrame(ranking_data)
                    st.dataframe(ranking_df.sort_values("順位"), use_container_width=True)
                else:
                    st.info("有効なスコアデータがありません。各プレイヤーのOUT/INスコアを入力してください。")
    
    # ナビゲーションボタン
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("メイン画面へ"):
            st.switch_page("app/app.py")
    
    with col2:
        if st.button("ログアウト"):
            st.session_state.logged_in = False
            st.session_state.admin_logged_in = False
            st.session_state.page = "login"
            st.rerun()

def main():
    # セッション状態に基づいてページを表示
    if not st.session_state.logged_in and not st.session_state.admin_logged_in:
        login_page()
    else:
        score_entry_page()

if __name__ == "__main__":
    main()
def score_entry_tab():
    """スコア入力タブ用の関数"""
    score_entry_page()
