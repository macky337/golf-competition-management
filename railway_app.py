#!/usr/bin/env python3
"""
Railway用最終手段：完全制御Streamlitアプリ
"""

import streamlit as st
import os
import sys
import importlib.util

# Streamlitの設定を強制上書き
st.set_page_config(
    page_title="88会ゴルフコンペ管理システム",
    page_icon="⛳",
    layout="wide"
)

def load_main_app():
    """メインアプリケーションを読み込み"""
    try:
        # app/app.pyを読み込み
        if os.path.exists('app/app.py'):
            sys.path.insert(0, 'app')
            import app as main_app
            return main_app
        elif os.path.exists('app.py'):
            # ルートのapp.pyを読み込み
            spec = importlib.util.spec_from_file_location("main_app", "app.py")
            main_app = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_app)
            return main_app
        else:
            st.error("アプリケーションファイルが見つかりません")
            return None
    except Exception as e:
        st.error(f"アプリケーション読み込みエラー: {e}")
        return None

def main():
    """メイン実行関数"""
    st.markdown("# 🚀 Railway緊急起動モード")
    st.markdown("環境変数を使用しない完全制御版で起動中...")
    
    # 環境情報表示
    st.markdown("## 📊 環境情報")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Python情報**")
        st.write(f"Python: {sys.version}")
        st.write(f"作業Dir: {os.getcwd()}")
        
    with col2:
        st.markdown("**Railway情報**")
        railway_env = os.environ.get('RAILWAY_ENVIRONMENT', '未設定')
        railway_project = os.environ.get('RAILWAY_PROJECT_NAME', '未設定')
        st.write(f"環境: {railway_env}")
        st.write(f"プロジェクト: {railway_project}")
    
    # Supabase接続確認
    st.markdown("## 🔌 Supabase接続確認")
    supabase_url = os.environ.get('SUPABASE_URL', '')
    supabase_key = os.environ.get('SUPABASE_KEY', '')
    
    if supabase_url and supabase_key:
        st.success("✅ Supabase環境変数が設定されています")
        st.write(f"URL長さ: {len(supabase_url)}")
        st.write(f"Key長さ: {len(supabase_key)}")
    else:
        st.warning("⚠️ Supabase環境変数が未設定です")
    
    # メインアプリケーション読み込み試行
    st.markdown("## 🎯 メインアプリケーション")
    
    if st.button("メインアプリを読み込む"):
        with st.spinner("アプリケーション読み込み中..."):
            main_app = load_main_app()
            if main_app:
                st.success("✅ アプリケーション読み込み成功！")
                st.info("通常のメインアプリケーションに切り替わります...")
                # メインアプリケーションを実行
                try:
                    # main_app の main関数またはrun関数を実行
                    if hasattr(main_app, 'main'):
                        main_app.main()
                    elif hasattr(main_app, 'run'):
                        main_app.run()
                    else:
                        st.info("アプリケーションが読み込まれました")
                except Exception as e:
                    st.error(f"アプリケーション実行エラー: {e}")
            else:
                st.error("❌ アプリケーション読み込み失敗")

if __name__ == "__main__":
    main()
