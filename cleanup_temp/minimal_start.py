#!/usr/bin/env python3
"""
Railway専用の最小限起動スクリプト
"""
import os
import sys
import subprocess

def main():
    print("🚀 Railway専用最小限起動スクリプト")
    
    # ポート設定
    port = 8080  # Railwayのデフォルト
    port_env = os.getenv('PORT')
    if port_env:
        try:
            port = int(port_env)
            print(f"✅ 環境変数PORTを使用: {port}")
        except:
            print(f"⚠️ 環境変数PORT無効、デフォルト使用: {port}")
    
    # 環境変数確認
    supabase_url = os.getenv('SUPABASE_URL', '')
    supabase_key = os.getenv('SUPABASE_KEY', '')
    
    print(f"SUPABASE_URL: {'設定済み' if supabase_url else '未設定'}")
    print(f"SUPABASE_KEY: {'設定済み' if supabase_key else '未設定'}")
    
    # Streamlit設定作成
    os.makedirs('/app/.streamlit', exist_ok=True)
    
    # 最小限のStreamlit起動
    cmd = ['python', '-m', 'streamlit', 'run', 'app.py', '--server.port=' + str(port), '--server.address=0.0.0.0', '--server.headless=true']
    
    print(f"🚀 実行: {' '.join(cmd)}")
    
    try:
        os.execvp('python', cmd)
    except Exception as e:
        print(f"❌ 起動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
