import re

# competition_management.pyの内容を読み込み
with open('app/competition_management.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. ID表示の安全化
old_id_display = '''                    st.write(f"**ID:** {selected_competition['id']}")'''
new_id_display = '''                    comp_id = selected_competition.get('id', '不明')
                    st.write(f"**ID:** {comp_id}")'''

# 2. 編集フォームのフィールド値を安全にする
old_form_fields = '''                    new_name = st.text_input("コンペ名", value=selected_competition['name'])'''
new_form_fields = '''                    new_name = st.text_input("コンペ名", value=selected_competition.get('name', ''))'''

# 3. その他のフィールドも安全にする
old_other_fields = '''                    new_location = st.text_input("開催地", value=selected_competition.get('location', ''))
                    new_course = st.text_input("ゴルフコース名", value=selected_competition.get('course', ''))
                    new_description = st.text_area("説明・備考", value=selected_competition.get('description', ''))
                    new_status = st.selectbox("ステータス", 
                                             options=["planned", "ongoing", "completed", "cancelled"],
                                             index=["planned", "ongoing", "completed", "cancelled"].index(selected_competition.get('status', 'planned')))'''

new_other_fields = '''                    new_location = st.text_input("開催地", value=selected_competition.get('location', ''))
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
                                             index=status_index)'''

# 4. 更新・削除処理でのID参照も安全にする
old_update_call = '''                        success, message = update_competition(supabase, selected_competition['id'], new_name, new_date, new_location, new_course, new_description, new_status)'''
new_update_call = '''                        comp_id = selected_competition.get('id')
                        if comp_id:
                            success, message = update_competition(supabase, comp_id, new_name, new_date, new_location, new_course, new_description, new_status)
                        else:
                            success, message = False, "コンペIDが見つかりません"'''

old_delete_call = '''                            success, message = delete_competition(supabase, selected_competition['id'])'''
new_delete_call = '''                            comp_id = selected_competition.get('id')
                            if comp_id:
                                success, message = delete_competition(supabase, comp_id)
                            else:
                                success, message = False, "コンペIDが見つかりません"'''

# 5. 削除確認メッセージも安全にする
old_delete_warning = '''                        st.warning(f"本当に「{selected_competition['name']}」を削除しますか？この操作は元に戻せません。")'''
new_delete_warning = '''                        comp_name = selected_competition.get('name', 'このコンペ')
                        st.warning(f"本当に「{comp_name}」を削除しますか？この操作は元に戻せません。")'''

# 6. 参加者管理でのID参照も安全にする
old_participant_id = '''                competition_id = selected_competition['id']'''
new_participant_id = '''                competition_id = selected_competition.get('id')
                if not competition_id:
                    st.error("コンペIDが見つかりません。")
                    return'''

# すべての置き換えを実行
content = content.replace(old_id_display, new_id_display)
content = content.replace(old_form_fields, new_form_fields)
content = content.replace(old_other_fields, new_other_fields)
content = content.replace(old_update_call, new_update_call)
content = content.replace(old_delete_call, new_delete_call)
content = content.replace(old_delete_warning, new_delete_warning)
content = content.replace(old_participant_id, new_participant_id)

# 修正した内容をファイルに書き込み
with open('app/competition_management.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ すべてのKeyErrorを修正しました")
print("- ID参照の安全化")
print("- フォームフィールドの安全化")
print("- ステータス選択の安全化")  
print("- 更新・削除処理の安全化")
print("- 参加者管理の安全化")
