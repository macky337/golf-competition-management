@echo off
echo 88会ゴルフコンペ・スコア管理システム - アプリケーション起動
echo =============================================

REM 現在のディレクトリをバッチファイルの場所に設定
cd /d %~dp0

REM 仮想環境を有効化
if exist .venv\Scripts\activate.bat (
    echo 仮想環境を有効化しています...
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    echo 仮想環境を有効化しています...
    call venv\Scripts\activate.bat
) else (
    echo 警告: 仮想環境が見つかりません。
    echo 最初に setup_env.bat を実行してください。
    pause
    exit /b 1
)

REM .streamlitディレクトリがなければ作成
if not exist .streamlit (
    mkdir .streamlit
    echo .streamlitディレクトリを作成しました。
)

REM secrets.tomlがなければサンプルを作成
if not exist .streamlit\secrets.toml (
    echo [supabase] > .streamlit\secrets.toml
    echo url = "あなたのSupabaseのURL" >> .streamlit\secrets.toml
    echo key = "あなたのSupabaseのAPIキー" >> .streamlit\secrets.toml
    echo .streamlit\secrets.toml を作成しました。実際の接続情報で更新してください。
)

<<<<<<< HEAD
=======
REM バージョン情報を更新
echo バージョン情報を更新中...
call .\venv\Scripts\activate.bat

>>>>>>> feature-branch
REM アプリケーションを起動
echo アプリケーションを起動しています...
streamlit run app\app.py

pause