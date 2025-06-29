#!/bin/bash
# Railway PostgreSQL版起動スクリプト

# STREAMLIT関連環境変数をクリア
unset STREAMLIT_SERVER_PORT
unset STREAMLIT_SERVER_ADDRESS
unset STREAMLIT_SERVER_HEADLESS

# PORT設定
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

# デバッグ情報
echo "DEBUG: PORT=$PORT"
echo "DEBUG: STREAMLIT_SERVER_PORT=$STREAMLIT_SERVER_PORT"

# アプリ起動（Railway用）
streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true