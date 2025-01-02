import streamlit as st
import session_manager  # セッション管理モジュール

def main_app():
    st.title("メインアプリケーション")
    st.write("ようこそ！こちらがメインアプリケーションです。")

    if st.button("ログアウト"):
        session_manager.set_logged_in(False)  # ログアウト状態に設定
        st.experimental_rerun()  # ログイン画面へリダイレクト

# メインアプリケーションを実行
if session_manager.is_logged_in():
    main_app()
else:
    st.warning("ログインが必要です。ログイン画面にリダイレクトします。")
    st.experimental_rerun()  # ログイン画面へリダイレクト