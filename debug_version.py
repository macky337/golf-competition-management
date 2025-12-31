import sys
import os
import subprocess
from datetime import datetime
import pytz
import re

def get_git_revision():
    try:
        result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                               capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return 'unknown'

def get_git_count():
    try:
        return subprocess.check_output(['git', 'rev-list', '--count', 'HEAD']).decode('ascii').strip()
    except Exception:
        return '0'

def get_git_date():
    try:
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d %H:%M'], 
                               capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return datetime.now().strftime('%Y-%m-%d %H:%M')

def get_git_date_jst():
    try:
        # JST時間で取得
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=format-local:%Y-%m-%d %H:%M'], 
                               capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    # フォールバック：現在のJST時間
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime('%Y-%m-%d %H:%M')

def get_git_latest_commit_message():
    try:
        return subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip()
    except Exception:
        return ''

def get_app_version():
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                               capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch == 'main':
                return parse_version_from_commit_history()  # 動的バージョン使用
            elif branch == 'feature-branch':
                return f"{parse_version_from_commit_history()}-dev"
            else:
                return f"{parse_version_from_commit_history()}-{branch}"
    except Exception:
        pass
    return '1.0.0 (dev)'

def parse_version_from_commit_history():
    major = 1
    minor = 0
    patch = 0
    
    try:
        latest_commit_message = get_git_latest_commit_message()
        print(f'Latest commit message: "{latest_commit_message}"')
        
        if re.search(r'^(major:|MAJOR:|!:)', latest_commit_message):
            major += 1
            minor = 0
            patch = 0
        elif re.search(r'^(feature:|feat:|FEATURE:)', latest_commit_message):
            minor += 1
            patch = 0
        elif re.search(r'^(fix:|bugfix:|FIX:)', latest_commit_message):
            patch += 1
        else:
            # コミット数をパッチバージョンとして使用
            count = int(get_git_count())
            patch = count % 100  # 最大99まで
            minor = (count // 100) % 100
            major = 1 + (count // 10000)
            
        return f'{major}.{minor}.{patch}'
    except Exception as e:
        print(f'Error in parse_version_from_commit_history: {e}')
        return '1.0.7'

if __name__ == "__main__":
    print(f'Git revision: {get_git_revision()}')
    print(f'Git commit count: {get_git_count()}')
    print(f'Current branch version: {get_app_version()}')
    print(f'Git date (original): {get_git_date()}')
    print(f'Git date (JST): {get_git_date_jst()}')
    print(f'Parsed version: {parse_version_from_commit_history()}')
    
    # 現在のタイムゾーン情報
    print(f'Current time (system): {datetime.now()}')
    jst = pytz.timezone('Asia/Tokyo')
    print(f'Current time (JST): {datetime.now(jst).strftime("%Y-%m-%d %H:%M")}')
