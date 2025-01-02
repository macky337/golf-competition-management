import streamlit as st

# ログイン状態を取得
def is_logged_in():
    return st.session_state.get("logged_in", False)

# ログイン状態を設定
def set_logged_in(status):
    st.session_state["logged_in"] = status