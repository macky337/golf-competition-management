#!/usr/bin/env python3
"""
Railway用Streamlit起動スクリプト
環境変数の競合を完全に回避
"""
import os
import sys
import subprocess

def main():
    # STREAMLIT関連環境変数をクリア
    env_to_clear = [
        'STREAMLIT_SERVER_PORT',
        'STREAMLIT_SERVER_ADDRESS', 
        'STREAMLIT_SERVER_HEADLESS',
        'STREAMLIT_BROWSER_GATHER_USAGE_STATS'
    ]
    
    for env_var in env_to_clear:
        if env_var in os.environ:
            del os.environ[env_var]
    
    # PORT設定
    port = os.getenv('PORT', '8501')
    
    print(f"🏌️ 88会ゴルフコンペ・スコア管理システム (Railway版) を起動しています...")
    print(f"📱 ポート: {port}")
    print(f"🔧 環境: Railway PostgreSQL")
    
    # データベース接続確認
    if os.getenv('DATABASE_URL'):
        print("🗄️ PostgreSQL: 接続設定済み")
    else:
        print("⚠️ PostgreSQL: 未設定（サンプルデータ使用）")
    
    # デバッグ情報
    print(f"DEBUG: PORT={port}")
    print(f"DEBUG: Python実行中")
    
    # Streamlit起動
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true'
    ]
    
    print(f"DEBUG: 実行コマンド: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Streamlit起動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
