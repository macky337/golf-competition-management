#!/bin/bash
# Railway環境での環境変数確認スクリプト

echo "=== Railway 環境変数確認スクリプト ==="
echo ""

# Railway環境の確認
if [ -n "$RAILWAY_ENVIRONMENT_NAME" ]; then
    echo "✅ Railway環境: $RAILWAY_ENVIRONMENT_NAME"
else
    echo "❌ Railway環境ではありません"
    exit 1
fi

echo ""
echo "=== 必須環境変数チェック ==="

# SUPABASE_URL の確認
if [ -n "$SUPABASE_URL" ]; then
    echo "✅ SUPABASE_URL: 設定済み ($SUPABASE_URL)"
else
    echo "❌ SUPABASE_URL: 未設定"
    MISSING_VARS=true
fi

# SUPABASE_KEY の確認
if [ -n "$SUPABASE_KEY" ]; then
    echo "✅ SUPABASE_KEY: 設定済み (***${SUPABASE_KEY: -10})"
else
    echo "❌ SUPABASE_KEY: 未設定"
    MISSING_VARS=true
fi

echo ""
echo "=== その他の環境変数 ==="
echo "PORT: ${PORT:-未設定}"
echo "NODE_ENV: ${NODE_ENV:-未設定}"

if [ "$MISSING_VARS" = true ]; then
    echo ""
    echo "❌ 環境変数が不足しています"
    echo ""
    echo "Railway Variables で以下を設定してください:"
    echo "1. SUPABASE_URL = https://your-project-ref.supabase.co"
    echo "2. SUPABASE_KEY = your-anon-public-key"
    echo ""
    echo "設定後、アプリケーションが自動的に再デプロイされます。"
    exit 1
else
    echo ""
    echo "✅ すべての必須環境変数が設定されています"
    exit 0
fi
