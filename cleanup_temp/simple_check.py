#!/usr/bin/env python3
"""
Railway エラー診断スクリプト（シンプル版）
"""
import os
import sys

def simple_diagnosis():
    """シンプルなエラー診断"""
    
    print("🩺 Railway シンプル診断")
    print("=" * 30)
    
    # 基本環境確認
    print("📋 基本情報:")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  作業ディレクトリ: {os.getcwd()}")
    print(f"  Railway環境: {os.getenv('RAILWAY_ENVIRONMENT_NAME', '未検出')}")
    
    # 環境変数確認
    print("\n🔍 環境変数:")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if supabase_url:
        print(f"  ✅ SUPABASE_URL: 設定済み ({len(supabase_url)} 文字)")
    else:
        print(f"  ❌ SUPABASE_URL: 未設定")
    
    if supabase_key:
        print(f"  ✅ SUPABASE_KEY: 設定済み ({len(supabase_key)} 文字)")
    else:
        print(f"  ❌ SUPABASE_KEY: 未設定")
    
    # ファイル存在確認
    print("\n📁 重要ファイル:")
    important_files = ['app.py', 'requirements.txt', 'Dockerfile']
    for file in important_files:
        if os.path.exists(file):
            print(f"  ✅ {file}: 存在")
        else:
            print(f"  ❌ {file}: 不在")
    
    # Pythonモジュール確認
    print("\n📦 重要モジュール:")
    modules_to_check = ['streamlit', 'supabase', 'requests', 'pandas']
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"  ✅ {module}: インストール済み")
        except ImportError:
            print(f"  ❌ {module}: 未インストール")
    
    # 推奨アクション
    print("\n💡 推奨アクション:")
    if not supabase_url or not supabase_key:
        print("  1. Railway Dashboard → Variables で環境変数を設定")
        print("  2. 設定後に手動再デプロイを実行")
    else:
        print("  1. 環境変数は設定済みです")
        print("  2. アプリケーションの動作を確認してください")
    
    return supabase_url and supabase_key

if __name__ == "__main__":
    try:
        success = simple_diagnosis()
        print(f"\n🎯 診断結果: {'成功' if success else '要対応'}")
    except Exception as e:
        print(f"❌ 診断エラー: {e}")
        sys.exit(1)
