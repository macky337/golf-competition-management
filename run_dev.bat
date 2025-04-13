@echo off
echo 88会ゴルフコンペ管理システム（開発環境）を起動します...
echo.

:: 仮想環境の名前を確認
set VENV_NAME=venv
if exist .venv (
    set VENV_NAME=.venv
)

:: 仮想環境が存在するか確認
if not exist %VENV_NAME% (
    echo 仮想環境が見つかりません。仮想環境を作成します。
    python -m venv %VENV_NAME%
    if errorlevel 1 (
        echo 仮想環境の作成に失敗しました。
        exit /b 1
    )
    echo 仮想環境を作成しました。必要なパッケージをインストールします。
    call %VENV_NAME%\Scripts\activate.bat
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo パッケージのインストールに失敗しました。
        call deactivate
        exit /b 1
    )
) else (
    echo 既存の仮想環境 %VENV_NAME% を使用します。
)

:: 仮想環境をアクティベート
call %VENV_NAME%\Scripts\activate.bat

:: アクティベートに成功したか確認
if not defined VIRTUAL_ENV (
    echo 仮想環境のアクティベートに失敗しました。
    exit /b 1
)

:: バージョン情報を更新
echo バージョン情報を自動更新中...

:: アプリケーション起動
echo アプリケーションを起動しています...
streamlit run app/app.py

:: 終了時に仮想環境を非アクティベート
call deactivate
