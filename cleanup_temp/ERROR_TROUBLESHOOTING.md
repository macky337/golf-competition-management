# Railway環境変数設定後のエラー対処ガイド

## 🚨 よくあるエラーパターンと解決方法

### 1. 環境変数設定エラー

#### エラー例：
```
❌ SUPABASE_URL: 未設定
❌ SUPABASE_KEY: 未設定
```

#### 対処法：
1. **Railway Dashboard確認**
   - Variables タブに `SUPABASE_URL` と `SUPABASE_KEY` が表示されているか
   - 値が正しく入力されているか（スペースや改行なし）

2. **再デプロイの実行**
   ```
   Railway Dashboard → Deployments → "Redeploy"
   ```

### 2. Supabase接続エラー

#### エラー例：
```
❌ Supabase接続失敗: 401
❌ Supabase接続失敗: 404
```

#### 対処法：
1. **Supabase設定確認**
   - URLが正しいか（https://で始まり.supabase.coで終わる）
   - APIキーが anon/public key か（service_role key ではない）

2. **Supabaseプロジェクト状態確認**
   - プロジェクトが一時停止されていないか
   - APIアクセスが有効か

### 3. Dockerビルドエラー

#### エラー例：
```
Build failed
Container failed to start
```

#### 対処法：
1. **requirements.txt確認**
   - 依存関係が正しく記載されているか
   - 互換性のないパッケージがないか

2. **Dockerfile確認**
   - 構文エラーがないか
   - ファイルパスが正しいか

### 4. Streamlit起動エラー

#### エラー例：
```
ModuleNotFoundError
ImportError
```

#### 対処法：
1. **依存関係インストール確認**
   ```
   pip install streamlit
   pip install supabase
   pip install requests
   ```

2. **パス設定確認**
   - PYTHONPATH が正しく設定されているか
   - アプリファイルが存在するか

### 5. 環境変数フォーマットエラー

#### よくある間違い：
```
❌ SUPABASE_URL = "https://abc.supabase.co"  # 引用符不要
✅ SUPABASE_URL = https://abc.supabase.co

❌ SUPABASE_KEY =  eyJhbG...  # 先頭スペース
✅ SUPABASE_KEY = eyJhbG...
```

### 6. Railway固有の問題

#### 対処法：
1. **ログ確認**
   ```
   Railway Dashboard → Deployments → View Logs
   ```

2. **手動再デプロイ**
   ```
   Railway Dashboard → Deployments → Redeploy
   ```

3. **環境変数再設定**
   - 既存の変数を削除
   - 新しく追加し直す

## 🔧 緊急デバッグ手順

### ステップ1: エラーログの取得
1. Railway Dashboard → Deployments
2. 最新のデプロイをクリック
3. "View Logs" でエラー詳細を確認

### ステップ2: 環境変数の再確認
1. Railway Dashboard → Variables
2. `SUPABASE_URL` と `SUPABASE_KEY` の存在確認
3. 値の正確性確認（コピー&ペースト推奨）

### ステップ3: Supabase側の確認
1. Supabase Dashboard → Settings → API
2. Project URL をコピー
3. anon public key をコピー
4. Railway Variables に正確に設定

### ステップ4: 手動再デプロイ
1. Railway Dashboard → Deployments
2. "Redeploy" ボタンをクリック
3. ビルドログとデプロイログを監視

## 📋 確認チェックリスト

### Railway Variables
- [ ] SUPABASE_URL が設定されている
- [ ] SUPABASE_KEY が設定されている
- [ ] 値に余分なスペース・改行がない
- [ ] 引用符で囲まれていない

### Supabase設定
- [ ] プロジェクトが稼働中
- [ ] Project URL が正しい
- [ ] anon public key を使用（service_role ではない）
- [ ] APIアクセスが有効

### デプロイ状況
- [ ] 最新のコミットがデプロイされている
- [ ] ビルドが成功している
- [ ] コンテナが正常起動している
- [ ] ログにエラーがない

## 🆘 さらなるサポートが必要な場合

具体的なエラーメッセージを教えてください：
1. Railway デプロイログのエラー内容
2. アプリケーション画面の表示内容
3. ブラウザコンソールのエラー（あれば）

これらの情報を基に、より具体的な解決策を提案します。
