#!/usr/bin/env python3
"""
最もシンプルで確実なStreamlit起動 - 完全config.toml依存
"""
import os
import sys

print("🚀 完全config.toml依存起動スクリプト開始")

# ポート決定（Railway PORTまたはデフォルト8501）
port = os.getenv('PORT', '8501')
if port == '$PORT' or not str(port).replace('-', '').isdigit():
    port = '8501'

print(f"✅ 使用ポート: {port}")

# すべてのSTREAMLIT_*環境変数を完全削除
removed_vars = []
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        removed_vars.append(f"{key}={os.environ[key]}")
        del os.environ[key]

print(f"🗑️ 削除した環境変数: {len(removed_vars)}個")
for var in removed_vars:
    print(f"  - {var}")

# Streamlitの設定ディレクトリを確実に作成
os.makedirs('.streamlit', exist_ok=True)

# 完全な設定ファイルを作成（コマンドライン引数不要）
config_content = f"""[server]
port = {port}
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = false
runOnSave = false

[browser]
gatherUsageStats = false
serverAddress = "0.0.0.0"
serverPort = {port}

[logger]
level = "info"

[theme]
base = "light"
"""

config_path = '.streamlit/config.toml'
with open(config_path, 'w') as f:
    f.write(config_content)

print(f"📝 {config_path} を作成完了")
print(f"📄 設定内容:")
print(config_content)

# 引数なしで起動（完全にconfig.tomlに依存）
cmd = "python3 -m streamlit run app.py"
print(f"📋 実行コマンド: {cmd}")
print("🎯 注意: コマンドライン引数は一切使用しません")

# 実行
print("🚀 Streamlit起動中...")
exit_code = os.system(cmd)

if exit_code != 0:
    print(f"❌ 終了コード: {exit_code}")
    sys.exit(1)
else:
    print("✅ 正常終了")
