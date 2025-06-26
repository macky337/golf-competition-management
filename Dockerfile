# Railway用のDockerfile
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージを更新・インストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Streamlit設定ディレクトリを作成
RUN mkdir -p /app/.streamlit /root/.streamlit

# スクリプトに実行権限を付与
RUN chmod +x start.sh railway_diagnose.py railway_start.py check-env.sh check_vars.py

# ポートを公開
EXPOSE 8501

# 段階的診断と起動
CMD ["sh", "-c", "echo '=== Railway環境変数チェック ===' && python check_vars.py && echo '=== 詳細診断開始 ===' && python railway_diagnose.py"]
