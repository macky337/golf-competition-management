# 実行方法

GitコマンドをターミナルやGitクライアントで実行する手順をご説明します。

## ターミナルでの実行方法

### [terminal_commands.sh](file:///c%3A/Users/user/Documents/GitHub/golf-competition-management/terminal_commands.sh)

ファイルに記載されたコマンドを実行するには、以下の手順に従ってください。

# 1. 変更をステージングエリアに追加
git add .

# 2. 変更をコミット
git commit -m "アプリケーションの更新"

# 3. リモートの最新変更を取得
git fetch origin

# 4. ローカルのmainブランチに切り替え（現在別のブランチにいる場合）
git checkout main

# 5. リモートの変更を取り込む
git pull origin main

# 6. コンフリクトが発生した場合は解決する
# (コンフリクトがある場合、エディタで解決した後に git add . を実行)

# 7. リモートのmainブランチに変更をプッシュ
git push origin main
