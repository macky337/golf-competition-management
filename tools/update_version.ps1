# エンコーディングをUTF-8に設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$OutputEncoding = [System.Text.Encoding]::UTF8

# デバッグ出力
Write-Host "スクリプトを実行しています..."
Write-Host "現在の作業ディレクトリ: $(Get-Location)"

try {
    # コミット数を取得
    $commitCount = (git rev-list --count HEAD)
    Write-Host "コミット数: $commitCount"

    # バージョン番号の設定
    $major = 1
    $minor = 0
    $patch = $commitCount

    # 新しいバージョン番号
    $newVersion = "$major.$minor.$patch"
    Write-Host "新しいバージョン番号: $newVersion"

    # app.py のパス
    $appPath = "app\app.py"
    Write-Host "ファイルパス: $appPath"
    Write-Host "ファイルが存在するか確認: $(Test-Path $appPath)"

    # ファイルの内容を取得
    if (Test-Path $appPath) {
        $content = Get-Content -Path $appPath -Raw -Encoding UTF8
        Write-Host "ファイル内容のサイズ: $($content.Length) 文字"

        # 現在のバージョンを取得（シンプルな正規表現パターン）
        if ($content -match 'APP_VERSION = "([0-9\.]+)"') {
            $currentVersion = $Matches[1]
            Write-Host "現在のバージョン: $currentVersion"
            
            # バージョン番号を更新（シンプルな置換パターン）
            $updatedContent = $content -replace 'APP_VERSION = "[0-9\.]+"', ('APP_VERSION = "' + $newVersion + '"')
            Set-Content -Path $appPath -Value $updatedContent -Encoding UTF8
            Write-Host "ファイルを更新しました"

            # 成功メッセージを表示
            Write-Host "========================================================"
            Write-Host "バージョンを $currentVersion から $newVersion に更新しました" -ForegroundColor Green
            Write-Host "========================================================"

            # 変更をステージングに追加
            git add $appPath
            Write-Host "app.pyをgitステージングエリアに追加しました"
        } else {
            Write-Host "バージョン情報が見つかりませんでした。正規表現: 'APP_VERSION = \"([0-9\.]+)\"'"
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