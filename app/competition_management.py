import streamlit as st
import pandas as pd
from datetime import datetime, date
import pytz

def fetch_competitions_data(supabase):
    """コンペ一覧を取得"""
    try:
        response = supabase.table("competitions").select("*").order("date", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"コンペデータの取得に失敗しました: {e}")
        return []

def add_competition(supabase, name, comp_date, location, course, description):
    """コンペを新規追加"""
    try:
        from datetime import date as date_type
        response = supabase.table("competitions").insert({
            "name": name,
            "date": comp_date.isoformat() if isinstance(comp_date, date_type) else str(comp_date),
            "location": location,
            "course": course,
            "description": description,
            "status": "planned"
        }).execute()
        return True, "コンペを追加しました"
    except Exception as e:
        return False, f"コンペの追加に失敗しました: {e}"

def update_competition(supabase, competition_id, name, comp_date, location, course, description, status):
    """コンペ情報を更新"""
    try:
        from datetime import date as date_type
        response = supabase.table("competitions").update({
            "name": name,
            "date": comp_date.isoformat() if isinstance(comp_date, date_type) else str(comp_date),
            "location": location,
            "course": course,
            "description": description,
            "status": status
        }).eq("id", competition_id).execute()
        return True, "コンペ情報を更新しました"
    except Exception as e:
        return False, f"コンペ情報の更新に失敗しました: {e}"

def delete_competition(supabase, competition_id):
    """コンペを削除"""
    try:
        # 関連するスコアがないか確認
        score_response = supabase.table("scores").select("id").eq("competition_id", competition_id).limit(1).execute()
        if score_response.data:
            return False, "このコンペに関連するスコアが存在するため、削除できません。先にスコアを削除してください。"
        
        # 関連する参加者情報も削除
        supabase.table("participants").delete().eq("competition_id", competition_id).execute()
        
        response = supabase.table("competitions").delete().eq("id", competition_id).execute()
        return True, "コンペを削除しました"
    except Exception as e:
        return False, f"コンペの削除に失敗しました: {e}"

def fetch_players_for_participation(supabase):
    """参加者選択用のプレイヤー一覧を取得"""
    try:
        response = supabase.table("players").select("*").order("name").execute()
        return response.data
    except Exception as e:
        st.error(f"プレイヤーデータの取得に失敗しました: {e}")
        return []

def fetch_participants(supabase, competition_id):
    """特定のコンペの参加者を取得"""
    try:
        response = supabase.table("participants").select(
            "*, players!inner(*)"
        ).eq("competition_id", competition_id).execute()
        return response.data
    except Exception as e:
        st.error(f"参加者データの取得に失敗しました: {e}")
        return []

def add_participant(supabase, competition_id, player_id):
    """コンペに参加者を追加"""
    try:
        # 既存の参加者をチェック
        existing = supabase.table("participants").select("id").eq("competition_id", competition_id).eq("player_id", player_id).execute()
        if existing.data:
            return False, "このプレイヤーは既に参加者として登録されています"
        
        response = supabase.table("participants").insert({
            "competition_id": competition_id,
            "player_id": player_id
        }).execute()
        return True, "参加者を追加しました"
    except Exception as e:
        return False, f"参加者の追加に失敗しました: {e}"

def remove_participant(supabase, competition_id, player_id):
    """コンペから参加者を削除"""
    try:
        response = supabase.table("participants").delete().eq("competition_id", competition_id).eq("player_id", player_id).execute()
        return True, "参加者を削除しました"
    except Exception as e:
        return False, f"参加者の削除に失敗しました: {e}"

