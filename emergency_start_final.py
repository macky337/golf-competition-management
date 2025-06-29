#!/usr/bin/env python3
"""
最終手段: 完全に環境変数を使わないStreamlit起動
"""
import os
import sys
import re

# PORTの取得と検証
port_env = os.getenv('PORT', '8501')
print(f"🔍 RAW PORT環境変数: '{port_env}' (type: {type(port_env)})")

# $PORTのような文字列の場合は8501を使用
if port_env == '$PORT' or not port_env.isdigit():
    port = '8501'
    print(f"⚠️ PORT修正: '{port_env}' -> '{port}'")
else:
    port = port_env

print(f"🔥 最終手段起動スクリプト - 使用ポート: {port}")

# 全STREAMLIT環境変数を削除
print("🧹 環境変数クリア:")
streamlit_vars_deleted = 0
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        print(f"  削除: {key}={os.environ[key]}")
        del os.environ[key]
        streamlit_vars_deleted += 1

print(f"✅ {streamlit_vars_deleted}個のSTREAMLIT環境変数を削除")

# 明示的にSTREAMLIT_SERVER_PORTが残っていないか確認
if 'STREAMLIT_SERVER_PORT' in os.environ:
    print(f"⚠️ STREAMLIT_SERVER_PORT が残存: {os.environ['STREAMLIT_SERVER_PORT']}")
    del os.environ['STREAMLIT_SERVER_PORT']
    print("✅ STREAMLIT_SERVER_PORT を強制削除")

print(f"🚀 streamlit起動開始...")

# streamlitを直接システムコマンドで起動
cmd = f"python3 -m streamlit run app.py --server.port {port} --server.address 0.0.0.0 --server.headless true"
print(f"📋 実行コマンド: {cmd}")

exit_code = os.system(cmd)
if exit_code != 0:
    print(f"❌ 起動失敗: exit code {exit_code}")
    sys.exit(1)