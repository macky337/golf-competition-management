# Railway環境テスト用設定ファイル

## 現在の問題
- ✅ Dockerビルド成功
- ✅ アプリケーション起動成功 
- ❌ 環境変数（SUPABASE_URL, SUPABASE_KEY）が認識されない

## 確認すべき項目

### Railway Dashboard確認事項
1. **Variables タブ**
   - [ ] SUPABASE_URL が設定されている
   - [ ] SUPABASE_KEY が設定されている
   - [ ] 値に余分なスペースや改行が含まれていない
   - [ ] 値が空文字列でない

2. **Settings タブ**
   - [ ] Environment が production になっている
   - [ ] Build Command が自動で設定されている
   - [ ] Start Command が空（Dockerfileで指定）

3. **Deployments タブ**
   - [ ] 最新のデプロイが Success になっている
   - [ ] ビルドログにエラーがない
   - [ ] 環境変数設定後に再デプロイされている

### デバッグ手順
1. **まず簡単な確認**
   ```bash
   # Railwayのログで以下が表示されるか確認
   "✅ SUPABASE_URL: 設定済み" または "❌ SUPABASE_URL: 未設定"
   ```

2. **詳細診断の確認**
   - Railway診断レポートの内容を確認
   - 特に「Supabase環境変数詳細」セクション

3. **考えられる原因**
   - Railway Variables設定の問題
   - 環境変数名のタイプミス
   - Docker環境での変数の伝播問題
   - Railway deployment環境の問題

### よくある解決方法
1. **Railway Variables再設定**
   - 既存の変数を削除
   - 新しく変数を追加
   - 手動で再デプロイ

2. **値の確認**
   - SUPABASE_URL: https://で始まっているか
   - SUPABASE_KEY: ey で始まっているか
   - 改行やスペースが含まれていないか

3. **デプロイ確認**
   - 変数設定後に確実に再デプロイされているか
   - キャッシュをクリアして再デプロイ
