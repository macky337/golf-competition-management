#!/bin/bash
# Railway環境変数設定確認・再デプロイスクリプト

echo "🚂 Railway環境変数設定確認"
echo "================================"

# プロジェクト情報
echo "📦 プロジェクト: $RAILWAY_PROJECT_NAME"
echo "🔧 サービス: $RAILWAY_SERVICE_NAME"  
echo "🌍 環境: $RAILWAY_ENVIRONMENT_NAME"
echo ""

# 環境変数チェック
echo "🔍 環境変数チェック:"
if [ -n "$SUPABASE_URL" ]; then
    echo "✅ SUPABASE_URL: 設定済み (${#SUPABASE_URL} 文字)"
else
    echo "❌ SUPABASE_URL: 未設定"
    MISSING_VARS=true
fi

if [ -n "$SUPABASE_KEY" ]; then
    echo "✅ SUPABASE_KEY: 設定済み (${#SUPABASE_KEY} 文字)"
else
    echo "❌ SUPABASE_KEY: 未設定"
    MISSING_VARS=true
fi

if [ "$MISSING_VARS" = true ]; then
    echo ""
    echo "⚠️ 環境変数が設定されていません！"
    echo ""
    echo "🔧 設定手順:"
    echo "1. Railway Dashboard を開く"
    echo "2. プロジェクト '$RAILWAY_PROJECT_NAME' を選択"
    echo "3. 'Variables' タブをクリック"
    echo "4. 以下の変数を追加:"
    echo "   - SUPABASE_URL = https://your-project.supabase.co"
    echo "   - SUPABASE_KEY = eyJhbGciOiJIUzI1NiI..."
    echo ""
    echo "📖 詳細: RAILWAY_ENV_SETUP.md を参照"
    exit 1
else
    echo ""
    echo "✅ すべての環境変数が設定されています"
    echo "🚀 アプリケーションを起動中..."
fi
