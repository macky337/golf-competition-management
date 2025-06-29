#!/usr/bin/env python3
"""
Railway環境デバッグ専用スクリプト
"""
import os
import sys
import subprocess

print("🔍 Railway環境完全分析")
print("=" * 60)

print("📍 基本情報:")
print(f"  Python: {sys.version}")
print(f"  作業ディレクトリ: {os.getcwd()}")
print(f"  ユーザー: {os.getenv('USER', 'unknown')}")

print("\n🌐 PORT関連環境変数:")
port_vars = {k: v for k, v in os.environ.items() if 'PORT' in k.upper()}
for k, v in port_vars.items():
    print(f"  {k} = '{v}' (type: {type(v).__name__})")

print("\n🎛️ STREAMLIT関連環境変数:")
streamlit_vars = {k: v for k, v in os.environ.items() if k.startswith('STREAMLIT_')}
for k, v in streamlit_vars.items():
    print(f"  {k} = '{v}'")

print("\n🚂 RAILWAY関連環境変数:")
railway_vars = {k: v for k, v in os.environ.items() if k.startswith('RAILWAY_')}
for k, v in railway_vars.items():
    print(f"  {k} = '{v}'")

print("\n💻 システム情報:")
try:
    result = subprocess.run(['which', 'streamlit'], capture_output=True, text=True)
    print(f"  streamlit path: {result.stdout.strip()}")
except:
    print("  streamlit path: 見つかりません")

try:
    result = subprocess.run(['streamlit', '--version'], capture_output=True, text=True)
    print(f"  streamlit version: {result.stdout.strip()}")
except:
    print("  streamlit version: 取得失敗")

print("\n🔧 修復開始:")

# 危険な環境変数を削除
dangerous_vars = []
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        dangerous_vars.append(f"{key}={os.environ[key]}")
        del os.environ[key]

print(f"🗑️ 削除した環境変数 ({len(dangerous_vars)}個):")
for var in dangerous_vars:
    print(f"  - {var}")

# ポート確定
port = os.getenv('PORT', '8501')
if port == '$PORT' or not str(port).isdigit():
    port = '8501'

print(f"\n✅ 確定ポート: {port}")

# 設定ファイル作成
os.makedirs('.streamlit', exist_ok=True)
config_content = f"""[server]
port = {port}
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
"""

with open('.streamlit/config.toml', 'w') as f:
    f.write(config_content)

print("📝 .streamlit/config.toml 作成完了")

print("\n🚀 Streamlit起動テスト:")
cmd = "python3 -m streamlit run app.py"
print(f"📋 コマンド: {cmd}")

# 起動
exit_code = os.system(cmd)
print(f"\n📊 結果: exit_code = {exit_code}")

if exit_code != 0:
    print("❌ 起動失敗")
    sys.exit(1)
else:
    print("✅ 起動成功")
