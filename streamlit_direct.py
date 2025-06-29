#!/usr/bin/env python3
"""
Streamlit直接起動スクリプト - Python API使用
"""
import os
import sys

print("🚀 Streamlit Python API直接起動")

# ポート取得
port_env = os.getenv('PORT', '8501')
port = 8501 if port_env == '$PORT' or not str(port_env).isdigit() else int(port_env)
print(f"✅ ポート: {port}")

# 危険な環境変数削除
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        del os.environ[key]

try:
    # Streamlit APIで直接起動
    import streamlit.web.cli as stcli
    
    sys.argv = [
        'streamlit', 'run', 'app.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true'
    ]
    
    print(f"📋 Streamlit直接起動: ポート{port}")
    stcli.main()
    
except Exception as e:
    print(f"❌ Streamlit API失敗: {e}")
    print("🔄 外部コマンド実行にフォールバック")
    
    import subprocess
    cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py', 
           '--server.port', str(port), '--server.address', '0.0.0.0', '--server.headless', 'true']
    subprocess.run(cmd)
