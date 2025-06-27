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

# 起動スクリプトを実行可能にする
RUN chmod +x render_start.py

# ポート公開（固定値を使用）
EXPOSE 8080

# Python起動スクリプトを使用
CMD ["python", "render_start.py"]
