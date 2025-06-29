#!/usr/bin/env python3
"""
Railway専用緊急起動ラッパー
環境変数に完全に依存しないStreamlit起動
"""

import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("RAILWAY緊急起動ラッパー - 環境変数完全無視モード")
    print("=" * 60)
    
    # 作業ディレクトリ確認
    print(f"現在のディレクトリ: {os.getcwd()}")
    print(f"ファイル一覧: {os.listdir('.')}")
    
    # app.pyの存在確認
    if not os.path.exists('app.py'):
        print("❌ app.pyが見つかりません！")
        sys.exit(1)
    
    # Streamlit設定ディレクトリ作成
    os.makedirs('.streamlit', exist_ok=True)
    
    # 固定設定ファイル作成
    config_content = """[server]
headless = true
port = 8080
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[logger]
level = "info"
"""
    
    with open('.streamlit/config.toml', 'w') as f:
        f.write(config_content)
    
    print("✅ Streamlit設定ファイル作成完了")
    
    # 環境変数の状況確認（デバッグ用）
    print("\n🔍 環境変数確認:")
    for key in ['PORT', 'RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_NAME']:
        value = os.environ.get(key, 'NOT_SET')
        print(f"{key}: {value}")
    
    # 完全固定コマンドでStreamlit起動
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port=8080',
        '--server.address=0.0.0.0', 
        '--server.headless=true',
        '--server.fileWatcherType=none',
        '--server.enableCORS=false',
        '--server.enableXsrfProtection=false'
    ]
    
    print(f"\n🚀 実行コマンド: {' '.join(cmd)}")
    print("Streamlit起動中...")
    
    try:
        # 環境変数をクリーンにしてから実行
        clean_env = os.environ.copy()
        # PORTを削除（Railwayが設定しているかもしれない）
        clean_env.pop('PORT', None)
        
        subprocess.run(cmd, env=clean_env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Streamlit起動エラー: {e}")
        print("エラーの詳細:")
        print(f"リターンコード: {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ 起動が中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
