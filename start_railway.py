#!/usr/bin/env python3
"""
Railway用Streamlit起動スクリプト
環境変数の競合を完全に回避
"""
import os
import sys
import subprocess

def main():
    print("=" * 50)
    print("🚀 Railway Python起動スクリプト開始")
    print("=" * 50)
    
    # 現在の環境変数をデバッグ出力
    print("📋 環境変数確認:")
    for key in sorted(os.environ.keys()):
        if 'PORT' in key or 'STREAMLIT' in key:
            print(f"  {key} = {os.environ[key]}")
    
    # STREAMLIT関連環境変数をクリア
    env_to_clear = [
        'STREAMLIT_SERVER_PORT',
        'STREAMLIT_SERVER_ADDRESS', 
        'STREAMLIT_SERVER_HEADLESS',
        'STREAMLIT_BROWSER_GATHER_USAGE_STATS'
    ]
    
    print("\n🧹 環境変数クリア:")
    for env_var in env_to_clear:
        if env_var in os.environ:
            print(f"  削除: {env_var} = {os.environ[env_var]}")
            del os.environ[env_var]
        else:
            print(f"  未設定: {env_var}")
    
    # PORT設定
    port = os.getenv('PORT', '8501')
    print(f"\n📱 ポート設定: {port}")
    
    # 最終環境変数確認
    print("\n🔍 クリア後環境変数:")
    for key in sorted(os.environ.keys()):
        if 'PORT' in key or 'STREAMLIT' in key:
            print(f"  {key} = {os.environ[key]}")
    
    print(f"\n🏌️ 88会ゴルフコンペ・スコア管理システム (Railway版) を起動しています...")
    print(f" 環境: Railway PostgreSQL")
    
    # データベース接続確認
    if os.getenv('DATABASE_URL'):
        print("🗄️ PostgreSQL: 接続設定済み")
    else:
        print("⚠️ PostgreSQL: 未設定（サンプルデータ使用）")
    
    # Streamlit起動
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port', port,
        '--server.address', '0.0.0.0',
        '--server.headless', 'true'
    ]
    
    print(f"\n🚀 実行コマンド: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: Streamlit起動失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: 予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
