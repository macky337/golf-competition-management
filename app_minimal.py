#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - 最小限テスト版
確実に正規版UIを表示するための最小限のアプリです。
"""

import streamlit as st
import os

# キャッシュクリアのためのコメント: 2025-07-05 13:00

# 環境変数を強制設定
os.environ['ENVIRONMENT'] = 'production'

st.set_page_config(
    page_title="88会ゴルフコンペ・スコア管理システム",
    page_icon="⛳",
    layout="wide"
)

# セッション状態の初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ログイン画面
if not st.session_state.logged_in:
    st.title("88会ログイン")
    st.markdown("### 正規版ログイン画面")
    
    # 画像を表示（あれば）
    image_path = os.path.join(os.path.dirname(__file__), 'image', '01205972-9563-43D7-B862-5B2B8DECF9FA.png')
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.info("ログイン画像: image/01205972-9563-43D7-B862-5B2B8DECF9FA.png")
    
    password = st.text_input("パスワードを入力してください", type="password")
    
    if st.button("ログイン"):
        if password == "88":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("パスワードが間違っています")

else:
    # メイン画面
    st.title("88会ゴルフコンペ・スコア管理システム")
    st.markdown("### 正規版メイン画面")
    st.success("✅ ログイン成功！正規版のメイン画面です。")
    
    # 画像を表示（あれば）
    image_path = os.path.join(os.path.dirname(__file__), 'image', '2025-04-13 172536.png')
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        st.info("メイン画像: image/2025-04-13 172536.png")
    
    st.markdown("### 第50回記念大会 (2025年4月13日)")
    
    # 環境変数の確認表示
    st.markdown("---")
    st.markdown("#### 環境確認")
    st.write(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', '未設定')}")
    st.write(f"RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', '未設定')}")
    st.write(f"現在時刻: 2025-07-05 13:00")
    
    if st.button("ログアウト"):
        st.session_state.logged_in = False
        st.rerun()

# フッター
st.markdown("---")
st.markdown("**88会ゴルフコンペ・スコア管理システム** - 正規版UI表示テスト")
