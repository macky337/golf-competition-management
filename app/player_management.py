import streamlit as st
import pandas as pd


def get_player_field_names(supabase):
    """実DBの players テーブルで利用可能なカラムを取得する。"""
    try:
        response = supabase.table("players").select("*").limit(1).execute()
        if response.data:
            return set(response.data[0].keys())
    except Exception:
        pass
    # 空テーブルや取得失敗でも、必須の氏名追加は可能にする
    return {"id", "name"}


def _player_payload(name, initial_handicap, affiliation, available_fields):
    """古いDBスキーマにも対応した追加・更新ペイロードを作成する。"""
    payload = {"name": name.strip()}
    if "initial_handicap" in available_fields:
        payload["initial_handicap"] = initial_handicap
    if "affiliation" in available_fields:
        payload["affiliation"] = affiliation.strip() or None
    return payload


def _format_database_error(error):
    """PostgREST/Supabaseのエラーを利用者向けに整形する。"""
    detail = str(error)
    code = getattr(error, "code", None)
    if code:
        detail = f"{detail}（コード: {code}）"
    return detail


def _next_player_id(supabase):
    """自動採番がない旧 players テーブル向けに次のIDを取得する。"""
    response = supabase.table("players").select("id").order("id", desc=True).limit(1).execute()
    if response.data:
        return int(response.data[0]["id"]) + 1
    return 1


def fetch_players_data(supabase):
    """プレイヤー一覧を取得"""
    try:
        response = supabase.table("players").select("*").order("id").execute()
        return response.data
    except Exception as e:
        st.error(f"プレイヤーデータの取得に失敗しました: {e}")
        return []

def add_player(supabase, name, initial_handicap, affiliation, available_fields=None):
    """プレイヤーを新規追加"""
    try:
        available_fields = available_fields or get_player_field_names(supabase)
        normalized_name = name.strip()
        existing = supabase.table("players").select("id").eq("name", normalized_name).limit(1).execute()
        if existing.data:
            return False, "同じ氏名のプレイヤーが既に登録されています。"

        payload = _player_payload(normalized_name, initial_handicap, affiliation, available_fields)
        try:
            supabase.table("players").insert(payload).execute()
        except Exception as insert_error:
            # 本番の旧スキーマでは id に DEFAULT/IDENTITY がないため、IDを明示して再試行する。
            if getattr(insert_error, "code", None) != "23502" or "column \"id\"" not in str(insert_error):
                raise
            payload["id"] = _next_player_id(supabase)
            supabase.table("players").insert(payload).execute()
        return True, f"プレイヤー「{normalized_name}」を追加しました。"
    except Exception as e:
        return False, f"プレイヤーの追加に失敗しました: {_format_database_error(e)}"

def update_player(supabase, player_id, name, initial_handicap, affiliation, available_fields=None):
    """プレイヤー情報を更新"""
    try:
        available_fields = available_fields or get_player_field_names(supabase)
        supabase.table("players").update(
            _player_payload(name, initial_handicap, affiliation, available_fields)
        ).eq("id", player_id).execute()
        return True, "プレイヤー情報を更新しました"
    except Exception as e:
        return False, f"プレイヤー情報の更新に失敗しました: {_format_database_error(e)}"

def delete_player(supabase, player_id):
    """プレイヤーを削除"""
    try:
        # 関連するスコアがないか確認
        score_response = supabase.table("scores").select("id").eq("player_id", player_id).limit(1).execute()
        if score_response.data:
            return False, "このプレイヤーに関連するスコアが存在するため、削除できません。先にスコアを削除してください。"

        response = supabase.table("players").delete().eq("id", player_id).execute()
        return True, "プレイヤーを削除しました"
    except Exception as e:
        return False, f"プレイヤーの削除に失敗しました: {e}"


