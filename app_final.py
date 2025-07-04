#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - 完全独立版
Railway環境で確実に動作する完全に独立したアプリです。
"""

import streamlit as st
import os
import sys

# デバッグ情報を強制的に非表示
import warnings
warnings.filterwarnings('ignore')

# Streamlitの設定
st.set_page_config(
    page_title="88会ゴルフコンペ・スコア管理システム",
    page_icon="⛳",
    layout="wide"
)

# 絶対に確実にログイン画面を表示
def show_login():
    st.title("🏌️‍♂️ 88会ゴルフコンペ・スコア管理システム")
    st.markdown("### ログイン")
    
    # 画像があれば表示
    try:
        import base64
        # 画像の代わりにテキストで表示
        st.markdown("---")
        st.markdown("#### ⛳ 88会ゴルフコンペ ⛳")
        st.markdown("---")
    except:
        pass
    
    # セッション状態の確実な初期化
    if "auth_state" not in st.session_state:
        st.session_state.auth_state = "login"
    
    # ログイン処理
    password = st.text_input("パスワードを入力してください", type="password", key="login_password")
    
    if st.button("ログイン", key="login_button"):
        if password == "88":
            st.session_state.auth_state = "logged_in"
            st.success("ログインしました！")
            st.rerun()
        else:
            st.error("パスワードが間違っています")

def show_main():
    st.title("🏌️‍♂️ 88会ゴルフコンペ・スコア管理システム")
    st.markdown("### メイン画面")
    
    st.success("✅ ログイン成功！")
    
    # 画像の代わりにテキストで表示
    st.markdown("---")
    st.markdown("#### 🏆 第50回記念大会 (2025年4月13日) 🏆")
    st.markdown("---")
    
    # 簡単なダミーデータ表示
    st.markdown("#### 📊 最新スコア一覧")
    
    import pandas as pd
    
    # ダミーデータ
    dummy_data = {
        'player_name': ['田中太郎', '佐藤花子', '山田文雄', '鈴木美咲', '高橋雄一'],
        'score': [82, 76, 88, 79, 84],
        'hdcp': [12, 8, 16, 10, 14],
        'net_score': [70, 68, 72, 69, 70],
        'date': ['2025-06-15'] * 5,
        'course': ['○○ゴルフクラブ'] * 5
    }
    
    df = pd.DataFrame(dummy_data)
    st.dataframe(df, use_container_width=True)
    
    # 統計情報
    st.markdown("#### 📈 統計情報")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("参加者数", "5")
    with col2:
        st.metric("平均スコア", "81.8")
    with col3:
        st.metric("ベストスコア", "76")
    with col4:
        st.metric("平均ネット", "69.8")
    
    st.markdown("---")
    if st.button("ログアウト", key="logout_button"):
        st.session_state.auth_state = "login"
        st.rerun()

# メイン処理
def main():
    # セッション状態の確実な初期化
    if "auth_state" not in st.session_state:
        st.session_state.auth_state = "login"
    
    # 認証状態に応じた画面表示
    if st.session_state.auth_state == "logged_in":
        show_main()
    else:
        show_login()

# 絶対に確実に実行
if __name__ == "__main__":
    main()
