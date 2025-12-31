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

def get_git_latest_commit_message():
    try:
        return subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip()
    except Exception:
        return ''

def get_git_date():
    """Git の最終コミット日時を JST で取得"""
    try:
        # JST時間で取得を試行
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=format-local:%Y-%m-%d %H:%M'], 
                               capture_output=True, text=True, cwd='.')
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # フォールバック：UTC時間を取得してJSTに変換
        result = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=iso'], 
                               capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            # ISO形式の日時をパースしてJSTに変換
            try:
                from dateutil import parser
                dt = parser.parse(result.stdout.strip())
                jst = pytz.timezone('Asia/Tokyo')
                dt_jst = dt.astimezone(jst)
                return dt_jst.strftime("%Y-%m-%d %H:%M")
            except:
                pass
    except Exception:
        pass
    
    # 最終フォールバック：現在のJST時間
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime("%Y-%m-%d %H:%M")

def parse_version_from_commit_history():
    """コミット履歴を解析し、適切なバージョン番号を計算する"""
    major = 1
    minor = 0
    patch = 0
    
    try:
        # 最新のコミットメッセージを取得
        latest_commit_message = get_git_latest_commit_message()
        print(f'Latest commit message: "{latest_commit_message}"')
        
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
    except Exception as e:
        print(f'Error: {e}')
        # デフォルトバージョン
        return "1.2.3"

def get_app_version():
    """アプリバージョンを取得（動的バージョン使用）"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                               capture_output=True, text=True, cwd='.')
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
    return "1.2.3-dev"

def get_app_last_update():
    """アプリの最終更新日を JST で動的に取得する"""
    try:
        return get_git_date()
    except Exception:
        # 現在のJST時間をフォールバック
        jst = pytz.timezone('Asia/Tokyo')
        return datetime.now(jst).strftime('%Y-%m-%d %H:%M')

if __name__ == "__main__":
    print("=== 修正後のバージョン管理テスト ===")
    print(f'Git revision: {get_git_revision()}')
    print(f'Git commit count: {get_git_count()}')
    print(f'Parsed version: {parse_version_from_commit_history()}')
    print(f'App version: {get_app_version()}')
    print(f'Git date (JST): {get_git_date()}')
    print(f'App last update (JST): {get_app_last_update()}')
