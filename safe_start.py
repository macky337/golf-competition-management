#!/usr/bin/env python3
"""
堅牢なStreamlit起動スクリプト
"""
import os
import sys
import subprocess

def safe_streamlit_start():
    """安全なStreamlit起動"""
    
    print("🚀 堅牢なStreamlit起動スクリプト")
    print("=" * 40)
    
    # ポート設定の確認と修正
    port_env = os.getenv('PORT', '8501')
    print(f"環境変数PORT: {port_env}")
    
    try:
        port = int(port_env)
        print(f"✅ ポート設定成功: {port}")
    except (ValueError, TypeError):
        port = 8501
        print(f"⚠️ ポート設定失敗、デフォルト使用: {port}")
    
    # 環境変数の確認
    print("\n🔍 環境変数確認:")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    print(f"SUPABASE_URL: {'✅ 設定済み' if supabase_url else '❌ 未設定'}")
    print(f"SUPABASE_KEY: {'✅ 設定済み' if supabase_key else '❌ 未設定'}")
    
    # Streamlit設定ディレクトリの作成
    streamlit_dirs = ['/app/.streamlit', '/root/.streamlit']
    for dir_path in streamlit_dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 {dir_path}: 作成済み")
    
    # Streamlit設定ファイルの作成
    config_content = f"""[server]
headless = true
port = {port}
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false
fileWatcherType = "none"

[browser]
gatherUsageStats = false

[logger]
level = "info"
"""
    
    for dir_path in streamlit_dirs:
        config_file = os.path.join(dir_path, 'config.toml')
        with open(config_file, 'w') as f:
            f.write(config_content)
        print(f"⚙️ {config_file}: 設定ファイル作成")
    
    # Streamlit起動コマンド
    cmd = [
        'streamlit', 'run', 'app.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true'
    ]
    
    print(f"\n🚀 起動コマンド: {' '.join(cmd)}")
    print("🔄 Streamlit起動中...")
    
    # プロセス置き換えで起動
    try:
        os.execvp('streamlit', cmd)
    except Exception as e:
        print(f"❌ Streamlit起動エラー: {e}")
        # フォールバック: subprocessで起動
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as se:
            print(f"❌ フォールバック起動も失敗: {se}")
            sys.exit(1)

if __name__ == "__main__":
    safe_streamlit_start()
