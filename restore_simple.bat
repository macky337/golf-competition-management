@echo off
chcp 65001 > nul
echo 特定のコミットに戻すシンプルツール
echo.

set COMMIT_HASH=0e600ab

git checkout %COMMIT_HASH%

echo.
echo 完了しました。新しいブランチを作成するには:
echo git checkout -b 新しいブランチ名
echo.
pause
