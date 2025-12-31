import re

# competition_management.pyの内容を読み込み
with open('app/competition_management.py', 'r', encoding='utf-8') as f:
    content = f.read()

# コンペ選択部分の表示も安全にする
old_selection = '''            competition_options = {f"{c['name']} ({c['date']})": c for c in competitions}'''
new_selection = '''            competition_options = {}
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
                competition_options[f"{name} ({date_str})"] = c'''

# 置き換えを実行
content = content.replace(old_selection, new_selection)

# 参加者管理のコンペ選択も同様に修正
old_participant_selection = '''            competition_options = {f"{c['name']} ({c['date']})": c for c in competitions}'''
new_participant_selection = '''            competition_options = {}
            for c in competitions:
                name = c.get('name', c.get('title', 'コンペ'))
                date_str = c.get('date', '未設定')
                if isinstance(date_str, str) and date_str != '未設定':
                    try:
                        parsed_date = pd.to_datetime(date_str)
                        date_str = parsed_date.strftime('%Y-%m-%d')
                    except:
                        pass
                competition_options[f"{name} ({date_str})"] = c'''

# 2回目の置き換え（参加者管理部分）
content = content.replace(old_participant_selection, new_participant_selection)

# 修正した内容をファイルに書き込み
with open('app/competition_management.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ コンペ選択表示も安全に修正しました")
print("- 安全な辞書作成")
print("- 存在しないキーへの対応")
print("- 日付フォーマットの統一")
