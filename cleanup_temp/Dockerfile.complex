# Railway緊急対応Dockerfile - 複数起動オプション
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

# すべてのスクリプトに実行権限付与
RUN chmod +x railway_wrapper.py || true
RUN chmod +x emergency_start.py || true

# Streamlit設定ディレクトリ作成
RUN mkdir -p .streamlit /root/.streamlit

# 複数の設定ファイルを作成
RUN echo '[server]\nheadless = true\nport = 8080\naddress = "0.0.0.0"\nenableCORS = false\nenableXsrfProtection = false\nfileWatcherType = "none"\n\n[browser]\ngatherUsageStats = false\n\n[logger]\nlevel = "info"' > .streamlit/config.toml

RUN cp .streamlit/config.toml /root/.streamlit/config.toml

# ポート公開
EXPOSE 8080

# 起動スクリプト作成
RUN echo '#!/bin/bash\nset -e\necho "=== Railway Emergency Startup ==="\necho "Trying multiple startup methods..."\n\n# Method 1: Wrapper script\necho "Method 1: Using wrapper script"\npython railway_wrapper.py &\nPID1=$!\n\n# Wait a bit\nsleep 5\n\n# Check if still running\nif kill -0 $PID1 2>/dev/null; then\n    echo "Method 1 successful, waiting..."\n    wait $PID1\nelse\n    echo "Method 1 failed, trying Method 2"\n    # Method 2: Direct streamlit\n    echo "Method 2: Direct streamlit"\n    python -m streamlit run app.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true\nfi' > startup.sh

RUN chmod +x startup.sh

# 緊急起動スクリプトを使用
CMD ["bash", "startup.sh"]
