import streamlit as st
import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import japanize_matplotlib
from datetime import datetime
import pytz

PASSWORD = "88"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def login_page():
    st.title("ログイン")
    password = st.text_input("パスワードを入力してください", type="password")
    if st.button("ログイン"):
        if password == PASSWORD:
            st.session_state["logged_in"] = True
            st.success("ログイン成功")
            st.experimental_rerun()  # ここで再描画してメイン画面に遷移
        else:
            st.error("パスワードが間違っています")

def main_app():
    st.title("88会ゴルフコンペ - スコア管理システム")
    st.write("こちらがメインアプリの画面です。")
    if st.button("ログアウト"):
        st.session_state["logged_in"] = False
        st.experimental_rerun()  # ここで再描画してログイン画面に遷移

if st.session_state["logged_in"]:
    main_app()
else:
    login_page()
