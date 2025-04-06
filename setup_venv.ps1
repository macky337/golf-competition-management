# 仮想環境のセットアップと有効化のためのPowerShellスクリプト

Write-Host "88会ゴルフコンペ管理システム - 環境セットアップツール" -ForegroundColor Cyan
Write-Host "------------------------------------------------" -ForegroundColor Cyan

# 現在の実行ポリシーを確認
$currentPolicy = Get-ExecutionPolicy
Write-Host "現在の実行ポリシー: $currentPolicy" -ForegroundColor Yellow

# 仮想環境が存在するか確認
if (-not (Test-Path -Path ".\venv")) {
    Write-Host "仮想環境が見つかりません。新しい仮想環境を作成します..." -ForegroundColor Yellow
    
    # Python が利用可能か確認
    try {
        $pythonVersion = python --version
        Write-Host "Python検出: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "Pythonが見つかりません。Pythonをインストールしてください。" -ForegroundColor Red
        exit 1
    }
    
    # venv モジュールを使用して仮想環境を作成
    Write-Host "venvを作成中..." -ForegroundColor Cyan
    python -m venv venv
    
    if (-not (Test-Path -Path ".\venv")) {
        Write-Host "仮想環境の作成に失敗しました。" -ForegroundColor Red
        exit 1
    }
}

# Activate.ps1スクリプトのパスを確認
$activateScript = ".\venv\Scripts\Activate.ps1"
if (-not (Test-Path -Path $activateScript)) {
    Write-Host "警告: $activateScript が見つかりません。" -ForegroundColor Red
    
    # 代替方法：Activateスクリプトを直接呼び出す
    $activateCmd = ".\venv\Scripts\activate.bat"
    if (Test-Path -Path $activateCmd) {
        Write-Host "代替方法: $activateCmd を使用します" -ForegroundColor Yellow
        cmd /c $activateCmd
        
        # 環境変数を確認
        if ($env:VIRTUAL_ENV) {
            Write-Host "仮想環境がアクティベートされました: $env:VIRTUAL_ENV" -ForegroundColor Green
        } else {
            Write-Host "仮想環境のアクティベートに失敗しました。" -ForegroundColor Red
        }
    } else {
        Write-Host "仮想環境のアクティベートスクリプトが見つかりません。" -ForegroundColor Red
        exit 1
    }
} else {
    # 仮想環境をアクティベート
    Write-Host "仮想環境をアクティベート中: $activateScript" -ForegroundColor Green
    try {
        & $activateScript
        Write-Host "仮想環境がアクティベートされました！" -ForegroundColor Green
    } catch {
        Write-Host "仮想環境のアクティベートに失敗しました: $_" -ForegroundColor Red
        exit 1
    }
}

# 必要なパッケージのインストール
if (Test-Path -Path ".\requirements.txt") {
    Write-Host "requirements.txt からパッケージをインストール中..." -ForegroundColor Cyan
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "パッケージのインストールに問題が発生しました。" -ForegroundColor Red
    } else {
        Write-Host "必要なパッケージがインストールされました。" -ForegroundColor Green
    }
} else {
    Write-Host "requirements.txt が見つかりません。パッケージは手動でインストールする必要があります。" -ForegroundColor Yellow
}

Write-Host "`nセットアップが完了しました！" -ForegroundColor Green
Write-Host "以下のコマンドでアプリを起動できます：" -ForegroundColor Cyan
Write-Host "streamlit run app.py" -ForegroundColor White -BackgroundColor DarkGreen
Write-Host "`n"
