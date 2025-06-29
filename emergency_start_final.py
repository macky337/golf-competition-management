#!/usr/bin/env python3
"""
最終手段: 完全に環境変数を使わないStreamlit起動
"""
import os
import sys

# 確実にPORT番号を取得
port = os.getenv('PORT', '8501')
print(f"🔥 最終手段起動スクリプト - ポート: {port}")

# 全STREAMLIT環境変数を削除
print("🧹 環境変数クリア:")
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        print(f"  削除: {key}")
        del os.environ[key]

print(f"🚀 streamlit起動開始...")

# streamlitを直接システムコマンドで起動
cmd = f"python3 -m streamlit run app.py --server.port {port} --server.address 0.0.0.0 --server.headless true"
print(f"📋 コマンド: {cmd}")

exit_code = os.system(cmd)
if exit_code != 0:
    print(f"❌ 起動失敗: exit code {exit_code}")
    sys.exit(1)