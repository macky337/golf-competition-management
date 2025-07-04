#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - 診断用シンプル版
本番環境の状態を診断するためのシンプルなアプリです。
"""

import streamlit as st
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# 本番環境であることを明示
os.environ['ENVIRONMENT'] = 'production'

st.set_page_config(
    page_title="88会ゴルフコンペ・スコア管理システム",
    page_icon="⛳",
    layout="wide"
)

# 診断情報
st.title("🏌️‍♂️ 88会ゴルフコンペ・スコア管理システム")
st.markdown("### 診断モード")

# 環境変数チェック
st.markdown("#### 環境変数チェック")
environment = os.getenv("ENVIRONMENT", "未設定")
st.write(f"ENVIRONMENT: {environment}")

supabase_url = os.getenv("SUPABASE_URL", "未設定")
supabase_key = os.getenv("SUPABASE_KEY", "未設定")

if supabase_url != "未設定":
    st.success("✅ SUPABASE_URL: 設定済み")
else:
    st.error("❌ SUPABASE_URL: 未設定")

if supabase_key != "未設定":
    st.success("✅ SUPABASE_KEY: 設定済み")
else:
    st.error("❌ SUPABASE_KEY: 未設定")

# セッション状態の初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "login"

# ログイン画面
if not st.session_state.logged_in:
    st.markdown("---")
    st.markdown("#### ログイン画面")
    
    # ログイン用画像を表示
    image_path = os.path.join(os.path.dirname(__file__), 'image', '01205972-9563-43D7-B862-5B2B8DECF9FA.png')
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.info("ログイン画像が見つかりませんでした")
    
    password = st.text_input("パスワードを入力してください", type="password")
    
    if st.button("ログイン"):
        if password == "88":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("パスワードが間違っています")
else:
    # メイン画面
    st.markdown("---")
    st.markdown("#### メイン画面")
    st.success("✅ ログイン成功！")
    
    if st.button("ログアウト"):
        st.session_state.logged_in = False
        st.rerun()
    
    # メイン画像を表示
    image_path = os.path.join(os.path.dirname(__file__), 'image', '2025-04-13 172536.png')
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
        st.markdown("### 第50回記念大会 (2025年4月13日)")
    else:
        st.info("メイン画像が見つかりませんでした")
        st.markdown("### 第50回記念大会 (2025年4月13日)")
    
    st.markdown("正規版のメイン画面が表示されました！")
