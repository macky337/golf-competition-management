#!/usr/bin/env python3
"""
核オプション: Streamlitを直接Pythonコードで起動
"""
import os
import sys

print("☢️ 核オプション起動スクリプト")

# ポート取得
port = int(os.getenv('PORT', '8501')) if os.getenv('PORT', '8501').isdigit() else 8501
print(f"🎯 確定ポート: {port}")

# 全STREAMLIT環境変数を物理削除
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        del os.environ[key]
        print(f"💥 強制削除: {key}")

print("🧹 環境クリーニング完了")

try:
    # Streamlitを直接Pythonモジュールとして起動
    print("🚀 Streamlit直接起動開始...")
    
    # sys.argvを完全に制御
    original_argv = sys.argv.copy()
    sys.argv = ['streamlit', 'run', 'app.py']
    
    print(f"📋 sys.argv設定: {sys.argv}")
    
    # Streamlitの設定を直接操作
    import streamlit as st
    from streamlit.web import cli as stcli
    
    # 設定を強制上書き
    st.set_option('server.port', port)
    st.set_option('server.address', '0.0.0.0')
    st.set_option('server.headless', True)
    st.set_option('server.enableCORS', False)
    
    print("⚙️ Streamlit設定完了")
    
    # CLI経由で起動
    stcli.main()
    
except Exception as e:
    print(f"❌ Streamlit直接起動失敗: {e}")
    print("🔄 フォールバック: subprocess起動")
    
    import subprocess
    
    # 最後の手段: subprocess
    cmd = [sys.executable, '-c', f'''
import os
import sys

# 環境クリーニング
for k in list(os.environ.keys()):
    if k.startswith("STREAMLIT_"):
        del os.environ[k]

# config.toml作成
os.makedirs(".streamlit", exist_ok=True)
with open(".streamlit/config.toml", "w") as f:
    f.write("""[server]
port = {port}
address = "0.0.0.0" 
headless = true
enableCORS = false
""")

# 起動
os.system("python3 -m streamlit run app.py")
''']
    
    subprocess.run(cmd)
