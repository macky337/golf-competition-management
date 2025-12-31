import re

# app.pyの内容を読み込み
with open('app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. get_git_date()関数をJST対応版に置き換え
old_get_git_date = '''def get_git_date():
    """Git の最終コミット日時を取得"""
    try:
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d %H:%M'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return datetime.now().strftime("%Y-%m-%d %H:%M")'''

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

# 2. parse_version_from_commit_history()関数を改良版に置き換え
old_parse_version = '''def parse_version_from_commit_history():
    """コミット履歴を解析し、適切なバージョン番号を計算する"""
    # バージョン番号の初期値
    major = 1
    minor = 0
    patch = 0
    
    try:
        # まず最新のコミットメッセージを取得
        latest_commit_message = get_git_latest_commit_message()
        
        # コミットメッセージに基づいてバージョンタイプを判断
        if re.search(r'^(major:|MAJOR:|!:)', latest_commit_message):
            # メジャーバージョンアップ
            major += 1
            minor = 0
            patch = 0
        elif re.search(r'^(feature:|feat:|FEATURE:)', latest_commit_message):
            # マイナーバージョンアップ
            minor += 1
            patch = 0
        elif re.search(r'^(fix:|bugfix:|FIX:)', latest_commit_message):
            # パッチバージョンアップ
            patch += 1
        else:
            # 特に指定がない場合はパッチバージョン
            patch = int(get_git_count())
            
        return f"{major}.{minor}.{patch}"
    except Exception:
        # デフォルトバージョン
        return "1.0.7"'''

new_parse_version = '''def parse_version_from_commit_history():
    """コミット履歴を解析し、適切なバージョン番号を計算する"""
    major = 1
    minor = 0
    patch = 0
    
    try:
        # 最新のコミットメッセージを取得
        latest_commit_message = get_git_latest_commit_message()
        
        # コミットメッセージに基づいてバージョンタイプを判断
        if re.search(r'^(major:|MAJOR:|!:)', latest_commit_message):
            # メジャーバージョンアップ
            major = 2  # 次のメジャーバージョン
            minor = 0
            patch = 0
        elif re.search(r'^(feature:|feat:|FEATURE:)', latest_commit_message):
            # マイナーバージョンアップ
            minor = 1
            patch = 0
        elif re.search(r'^(fix:|bugfix:|FIX:)', latest_commit_message):
            # パッチバージョンアップ
            patch = 1
        else:
            # コミット数を基にしたバージョン番号計算
            count = int(get_git_count())
            # より現実的なバージョン管理
            major = 1
            minor = count // 100  # 100コミットごとにマイナーバージョンアップ
            patch = count % 100   # パッチバージョンは100未満
            
        return f"{major}.{minor}.{patch}"
    except Exception:
        # デフォルトバージョン
        return "1.2.4"'''

# 3. get_app_version()関数を動的バージョン対応版に置き換え
old_get_app_version = '''def get_app_version():
    """アプリバージョンを取得"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch == "main":
                return "1.0.0"
            elif branch == "feature-branch":
                return "1.0.0-dev"
            else:
                return f"1.0.0-{branch}"
    except Exception:
        pass
    return "1.0.0 (dev)"'''

new_get_app_version = '''def get_app_version():
    """アプリバージョンを取得（動的バージョン使用）"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                               capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            branch = result.stdout.strip()
            base_version = parse_version_from_commit_history()
            
            if branch == "main":
                return base_version  # メインブランチは動的バージョン
            elif branch == "feature-branch":
                return f"{base_version}-dev"  # 開発ブランチ
            else:
                return f"{base_version}-{branch}"  # 機能ブランチ
    except Exception:
        pass
    return "1.2.4-dev"'''

# 4. get_app_last_update()関数をJST対応版に置き換え
old_get_app_last_update = '''def get_app_last_update():
    """アプリの最終更新日を動的に取得する"""
    try:
        return get_git_date()
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')  # 現在の日付'''

new_get_app_last_update = '''def get_app_last_update():
    """アプリの最終更新日を JST で動的に取得する"""
    try:
        return get_git_date()
    except Exception:
        # 現在のJST時間をフォールバック
        jst = pytz.timezone('Asia/Tokyo')
        return datetime.now(jst).strftime('%Y-%m-%d %H:%M')'''

# 関数を順次置き換え
content = content.replace(old_get_git_date, new_get_git_date)
content = content.replace(old_parse_version, new_parse_version)
content = content.replace(old_get_app_version, new_get_app_version)
content = content.replace(old_get_app_last_update, new_get_app_last_update)

# 修正した内容をファイルに書き込み
with open('app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ app.pyのバージョン管理機能を修正しました")
print("修正内容:")
print("1. get_git_date() - JST時間対応")
print("2. parse_version_from_commit_history() - 改良版バージョン計算")
print("3. get_app_version() - 動的バージョン使用")
print("4. get_app_last_update() - JST時間対応")
