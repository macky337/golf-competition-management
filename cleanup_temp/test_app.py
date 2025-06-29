#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡単なテストアプリ - Renderデプロイメント確認用
"""

import streamlit as st
import os

# ページ設定
st.set_page_config(
    page_title="88会ゴルフコンペ・スコア管理システム", 
    page_icon="🏌️",
    layout="wide"
)

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

# フッター
st.markdown("---")
st.markdown("**🚀 Railway問題解決 → Render移行成功！**")
st.markdown("*最終更新: 2025-06-27*")
