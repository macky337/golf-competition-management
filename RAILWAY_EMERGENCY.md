# Railway緊急対応手順

## 現在の状況
- Dockerfileは修正済みで固定ポート8080を使用するように設定
- すべての変更はGitにコミット・プッシュ済み
- しかし、Railwayでまだポートエラーが発生している可能性

## 緊急対応手順

### 1. 即座に試す方法

#### A. 新しいビルドを強制実行
Railwayダッシュボードで：
1. Settings → General → Deployment triggers
2. "Redeploy" ボタンをクリック
3. または、Settings → Source → Repository で "Deploy Latest" をクリック

#### B. 代替Dockerfileを使用
もし通常のDockerfileで問題が続く場合：

```bash
# リポジトリ内でDockerfileを一時的に置き換え
mv Dockerfile Dockerfile.backup
mv Dockerfile.emergency Dockerfile
git add . && git commit -m "Emergency: Use alternative Dockerfile" && git push
```

### 2. 環境変数の再設定

Railwayダッシュボードで環境変数を完全にリセット：

1. **既存の環境変数を削除**
   - SUPABASE_URL を削除
   - SUPABASE_KEY を削除

2. **新しく設定し直す**
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   ```

3. **デプロイをトリガー**
   - "Deploy Latest" または手動デプロイ

### 3. ログ確認ポイント

Railwayのログで以下を確認：

#### 成功ケース
```
✓ Building with Dockerfile
✓ Setting PORT to 8080
✓ Streamlit starting on port 8080
✓ Server is running on 0.0.0.0:8080
```

#### 失敗ケース
```
✗ Invalid value for '--server.port': '$PORT' is not a valid integer
✗ ModuleNotFoundError
✗ Address already in use
```

### 4. 診断スクリプトの実行

以下のスクリプトでRailway環境を診断可能：

```bash
# 基本診断
python3 final_check.py

# 緊急起動テスト
python3 emergency_start.py
```

### 5. 最終手段

すべてが失敗した場合：

1. **新しいRailwayプロジェクトを作成**
   - 既存プロジェクトを削除
   - 新規作成してGitリポジトリを接続

2. **環境変数を最初から設定**
   - SUPABASE_URL
   - SUPABASE_KEY

3. **Dockerfile.emergency を使用**
   ```bash
   mv Dockerfile.emergency Dockerfile
   git add . && git commit -m "Use emergency Dockerfile" && git push
   ```

## 現在のファイル状況

- ✅ `Dockerfile` - 固定ポート8080使用
- ✅ `Dockerfile.emergency` - 緊急対応版
- ✅ `emergency_start.py` - 環境変数に依存しない起動スクリプト
- ✅ `final_check.py` - 最終診断スクリプト
- ✅ すべての変更がGitにコミット済み

## 次のステップ

1. Railwayで新しいビルドが開始されるのを待つ
2. ログでポートエラーが解決されているか確認
3. 必要に応じて環境変数を再設定
4. 最終的にアプリが正常に動作することを確認
