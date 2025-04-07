@echo off
chcp 65001 > nul
:: 指定されたコミットハッシュの状態にリポジトリを戻すバッチファイル

echo 88会ゴルフコンペ管理システム - 復元ツール
echo --------------------------------------
echo.

set COMMIT_HASH=0e600ab

:: 現在の変更を確認
git status
echo.
echo 未コミットの変更があります。これらの変更を保存しますか？
choice /C YN /M "変更を保存しますか (Y/N)？"

if errorlevel 2 goto SKIP_COMMIT
if errorlevel 1 goto COMMIT_CHANGES

:COMMIT_CHANGES
echo.
echo 現在の変更を保存しています...
git add .
git commit -m "復元前の変更を自動保存 (%date% %time%)"
echo 変更が保存されました。
goto RESTORE

:SKIP_COMMIT
echo.
echo 変更を保存せずに続行します。

:RESTORE
echo.
echo コミット %COMMIT_HASH% の状態に戻しています...
git checkout %COMMIT_HASH%

if errorlevel 1 (
    echo エラーが発生しました。復元に失敗しました。
    exit /b 1
) else (
    echo.
    echo コミット %COMMIT_HASH% の状態に正常に復元されました。
    
    echo.
    echo 【注意】現在 "detached HEAD" 状態です。
    echo この状態では変更を行うと、ブランチに戻る際に変更が失われる可能性があります。
    echo.
    echo 以下のオプションから選択してください:
    echo.
    echo [1] 新しいブランチを作成して作業を続ける (推奨)
    echo [2] 元のブランチ(main)に戻る
    echo [3] 現在の状態のまま作業を続ける
    echo.
    
    choice /C 123 /M "オプションを選択してください (1-3)："
    
    if errorlevel 3 goto CONTINUE_DETACHED
    if errorlevel 2 goto RETURN_MAIN
    if errorlevel 1 goto CREATE_BRANCH
    
    :CREATE_BRANCH
    echo.
    set /p BRANCH_NAME=新しいブランチ名を入力してください: 
    git checkout -b %BRANCH_NAME%
    echo ブランチ '%BRANCH_NAME%' を作成し、切り替えました。
    goto END
    
    :RETURN_MAIN
    echo.
    echo mainブランチに戻ります...
    git checkout main
    echo mainブランチに戻りました。
    goto END
    
    :CONTINUE_DETACHED
    echo.
    echo detached HEAD状態で作業を続けます。
    echo 注意: 変更を行った場合は、後でコミットしてブランチを作成することをお勧めします。
)

:END
echo.
echo 操作が完了しました。
pause
