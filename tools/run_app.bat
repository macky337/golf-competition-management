@echo off
:: filepath: c:\Users\user\Documents\GitHub\golf-competition-management\run_app.bat
:: 88会ゴルフコンペ管理システム起動バッチファイル

echo 88会ゴルフコンペ管理システムを起動します...
echo.

:: 仮想環境が存在するか確認
if not exist venv (
    echo 仮想環境が見つかりません。setup_venv.ps1を実行してください。
    exit /b 1
)

:: 仮想環境をアクティベート
call venv\Scripts\activate.bat

:: アクティベートに成功したか確認
if not defined VIRTUAL_ENV (
    echo 仮想環境のアクティベートに失敗しました。
    exit /b 1
)

:: アプリケーション起動
echo アプリケーションを起動しています...
streamlit run app.py

:: 終了時に仮想環境を非アクティベート
call deactivate