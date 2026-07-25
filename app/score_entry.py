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
from scorecard_reader import extraction_to_review_rows, read_scorecard_images

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
    SUPABASE_KEY = (
        st.secrets.get("supabase", {}).get("key", "")
        or st.secrets.get("supabase", {}).get("anon_key", "")
        or st.secrets.get("supabase", {}).get("anonKey", "")
    )
except Exception:
    # 次に環境変数を試す
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

# 単体起動時にも固定パスワードへフォールバックしない。
try:
    auth_secrets = st.secrets.get("auth", {})
except Exception:
    auth_secrets = {}
USER_PASSWORD = (
    auth_secrets.get("user_password", "")
    or auth_secrets.get("password", "")
    or os.getenv("USER_PASSWORD", "")
).strip()
ADMIN_PASSWORD = (
    auth_secrets.get("admin_password", "")
    or os.getenv("ADMIN_PASSWORD", "")
).strip()

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

def fetch_competitions(supabase=None):
    """コンペデータをSupabaseから取得"""
    supabase = supabase or get_supabase_client()
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

def fetch_players(supabase=None):
    """プレイヤーデータをSupabaseから取得"""
    supabase = supabase or get_supabase_client()
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

def fetch_participants(competition_id, supabase=None):
    """参加者データをSupabaseから取得"""
    supabase = supabase or get_supabase_client()
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

def fetch_existing_scores(competition_id, supabase=None):
    """既存のスコアデータをSupabaseから取得"""
    supabase = supabase or get_supabase_client()
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


def _optional_int(value):
    """Convert an editable table value to int without treating blanks as zero."""
    if value is None or pd.isna(value):
        return None
    return int(value)


