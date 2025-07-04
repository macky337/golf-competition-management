#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - 本番環境強制版
Railway環境で確実に正規版UIを表示するための修正版
"""

import os
import sys

# 最初に環境変数を強制設定
os.environ['ENVIRONMENT'] = 'production'
os.environ['RAILWAY_ENVIRONMENT'] = 'production'

# 本番環境では警告を一切表示しない
import warnings
warnings.filterwarnings('ignore')

# Streamlitの設定
import streamlit as st

st.set_page_config(
    page_title="88会ゴルフコンペ・スコア管理システム",
    page_icon="⛳",
    layout="wide"
)

# 最小限のインポート
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Supabase関連（本番環境では静かに処理）
try:
    from supabase import create_client
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except:
    supabase = None

# パスワード設定
USER_PASSWORD = "88"
ADMIN_PASSWORD = "admin88"

# セッション状態の初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"

def get_supabase_client():
    """Supabaseクライアントを取得（本番環境では静かに処理）"""
    return supabase

def fetch_scores():
    """スコアデータを取得"""
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("scores").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
    except:
        pass
    return pd.DataFrame()

def fetch_players():
    """プレイヤーデータを取得"""
    if not supabase:
        return pd.DataFrame()
    
    try:
        response = supabase.table("players").select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
    except:
        pass
    return pd.DataFrame()

def login_page():
    """ログイン画面"""
    st.title("88会ログイン")
    
    # ログイン画面に画像を表示
    image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'image', '01205972-9563-43D7-B862-5B2B8DECF9FA.png')
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == USER_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.page = "main"
            st.rerun()
        else:
            st.error("パスワードが間違っています")

def admin_login_page():
    """管理者ログイン画面"""
    st.title("管理者ログイン")
    password = st.text_input("管理者パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == ADMIN_PASSWORD:
            st.session_state.admin_logged_in = True
            st.session_state.page = "admin"
            st.rerun()
        else:
            st.error("パスワードが間違っています")

def main_app():
    """メインアプリケーション"""
    st.title("88会ゴルフコンペ・スコア管理システム")
    
    # タイトルの下に画像を追加
    try:
        image_file = "2025-04-13 172536.png"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        image_path = os.path.join(project_root, "image", image_file)
        
        if os.path.exists(image_path):
            st.image(image_path, use_container_width=True)
            st.markdown("### 第50回記念大会 (2025年4月13日)")
        else:
            st.markdown("### 第50回記念大会 (2025年4月13日)")
    except:
        st.markdown("### 第50回記念大会 (2025年4月13日)")
    
    # データを取得して表示
    scores_df = fetch_scores()
    players_df = fetch_players()
    
    if not scores_df.empty and not players_df.empty:
        st.subheader("📊 最新スコア一覧")
        st.dataframe(scores_df)
        
        st.subheader("👥 プレイヤー一覧")
        st.dataframe(players_df)
    else:
        st.info("データを読み込み中...")

def admin_app():
    """管理者画面"""
    st.title("管理者設定画面")
    st.write("管理者用の機能です。")
    
    if st.button("ログアウト"):
        st.session_state.admin_logged_in = False
        st.session_state.page = "login"
        st.rerun()

def page_router():
    """ページルーティング"""
    if st.session_state.page == "main":
        if st.session_state.logged_in:
            main_app()
        else:
            login_page()
    elif st.session_state.page == "admin":
        if st.session_state.admin_logged_in:
            admin_app()
        else:
            admin_login_page()
    else:
        login_page()

# =============================================================================
# メイン実行 - 必ず最後に実行
# =============================================================================

# デフォルトページ設定
if not st.session_state.logged_in and not st.session_state.admin_logged_in:
    st.session_state.page = "login"

# ページルーティング実行
page_router()
