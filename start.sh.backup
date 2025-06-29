#!/bin/bash
# ローカル開発用起動スクリプト

unset STREAMLIT_SERVER_PORT
export PORT=${PORT:-8501}

echo "🏌️ 88会ゴルフコンペ・スコア管理システム を起動しています..."
echo "📱 ポート: $PORT"
echo "🔧 環境: ローカル開発"

# アプリ起動（ローカル用）
streamlit run app.py --server.port $PORT
