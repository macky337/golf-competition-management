import streamlit as st
import pandas as pd

def fetch_players_data(supabase):
    """プレイヤー一覧を取得"""
    try:
        response = supabase.table("players").select("*").order("id").execute()
        return response.data
    except Exception as e:
        st.error(f"プレイヤーデータの取得に失敗しました: {e}")
        return []

def add_player(supabase, name, initial_handicap, affiliation):
    """プレイヤーを新規追加"""
    try:
        response = supabase.table("players").insert({
            "name": name,
            "initial_handicap": initial_handicap,
            "affiliation": affiliation
        }).execute()
        return True, "プレイヤーを追加しました"
    except Exception as e:
        return False, f"プレイヤーの追加に失敗しました: {e}"

def update_player(supabase, player_id, name, initial_handicap, affiliation):
    """プレイヤー情報を更新"""
    try:
        response = supabase.table("players").update({
            "name": name,
            "initial_handicap": initial_handicap,
            "affiliation": affiliation
        }).eq("id", player_id).execute()
        return True, "プレイヤー情報を更新しました"
    except Exception as e:
        return False, f"プレイヤー情報の更新に失敗しました: {e}"

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

    sub_tabs = st.tabs(["プレイヤー一覧", "新規追加", "編集・削除"])

    with sub_tabs[0]:
        st.write("### 登録プレイヤー一覧")
        players = fetch_players_data(supabase)
        if players:
            df = pd.DataFrame(players)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("現在登録されているプレイヤーはいません。")

    with sub_tabs[1]:
        st.write("### 新規プレイヤー追加")
        with st.form("add_player_form"):
            name = st.text_input("氏名")
            initial_handicap = st.number_input("ハンディキャップ", min_value=0.0, step=0.1)
            affiliation = st.text_input("所属")
            
            submitted = st.form_submit_button("追加")
            if submitted:
                if not name:
                    st.error("氏名は必須です。")
                else:
                    success, message = add_player(supabase, name, initial_handicap, affiliation)
                    if success:
                        st.success(message)
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
                    new_handicap = st.number_input("ハンディキャップ", value=float(selected_player.get('initial_handicap', 0.0)))
                    new_affiliation = st.text_input("所属", value=selected_player.get('affiliation', ''))

                    col1, col2 = st.columns(2)
                    with col1:
                        update_submitted = st.form_submit_button("更新")
                    with col2:
                        delete_submitted = st.form_submit_button("削除", type="secondary")

                    if update_submitted:
                        success, message = update_player(supabase, selected_player['id'], new_name, new_handicap, new_affiliation)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_submitted:
                        # 削除前の確認
                        st.warning(f"本当に {selected_player['name']} さんを削除しますか？この操作は元に戻せません。")
                        if st.checkbox("はい、削除します。"):
                            success, message = delete_player(supabase, selected_player['id'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

        else:
            st.info("編集・削除できるプレイヤーがいません。")