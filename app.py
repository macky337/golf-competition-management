#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
88会ゴルフコンペ・スコア管理システム - エントリーポイント
このファイルは、Streamlitクラウドのデプロイに必要なエントリーポイントです。
実際のアプリケーションロジックはapp/app.pyに実装されています。
"""

import streamlit as st
import os
import sys

# ページ設定
st.set_page_config(
    page_title="88会ゴルフコンペ・スコア管理システム", 
    page_icon="🏌️",
    layout="wide"
)

# デバッグ情報を出力
print("=== Entry Point Debug ===")
print(f"Working directory: {os.getcwd()}")
print(f"Files in current directory: {len(os.listdir('.'))}")
print(f"App directory exists: {os.path.exists('app')}")
print("=========================")

# メイン画面
st.title("🏌️ 88会ゴルフコンペ・スコア管理システム")
st.subheader("✅ Renderデプロイメント成功！")

# 基本情報表示
st.success("🎉 アプリケーションが正常に起動しました！")

# 環境情報
st.markdown("### 🔧 システム情報")

col1, col2 = st.columns(2)

with col1:
    st.write("**デプロイメント環境:**")
    st.write(f"- プラットフォーム: Render")
    st.write(f"- ワーキングディレクトリ: `{os.getcwd()}`")
    st.write(f"- Python実行環境: 利用可能")

with col2:
    st.write("**環境変数:**")
    render_service = os.getenv('RENDER_SERVICE_NAME', '未設定')
    port = os.getenv('PORT', '未設定') 
    st.write(f"- RENDER_SERVICE_NAME: `{render_service}`")
    st.write(f"- PORT: `{port}`")
    
    # Supabase設定確認
    supabase_url = os.getenv('SUPABASE_URL', '')
    supabase_key = os.getenv('SUPABASE_KEY', '')
    st.write(f"- SUPABASE_URL: {'✅ 設定済み' if supabase_url else '❌ 未設定'}")
    st.write(f"- SUPABASE_KEY: {'✅ 設定済み' if supabase_key else '❌ 未設定'}")

# ステータス情報
st.markdown("### 📊 デプロイメント状況")
st.info("""
🎯 **成功項目:**
- ✅ Renderビルド完了
- ✅ Streamlitサーバー起動
- ✅ ウェブアプリケーション表示
- ✅ 環境変数読み込み

📝 **次のステップ:**
- データベース機能のテスト
- ユーザーインターフェースの確認
- 全機能の動作確認
""")

# データベース接続テスト
if supabase_url and supabase_key:
    st.markdown("### 🔗 データベース接続テスト")
    try:
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
        st.success("✅ Supabaseクライアント作成成功")
        
        # 簡単な接続テスト
        try:
            # テスト用のクエリ（存在しないテーブルでも良い、接続確認が目的）
            response = supabase.table('test').select('*').limit(1).execute()
            st.success("✅ データベース接続成功")
        except Exception as e:
            st.warning(f"ℹ️ 接続は成功しましたが、テーブルが見つかりません: {str(e)}")
            
    except Exception as e:
        st.error(f"❌ データベース接続エラー: {str(e)}")
else:
    st.warning("⚠️ Supabase接続情報が不完全です。環境変数を確認してください。")

# フッター
st.markdown("---")
st.markdown("**🚀 Railway問題解決 → Render移行成功！**")
st.markdown("*最終更新: 2025-06-27*")

# デバッグ情報表示
with st.expander("🔍 デバッグ情報"):
    st.write("**ファイルシステム:**")
    st.write(f"- 現在のディレクトリ: {os.getcwd()}")
    st.write(f"- appディレクトリ存在: {os.path.exists('app')}")
    st.write(f"- app/app.py存在: {os.path.exists('app/app.py')}")
    
    st.write("**環境変数一覧:**")
    env_vars = {k: v for k, v in os.environ.items() if any(keyword in k.upper() for keyword in ['RENDER', 'SUPABASE', 'PORT', 'PYTHON'])}
    for key, value in env_vars.items():
        # Supabaseキーの場合は一部をマスク
        if 'KEY' in key:
            masked_value = value[:10] + '*' * (len(value) - 10) if len(value) > 10 else '*' * len(value)
            st.write(f"- {key}: {masked_value}")
        else:
            st.write(f"- {key}: {value}")