def render_scorecard_image_import(competition_id, participants, players_dict):
    """Read aggregate cells and pass only OUT/IN scores to the existing logic."""
    participant_names = [
        players_dict[player_id]
        for player_id in participants
        if player_id in players_dict
    ]
    if not participant_names:
        return

    with st.expander("📷 スコアカード画像から読み込む", expanded=False):
        st.caption(
            "スマホのスクリーンショットを最大4枚選択できます。"
            "OUT・IN・EXTRA・GROSSの集計欄だけを読み取り、確認後に反映します。"
        )
        uploaded_images = st.file_uploader(
            "スコアカード画像",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key=f"scorecard_images_{competition_id}",
        )
        if uploaded_images and len(uploaded_images) > 4:
            st.error("一度にアップロードできる画像は4枚までです。")

        result_key = f"scorecard_ocr_result_{competition_id}"
        if st.button(
            "画像を解析",
            key=f"analyze_scorecard_{competition_id}",
            disabled=not uploaded_images or len(uploaded_images) > 4,
        ):
            payloads = [image.getvalue() for image in uploaded_images]
            if any(len(payload) > 12 * 1024 * 1024 for payload in payloads):
                st.error("画像1枚のサイズは12MB以下にしてください。")
            else:
                try:
                    with st.spinner("集計欄を読み取っています…"):
                        extraction = read_scorecard_images(payloads, participant_names)
                    st.session_state[result_key] = {
                        "rows": extraction_to_review_rows(
                            extraction,
                            participant_names,
                        ),
                        "warnings": extraction.warnings,
                    }
                except Exception as error:
                    error_name = type(error).__name__
                    if error_name == "AuthenticationError":
                        st.error("OpenAI APIキーが無効です。RailwayのOPENAI_API_KEYを確認してください。")
                    elif error_name in {"RateLimitError", "PermissionDeniedError"}:
                        st.error("画像解析APIを利用できません。API残高・モデル権限・利用上限を確認してください。")
                    else:
                        st.error(f"画像の解析に失敗しました（{error_name}）。")

        result = st.session_state.get(result_key)
        if not result:
            return

        for warning in result.get("warnings", []):
            st.warning(warning)

        rows = result.get("rows", [])
        if not rows:
            st.warning("画像からプレーヤーの集計欄を読み取れませんでした。")
            return

        st.markdown("##### 読み取り結果の確認")
        st.caption(
            "低信頼度の値や氏名の対応を確認し、必要なら表を修正してください。"
            "通常計算へ渡すのはOUTスコアとINスコアだけです。"
            "EXTRAとGROSSは独立した読み取り結果として保持し、計算には加えません。"
        )
        review_df = st.data_editor(
            pd.DataFrame(rows),
            width="stretch",
            hide_index=True,
            num_rows="fixed",
            column_config={
                "反映": st.column_config.CheckboxColumn("反映"),
                "画像の氏名": st.column_config.TextColumn("画像の氏名", disabled=True),
                "参加者": st.column_config.SelectboxColumn(
                    "登録参加者",
                    options=["選択してください", *participant_names],
                    required=True,
                ),
                "最低信頼度": st.column_config.NumberColumn(
                    "最低信頼度",
                    min_value=0.0,
                    max_value=1.0,
                    format="%.2f",
                    disabled=True,
                ),
            },
            key=f"scorecard_review_{competition_id}",
        )

        low_confidence = review_df[
            pd.to_numeric(review_df["最低信頼度"], errors="coerce").fillna(0) < 0.8
        ]
        if not low_confidence.empty:
            st.warning("信頼度0.80未満の行があります。画像と照合してから反映してください。")

        if st.button(
            "確認したOUT・INを入力欄へ反映",
            type="primary",
            key=f"apply_scorecard_{competition_id}",
        ):
            name_to_id = {
                players_dict[player_id]: player_id
                for player_id in participants
                if player_id in players_dict
            }
            errors = []
            applied = 0
            aggregate_readings = st.session_state.setdefault(
                "scorecard_aggregate_readings",
                {},
            ).setdefault(competition_id, {})

            for row in review_df.to_dict("records"):
                if not row.get("反映"):
                    continue
                participant_name = row.get("参加者")
                player_id = name_to_id.get(participant_name)
                out_score = _optional_int(row.get("OUTスコア"))
                in_score = _optional_int(row.get("INスコア"))
                if player_id is None:
                    errors.append(f"{row.get('画像の氏名', '氏名不明')}: 登録参加者を選択してください。")
                    continue
                if out_score is None or in_score is None:
                    errors.append(f"{participant_name}: OUTとINの両方を確認してください。")
                    continue
                if not 0 <= out_score <= 100 or not 0 <= in_score <= 100:
                    errors.append(f"{participant_name}: OUT/INは0〜100で入力してください。")
                    continue

                existing = st.session_state.get("score_data", {}).get(player_id, {})
                st.session_state.score_data[player_id] = {
                    **existing,
                    "out_score": out_score,
                    "in_score": in_score,
                }
                st.session_state[f"out_{player_id}"] = out_score
                st.session_state[f"in_{player_id}"] = in_score

                # Preserve every directly-read aggregate separately.  These values
                # are not fed into the legacy score/ranking calculation.
                aggregate_readings[player_id] = {
                    "out": {
                        "score": out_score,
                        "putts": _optional_int(row.get("OUTパット")),
                        "game_point": _optional_int(row.get("OUTゲームポイント")),
                    },
                    "in": {
                        "score": in_score,
                        "putts": _optional_int(row.get("INパット")),
                        "game_point": _optional_int(row.get("INゲームポイント")),
                    },
                    "extra": {
                        "score": _optional_int(row.get("EXTRAスコア")),
                        "putts": _optional_int(row.get("EXTRAパット")),
                        "game_point": _optional_int(row.get("EXTRAゲームポイント")),
                    },
                    "total": {
                        "score": _optional_int(row.get("GROSS")),
                        "putts": _optional_int(row.get("合計パット")),
                        "game_point": _optional_int(row.get("合計ゲームポイント")),
                    },
                    "minimum_confidence": float(row.get("最低信頼度") or 0),
                }
                applied += 1

            if errors:
                for message in errors:
                    st.error(message)
            if applied:
                st.success(f"{applied}名のOUT・INを入力欄へ反映しました。")
                st.rerun()

