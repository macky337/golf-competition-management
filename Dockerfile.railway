# Railway最終手段Dockerfile - ENTRYPOINT使用
FROM python:3.11-slim

WORKDIR /app

# 基本パッケージ
RUN apt-get update && apt-get install -y gcc && apt-get clean

# 依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーション
COPY . .

# 最終起動スクリプト作成
RUN echo '#!/bin/bash\nset -e\nexport PORT=8080\nunset RAILWAY_PORT 2>/dev/null || true\nunset NIXPACKS_PORT 2>/dev/null || true\necho "=== FINAL RAILWAY STARTUP ==="\necho "Environment cleaned, starting Streamlit..."\nmkdir -p .streamlit\necho "[server]\nheadless=true\nport=8080\naddress=\"0.0.0.0\"\n[browser]\ngatherUsageStats=false" > .streamlit/config.toml\npython -m streamlit run app.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true' > final_start.sh

RUN chmod +x final_start.sh

EXPOSE 8080

# ENTRYPOINTを使用してCMD上書きを防ぐ
ENTRYPOINT ["bash", "final_start.sh"]
