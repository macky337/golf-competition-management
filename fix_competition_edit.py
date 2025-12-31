import re

# competition_management.pyの内容を読み込み
with open('app/competition_management.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 編集機能の日付処理も安全にする
old_date_processing = '''                    new_date = st.date_input("開催日", value=datetime.fromisoformat(selected_competition['date'].replace('Z', '+00:00')).date())'''

new_date_processing = '''                    # 安全な日付処理
                    try:
                        if isinstance(selected_competition['date'], str):
                            # ISO形式の文字列から日付を取得
                            date_str = selected_competition['date'].replace('Z', '+00:00')
                            parsed_date = datetime.fromisoformat(date_str).date()
                        else:
                            parsed_date = selected_competition['date']
                    except (ValueError, AttributeError):
                        parsed_date = datetime.now().date()
                    
                    new_date = st.date_input("開催日", value=parsed_date)'''

# 置き換えを実行
content = content.replace(old_date_processing, new_date_processing)

# 修正した内容をファイルに書き込み
with open('app/competition_management.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 編集機能の日付処理も安全に修正しました")
print("- try-except文で安全な日付パース")
print("- 異なる日付形式に対応")
print("- フォールバック処理を追加")