def player_management_tab(supabase):
    """プレイヤー管理タブのUI"""
    st.subheader("👤 プレイヤー管理")
    available_fields = get_player_field_names(supabase)

    add_result = st.session_state.pop("player_add_result", None)
    if add_result:
        st.success(add_result)
        st.caption("「プレイヤー一覧」タブを開くと、登録内容を確認できます。")

    sub_tabs = st.tabs(["プレイヤー一覧", "新規追加", "編集・削除"])

    with sub_tabs[0]:
        st.write("### 登録プレイヤー一覧")
        players = fetch_players_data(supabase)
        if players:
            df = pd.DataFrame(players)
            st.dataframe(df, width="stretch")
        else:
            st.info("現在登録されているプレイヤーはいません。")

    with sub_tabs[1]:
        st.write("### 新規プレイヤー追加")
        st.caption("氏名を入力後、「追加」ボタンを押してください。Enterキーだけでは登録されません。")
        with st.form("add_player_form", enter_to_submit=False):
            name = st.text_input("氏名", key="add_player_name")
            initial_handicap = 0.0
            affiliation = ""
            if "initial_handicap" in available_fields:
                initial_handicap = st.number_input("ハンディキャップ", min_value=0.0, step=0.1)
            if "affiliation" in available_fields:
                affiliation = st.text_input("所属")
            
            submitted = st.form_submit_button("追加")
            if submitted:
                if not name.strip():
                    st.error("氏名は必須です。")
                else:
                    success, message = add_player(supabase, name, initial_handicap, affiliation, available_fields)
                    if success:
                        st.session_state["player_add_result"] = message
                        st.rerun()
                    else:
                        st.error(message)

    with sub_tabs[2]:
        st.write("### プレイヤー情報の編集・削除")
        players = fetch_players_data(supabase)
        if players:
            player_options = {f"{p['name']} (ID: {p['id']})": p for p in players}
            selected_player_key = st.selectbox("編集または削除するプレイヤーを選択", player_options.keys())
            
            if selected_player_key:
                selected_player = player_options[selected_player_key]
                
                with st.form("edit_player_form"):
                    st.write(f"**ID:** {selected_player['id']}")
                    new_name = st.text_input("氏名", value=selected_player['name'])
                    new_handicap = 0.0
                    new_affiliation = ""
                    if "initial_handicap" in available_fields:
                        new_handicap = st.number_input("ハンディキャップ", value=float(selected_player.get('initial_handicap', 0.0)))
                    if "affiliation" in available_fields:
                        new_affiliation = st.text_input("所属", value=selected_player.get('affiliation', ''))

                    col1, col2 = st.columns(2)
                    with col1:
                        update_submitted = st.form_submit_button("更新")
                    with col2:
                        delete_submitted = st.form_submit_button("削除", type="secondary")

                    if update_submitted:
                        success, message = update_player(supabase, selected_player['id'], new_name, new_handicap, new_affiliation, available_fields)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_submitted:
                        st.session_state["pending_player_delete"] = selected_player["id"]

                if st.session_state.get("pending_player_delete") == selected_player["id"]:
                    st.warning(f"「{selected_player['name']}」さんを削除します。この操作は元に戻せません。")
                    confirmation = st.text_input(
                        f"削除するには「{selected_player['name']}」と入力してください",
                        key=f"confirm_player_delete_{selected_player['id']}",
                    )
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button(
                            "削除を確定する",
                            type="primary",
                            key=f"confirm_player_delete_button_{selected_player['id']}",
                            disabled=confirmation != selected_player["name"],
                        ):
                            success, message = delete_player(supabase, selected_player["id"])
                            if success:
                                st.session_state.pop("pending_player_delete", None)
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    with col_cancel:
                        if st.button("削除を取り消す", key=f"cancel_player_delete_{selected_player['id']}"):
                            st.session_state.pop("pending_player_delete", None)
                            st.rerun()

        else:
            st.info("編集・削除できるプレイヤーがいません。")
