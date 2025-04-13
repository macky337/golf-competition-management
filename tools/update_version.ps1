# エンコーディングをUTF-8に設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$OutputEncoding = [System.Text.Encoding]::UTF8

# デバッグ出力
Write-Host "バージョン自動更新スクリプトを実行しています..."
Write-Host "現在の作業ディレクトリ: $(Get-Location)"

# 日付と時刻の取得
$currentDate = Get-Date -Format "yyyy-MM-dd"
$currentDateTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

try {
    # コミット数を取得
    $commitCount = (git rev-list --count HEAD)
    Write-Host "コミット数: $commitCount"

    # 最新のコミットメッセージを取得
    $latestCommitMessage = (git log -1 --pretty=%B)
    Write-Host "最新のコミットメッセージ: $latestCommitMessage"
    
    # 現在のブランチ名を取得
    $currentBranch = (git rev-parse --abbrev-ref HEAD)
    Write-Host "現在のブランチ: $currentBranch"

    # 現在のバージョン番号を取得するためのファイルパス
    $appPath = "app\app.py"
    $changelogPath = "CHANGELOG.md"

    # 現在のバージョン番号を取得
    $currentVersion = "1.0.0"  # デフォルト値
    if (Test-Path $appPath) {
        $content = Get-Content -Path $appPath -Raw -Encoding UTF8
        if ($content -match 'APP_VERSION = "([0-9\.]+)"') {
            $currentVersion = $matches[1]
            Write-Host "現在のバージョン: $currentVersion"
        }
    }

    # 現在のバージョン番号をパースする
    $versionParts = $currentVersion.Split('.')
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    $patch = [int]$versionParts[2]

    # 変更タイプの判別 (メジャー、マイナー、パッチ)
    $changeType = "patch" # デフォルトはパッチ更新
    $commitMessageFirstLine = ($latestCommitMessage -split "`n")[0].Trim()
    
    # コミットメッセージに基づいてバージョンを更新
    if ($latestCommitMessage -match '^major:' -or $latestCommitMessage -match '^MAJOR:' -or 
        $latestCommitMessage -match '!:') {
        # メジャーバージョンを増加、マイナーとパッチをリセット
        $major += 1
        $minor = 0
        $patch = 0
        $changeType = "major"
        Write-Host "メジャーバージョンを増加します"
    } elseif ($latestCommitMessage -match '^feature:' -or $latestCommitMessage -match '^FEATURE:' -or 
              $latestCommitMessage -match '^feat:' -or $latestCommitMessage -match '^FEAT:' -or
              $latestCommitMessage -match '\bfeat\(' -or $latestCommitMessage -match '\bfeature\(') {
        # マイナーバージョンを増加、パッチをリセット
        $minor += 1
        $patch = 0
        $changeType = "minor"
        Write-Host "マイナーバージョンを増加します"
    } elseif ($latestCommitMessage -match '^fix:' -or $latestCommitMessage -match '^FIX:' -or 
              $latestCommitMessage -match '^bugfix:' -or $latestCommitMessage -match '^BUGFIX:' -or
              $latestCommitMessage -match '\bfix\(' -or $latestCommitMessage -match '\bbugfix\(') {
        # パッチバージョンのみを増加
        $patch += 1
        Write-Host "パッチバージョンを増加します"
    } else {
        # デフォルトではパッチバージョンを増加
        $patch += 1
        Write-Host "デフォルト: パッチバージョンを増加します"
    }

    # 新しいバージョン番号
    $newVersion = "$major.$minor.$patch"
    Write-Host "新しいバージョン番号: $newVersion"

    # app.py のパス
    Write-Host "ファイルパス: $appPath"
    Write-Host "ファイルが存在するか確認: $(Test-Path $appPath)"

    # ファイルの内容を取得
    if (Test-Path $appPath) {
        $content = Get-Content -Path $appPath -Raw -Encoding UTF8
        Write-Host "ファイル内容のサイズ: $($content.Length) 文字"

        # 現在のバージョンを取得（シンプルな正規表現パターン）
        if ($content -match 'APP_VERSION = "([0-9\.]+)"') {
            $currentVersion = $matches[1]
            Write-Host "現在のバージョン: $currentVersion"
            
            # バージョン番号を更新（シンプルな置換パターン）
            $updatedContent = $content -replace 'APP_VERSION = "[0-9\.]+"', ('APP_VERSION = "' + $newVersion + '"')
            Set-Content -Path $appPath -Value $updatedContent -Encoding UTF8
            Write-Host "ファイルを更新しました"
            
            # CHANGELOG.md の更新
            if (Test-Path $changelogPath) {
                # 変更内容のサマリーを作成
                $changelogSummary = "- $commitMessageFirstLine"
                
                # 変更タイプに応じたヘッダーを作成
                $changelogHeader = ""
                switch ($changeType) {
                    "major" { $changelogHeader = "### 破壊的変更 (Breaking Changes)" }
                    "minor" { $changelogHeader = "### 機能追加 (Features)" }
                    "patch" { $changelogHeader = "### バグ修正 (Bug Fixes)" }
                }
                
                # 既存のCHANGELOGを読み込む
                $changelog = Get-Content -Path $changelogPath -Raw -Encoding UTF8
                
                # 新しいバージョンエントリを作成
                $newEntry = "## [$newVersion] - $currentDate`n`n$changelogHeader`n$changelogSummary`n`n"
                
                # CHANGELOGの先頭に新しいエントリを追加（ヘッダーの後）
                if ($changelog -match '# Changelog') {
                    $updatedChangelog = $changelog -replace '# Changelog', "# Changelog`n`n$newEntry"
                } else {
                    $updatedChangelog = "# Changelog`n`n$newEntry" + $changelog
                }
                
                # 更新したCHANGELOGを保存
                Set-Content -Path $changelogPath -Value $updatedChangelog -Encoding UTF8
                Write-Host "CHANGELOGを更新しました"
            } else {
                # CHANGELOGが存在しない場合は新規作成
                $changelogContent = @"
# Changelog

## [$newVersion] - $currentDate

### 変更内容
- $commitMessageFirstLine

"@
                Set-Content -Path $changelogPath -Value $changelogContent -Encoding UTF8
                Write-Host "CHANGELOGを新規作成しました"
            }

            # 成功メッセージを表示
            Write-Host "========================================================"
            Write-Host "バージョンを $currentVersion から $newVersion に更新しました" -ForegroundColor Green
            Write-Host "CHANGELOGも更新されました" -ForegroundColor Green
            Write-Host "========================================================"

            # 変更をステージングに追加
            git add $appPath
            git add $changelogPath
            Write-Host "変更されたファイルをgitステージングエリアに追加しました"
            
            # 自動コミットするかどうかを確認
            $autoCommit = $false
            if ($autoCommit) {
                git commit -m "chore: バージョンを $newVersion に更新 [自動コミット]"
                Write-Host "バージョン更新の変更をコミットしました" -ForegroundColor Green
            } else {
                Write-Host "以下のコマンドでバージョン更新の変更をコミットできます:" -ForegroundColor Yellow
                Write-Host "git commit -m ""chore: バージョンを $newVersion に更新""" -ForegroundColor Yellow
            }
        } else {
            Write-Host "バージョン情報が見つかりませんでした。正規表現: 'APP_VERSION = ""([0-9\.]+)""'"
            Write-Host "ファイルの先頭20行:"
            Get-Content -Path $appPath -TotalCount 20
        }
    } else {
        Write-Host "エラー: app.pyファイルが見つかりません" -ForegroundColor Red
    }
} catch {
    Write-Host "エラーが発生しました: $_" -ForegroundColor Red
    Write-Host "スタックトレース: $($_.ScriptStackTrace)" -ForegroundColor Red
}

