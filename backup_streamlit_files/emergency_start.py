#!/usr/bin/env python3
"""
Railway緊急起動スクリプト
環境変数に依存せず、固定設定でStreamlitを起動
"""

import subprocess
import sys
import os

def emergency_start():
    """緊急起動: 固定設定でStreamlitを起動"""
    print("=" * 50)
    print("RAILWAY緊急起動モード")
    print("=" * 50)
    
    # 作業ディレクトリを確認・変更
    if not os.path.exists('app.py'):
        print("app.pyが見つかりません。アプリディレクトリを検索...")
        if os.path.exists('app/app.py'):
            os.chdir('app')
            print("app/ディレクトリに移動しました")
        else:
            print("app.pyが見つかりません！")
            sys.exit(1)
    
    # Streamlit設定ディレクトリを作成
    os.makedirs('.streamlit', exist_ok=True)
    
    # 固定設定ファイルを作成
    config_content = """[server]
headless = true
port = 8080
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false
fileWatcherType = "none"

[browser]
gatherUsageStats = false

[logger]
level = "info"
"""
    
    with open('.streamlit/config.toml', 'w') as f:
        f.write(config_content)
    
    print("Streamlit設定ファイルを作成しました")
    
    # 環境変数状況を確認
    print("\n環境変数確認:")
    print(f"SUPABASE_URL: {'設定済み' if os.environ.get('SUPABASE_URL') else '未設定'}")
    print(f"SUPABASE_KEY: {'設定済み' if os.environ.get('SUPABASE_KEY') else '未設定'}")
    
    # Streamlitを固定ポートで起動
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port=8080',
        '--server.address=0.0.0.0',
        '--server.headless=true'
    ]
    
    print(f"\n起動コマンド: {' '.join(cmd)}")
    print("Streamlitを起動中...")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n起動が中断されました")
    except subprocess.CalledProcessError as e:
        print(f"\n起動エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    emergency_start()
