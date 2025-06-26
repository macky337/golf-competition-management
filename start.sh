#!/bin/bash
# Railway デプロイ用の起動スクリプト

echo "=== Railway デプロイ起動スクリプト開始 ==="
echo "現在時刻: $(date)"
echo "現在のディレクトリ: $(pwd)"

# 環境変数の確認
echo "=== 環境変数の確認 ==="
echo "RAILWAY_ENVIRONMENT_NAME: ${RAILWAY_ENVIRONMENT_NAME:-未設定}"
echo "PORT: ${PORT:-未設定}"

# Supabase環境変数の詳細チェック
echo "=== Supabase環境変数の詳細チェック ==="
if [ -n "$SUPABASE_URL" ]; then
    echo "✅ SUPABASE_URL: 設定済み (${#SUPABASE_URL} 文字)"
    echo "   値の先頭: ${SUPABASE_URL:0:20}..."
else
    echo "❌ SUPABASE_URL: 未設定"
fi

if [ -n "$SUPABASE_KEY" ]; then
    echo "✅ SUPABASE_KEY: 設定済み (${#SUPABASE_KEY} 文字)"
    echo "   値の先頭: ${SUPABASE_KEY:0:20}..."
else
    echo "❌ SUPABASE_KEY: 未設定"
fi

# 環境変数一覧の表示（Railway関連）
echo "=== Railway関連環境変数 ==="
env | grep -E "(RAILWAY|SUPABASE)" | sort

# Streamlit設定ディレクトリを作成
echo "=== Streamlit設定ディレクトリの作成 ==="
mkdir -p /app/.streamlit
mkdir -p /root/.streamlit
echo "/app/.streamlit ディレクトリを作成しました"
echo "/root/.streamlit ディレクトリを作成しました"

# Streamlit設定ファイルを作成（両方の場所に）
echo "=== Streamlit設定ファイルの作成 ==="
cat > /app/.streamlit/config.toml << EOF
[server]
headless = true
enableCORS = false
enableXsrfProtection = false
fileWatcherType = "none"

[browser]
gatherUsageStats = false

[logger]
level = "info"
EOF

cp /app/.streamlit/config.toml /root/.streamlit/config.toml
echo "Streamlit設定ファイルを作成しました"

# 環境変数が設定されているかチェック
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "❌ 警告: SUPABASE_URL または SUPABASE_KEY が設定されていません"
    echo "Railway の Variables タブで以下の環境変数を設定してください:"
    echo "- SUPABASE_URL"
    echo "- SUPABASE_KEY"
    echo ""
    echo "アプリケーションは起動しますが、データベース機能は使用できません。"
else
    echo "✅ Supabase環境変数が設定されています"
fi

# ディレクトリ構造の確認
echo "=== ディレクトリ構造の確認 ==="
echo "ファイル一覧:"
ls -la /app/ 2>/dev/null || ls -la ./ 
echo ""
echo ".streamlit ディレクトリの内容:"
ls -la /app/.streamlit/ 2>/dev/null || echo "/app/.streamlit/ が見つかりません"
ls -la /root/.streamlit/ 2>/dev/null || echo "/root/.streamlit/ が見つかりません"

# アプリケーションを起動
echo "=== アプリケーション起動 ==="
echo "Streamlitアプリケーションを起動しています..."

exec streamlit run app.py \
  --server.port ${PORT:-8501} \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false
