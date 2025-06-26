#!/usr/bin/env python3
"""
Railway環境の詳細診断とSupabase接続確認
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def diagnose_railway_environment():
    """Railway環境を徹底的に診断"""
    
    print("=" * 60)
    print("RAILWAY環境診断レポート")
    print("=" * 60)
    
    # 基本情報
    print(f"Python実行パス: {sys.executable}")
    print(f"Python バージョン: {sys.version}")
    print(f"現在のディレクトリ: {os.getcwd()}")
    print(f"プロセスID: {os.getpid()}")
    
    # Railway固有の環境変数
    print("\n--- Railway固有情報 ---")
    railway_vars = [
        'RAILWAY_ENVIRONMENT_NAME',
        'RAILWAY_PROJECT_ID',
        'RAILWAY_PROJECT_NAME',
        'RAILWAY_SERVICE_ID',
        'RAILWAY_SERVICE_NAME',
        'RAILWAY_DEPLOYMENT_ID',
        'RAILWAY_REPLICA_ID',
        'RAILWAY_SNAPSHOT_ID',
        'RAILWAY_VOLUME_MOUNT_PATH',
        'NIXPACKS_METADATA'
    ]
    
    for var in railway_vars:
        value = os.getenv(var)
        print(f"{var}: {value if value else '未設定'}")
    
    # Supabase環境変数の詳細チェック
    print("\n--- Supabase環境変数詳細 ---")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    print(f"SUPABASE_URL:")
    print(f"  - os.environ内存在: {'SUPABASE_URL' in os.environ}")
    print(f"  - os.getenv()結果: {supabase_url is not None}")
    if supabase_url:
        print(f"  - 長さ: {len(supabase_url)} 文字")
        print(f"  - プレビュー: {supabase_url[:50]}...")
        print(f"  - 末尾プレビュー: ...{supabase_url[-20:]}")
    
    print(f"SUPABASE_KEY:")
    print(f"  - os.environ内存在: {'SUPABASE_KEY' in os.environ}")
    print(f"  - os.getenv()結果: {supabase_key is not None}")
    if supabase_key:
        print(f"  - 長さ: {len(supabase_key)} 文字")
        print(f"  - プレビュー: {supabase_key[:50]}...")
    
    # 全環境変数のキー一覧（機密性の高いもの以外）
    print("\n--- 全環境変数キー ---")
    env_keys = sorted(os.environ.keys())
    for key in env_keys:
        if any(keyword in key.upper() for keyword in ['SUPABASE', 'RAILWAY', 'PORT', 'HOST']):
            print(f"  {key}")
    
    # プロセス環境の確認
    print("\n--- プロセス環境 ---")
    try:
        # 現在のプロセスの環境変数を別の方法で取得
        with open(f'/proc/{os.getpid()}/environ', 'rb') as f:
            proc_env = f.read().decode('utf-8', errors='ignore').split('\0')
            supabase_found = [var for var in proc_env if 'SUPABASE' in var]
            print(f"プロセス環境内のSupabase変数: {len(supabase_found)}個")
            for var in supabase_found:
                if var:
                    key, value = var.split('=', 1) if '=' in var else (var, '')
                    if 'KEY' in key:
                        print(f"  {key}=***masked***")
                    else:
                        print(f"  {key}={value[:50]}...")
    except Exception as e:
        print(f"プロセス環境読み取りエラー: {e}")
    
    # ファイルシステムの確認
    print("\n--- ファイルシステム確認 ---")
    paths_to_check = [
        '/.env',
        '/app/.env',
        '/workspaces/golf-competition-management/.env',
        '.env',
        '.streamlit/secrets.toml'
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            print(f"  {path}: 存在")
            try:
                size = os.path.getsize(path)
                print(f"    サイズ: {size} bytes")
            except:
                print(f"    サイズ: 読み取り不可")
        else:
            print(f"  {path}: 不存在")
    
    # ネットワーク・ポート確認
    print("\n--- ネットワーク設定 ---")
    port = os.getenv('PORT', '8501')
    host = os.getenv('HOST', '0.0.0.0')
    print(f"PORT: {port}")
    print(f"HOST: {host}")
    
    return supabase_url, supabase_key

def test_supabase_connection(url, key):
    """Supabase接続テスト"""
    if not url or not key:
        print("\n❌ Supabase環境変数が設定されていません")
        return False
    
    print("\n--- Supabase接続テスト ---")
    try:
        import requests
        
        # 簡単なAPIテスト
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        
        # REST APIエンドポイントにGETリクエスト
        test_url = f"{url}/rest/v1/"
        print(f"テストURL: {test_url}")
        
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"レスポンスステータス: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Supabase接続成功")
            return True
        else:
            print(f"❌ Supabase接続失敗: {response.status_code}")
            print(f"レスポンス: {response.text[:200]}")
            return False
            
    except ImportError:
        print("⚠️ requestsライブラリが見つかりません - pip install requestsを実行してください")
        return False
    except Exception as e:
        print(f"❌ 接続テストエラー: {e}")
        return False

def create_env_file_fallback():
    """環境変数のファイルフォールバック作成"""
    env_data = {
        'SUPABASE_URL': os.getenv('SUPABASE_URL', ''),
        'SUPABASE_KEY': os.getenv('SUPABASE_KEY', ''),
        'PORT': os.getenv('PORT', '8501'),
        'RAILWAY_ENVIRONMENT_NAME': os.getenv('RAILWAY_ENVIRONMENT_NAME', ''),
    }
    
    # 複数の場所にファイルを作成
    fallback_paths = [
        '/tmp/railway_env.txt',
        '/tmp/railway_env.json',
        'railway_env.txt'
    ]
    
    print("\n--- 環境変数ファイルフォールバック作成 ---")
    for path in fallback_paths:
        try:
            if path.endswith('.json'):
                with open(path, 'w') as f:
                    json.dump(env_data, f, indent=2)
            else:
                with open(path, 'w') as f:
                    for key, value in env_data.items():
                        f.write(f"{key}={value}\n")
            print(f"✅ {path} 作成成功")
        except Exception as e:
            print(f"❌ {path} 作成失敗: {e}")

def main():
    """メイン関数"""
    try:
        supabase_url, supabase_key = diagnose_railway_environment()
        create_env_file_fallback()
        test_supabase_connection(supabase_url, supabase_key)
        
        print("\n" + "=" * 60)
        print("診断完了 - Streamlitアプリケーション起動中...")
        print("=" * 60)
        
        # Streamlit起動
        port = os.getenv('PORT', '8501')
        cmd = [
            'streamlit', 'run', 'app.py',
            '--server.port', port,
            '--server.address', '0.0.0.0',
            '--server.headless', 'true',
            '--server.enableCORS', 'false',
            '--server.enableXsrfProtection', 'false',
            '--server.fileWatcherType', 'none',
            '--browser.gatherUsageStats', 'false'
        ]
        
        print(f"起動コマンド: {' '.join(cmd)}")
        subprocess.run(cmd)
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
