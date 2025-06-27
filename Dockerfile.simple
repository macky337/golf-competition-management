# Railway超シンプルDockerfile
FROM python:3.11-slim

WORKDIR /app

# 必要最小限のパッケージをインストール
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションをコピー
COPY . .

# ポート8080を公開
EXPOSE 8080

# 直接streamlitを起動（環境変数は一切使用しない）
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
