﻿# -*- coding: utf-8 -*-
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

# より確実な環境変数読み込み
import sys

# Railway環境での代替環境変数読み込み
def load_railway_env():
    """Railwayの複数の方法で環境変数を読み込む"""
    env_vars = {}
    
    # 複数のファイルパスを試行
    file_paths = [
        '/tmp/railway_env.txt',
        '/tmp/railway_env.json',
        'railway_env.txt',
        'railway_env.json'
    ]
    
    for env_file_path in file_paths:
        try:
            if os.path.exists(env_file_path):
                print(f"Railway環境ファイル発見: {env_file_path}")
                
                if env_file_path.endswith('.json'):
                    # JSON形式で読み込み
                    with open(env_file_path, 'r') as f:
                        data = json.load(f)
                        for key, value in data.items():
                            if value and value.strip():  # 空でない場合のみ設定
                                env_vars[key] = value.strip()
                                print(f"JSON環境変数読み込み: {key}={'*' * len(value) if 'KEY' in key else value[:30]}...")
                else:
                    # テキスト形式で読み込み
                    with open(env_file_path, 'r') as f:
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                if value and value.strip():  # 空でない場合のみ設定
                                    env_vars[key] = value.strip()
                                    print(f"テキスト環境変数読み込み: {key}={'*' * len(value) if 'KEY' in key else value[:30]}...")
                
                # 最初に見つかったファイルを使用
                if env_vars:
                    break
                    
        except Exception as e:
            print(f"Railway環境ファイル読み込みエラー ({env_file_path}): {e}")
    
    # プロセス環境から直接読み取りを試行
    if not env_vars:
        try:
            print("プロセス環境から直接読み取りを試行...")
            with open(f'/proc/{os.getpid()}/environ', 'rb') as f:
                proc_env = f.read().decode('utf-8', errors='ignore').split('\0')
                for var in proc_env:
                    if var and '=' in var:
                        key, value = var.split('=', 1)
                        if key in ['SUPABASE_URL', 'SUPABASE_KEY'] and value:
                            env_vars[key] = value
                            print(f"プロセス環境変数発見: {key}={'*' * len(value) if 'KEY' in key else value[:30]}...")
        except Exception as e:
            print(f"プロセス環境読み取りエラー: {e}")
    
    return env_vars

def get_supabase_config():
    """Supabase設定を複数の方法で取得"""
    
    print("=== Supabase設定取得開始 ===")
    
    # 方法1: 環境変数から直接取得
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = os.getenv("SUPABASE_KEY", "").strip()
    
    print(f"方法1 - 環境変数:")
    print(f"  SUPABASE_URL: {'設定済み' if supabase_url else '未設定'} ({'*' * len(supabase_url) if supabase_url else 'N/A'})")
    print(f"  SUPABASE_KEY: {'設定済み' if supabase_key else '未設定'} ({'*' * len(supabase_key) if supabase_key else 'N/A'})")
    
    # 方法2: Railway環境でのファイルフォールバック
    if (not supabase_url or not supabase_key) and os.getenv('RAILWAY_ENVIRONMENT_NAME'):
        print("方法2 - Railway環境ファイル読み込み:")
        alt_vars = load_railway_env()
        if alt_vars:
            supabase_url = alt_vars.get('SUPABASE_URL', supabase_url)
            supabase_key = alt_vars.get('SUPABASE_KEY', supabase_key)
            print(f"  更新後 SUPABASE_URL: {'設定済み' if supabase_url else '未設定'}")
            print(f"  更新後 SUPABASE_KEY: {'設定済み' if supabase_key else '未設定'}")
        else:
            print("  ファイルから追加設定なし")
    
    # 方法3: Streamlit secretsから取得
    if not supabase_url or not supabase_key:
        print("方法3 - Streamlit secrets:")
        try:
            secrets_url = st.secrets.get("supabase", {}).get("url", "")
            secrets_key = st.secrets.get("supabase", {}).get("key", "")
            
            supabase_url = secrets_url.strip() if secrets_url else supabase_url
            supabase_key = secrets_key.strip() if secrets_key else supabase_key
            
            print(f"  secrets SUPABASE_URL: {'設定済み' if secrets_url else '未設定'}")
            print(f"  secrets SUPABASE_KEY: {'設定済み' if secrets_key else '未設定'}")
            
        except Exception as e:
            print(f"  Streamlit secrets読み込みエラー: {e}")
    
    # 方法4: .envファイルから読み込み（ローカル開発用）
    if not supabase_url or not supabase_key:
        print("方法4 - .envファイル:")
        try:
            load_dotenv()
            env_url = os.getenv("SUPABASE_URL", "").strip()
            env_key = os.getenv("SUPABASE_KEY", "").strip()
            
            supabase_url = env_url if env_url else supabase_url
            supabase_key = env_key if env_key else supabase_key
            
            print(f"  .env SUPABASE_URL: {'設定済み' if env_url else '未設定'}")
            print(f"  .env SUPABASE_KEY: {'設定済み' if env_key else '未設定'}")
            
        except Exception as e:
            print(f"  .envファイル読み込みエラー: {e}")
    
    # 空文字列の場合は未設定と見なす
    if supabase_url == "" or supabase_key == "":
        supabase_url = ""
        supabase_key = ""
    
    print(f"=== 最終設定結果 ===")
    print(f"SUPABASE_URL: {'✅ 設定済み' if supabase_url else '❌ 未設定'}")
    print(f"SUPABASE_KEY: {'✅ 設定済み' if supabase_key else '❌ 未設定'}")
    print("=" * 30)
    
    return supabase_url, supabase_key

