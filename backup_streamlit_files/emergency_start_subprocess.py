#!/usr/bin/env python3
"""
超絶安全起動スクリプト: subprocess使用
"""
import os
import sys
import subprocess

# 安全にPORTを取得
port_raw = os.getenv('PORT', '8501')
print(f"🔍 元PORT値: '{port_raw}'")

# 数値チェック
try:
    if port_raw and port_raw != '$PORT' and port_raw.isdigit():
        port = int(port_raw)
    else:
        port = 8501
        print(f"⚠️ ポート修正: '{port_raw}' -> {port}")
except:
    port = 8501
    print(f"❌ ポート解析失敗、デフォルト: {port}")

print(f"🚀 超絶安全起動 - ポート: {port}")

# 完全環境クリア
env_clean = {}
for k, v in os.environ.items():
    if not k.startswith('STREAMLIT_'):
        env_clean[k] = v

print(f"🧹 STREAMLIT_*環境変数を除外した新環境準備完了")

# subprocessで完全分離実行
cmd = [
    sys.executable, '-m', 'streamlit', 'run', 'app.py',
    '--server.port', str(port),
    '--server.address', '0.0.0.0',
    '--server.headless', 'true'
]

print(f"📋 実行: {' '.join(cmd)}")

try:
    result = subprocess.run(cmd, env=env_clean, cwd=os.getcwd())
    sys.exit(result.returncode)
except Exception as e:
    print(f"❌ subprocess実行エラー: {e}")
    sys.exit(1)
