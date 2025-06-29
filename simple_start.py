#!/usr/bin/env python3
"""
最もシンプルで確実なStreamlit起動
"""
import os
import sys

print("🚀 シンプル起動スクリプト開始")

# ポート決定（Railway PORTまたはデフォルト8501）
port = os.getenv('PORT', '8501')
if port == '$PORT' or not str(port).replace('-', '').isdigit():
    port = '8501'

print(f"✅ 使用ポート: {port}")

# すべてのSTREAMLIT_*環境変数を削除
removed_count = 0
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        print(f"🗑️ 削除: {key}")
        del os.environ[key]
        removed_count += 1

print(f"✅ {removed_count}個の環境変数を削除")

# Streamlitの設定ファイルディレクトリを作成
os.makedirs('.streamlit', exist_ok=True)

# 設定ファイルを直接作成
config_content = f"""[server]
port = {port}
address = "0.0.0.0"
headless = true
enableCORS = false

[browser]
gatherUsageStats = false
"""

with open('.streamlit/config.toml', 'w') as f:
    f.write(config_content)

print("📝 .streamlit/config.toml を作成/更新")

# 最もシンプルなコマンドで起動
cmd = f"python3 -m streamlit run app.py"
print(f"📋 実行: {cmd}")

# 実行
exit_code = os.system(cmd)
if exit_code != 0:
    print(f"❌ 終了コード: {exit_code}")
    sys.exit(1)
else:
    print("✅ 正常終了")
