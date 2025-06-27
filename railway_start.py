#!/usr/bin/env python3
"""
Railway環境での環境変数確認・設定スクリプト
"""
import os
import sys

def check_railway_env():
    """Railway環境の環境変数をチェックし、ファイルに保存"""
    
    print("=== Railway環境変数チェックスクリプト ===")
    print(f"Python実行パス: {sys.executable}")
    print(f"現在のディレクトリ: {os.getcwd()}")
    print(f"RAILWAY_ENVIRONMENT_NAME: {os.getenv('RAILWAY_ENVIRONMENT_NAME', '未設定')}")
    
    # 環境変数の確認
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    print(f"SUPABASE_URL in os.environ: {'SUPABASE_URL' in os.environ}")
    print(f"SUPABASE_KEY in os.environ: {'SUPABASE_KEY' in os.environ}")
    
    if supabase_url:
        print(f"SUPABASE_URL 長さ: {len(supabase_url)} 文字")
        print(f"SUPABASE_URL プレビュー: {supabase_url[:30]}...")
    
    if supabase_key:
        print(f"SUPABASE_KEY 長さ: {len(supabase_key)} 文字")
        print(f"SUPABASE_KEY プレビュー: {supabase_key[:30]}...")
    
    # Railway関連の環境変数を表示
    print("\n=== Railway関連環境変数 ===")
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ['RAILWAY', 'SUPABASE', 'PORT']):
            if 'KEY' in key or 'SECRET' in key:
                print(f"{key}: {'*' * len(value) if value else '未設定'}")
            else:
                print(f"{key}: {value}")
    
    # 環境変数をファイルに保存（デバッグ用）
    env_file_path = '/tmp/railway_env.txt'
    with open(env_file_path, 'w') as f:
        f.write(f"RAILWAY_ENVIRONMENT_NAME={os.getenv('RAILWAY_ENVIRONMENT_NAME', '')}\n")
        f.write(f"SUPABASE_URL={os.getenv('SUPABASE_URL', '')}\n")
        f.write(f"SUPABASE_KEY={os.getenv('SUPABASE_KEY', '')}\n")
        f.write(f"PORT={os.getenv('PORT', '')}\n")
    
    print(f"\n環境変数情報を {env_file_path} に保存しました")
    
    # Streamlitの起動
    print("\n=== Streamlitアプリケーション起動 ===")
    import subprocess
    
    # ポート設定の確認
    port_env = os.getenv('PORT', '8501')
    try:
        port = int(port_env)
    except (ValueError, TypeError):
        port = 8501
    
    cmd = [
        'streamlit', 'run', 'app.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false',
        '--server.fileWatcherType', 'none',
        '--browser.gatherUsageStats', 'false'
    ]
    
    print(f"起動コマンド: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    check_railway_env()
