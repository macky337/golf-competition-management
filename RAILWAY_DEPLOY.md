# Railway デプロイガイド

## 📦 Railway へのデプロイ手順

### 1. プロジェクトの準備

プロジェクトに以下のファイルが含まれていることを確認：

✅ `Procfile` - Railway用の起動コマンド  
✅ `requirements.txt` - Python依存関係  
✅ `runtime.txt` - Pythonバージョン指定  
✅ `railway.json` - Railway設定ファイル  

### 2. Railwayプロジェクトの作成

1. [Railway](https://railway.app) にアクセス
2. GitHubアカウントでログイン
3. "New Project" → "Deploy from GitHub repo"
4. このリポジトリを選択

### 3. 環境変数の設定

Railwayの Variables タブで以下の環境変数を設定：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `SUPABASE_URL` | `https://your-project-ref.supabase.co` | SupabaseプロジェクトのURL |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI...` | Supabaseのanon/public key |
| `STREAMLIT_CONFIG_DIR` | `/app/.streamlit` | Streamlit設定ディレクトリ（オプション） |
| `PYTHONPATH` | `/app` | Pythonモジュール検索パス（オプション） |

**環境変数の設定方法:**
1. Railwayのプロジェクトダッシュボードを開く
2. "Variables" タブをクリック
3. "New Variable" で上記の変数を追加

**必須の環境変数:**
- `SUPABASE_URL` と `SUPABASE_KEY` は必須です
- その他の変数は起動スクリプトが自動設定します

### 4. Supabase接続情報の取得

1. [Supabase](https://app.supabase.com) でプロジェクトを開く
2. Settings → API に移動
3. 以下の情報をコピー：
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJhbGciOiJIUzI1NiI...`

### 5. デプロイの実行

1. 環境変数設定後、Railwayが自動的に再デプロイを開始
2. ビルドログを確認してエラーがないことを確認
3. "View Logs" でアプリケーションの起動を確認

### 6. アクセス確認

1. Railwayが提供するURLでアプリケーションにアクセス
2. Supabase接続状況をフッターで確認
3. ログイン機能が正常に動作することを確認

---

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. アプリケーションが起動しない

**症状**: デプロイは成功するがアプリケーションにアクセスできない

**解決方法**:
- ビルドログを確認
- `Procfile` のコマンドが正しいか確認
- `requirements.txt` に必要な依存関係がすべて含まれているか確認

#### 2. Supabase接続エラー

**症状**: "Supabase接続情報が見つかりません" エラー

**解決方法**:
- 環境変数 `SUPABASE_URL` と `SUPABASE_KEY` が正しく設定されているか確認
- Supabaseプロジェクトが稼働中か確認
- APIキーが有効か確認

#### 3. ポートエラー

**症状**: "Port already in use" エラー

**解決方法**:
- `Procfile` で `$PORT` 環境変数を使用していることを確認
- Railway側で自動的にポートが割り当てられます

#### 4. 依存関係エラー

**症状**: パッケージのインストールに失敗

**解決方法**:
- `requirements.txt` の書式を確認
- 不要な依存関係を削除
- Python バージョンの互換性を確認

#### 6. Railway固有のエラー

**症状**: "No secrets found" エラー

**解決方法**:
- Railway Variables で `SUPABASE_URL` と `SUPABASE_KEY` が設定されているか確認
- 変数名にタイポがないか確認
- デプロイ後に環境変数を追加した場合は、手動で再デプロイを実行

**症状**: "Permission denied" エラー

**解決方法**:
- `start.sh` ファイルに実行権限があることを確認
- Gitリポジトリで `chmod +x start.sh` を実行してコミット

**症状**: Streamlit設定エラー

**解決方法**:
- アプリケーションのデバッグ情報を確認
- `/app/.streamlit` ディレクトリが正しく作成されているか確認
- 起動スクリプトが正常に実行されているかログで確認

---

## 📝 設定ファイルの詳細

### Procfile
```
web: ./start.sh
```

### start.sh (起動スクリプト)
```bash
#!/bin/bash
# Railway デプロイ用の起動スクリプト

# Streamlit設定ディレクトリを作成
mkdir -p /app/.streamlit

# Streamlit設定ファイルを作成（Railway環境用）
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

# アプリケーションを起動
exec streamlit run app.py \
  --server.port ${PORT:-8501} \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false
```

### railway.json
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "./start.sh",
    "healthcheckPath": "/_stcore/health",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### runtime.txt
```
python-3.11.12
```

---

## ⚠️ Railway特有の設定

### コンテナ内でのパス設定

Railwayのコンテナ環境では、アプリケーションは `/app` ディレクトリに配置されます。
以下の環境変数を追加設定することで、パスの問題を解決できます：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `STREAMLIT_CONFIG_DIR` | `/app/.streamlit` | Streamlit設定ディレクトリ |
| `PYTHONPATH` | `/app` | Pythonモジュール検索パス |

### Railway専用の起動設定

Railwayコンテナでの最適化されたStreamlit起動オプション：

```bash
streamlit run app.py \
  --server.port $PORT \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --server.fileWatcherType none \
  --browser.gatherUsageStats false
```

---

## 🔒 セキュリティ考慮事項

1. **環境変数の管理**
   - Supabase APIキーは必ず環境変数で管理
   - .envファイルはGitにコミットしない

2. **Supabaseセキュリティ**
   - Row Level Security (RLS) を有効化
   - 適切な認証ポリシーを設定

3. **アクセス制御**
   - アプリケーション内でのパスワード認証
   - 管理者機能の保護

---

## 📞 サポート

デプロイで問題が発生した場合：

1. まずこのガイドのトラブルシューティングを確認
2. Railwayのビルドログを詳細に確認
3. プロジェクト管理者にお問い合わせ

## 🚀 更新とメンテナンス

### コードの更新
1. GitHubにプッシュするとRailwayが自動的に再デプロイ
2. 環境変数の変更時は手動で再デプロイが必要

### データベースメンテナンス
1. アプリケーション内のバックアップ機能を定期実行
2. Supabaseダッシュボードでのモニタリング
