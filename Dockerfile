# Render最適化Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 基本パッケージ
RUN apt-get update && apt-get install -y gcc && apt-get clean

# 依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーション
COPY . .

# Streamlit設定とポート動的対応
RUN mkdir -p .streamlit
RUN echo '[server]\nheadless=true\naddress="0.0.0.0"\n[browser]\ngatherUsageStats=false' > .streamlit/config.toml

# 起動スクリプト作成（ポート動的対応 + デバッグ情報）
RUN echo '#!/bin/bash\necho "=== Render Startup Debug ==="\necho "Working directory: $(pwd)"\necho "Files in current directory:"\nls -la\necho "Python version: $(python --version)"\necho "Streamlit version: $(python -c \"import streamlit; print(streamlit.__version__)\")"\necho "Environment variables:"\nenv | grep -E "(PORT|RENDER|SUPABASE)" || echo "No relevant vars found"\nPORT=${PORT:-8080}\necho "Using port: $PORT"\necho "Testing app.py syntax..."\npython -m py_compile app.py\necho "App syntax OK"\necho "Starting Streamlit server..."\nexec python -m streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false --logger.level=info' > start.sh
RUN chmod +x start.sh

# ポート公開（固定値を使用）
EXPOSE 8080

# 動的ポートで起動
CMD ["bash", "start.sh"]
