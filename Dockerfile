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

# 起動スクリプト作成（ポート動的対応）
RUN echo '#!/bin/bash\nPORT=${PORT:-8080}\npython -m streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true' > start.sh
RUN chmod +x start.sh

EXPOSE $PORT

# 動的ポートで起動
CMD ["bash", "start.sh"]
