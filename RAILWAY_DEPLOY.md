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

**重要**: 現在Railway環境でアプリケーションは起動していますが、Supabase環境変数が設定されていません。

Railwayの Variables タブで以下の環境変数を設定：

| 変数名 | 値 | 説明 | 状況 |
|--------|-----|------|------|
| `SUPABASE_URL` | `https://your-project-ref.supabase.co` | SupabaseプロジェクトのURL | ❌ 未設定 |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI...` | Supabaseのanon/public key | ❌ 未設定 |
| `STREAMLIT_CONFIG_DIR` | `/app/.streamlit` | Streamlit設定ディレクトリ（オプション） | ✅ 自動設定 |
| `PYTHONPATH` | `/app` | Pythonモジュール検索パス（オプション） | ✅ 自動設定 |

**今すぐ設定する手順:**
1. [Railway](https://railway.app) のプロジェクトページを開く
2. **"Variables"** タブをクリック
3. **"New Variable"** で以下を追加:
   ```
   SUPABASE_URL = https://your-project-ref.supabase.co
   SUPABASE_KEY = eyJhbGciOiJIUzI1NiI...
   ```
4. 保存すると自動的に再デプロイが開始されます

**必須の環境変数:**
- `SUPABASE_URL` と `SUPABASE_KEY` は必須です
- 設定しないとデータベース機能が使用できません
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

**✅ 設定完了チェックリスト:**
- [ ] Railway環境でアプリケーションが起動している
- [ ] 環境変数 `SUPABASE_URL` と `SUPABASE_KEY` が設定済み
- [ ] アプリケーション画面で "✅ Railway環境: Supabase接続情報が設定されています" と表示される
- [ ] Supabase接続テストが成功する
- [ ] ログイン画面が表示される

### 7. デプロイ成功後の確認

**アプリケーションが正常に動作している場合:**

1. **Railway環境確認**:
   - "🚂 Railway環境で実行中" が表示される
   - デバッグ情報で `RAILWAY_ENVIRONMENT_NAME: production` が確認できる

2. **Supabase接続確認**:
   - "✅ Railway環境: Supabase接続情報が設定されています" が表示される
   - "🔗 Supabase接続テスト" で接続テストが成功する

3. **機能確認**:
   - ユーザーログイン (パスワード: 88)
   - 管理者ログイン (パスワード: admin88)
   - データの表示と分析機能

**次のステップ:**
- 初期データの投入
- ユーザーへのアクセス情報共有
- 定期バックアップの設定

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

**症状**: "No secrets found" エラー、環境変数が未設定と表示される

**原因と解決方法**:

1. **Railway Variables の設定確認**:
   - [Railway](https://railway.app) → プロジェクト → "Variables" タブ
   - `SUPABASE_URL` と `SUPABASE_KEY` が表示されているか確認
   - 変数名にタイポがないか確認（大文字小文字も正確に）

2. **変数値の確認**:
   - 値に余分なスペース、改行、引用符が含まれていないか確認
   - Supabase URL形式: `https://xxxxx.supabase.co`
   - Supabase Key形式: `eyJhbGciOiJIUzI1NiI...` (長い文字列)

3. **デプロイの確認**:
   - 環境変数を保存した後、自動デプロイが開始されたか確認
   - "Deployments" タブで最新のデプロイが成功しているか確認

4. **手動再デプロイ**:
   - 自動デプロイされない場合、手動で "Redeploy" を実行
   - ビルドログで環境変数が正しく読み込まれているか確認

5. **アプリケーションログの確認**:
   - "View Logs" でアプリケーションの起動ログを確認
   - 環境変数の値が正しく表示されているか確認

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
