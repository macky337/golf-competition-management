import streamlit as st
import main  # main.py をインポート

# パスワード設定
PASSWORD = "88"

# セッション状態を初期化
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

def login_page():
    st.title("ログイン画面")
    password = st.text_input("パスワードを入力してください", type="password")

    if st.button("ログイン"):
        if password == PASSWORD:
            st.session_state.logged_in = True
            st.session_state.current_page = "main"
        else:
            st.error("パスワードが間違っています")

def main_app_redirect():
    # セッション状態に応じて画面を切り替え
    if st.session_state.logged_in and st.session_state.current_page == "main":
        main.main_app()  # main.py の main_app を呼び出し
    else:
        login_page()

if __name__ == "__main__":
    main_app_redirect()
