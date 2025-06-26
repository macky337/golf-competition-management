# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム (Supabase版)

このスクリプトは、88会ゴルフコンペのスコアを管理するためのStreamlitアプリケーションです。
ユーザーはスコアデータを閲覧し、データの分析や可視化を行うことができます。
また、管理者はデータベースのバックアップおよびリストアを行うことができます。

機能:
- ユーザー認証
- スコアデータの取得と表示
- データの分析と可視化
- 優勝回数ランキングの表示
- データベースのバックアップとリストア

使用方法:
1. Streamlitをインストールします。
2. このスクリプトを実行します `streamlit run app.py`
3. ブラウザで表示されるアプリケーションにアクセスします。

"""

# Railway環境での初期化処理
import os

# Railway環境の検出と設定
if os.getenv('RAILWAY_ENVIRONMENT_NAME'):
    # Railway環境でのStreamlit設定ディレクトリを作成
    streamlit_dir = '/app/.streamlit'
    if not os.path.exists(streamlit_dir):
        os.makedirs(streamlit_dir, exist_ok=True)
    
    # 環境変数でStreamlit設定ディレクトリを指定
    os.environ['STREAMLIT_CONFIG_DIR'] = streamlit_dir

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
# japanize_matplotlibの代わりに直接日本語フォントを設定
import matplotlib
matplotlib.rcParams['font.family'] = 'MS Gothic'  # Windowsの場合
# Linux/Macの場合は以下のいずれかを使用
# matplotlib.rcParams['font.family'] = 'IPAGothic'
# matplotlib.rcParams['font.family'] = 'Noto Sans CJK JP'
from datetime import datetime
import pytz
import json
from supabase import create_client
from dotenv import load_dotenv
import subprocess
import warnings
import logging
import japanize_matplotlib
import re

import matplotlib
import platform

# 実行環境に応じてフォントを設定
if platform.system() == 'Windows':
    matplotlib.rcParams['font.family'] = 'MS Gothic'
elif platform.system() == 'Darwin':  # Macの場合
    matplotlib.rcParams['font.family'] = 'Hiragino Maru Gothic Pro'
else:  # Linux（Streamlit Cloud含む）
    matplotlib.rcParams['font.family'] = 'IPAexGothic'  # あるいは 'Noto Sans CJK JP'

# 警告メッセージを非表示にする
warnings.filterwarnings('ignore')
# ログレベルを設定してmatplotlibの警告を抑制
logging.getLogger('matplotlib').setLevel(logging.ERROR)

# Gitからバージョン情報を取得する関数
def get_git_revision():
    """現在のGitリビジョン（コミットハッシュ）を取得する"""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "dev"  # Git情報が取得できない場合

def get_git_count():
    """Gitのコミット数を取得する"""
    try:
        return subprocess.check_output(['git', 'rev-list', '--count', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "0"  # Git情報が取得できない場合

def get_git_date():
    """最新コミットの日付を取得する"""
    try:
        return subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short']).decode('ascii').strip()
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')  # Git情報が取得できない場合は現在日付

def get_git_latest_commit_message():
    """最新のコミットメッセージを取得する"""
    try:
        return subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip()
    except Exception:
        return ""  # Git情報が取得できない場合は空文字列

def parse_version_from_commit_history():
    """コミット履歴を解析し、適切なバージョン番号を計算する"""
    # バージョン番号の初期値
    major = 1
    minor = 0
    patch = 0
    
    try:
        # まず最新のコミットメッセージを取得
        latest_commit_message = get_git_latest_commit_message()
        
        # コミットメッセージに基づいてバージョンタイプを判断
        if re.search(r'^(major:|MAJOR:|!:)', latest_commit_message):
            # メジャーバージョンアップ
            major += 1
            minor = 0
            patch = 0
        elif re.search(r'^(feature:|feat:|FEATURE:)', latest_commit_message):
            # マイナーバージョンアップ
            minor += 1
            patch = 0
        elif re.search(r'^(fix:|bugfix:|FIX:)', latest_commit_message):
            # パッチバージョンアップ
            patch += 1
        else:
            # 特に指定がない場合はパッチバージョン
            patch = int(get_git_count())
            
        return f"{major}.{minor}.{patch}"
    except Exception:
        # デフォルトバージョン
        return "1.0.7"

def get_app_version():
    """アプリのバージョンを動的に取得する"""
    try:
        # コミット履歴に基づいてバージョン番号を解析
        return parse_version_from_commit_history()
    except Exception:
        return "1.0.7"  # デフォルトバージョン

def get_app_last_update():
    """アプリの最終更新日を動的に取得する"""
    try:
        return get_git_date()
    except Exception:
        return datetime.now().strftime('%Y-%m-%d')  # 現在の日付

# バージョン情報を動的に設定
APP_VERSION = get_app_version()
APP_LAST_UPDATE = get_app_last_update()

# ページ最上部に追加（st.titleの前）
st.markdown("""
<style>
    .footer-container {
        position: fixed;
        bottom: 0;
        right: 0;
        left: 0;
        padding: 10px;
        background-color: rgba(255, 255, 255, 0.8);
        border-top: 1px solid #ddd;
        z-index: 999;
    }
    .footer-text {
        font-size: 0.8rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# 環境変数の読み込み
load_dotenv()

# Supabase接続情報 - 環境変数を優先し、Streamlit secretsもサポート
# Railway環境では環境変数が優先される
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# 環境変数が設定されていない場合、Streamlit secretsを試す
if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        SUPABASE_URL = st.secrets.get("supabase", {}).get("url", "") or SUPABASE_URL
        SUPABASE_KEY = st.secrets.get("supabase", {}).get("key", "") or SUPABASE_KEY
    except Exception:
        pass

# 接続情報が不足している場合の対応
if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("""
    🔴 Supabase接続情報が見つかりません。
    
    **デプロイ環境別の設定方法:**
    
    📦 **Railway**: 
    プロジェクト設定の Variables タブで以下の環境変数を設定:
    - SUPABASE_URL = あなたのSupabaseのURL
    - SUPABASE_KEY = あなたのSupabaseのAPIキー
    
    ☁️ **Streamlit Cloud**: 
    .streamlit/secrets.toml ファイルまたは設定画面で以下を設定:
    [supabase]
    url = "あなたのSupabaseのURL"
    key = "あなたのSupabaseのAPIキー"
    
    💻 **ローカル開発**: 
    プロジェクトルートに .env ファイルを作成し、以下を設定:
    SUPABASE_URL=あなたのSupabaseのURL
    SUPABASE_KEY=あなたのSupabaseのAPIキー
    
    **接続情報の取得方法:**
    1. Supabase でプロジェクトを開く
    2. Settings > API から URL と anon/public key をコピー
    """)
    
    # Railway環境でのデバッグ情報を表示
    if os.getenv('RAILWAY_ENVIRONMENT_NAME'):
        st.info("🚂 Railway環境で実行中")
        with st.expander("🔍 デバッグ情報"):
            st.write("**環境変数:**")
            st.write(f"- RAILWAY_ENVIRONMENT_NAME: {os.getenv('RAILWAY_ENVIRONMENT_NAME', 'Not Set')}")
            st.write(f"- PORT: {os.getenv('PORT', 'Not Set')}")
            st.write(f"- SUPABASE_URL: {'設定済み' if os.getenv('SUPABASE_URL') else '未設定'}")
            st.write(f"- SUPABASE_KEY: {'設定済み' if os.getenv('SUPABASE_KEY') else '未設定'}")
            
            st.write("**ファイルシステム:**")
            st.write(f"- 現在のディレクトリ: {os.getcwd()}")
            st.write(f"- アプリディレクトリ存在: {os.path.exists('/app')}")
            st.write(f"- .streamlitディレクトリ存在: {os.path.exists('/app/.streamlit')}")
            
            if os.path.exists('/app/.streamlit'):
                st.write("- .streamlitディレクトリの内容:")
                try:
                    files = os.listdir('/app/.streamlit')
                    for file in files:
                        st.write(f"  - {file}")
                except Exception as e:
                    st.write(f"  - エラー: {e}")
    
    # アプリケーションを停止（環境変数が設定されていない場合）
    st.stop()




