import streamlit as st

def main_app():
    st.title("メインアプリケーション")
    st.write("こちらがメインアプリケーションです。")

    if st.button("ログアウト"):
        # セッションをリセットしてログイン画面に戻る
        st.session_state.logged_in = False
        st.session_state.current_page = "login"