def save_scores(competition_id, scores_data, players_data, supabase=None):
    """スコアデータをSupabaseに保存"""
    supabase = supabase or get_supabase_client()
    if not supabase:
        return False
    
    try:
        # データ登録用の辞書のリストを作成
        records_to_insert = []
        competition_info = st.session_state.competitions[
            st.session_state.get("competitions", pd.DataFrame())["competition_id"] == competition_id
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
        
        # 一意制約 (competition_id, player_id) を使って原子的に追加・更新する。
        # 先に既存行を削除しないため、通信・検証エラーでも保存済みデータを失わない。
        if records_to_insert:
            supabase.table("scores").upsert(
                records_to_insert,
                on_conflict="competition_id,player_id",
            ).execute()
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
        st.image(image_path, width="stretch")
    
    if not USER_PASSWORD and not ADMIN_PASSWORD:
        st.error("ログインパスワードが設定されていません。")
        return

    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if USER_PASSWORD and password == USER_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.page = "main"
            st.rerun()  # ページを強制的に再読み込み
        elif ADMIN_PASSWORD and password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.session_state.page = "main"
            st.rerun()
        else:
            st.error("パスワードが間違っています")

def score_entry_page(supabase=None):
    st.title("88会ゴルフコンペ・スコア入力")
    
    # 管理画面で作成・更新したコンペを、スコア入力画面へ即時反映する。
    st.session_state.competitions = fetch_competitions(supabase)
    
    if "players" not in st.session_state:
        st.session_state.players = fetch_players(supabase)
    
    if st.session_state.get("competitions", pd.DataFrame()).empty or st.session_state.get("players", pd.DataFrame()).empty:
        st.error("コンペまたはプレイヤーのデータが取得できませんでした。")
        if st.button("再試行"):
            st.session_state.competitions = fetch_competitions(supabase)
            st.session_state.players = fetch_players(supabase)
            st.rerun()
        return
    
    # コンペ選択（文字列を分解せず、選択したレコードからIDを取得する）
    competition_records = st.session_state.competitions.to_dict("records")
    selected_competition = st.selectbox(
        "スコアを入力するコンペを選択してください",
        competition_records,
        format_func=lambda competition: (
            f"第{competition.get('competition_id', '')}回 - "
            f"{competition.get('date', '')} {competition.get('course', '')}"
        ),
        key="score_entry_competition_selector",
    )
    
    if selected_competition:
        competition_id = int(selected_competition["competition_id"])
        
        if st.session_state.get("selected_competition") != competition_id:
            st.session_state.selected_competition = competition_id
            # 既存のスコアを取得
            existing_scores = fetch_existing_scores(competition_id, supabase)
            
            # スコアデータの初期化
            st.session_state.score_data = {}
            
            # 既存のスコアデータがあれば設定
            if not existing_scores.empty:
                for _, score in existing_scores.iterrows():
                    player_id = score["player_id"]
                    out_score = score.get("out_score", 0) or 0
                    in_score = score.get("in_score", 0) or 0
                    gross_score = out_score + in_score
                    st.session_state.get("score_data", {})[player_id] = {
                        "out_score": out_score,
                        "in_score": in_score,
                        "handicap": score.get("handicap", 0) or 0,
                        "gross_score": gross_score,
                        "net_score": score.get("net_score", 0) or 0
                    }
            
            st.rerun()

        # コンペ設定で登録された参加者を毎回反映する。
        # スコア入力画面では参加者を重複して選択しない。
        st.session_state.participants = fetch_participants(competition_id, supabase)
        
        # プレイヤーデータをID->名前の辞書に変換
        players_df = st.session_state.get("players", pd.DataFrame())
        if not players_df.empty and "id" in players_df.columns and "name" in players_df.columns:
            players_dict = dict(zip(players_df["id"], players_df["name"]))
        else:
            players_dict = {}
            st.warning("プレイヤーデータが正しく読み込まれていません。")
        
        if not st.session_state.get("participants", []):
            st.warning("このコンペには参加者が登録されていません。")
            st.info("「コンペ設定」→「参加者管理」で参加者を登録してから、スコア入力画面へ戻ってください。")
        else:
            st.success(f"第{competition_id}回の登録済み参加者 {len(st.session_state.participants)} 名を読み込みました。")
            # スコア入力フォームの表示
            st.subheader("スコア入力")

            render_scorecard_image_import(
                competition_id,
                st.session_state.get("participants", []),
                players_dict,
            )
            
            with st.form("score_entry_form"):
                scores_changed = False
                
                # 各プレイヤーのスコア入力欄を表示
                for player_id in st.session_state.get("participants", []):
                    player_name = players_dict.get(player_id, f"不明なプレイヤー({player_id})")
                    
                    with st.expander(f"{player_name} のスコア", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        
                        # 既存の値を取得
                        existing_data = st.session_state.get("score_data", {}).get(player_id, {})
                        
                        with col1:
                            out_score = st.number_input(
                                "OUTスコア", 
                                min_value=0, 
                                max_value=100, 
                                value=int(existing_data.get("out_score", 0)),
                                step=1,
                                key=f"out_{player_id}"
                            )
                        
                        with col2:
                            in_score = st.number_input(
                                "INスコア", 
                                min_value=0, 
                                max_value=100, 
                                value=int(existing_data.get("in_score", 0)),
                                step=1,
                                key=f"in_{player_id}"
                            )
                        
                        with col3:
                            handicap = st.number_input(
                                "ハンディキャップ",
                                min_value=0.0,
                                max_value=50.0,
                                value=float(existing_data.get("handicap", 0.0)),
                                step=0.1,
                                key=f"hcp_{player_id}"
                            )
                        
                        # グロススコアとネットスコアを計算
                        if out_score > 0 and in_score > 0:
                            gross_score = out_score + in_score
                            
                            # スコアの妥当性チェック
                            if gross_score > 200:
                                st.warning(f"⚠️ グロススコア ({gross_score}) が通常の範囲を超えています。入力内容を確認してください。")
                            elif gross_score < 50:
                                st.warning(f"⚠️ グロススコア ({gross_score}) が通常より低すぎます。入力内容を確認してください。")
                            
                            net_score = gross_score - handicap
                            
                            # ネットスコアの妥当性チェック
                            if net_score < 0:
                                st.error("❌ ネットスコアがマイナスです。ハンディキャップを確認してください。")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"グロススコア: {gross_score:.1f}")
                            with col2:
                                st.info(f"ネットスコア: {net_score:.1f}")
                            
                            # スコアデータを更新
                            st.session_state.get("score_data", {})[player_id] = {
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
                    if save_scores(competition_id, st.session_state.get("score_data", {}), st.session_state.get("players", pd.DataFrame()), supabase):
                        st.success("スコアが正常に登録されました！")
                        # 最新のデータを再取得
                        existing_scores = fetch_existing_scores(competition_id, supabase)
                        st.session_state.score_data = {}
                        if not existing_scores.empty:
                            for _, score in existing_scores.iterrows():
                                player_id = score["player_id"]
                                out_score = score.get("out_score", 0) or 0
                                in_score = score.get("in_score", 0) or 0
                                gross_score = out_score + in_score
                                st.session_state.get("score_data", {})[player_id] = {
                                    "out_score": out_score,
                                    "in_score": in_score,
                                    "handicap": score.get("handicap", 0) or 0,
                                    "gross_score": gross_score,
                                    "net_score": score.get("net_score", 0) or 0
                                }
                    else:
                        st.error("スコア登録に失敗しました。もう一度お試しください。")
            
            # 現在の順位を表示
            if st.session_state.get("score_data", {}):
                st.subheader("現在の順位")
                
                # 有効なスコアデータ（OUT/INスコアが入力されている）のみ抽出
                valid_scores = {
                    player_id: data for player_id, data in st.session_state.get("score_data", {}).items()
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
                    st.dataframe(ranking_df.sort_values("順位"), width="stretch")
                else:
                    st.info("有効なスコアデータがありません。各プレイヤーのOUT/INスコアを入力してください。")
    
    # ナビゲーションボタン
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("メイン画面へ"):
            st.session_state.page = "main"
            st.rerun()
    
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
