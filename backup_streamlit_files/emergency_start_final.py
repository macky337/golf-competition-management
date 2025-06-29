#!/usr/bin/env python3
"""
最終手段: 完全に環境変数を使わないStreamlit起動
"""
import os
import sys
import subprocess

print("🔥 最終手段起動スクリプト開始")

# 全環境変数を確認
print("🔍 全環境変数調査:")
for key, value in os.environ.items():
    if 'PORT' in key or key.startswith('STREAMLIT_'):
        print(f"  {key}={value}")

# PORTの取得と検証
port_env = os.getenv('PORT', '8501')
print(f"🔍 RAW PORT環境変数: '{port_env}' (type: {type(port_env)})")

# 安全なポート決定
if port_env and port_env != '$PORT' and port_env.isdigit() and int(port_env) > 0:
    port = int(port_env)
else:
    port = 8501
    print(f"⚠️ PORT修正: '{port_env}' -> {port}")

print(f"✅ 確定ポート: {port}")

# 完全環境変数クリーニング
print("🧹 危険な環境変数を完全削除:")
dangerous_vars = []
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_') or key in ['STREAMLIT_SERVER_PORT', 'STREAMLIT_SERVER_ADDRESS']:
        dangerous_vars.append(key)
        print(f"  削除対象: {key}={os.environ[key]}")
        del os.environ[key]

print(f"✅ {len(dangerous_vars)}個の危険な環境変数を削除")

# 最終確認
if 'STREAMLIT_SERVER_PORT' in os.environ:
    print(f"🚨 まだ残存: STREAMLIT_SERVER_PORT={os.environ['STREAMLIT_SERVER_PORT']}")
    del os.environ['STREAMLIT_SERVER_PORT']

print("🚀 subprocess経由でstreamlit起動...")

# 完全に分離されたプロセスで起動
try:
    # 新しい環境辞書を作成（STREAMLIT_*を完全除外）
    clean_env = {}
    for k, v in os.environ.items():
        if not k.startswith('STREAMLIT_'):
            clean_env[k] = v
    
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', str(port),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.enableCORS', 'false'
    ]
    
    print(f"📋 実行コマンド: {' '.join(cmd)}")
    print(f"� クリーン環境変数数: {len(clean_env)}")
    
    # subprocessで完全分離実行
    process = subprocess.Popen(cmd, env=clean_env, cwd=os.getcwd())
    process.wait()
    
    if process.returncode != 0:
        print(f"❌ subprocess失敗: {process.returncode}")
        sys.exit(1)
        
except Exception as e:
    print(f"🚨 subprocess例外: {e}")
    print("💥 フォールバック: os.systemで再試行...")
    
    # フォールバック: os.system
    cmd_str = f"python3 -m streamlit run app.py --server.port {port} --server.address 0.0.0.0 --server.headless true --server.enableCORS false"
    print(f"📋 フォールバックコマンド: {cmd_str}")
    
    exit_code = os.system(cmd_str)
    if exit_code != 0:
        print(f"❌ フォールバックも失敗: {exit_code}")
        sys.exit(1)