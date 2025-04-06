# 1. 変更をステージングしてコミット
git add .
git commit -m "アプリケーションの更新"

# 2. mainブランチに切り替え
git checkout main

# 3. リモートの最新変更を取得
git pull origin main

# 4. 作業ブランチの変更をmainにマージ（例：feature-branch を作業ブランチ名に置き換え）
git merge feature-branch

# 5. コンフリクトがあれば解決する
# (コンフリクトを解決したら git add . を実行)

# 6. マージが完了したらリモートにプッシュ
git push origin main
