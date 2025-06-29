#!/usr/bin/env python3
"""
完全回避: streamlitコマンドを一切使わない起動
"""
import os
import sys

print("🚫 streamlitコマンド完全回避起動")

# ポート取得
port = os.getenv('PORT', '8501')
if port == '$PORT' or not str(port).isdigit():
    port = '8501'

port = int(port)
print(f"✅ ポート: {port}")

# 危険な環境変数を完全削除
deleted_vars = []
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        deleted_vars.append(key)
        del os.environ[key]

print(f"🗑️ 削除: {deleted_vars}")

try:
    # Streamlitを直接Pythonモジュールとして実行
    print("🔧 Streamlit直接制御開始...")
    
    import streamlit as st
    from streamlit.web.bootstrap import run
    
    # 設定を直接制御
    st.set_option('server.port', port)
    st.set_option('server.address', '0.0.0.0')
    st.set_option('server.headless', True)
    st.set_option('server.enableCORS', False)
    st.set_option('browser.gatherUsageStats', False)
    
    print("⚙️ Streamlit設定完了")
    
    # アプリファイルを直接実行
    print(f"🚀 app.py直接実行開始...")
    
    # Streamlitの内部起動メカニズムを使用
    run('app.py', 'streamlit run', [], flag_options={})
    
except ImportError as e:
    print(f"❌ Streamlitインポートエラー: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 直接制御失敗: {e}")
    print("🔄 フォールバック試行...")
    
    # 最後の手段: Python内でstreamlitプロセス起動
    import subprocess
    
    # 新しい環境を作成（STREAMLIT_*なし）
    clean_env = {}
    for k, v in os.environ.items():
        if not k.startswith('STREAMLIT_'):
            clean_env[k] = v
    
    # .streamlit/config.tomlを確実に作成
    os.makedirs('.streamlit', exist_ok=True)
    with open('.streamlit/config.toml', 'w') as f:
        f.write(f'''[server]
port = {port}
address = "0.0.0.0"
headless = true
enableCORS = false
''')
    
    print("📝 config.toml作成完了")
    
    # Python経由でstreamlit実行（環境変数なし）
    cmd = [sys.executable, '-m', 'streamlit', 'run', 'app.py']
    print(f"📋 クリーン実行: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, env=clean_env)
    sys.exit(result.returncode)