# バージョン更新を自動化するための Git hook を設定する関数
function Setup-GitHooks {
    $hooksDir = ".git\hooks"
    $postCommitHook = "$hooksDir\post-commit"
    
    # hooksディレクトリが存在するか確認
    if (-not (Test-Path $hooksDir)) {
        Write-Host "Git hooksディレクトリが見つかりません。リポジトリのルートディレクトリで実行してください。" -ForegroundColor Red
        return
    }
    
    # post-commitフックを作成
    $hookContent = @"
#!/bin/sh
# バージョン自動更新のためのpost-commitフック
echo "コミット後のバージョン自動更新を実行中..."
powershell -ExecutionPolicy Bypass -File "tools\update_version.ps1"
"@
    
    Set-Content -Path $postCommitHook -Value $hookContent -Encoding UTF8
    
    # Linuxやmacでも実行可能にする
    if (Test-Path $postCommitHook) {
        if ($IsLinux -or $IsMacOS) {
            chmod +x $postCommitHook
        } else {
            # Windows環境では特に権限設定は必要ないが、念のため確認メッセージを出す
            Write-Host "post-commitフックを作成しました: $postCommitHook" -ForegroundColor Green
        }
        Write-Host "Git post-commitフックの設定が完了しました。これからのコミット後に自動的にバージョンが更新されます。" -ForegroundColor Green
    } else {
        Write-Host "Git hookの作成に失敗しました。" -ForegroundColor Red
    }
}

# 引数に --setup-hooks が指定されている場合はGit hooksを設定
if ($args -contains "--setup-hooks") {
    Setup-GitHooks
}