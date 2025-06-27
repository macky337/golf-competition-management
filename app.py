#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - エントリーポイント
このファイルは、Streamlitクラウドのデプロイに必要なエントリーポイントです。
実際のアプリケーションロジックはapp/app.pyに実装されています。
"""

import sys
import os

# デバッグ情報を出力
print("=== Entry Point Debug ===")
print(f"Working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")
print(f"App directory exists: {os.path.exists('app')}")
if os.path.exists('app'):
    print(f"Files in app directory: {os.listdir('app')}")
print("=========================")

# app/app.pyのパスを設定
app_path = os.path.join(os.path.dirname(__file__), 'app', 'app.py')

# sys.pathにappディレクトリを追加
app_dir = os.path.join(os.path.dirname(__file__), 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# app.pyの内容を直接実行
if os.path.exists(app_path):
    with open(app_path, 'r', encoding='utf-8') as f:
        exec(f.read())
else:
    # フォールバック
    import streamlit as st
    st.error(f"アプリケーションファイルが見つかりません: {app_path}")
    st.title("🏌️ 88会ゴルフコンペ・スコア管理システム")
    st.info("アプリケーションは起動していますが、メインファイルが見つかりません。")