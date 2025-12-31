import re

# competition_management.pyの内容を読み込み
with open('app/competition_management.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 日付参照の安全化
old_date_reference = '''                        if isinstance(selected_competition['date'], str):
                            # ISO形式の文字列から日付を取得
                            date_str = selected_competition['date'].replace('Z', '+00:00')'''

new_date_reference = '''                        comp_date = selected_competition.get('date', '')
                        if isinstance(comp_date, str) and comp_date:
                            # ISO形式の文字列から日付を取得
                            date_str = comp_date.replace('Z', '+00:00')'''

# その他の日付参照も修正
old_date_else = '''                        else:
                            parsed_date = selected_competition['date']'''

new_date_else = '''                        elif comp_date:
                            parsed_date = comp_date'''

# 置き換えを実行
content = content.replace(old_date_reference, new_date_reference)
content = content.replace(old_date_else, new_date_else)

# 修正した内容をファイルに書き込み
with open('app/competition_management.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 日付参照エラーも修正しました")
print("- 安全な日付取得")
print("- 空の日付値への対応")
