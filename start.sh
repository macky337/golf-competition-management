#!/bin/bash
# Railway デプロイ用の起動スクリプト

# Streamlit設定ディレクトリを作成
mkdir -p /app/.streamlit

# Streamlit設定ファイルを作成（Railway環境用）
cat > /app/.streamlit/config.toml << EOF
[server]
headless = true
enableCORS = false
enableXsrfProtection = false
fileWatcherType = "none"

[browser]
gatherUsageStats = false

[logger]
level = "info"
EOF

# アプリケーションを起動
exec streamlit run app.py \
  --server.port ${PORT:-8501} \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false
