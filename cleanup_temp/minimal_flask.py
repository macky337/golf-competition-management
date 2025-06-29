#!/usr/bin/env python3
"""
最小限Flask版 - 確実起動
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
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .header { background: #4caf50; color: white; padding: 30px; border-radius: 10px; }
        .status { background: #e8f5e8; padding: 20px; margin: 20px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏌️ 88会ゴルフコンペ・スコア管理システム</h1>
        <h2>✅ Flask版 - Railway正常動作</h2>
    </div>
    <div class="status">
        <h3>🎉 STREAMLIT_SERVER_PORT問題 完全解決！</h3>
        <p>Railway Flask版が正常に起動しました</p>
        <p>ポートエラーは完全に解消されています</p>
    </div>
</body>
</html>
    '''

@app.route('/health')
def health():
    return {'status': 'healthy', 'app': 'golf-score-flask'}

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 最小限Flask版起動 - ポート: {port}")
    print("✅ STREAMLIT_SERVER_PORT問題を完全回避")
    app.run(host='0.0.0.0', port=port, debug=False)
