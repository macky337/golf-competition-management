#!/bin/bash
# Railway デプロイ用起動スクリプト

export PORT=${PORT:-8501}
export PYTHONPATH=/app:$PYTHONPATH

echo "🏌️ 88会ゴルフコンペ・スコア管理システム を起動しています..."
echo "📱 ポート: $PORT"
echo "🔧 環境: Railway"

# Streamlit設定
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# アプリ起動
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
