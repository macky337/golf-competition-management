# 88会ゴルフコンペ管理システム（開発環境）起動スクリプト
Write-Host "88会ゴルフコンペ管理システム（開発環境）を起動します..." -ForegroundColor Cyan
Write-Host ""

# 仮想環境の名前を確認
$venvName = "venv"
if (Test-Path ".venv") {
    $venvName = ".venv"
    Write-Host "既存の仮想環境 .venv を使用します。" -ForegroundColor Green
}
elseif (Test-Path "venv") {
    Write-Host "既存の仮想環境 venv を使用します。" -ForegroundColor Green
}
else {
    Write-Host "仮想環境が見つかりません。仮想環境を作成します。" -ForegroundColor Yellow
    python -m venv $venvName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "仮想環境の作成に失敗しました。" -ForegroundColor Red
        exit 1
    }
    Write-Host "仮想環境を作成しました。必要なパッケージをインストールします。" -ForegroundColor Green
    
    # 仮想環境をアクティベート
    & "$venvName\Scripts\Activate.ps1"
    
    # 依存関係をインストール
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "パッケージのインストールに失敗しました。" -ForegroundColor Red
        deactivate
        exit 1
    }
}

# 仮想環境をアクティベート
try {
    & "$venvName\Scripts\Activate.ps1"
}
catch {
    Write-Host "仮想環境のアクティベートに失敗しました。" -ForegroundColor Red
    Write-Host "エラー: $_" -ForegroundColor Red
    exit 1
}

<<<<<<< HEAD
=======
# バージョン情報を自動更新
Write-Host "バージョン情報を自動更新中..." -ForegroundColor Cyan

>>>>>>> feature-branch
# アプリケーション起動
Write-Host "アプリケーションを起動しています..." -ForegroundColor Cyan
streamlit run app/app.py

# スクリプト終了時に自動的に仮想環境が非アクティベートされます