# デバッグ: 環境変数の状態を確認
if os.getenv('RAILWAY_ENVIRONMENT_NAME'):
    print("=== Railway環境での環境変数デバッグ ===")
    print(f"RAILWAY_ENVIRONMENT_NAME: {os.getenv('RAILWAY_ENVIRONMENT_NAME')}")
    print(f"SUPABASE_URL in os.environ: {'SUPABASE_URL' in os.environ}")
    print(f"SUPABASE_KEY in os.environ: {'SUPABASE_KEY' in os.environ}")
    if 'SUPABASE_URL' in os.environ:
        print(f"SUPABASE_URL value length: {len(os.environ['SUPABASE_URL'])}")
    if 'SUPABASE_KEY' in os.environ:
        print(f"SUPABASE_KEY value length: {len(os.environ['SUPABASE_KEY'])}")
    print("=" * 40)

# 強化された環境変数取得
SUPABASE_URL, SUPABASE_KEY = get_supabase_config()

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
        
        with st.expander("🔧 今すぐ設定する手順"):
            st.markdown("""
            ### 1. Supabase接続情報を取得
            1. **Supabase** にアクセス
            2. プロジェクトを選択
            3. **Settings → API** をクリック
            4. 以下の情報をコピー:
               - **Project URL**: `https://xxxxx.supabase.co`
               - **anon public key**: `eyJhbGciOiJIUzI1NiI...`
            
            ### 2. Railway環境変数を設定
            1. **Railway** のプロジェクトページを開く
            2. **"Variables"** タブをクリック
            3. **"New Variable"** で以下を追加:
            
            **変数名**: `SUPABASE_URL`  
            **値**: `https://your-project-ref.supabase.co`
            
            **変数名**: `SUPABASE_KEY`  
            **値**: `eyJhbGciOiJIUzI1NiI...` (anon public key)
            
            ### 3. 再デプロイ
            - 環境変数を保存すると自動的に再デプロイされます
            - 数分後にこのページを再読み込みしてください
            """)
        
        with st.expander("🔍 現在の設定状況"):
            st.write("**環境変数:**")
            st.write(f"- RAILWAY_ENVIRONMENT_NAME: {os.getenv('RAILWAY_ENVIRONMENT_NAME', 'Not Set')}")
            st.write(f"- RAILWAY_PROJECT_NAME: {os.getenv('RAILWAY_PROJECT_NAME', 'Not Set')}")
            st.write(f"- RAILWAY_SERVICE_NAME: {os.getenv('RAILWAY_SERVICE_NAME', 'Not Set')}")
            st.write(f"- PORT: {os.getenv('PORT', 'Not Set')}")
            
            # より詳細な環境変数チェック
            st.write("**Supabase環境変数の詳細:**")
            supabase_url_exists = 'SUPABASE_URL' in os.environ
            supabase_key_exists = 'SUPABASE_KEY' in os.environ
            
            if supabase_url_exists:
                st.write(f"✅ SUPABASE_URL: 設定済み")
            else:
                st.write(f"❌ SUPABASE_URL: 未設定")
                
            if supabase_key_exists:
                st.write(f"✅ SUPABASE_KEY: 設定済み")
            else:
                st.write(f"❌ SUPABASE_KEY: 未設定")
        
        # Railway環境変数設定ガイドへのリンク
        st.info("""
        📖 **詳細な設定手順**: `RAILWAY_ENV_SETUP.md` ファイルを参照してください。
        
        Railwayでの環境変数設定に関するよくある問題と解決方法が記載されています。
        """)
    
    # デモ機能の提供
    st.warning("⚠️ データベース機能は無効です。環境変数を設定してデプロイし直してください。")
    
    # 基本的なアプリケーション情報を表示
    st.title("🏌️ 88会ゴルフコンペ・スコア管理システム")
    st.subheader("📋 デモモード: データベース接続が無効です")
    
    if os.getenv('RAILWAY_ENVIRONMENT_NAME'):
        st.info(f"🚂 Railway環境: 環境変数が設定されていません")
    
    st.markdown("""
    ### ⚠️ 設定が必要です
    Railway環境でアプリケーションが正常に起動していますが、データベース接続情報が設定されていません。
    """)
    
    st.markdown("""
    ### 📖 アプリケーション機能一覧
    - 🏆 歴代優勝者の管理と表示
    - 📊 優勝回数ランキングの可視化  
    - ⛳ スコア入力および管理
    - 💾 データのバックアップ機能
    - 📈 スコア分析とグラフ表示
    """)
    
    # 環境変数設定後に再読み込みするよう案内
    st.success("💡 **設定完了後**: ページを再読み込みしてデータベース機能をご利用ください。")




