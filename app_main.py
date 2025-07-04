#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - Railway/Supabase統合版
"""

import sys
import os
import importlib.util

# 環境に応じてアプリケーションを切り替え
def load_app_module():
    """環境に応じてアプリケーションモジュールを読み込み"""
    
    # Railway環境（PostgreSQL）の場合
    if os.getenv('RAILWAY_ENVIRONMENT') and os.getenv('DATABASE_URL'):
        app_path = os.path.join(os.path.dirname(__file__), 'app_railway.py')
        if os.path.exists(app_path):
            spec = importlib.util.spec_from_file_location("railway_app", app_path)
            app_module = importlib.util.module_from_spec(spec)
            sys.modules["railway_app"] = app_module
            spec.loader.exec_module(app_module)
            return app_module
    
    # Supabase環境またはローカル環境の場合
    app_path = os.path.join(os.path.dirname(__file__), 'app', 'app.py')
    if os.path.exists(app_path):
        spec = importlib.util.spec_from_file_location("supabase_app", app_path)
        app_module = importlib.util.module_from_spec(spec)
        sys.modules["supabase_app"] = app_module
        spec.loader.exec_module(app_module)
        return app_module
    
    # フォールバック：Railway アプリを直接実行
    app_path = os.path.join(os.path.dirname(__file__), 'app_railway.py')
    if os.path.exists(app_path):
        spec = importlib.util.spec_from_file_location("fallback_app", app_path)
        app_module = importlib.util.module_from_spec(spec)
        sys.modules["fallback_app"] = app_module
        spec.loader.exec_module(app_module)
        return app_module
    
    raise ImportError("適切なアプリケーションモジュールが見つかりません")

# アプリケーションを読み込み実行
if __name__ == "__main__":
    try:
        app_module = load_app_module()
        # メイン関数が存在する場合は実行
        if hasattr(app_module, 'main'):
            app_module.main()
    except Exception as e:
        import streamlit as st
        st.error(f"アプリケーション読み込みエラー: {e}")
        st.info("デバッグ情報:")
        st.write(f"作業ディレクトリ: {os.getcwd()}")
        st.write(f"利用可能ファイル: {os.listdir('.')}")
        st.write(f"環境変数 RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT')}")
        st.write(f"環境変数 DATABASE_URL: {'設定済み' if os.getenv('DATABASE_URL') else '未設定'}")
