#!/usr/bin/env python3
"""
Render専用起動スクリプト
"""
import os
import sys
import subprocess

def main():
    print("=== Render Startup Debug ===")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    
    # 環境変数確認
    print("Environment variables:")
    for key in ['PORT', 'RENDER_SERVICE_NAME', 'SUPABASE_URL', 'SUPABASE_KEY']:
        value = os.environ.get(key, 'NOT SET')
        if 'KEY' in key and value != 'NOT SET':
            print(f"  {key}: {value[:10]}***")
        else:
            print(f"  {key}: {value}")
    
    # ファイル確認
    print("Files in current directory:")
    for file in sorted(os.listdir('.')):
        print(f"  {file}")
    
    # app.pyの構文チェック
    print("Testing app.py syntax...")
    try:
        with open('app.py', 'r') as f:
            code = f.read()
        compile(code, 'app.py', 'exec')
        print("✅ app.py syntax OK")
    except Exception as e:
        print(f"❌ app.py syntax error: {e}")
        sys.exit(1)
    
    # Streamlitバージョン確認
    try:
        import streamlit as st
        print(f"Streamlit version: {st.__version__}")
    except Exception as e:
        print(f"❌ Streamlit import error: {e}")
        sys.exit(1)
    
    # ポート設定
    port = int(os.environ.get('PORT', 8080))
    print(f"Using port: {port}")
    
    # Streamlit起動
    print("Starting Streamlit server...")
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false',
        '--logger.level', 'info'
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    # Streamlitを実行
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Streamlit execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
