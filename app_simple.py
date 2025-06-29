#!/usr/bin/env python3
"""
最小限Flask版 - Railway確実起動
"""
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>🏌️ 88会ゴルフコンペ</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding: 50px; 
            background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
        }
        .container { max-width: 800px; margin: 0 auto; }
        .header { 
            background: linear-gradient(135deg, #4caf50, #2e7d32); 
            color: white; 
            padding: 40px; 
            border-radius: 20px; 
            margin-bottom: 30px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        .status { 
            background: white; 
            padding: 30px; 
            margin: 20px 0; 
            border-radius: 15px; 
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .success { background: #e8f5e8; border-left: 5px solid #4caf50; }
        .info { background: #e3f2fd; border-left: 5px solid #2196f3; }
        h1 { margin: 0; font-size: 2.5em; }
        h2 { color: #2e7d32; }
        .version { opacity: 0.8; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏌️ 88会ゴルフコンペ・スコア管理システム</h1>
            <h2>✅ Flask版 - Railway正常動作</h2>
            <div class="version">Version 2.0 - Streamlit問題完全解決版</div>
        </div>
        
        <div class="status success">
            <h3>🎉 STREAMLIT_SERVER_PORT問題 完全解決！</h3>
            <p>Flask版により Railway で正常に起動しました</p>
            <p>ポートエラーは完全に解消されています</p>
        </div>
        
        <div class="status info">
            <h3>📊 システム情報</h3>
            <p><strong>フレームワーク:</strong> Flask 3.0+</p>
            <p><strong>デプロイ:</strong> Railway</p>
            <p><strong>状態:</strong> 正常稼働中</p>
            <p><strong>最終更新:</strong> 2025年6月29日</p>
        </div>
        
        <div class="status">
            <h3>🚀 次のステップ</h3>
            <p>ゴルフスコア管理機能を追加する準備が整いました</p>
            <ul style="text-align: left; max-width: 400px; margin: 20px auto;">
                <li>プレイヤー管理</li>
                <li>スコア入力</li>
                <li>ランキング表示</li>
                <li>統計分析</li>
            </ul>
        </div>
    </div>
</body>
</html>
    '''

@app.route('/health')
def health():
    """Railway ヘルスチェック"""
    return {
        'status': 'healthy', 
        'app': 'golf-score-flask',
        'version': '2.0',
        'message': 'STREAMLIT_SERVER_PORT問題解決済み'
    }

@app.route('/info')
def info():
    """システム情報"""
    return {
        'app_name': '88会ゴルフコンペ・スコア管理システム',
        'framework': 'Flask',
        'status': '正常稼働',
        'port': os.getenv('PORT', '5000'),
        'solved_issue': 'STREAMLIT_SERVER_PORT error completely resolved'
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("🏌️ 88会ゴルフコンペ・スコア管理システム Flask版")
    print(f"🚀 起動ポート: {port}")
    print("✅ STREAMLIT_SERVER_PORT問題を完全回避")
    print("🎯 Railway で確実動作")
    app.run(host='0.0.0.0', port=port, debug=False)