def competition_management_tab(supabase):
    """コンペ管理タブのUI"""
    st.subheader("🏆 コンペ管理")

    sub_tabs = st.tabs(["コンペ一覧", "新規作成", "編集・削除", "参加者管理"])

    with sub_tabs[0]:
        st.write("### 登録済みコンペ一覧")
        competitions = fetch_competitions_data(supabase)
        if competitions:
            df = pd.DataFrame(competitions)
            
            # 安全なカラム表示（存在するカラムのみ使用）
            display_df = df.copy()
            
            # 日付カラムの処理（存在する場合）
            if 'date' in df.columns:
                try:
                    display_df['date'] = pd.to_datetime(display_df['date'])
                    display_df = display_df.sort_values('date', ascending=False)
                    display_df['開催日'] = display_df['date'].dt.strftime('%Y-%m-%d')
                except:
                    pass
            
            # カラム名を日本語に変換（存在する場合のみ）
            column_rename = {
                'name': 'コンペ名',
                'title': 'コンペ名', 
                'location': '開催地',
                'course': 'コース',
                'status': 'ステータス',
                'description': '説明',
                'id': 'ID'
            }
            
            # 存在するカラムのみリネーム
            for old_name, new_name in column_rename.items():
                if old_name in display_df.columns:
                    display_df = display_df.rename(columns={old_name: new_name})
            
            # 不要なカラムを除外（内部カラムやタイムスタンプなど）
            exclude_cols = ['created_at', 'updated_at', 'date']
            display_columns = [col for col in display_df.columns if col not in exclude_cols]
            
            if display_columns:
                st.dataframe(display_df[display_columns], use_container_width=True)
            else:
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info("現在登録されているコンペはありません。")

    with sub_tabs[1]:
        st.write("### 新規コンペ作成")
        with st.form("add_competition_form"):
            name = st.text_input("コンペ名")
            comp_date = st.date_input("開催日", value=datetime.now().date())
            location = st.text_input("開催地")
            course = st.text_input("ゴルフコース名")
            description = st.text_area("説明・備考")
            
            submitted = st.form_submit_button("作成")
            if submitted:
                if not name:
                    st.error("コンペ名は必須です。")
                else:
                    success, message = add_competition(supabase, name, comp_date, location, course, description)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with sub_tabs[2]:
        st.write("### コンペ情報の編集・削除")
        competitions = fetch_competitions_data(supabase)
        if competitions:
            competition_options = {}
            for c in competitions:
                # 安全な表示名の作成
                name = c.get('name', c.get('title', 'コンペ'))
                date_str = c.get('date', '未設定')
                if isinstance(date_str, str) and date_str != '未設定':
                    try:
                        # 日付文字列を短縮形式に変換
                        parsed_date = pd.to_datetime(date_str)
                        date_str = parsed_date.strftime('%Y-%m-%d')
                    except:
                        pass
                competition_options[f"{name} ({date_str})"] = c
            selected_competition_key = st.selectbox("編集または削除するコンペを選択", competition_options.keys())
            
            if selected_competition_key:
                selected_competition = competition_options[selected_competition_key]
                
                with st.form("edit_competition_form"):
                    comp_id = selected_competition.get('id', '不明')
                    st.write(f"**ID:** {comp_id}")
                    new_name = st.text_input("コンペ名", value=selected_competition.get('name', ''))
                    # 安全な日付処理
                    parsed_date = datetime.now().date()  # デフォルト値を設定
                    try:
                        comp_date = selected_competition.get('date', '')
                        if isinstance(comp_date, str) and comp_date:
                            # ISO形式の文字列から日付を取得
                            date_str = comp_date.replace('Z', '+00:00')
                            parsed_date = datetime.fromisoformat(date_str).date()
                        elif comp_date:
                            parsed_date = comp_date
                    except (ValueError, AttributeError):
                        parsed_date = datetime.now().date()
                    
                    new_date = st.date_input("開催日", value=parsed_date)
                    new_location = st.text_input("開催地", value=selected_competition.get('location', ''))
                    new_course = st.text_input("ゴルフコース名", value=selected_competition.get('course', ''))
                    new_description = st.text_area("説明・備考", value=selected_competition.get('description', ''))
                    
                    # ステータスの安全な取得
                    current_status = selected_competition.get('status', 'planned')
                    status_options = ["planned", "ongoing", "completed", "cancelled"]
                    try:
                        status_index = status_options.index(current_status)
                    except ValueError:
                        status_index = 0  # デフォルトは'planned'
                    
                    new_status = st.selectbox("ステータス", 
                                             options=status_options,
                                             index=status_index)

                    col1, col2 = st.columns(2)
                    with col1:
                        update_submitted = st.form_submit_button("更新")
                    with col2:
                        delete_submitted = st.form_submit_button("削除", type="secondary")

                    if update_submitted:
                        comp_id = selected_competition.get('id')
                        if comp_id:
                            success, message = update_competition(supabase, comp_id, new_name, new_date, new_location, new_course, new_description, new_status)
                        else:
                            success, message = False, "コンペIDが見つかりません"
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_submitted:
                        comp_name = selected_competition.get('name', 'このコンペ')
                        st.warning(f"本当に「{comp_name}」を削除しますか？この操作は元に戻せません。")
                        if st.checkbox("はい、削除します。"):
                            comp_id = selected_competition.get('id')
                            if comp_id:
                                success, message = delete_competition(supabase, comp_id)
                            else:
                                success, message = False, "コンペIDが見つかりません"
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
        else:
            st.info("編集・削除できるコンペがありません。")

    with sub_tabs[3]:
        st.write("### 参加者管理")
        competitions = fetch_competitions_data(supabase)
        if competitions:
            # コンペ選択
            competition_options = {}
            for c in competitions:
                # 安全な表示名の作成
                name = c.get('name', c.get('title', 'コンペ'))
                date_str = c.get('date', '未設定')
                if isinstance(date_str, str) and date_str != '未設定':
                    try:
                        # 日付文字列を短縮形式に変換
                        parsed_date = pd.to_datetime(date_str)
                        date_str = parsed_date.strftime('%Y-%m-%d')
                    except:
                        pass
                competition_options[f"{name} ({date_str})"] = c
            selected_competition_key = st.selectbox("参加者を管理するコンペを選択", competition_options.keys(), key="participant_comp")
            
            if selected_competition_key:
                selected_competition = competition_options[selected_competition_key]
                competition_id = selected_competition.get('id')
                if not competition_id:
                    st.error("コンペIDが見つかりません。")
                    return
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("#### 現在の参加者")
                    participants = fetch_participants(supabase, competition_id)
                    if participants:
                        participant_names = [p['players']['name'] for p in participants]
                        for name in participant_names:
                            st.write(f"• {name}")
                    else:
                        st.info("参加者はまだいません。")
                
                with col2:
                    st.write("#### 参加者を追加")
                    players = fetch_players_for_participation(supabase)
                    if players:
                        # 既存の参加者を除外
                        participant_player_ids = [p['player_id'] for p in participants] if participants else []
                        available_players = [p for p in players if p['id'] not in participant_player_ids]
                        
                        if available_players:
                            player_options = {f"{p['name']} ({p.get('affiliation', '所属なし')})": p['id'] for p in available_players}
                            selected_player_name = st.selectbox("追加するプレイヤーを選択", list(player_options.keys()))
                            
                            if st.button("参加者として追加"):
                                player_id = player_options[selected_player_name]
                                success, message = add_participant(supabase, competition_id, player_id)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            st.info("追加可能なプレイヤーがいません。")
                
                # 参加者削除
                if participants:
                    st.write("#### 参加者を削除")
                    participant_options = {p['players']['name']: p['player_id'] for p in participants}
                    selected_participant = st.selectbox("削除する参加者を選択", list(participant_options.keys()))
                    
                    if st.button("参加者から削除", type="secondary"):
                        player_id = participant_options[selected_participant]
                        success, message = remove_participant(supabase, competition_id, player_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("参加者を管理できるコンペがありません。")
