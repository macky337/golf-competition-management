# Railway環境変数設定ガイド

## 🚨 現在の状況
- ✅ Railway環境認識: `production`
- ✅ プロジェクト認識: `earnest-vitality`
- ✅ サービス認識: `golf-competition-management`
- ❌ SUPABASE_URL: **完全に未設定**
- ❌ SUPABASE_KEY: **完全に未設定**

## 🔧 Railway環境変数設定手順（詳細版）

### ステップ1: Railway Dashboardにアクセス
1. [Railway Dashboard](https://railway.app/dashboard) を開く
2. プロジェクト `earnest-vitality` をクリック
3. サービス `golf-competition-management` を選択

### ステップ2: 環境変数設定画面を開く
1. **左メニューから "Variables" タブをクリック**
   - または "Settings" → "Environment" → "Variables"
2. 現在設定されている変数一覧を確認
3. **"New Variable" または "Add Variable" ボタンをクリック**

### ステップ3: SUPABASE_URL を設定
1. **Variable Name**: `SUPABASE_URL`（正確にタイプ）
2. **Value**: `https://your-project-ref.supabase.co`
   - Supabaseプロジェクトの正確なURLを入力
   - 例: `https://abcdefghijklmnop.supabase.co`
3. **"Add" または "Save" をクリック**

### ステップ4: SUPABASE_KEY を設定  
1. **Variable Name**: `SUPABASE_KEY`（正確にタイプ）
2. **Value**: `eyJhbGciOiJIUzI1NiI...`
   - Supabaseの anon/public key を入力
   - 通常150文字程度の長いキー
3. **"Add" または "Save" をクリック**

### ステップ5: 設定確認と再デプロイ
1. **Variables一覧で両方の変数が表示されることを確認**
2. **値が正しく設定されていることを確認**
3. **"Deploy" または自動再デプロイを待つ**

## 🔍 Supabase接続情報の取得方法

### Supabase Dashboard
1. [Supabase Dashboard](https://app.supabase.com) にログイン
2. 対象プロジェクトを選択
3. **Settings** → **API** をクリック
4. 以下の情報をコピー：

#### Project URL
```
https://your-project-ref.supabase.co
```
- これをそのまま `SUPABASE_URL` に設定

#### anon public key
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...
```
- これをそのまま `SUPABASE_KEY` に設定

## ⚠️ よくある設定ミス

1. **変数名のタイプミス**
   - ❌ `SUPABASE_url` 
   - ✅ `SUPABASE_URL`

2. **値の前後にスペース**
   - ❌ ` https://abc.supabase.co `
   - ✅ `https://abc.supabase.co`

3. **間違ったキーの使用**
   - ❌ service_role key（秘匿性が高い）
   - ✅ anon public key

4. **URLの不完全**
   - ❌ `abc.supabase.co`
   - ✅ `https://abc.supabase.co`

## 📋 設定完了チェックリスト

設定後、以下を確認してください：

- [ ] Railway Dashboard の Variables タブに `SUPABASE_URL` が表示される
- [ ] Railway Dashboard の Variables タブに `SUPABASE_KEY` が表示される  
- [ ] 値が正しく設定されている（プレビューで確認）
- [ ] 再デプロイが完了している
- [ ] アプリケーションログで「✅ SUPABASE_URL: 設定済み」と表示される

## 🚀 次のステップ

1. **上記手順に従ってRailway Dashboardで環境変数を設定**
2. **再デプロイを待つ（通常1-3分）**
3. **デプロイログで以下が表示されることを確認：**
   ```
   ✅ SUPABASE_URL: 設定済み (45 文字)
   ✅ SUPABASE_KEY: 設定済み (150 文字)
   ```

環境変数が正しく設定されれば、アプリケーションは正常にSupabaseに接続できるようになります。
