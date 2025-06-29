#!/usr/bin/env python3
"""
Railway緊急診断スクリプト
"""
import os
import sys
import subprocess

print("🚨 Railway緊急診断開始")
print("=" * 60)

# 基本情報
print("📍 システム情報:")
print(f"  Python: {sys.version}")
print(f"  作業ディレクトリ: {os.getcwd()}")
print(f"  スクリプト: {__file__}")

# ファイル存在確認
files_to_check = [
    'Procfile',
    'flask_emergency.py', 
    'app.py',
    'requirements.txt'
]

print("\n📁 ファイル存在確認:")
for file in files_to_check:
    exists = os.path.exists(file)
    print(f"  {file}: {'✅' if exists else '❌'}")

# Procfile内容確認
print("\n📜 Procfile内容:")
try:
    with open('Procfile', 'r') as f:
        content = f.read()
        print(f"  内容: {content.strip()}")
except Exception as e:
    print(f"  エラー: {e}")

# 環境変数確認
print("\n🌐 重要な環境変数:")
important_vars = ['PORT', 'STREAMLIT_SERVER_PORT', 'RAILWAY_ENVIRONMENT']
for var in important_vars:
    value = os.getenv(var, 'NOT_SET')
    print(f"  {var}: {value}")

# Streamlit関連環境変数
print("\n🎛️ すべてのSTREAMLIT環境変数:")
streamlit_vars = {k: v for k, v in os.environ.items() if k.startswith('STREAMLIT_')}
if streamlit_vars:
    for k, v in streamlit_vars.items():
        print(f"  {k}: {v}")
else:
    print("  なし")

# Flask起動テスト
print("\n🧪 Flask起動テスト:")
try:
    port = int(os.getenv('PORT', 5000))
    print(f"  ポート: {port}")
    
    # Flask アプリをインポートしてテスト
    sys.path.insert(0, os.getcwd())
    
    print("  Flask インポート中...")
    from flask_emergency import app
    
    print("  ✅ Flask アプリ正常インポート")
    print(f"  🚀 Flask起動準備完了 (ポート: {port})")
    
    # 実際に起動
    print("  🌟 Flask サーバー起動中...")
    app.run(host='0.0.0.0', port=port, debug=False)
    
except ImportError as e:
    print(f"  ❌ インポートエラー: {e}")
    print("  🔄 代替起動を試行...")
    
    # 代替起動
    os.system("python3 flask_emergency.py")
    
except Exception as e:
    print(f"  ❌ Flask起動エラー: {e}")
    print("  🚨 重大な問題が発生しました")
    sys.exit(1)
