#!/usr/bin/env python3
"""
Railway専用：最小限起動スクリプト
"""
import os
import subprocess
import sys

# ポート取得
port = os.getenv('PORT', '8501')
print(f"Railway Port: {port}")

# 危険な環境変数をすべて削除
for var in list(os.environ.keys()):
    if var.startswith('STREAMLIT_'):
        del os.environ[var]

# 新しいプロセス環境を作成
new_env = os.environ.copy()

# 絶対に確実な起動コマンド
try:
    subprocess.run([
        sys.executable, '-c', f'''
import streamlit.web.cli as stcli
import sys
sys.argv = ["streamlit", "run", "app.py", "--server.port", "{port}", "--server.address", "0.0.0.0", "--server.headless", "true"]
stcli.main()
'''
    ], env=new_env, check=True)
except Exception as e:
    print(f"エラー: {e}")
    # フォールバック
    os.system(f"python3 -m streamlit run app.py --server.port {port} --server.address 0.0.0.0 --server.headless true")
