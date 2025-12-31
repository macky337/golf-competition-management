import re

# app.pyの内容を読み込み
with open('app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 問題のある get_git_date 関数を修正版に置き換え
old_get_git_date = '''def get_git_date():
    """Git の最終コミット日時を JST で取得"""
    try:
        # JST時間で取得を試行
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=format-local:%Y-%m-%d %H:%M'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # フォールバック：UTC時間を取得してJSTに変換
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=iso'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            # 簡易的なUTC→JST変換（+9時間）
            import re
            from datetime import datetime, timedelta
            match = re.match(r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}):\d{2}', result.stdout.strip())
            if match:
                date_part, time_part = match.groups()
                dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
                dt_jst = dt + timedelta(hours=9)  # UTCからJSTに変換
                return dt_jst.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    
    # 最終フォールバック：現在のJST時間
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M")'''

# datetimeの競合を避けた修正版
new_get_git_date = '''def get_git_date():
    """Git の最終コミット日時を JST で取得"""
    try:
        # JST時間で取得を試行
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=format-local:%Y-%m-%d %H:%M'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # フォールバック：UTC時間を取得してJSTに変換
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=iso'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            # 簡易的なUTC→JST変換（+9時間）
            import re
            from datetime import datetime as dt_class, timedelta
            match = re.match(r'(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}):\d{2}', result.stdout.strip())
            if match:
                date_part, time_part = match.groups()
                dt = dt_class.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
                dt_jst = dt + timedelta(hours=9)  # UTCからJSTに変換
                return dt_jst.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    
    # 最終フォールバック：現在のJST時間
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M")'''

# 関数を置き換え
content = content.replace(old_get_git_date, new_get_git_date)

# 修正した内容をファイルに書き込み
with open('app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ datetime競合エラーを修正しました")
