#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - 最新版 2025-07-05
新しいRailwayプロジェクト用の確実に動作するバージョン
"""

import streamlit as st
import os
from datetime import datetime

# 確実にページ設定を最初に実行
st.set_page_config(
    page_title="88会ゴルフコンペ",
    page_icon="⛳",
    layout="wide"
)

# タイムスタンプを表示してキャッシュを確認
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.title("🏌️‍♂️ 88会ゴルフコンペ・スコア管理システム")
st.markdown(f"### 新しいRailwayプロジェクト - {current_time}")

# 環境変数の状態を表示
st.markdown("#### 🔧 環境確認")
railway_env = os.getenv("RAILWAY_ENVIRONMENT", "未設定")
supabase_url = os.getenv("SUPABASE_URL", "未設定")
supabase_key_exists = "設定済み" if os.getenv("SUPABASE_KEY") else "未設定"

col1, col2, col3 = st.columns(3)
with col1:
    st.write(f"**Railway環境**: {railway_env}")
with col2:
    st.write(f"**Supabase URL**: {'設定済み' if supabase_url != '未設定' else '未設定'}")
with col3:
    st.write(f"**Supabase KEY**: {supabase_key_exists}")

# セッション状態の初期化
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False

st.markdown("---")

# ログイン処理
if not st.session_state.user_logged_in:
    st.markdown("### 🔐 ログイン")
    
    # ゴルフのアイコンでデザイン
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h2>⛳ 88会ゴルフコンペ ⛳</h2>
        <p>スコア管理システム</p>
    </div>
    """, unsafe_allow_html=True)
    
    password = st.text_input("パスワードを入力してください", type="password", key="login_pwd")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔓 ログイン", key="login_btn", use_container_width=True):
            if password == "88":
                st.session_state.user_logged_in = True
                st.success("ログインしました！")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ パスワードが間違っています")

else:
    # メイン画面
    st.markdown("### 🏆 メイン画面")
    st.success("✅ ログイン成功！正規版のメイン画面です。")
    
    # 記念大会の情報
    st.markdown("""
    <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
        <h3 style="color: #2e8b57;">🎉 第50回記念大会 (2025年4月13日) 🎉</h3>
        <p style="color: #333;">88会ゴルフコンペの栄えある第50回記念大会</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Supabase接続テスト
    if supabase_url != "未設定" and supabase_key_exists == "設定済み":
        try:
            from supabase import create_client
            supabase = create_client(supabase_url, os.getenv("SUPABASE_KEY"))
            
            # テスト用データ取得
            response = supabase.table("players").select("*").limit(3).execute()
            
            if response.data:
                st.markdown("#### 📊 プレイヤーデータ（抜粋）")
                st.json(response.data)
            else:
                st.info("データベースに接続しましたが、データがありません")
                
        except Exception as e:
            st.warning(f"Supabase接続エラー: {str(e)[:100]}...")
    else:
        st.info("Supabase環境変数が設定されていません")
    
    # ダミーデータ表示
    st.markdown("#### 📈 サンプルスコアデータ")
    import pandas as pd
    
    sample_data = {
        'プレイヤー': ['田中太郎', '佐藤花子', '山田文雄'],
        'スコア': [82, 76, 88],
        'ハンディ': [12, 8, 16],
        'ネット': [70, 68, 72],
        '順位': [2, 1, 3]
    }
    
    df = pd.DataFrame(sample_data)
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 データ更新", key="refresh_btn"):
            st.rerun()
    with col2:
        if st.button("🚪 ログアウト", key="logout_btn"):
            st.session_state.user_logged_in = False
            st.rerun()

# フッター
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; color: #666; font-size: 0.8em;">
    88会ゴルフコンペ・スコア管理システム | 更新時刻: {current_time}<br>
    新しいRailwayプロジェクト | 正規版UI表示
</div>
""", unsafe_allow_html=True)
