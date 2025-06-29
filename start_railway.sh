#!/bin/bash
# Railway PostgreSQL版起動スクリプト

unset STREAMLIT_SERVER_PORT
export PORT=${PORT:-8501}

echo "🏌️ 88会ゴルフコンペ・スコア管理システム (Railway版) を起動しています..."
echo "📱 ポート: $PORT"
echo "🔧 環境: Railway PostgreSQL"

# データベース接続確認
if [ -n "$DATABASE_URL" ]; then
    echo "🗄️ PostgreSQL: 接続設定済み"
else
    echo "⚠️ PostgreSQL: 未設定（サンプルデータ使用）"
fi

# アプリ起動（Railway用）
streamlit run app_railway.py --server.port $PORT --server.address 0.0.0.0 --server.headless true