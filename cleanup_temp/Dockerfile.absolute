# Railway絶対確実Dockerfile
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# 基本パッケージインストール
RUN apt-get update && apt-get install -y gcc && apt-get clean

# 要件ファイルコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 全ファイルコピー
COPY . .

# Streamlit設定
RUN mkdir -p .streamlit && echo '[server]\nheadless=true\nport=8080\naddress="0.0.0.0"\n[browser]\ngatherUsageStats=false' > .streamlit/config.toml

# ポート公開
EXPOSE 8080

# 絶対確実な起動コマンド
CMD ["python", "-m", "streamlit", "run", "./app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true", "--server.fileWatcherType=none"]
