#!/usr/bin/env python3
"""
緊急フォールバック: Flask版簡易ゴルフスコア管理
"""
from flask import Flask, render_template_string, request, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

# データファイル
DATA_FILE = 'golf_scores.json'

def load_data():
    """スコアデータを読み込み"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'players': [], 'scores': []}

def save_data(data):
    """スコアデータを保存"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def home():
    """メインページ"""
    data = load_data()
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>🏌️ 88会ゴルフコンペ・スコア管理</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2e7d32; color: white; padding: 20px; border-radius: 10px; }
        .card { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        input, button { padding: 10px; margin: 5px; border-radius: 5px; border: 1px solid #ccc; }
        button { background: #4caf50; color: white; cursor: pointer; }
        button:hover { background: #45a049; }
        .score-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        .score-table th, .score-table td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        .score-table th { background: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏌️ 88会ゴルフコンペ・スコア管理システム</h1>
        <p>📱 緊急Flask版 - Railway対応</p>
    </div>
    
    <div class="card">
        <h2>🆕 プレイヤー追加</h2>
        <input type="text" id="playerName" placeholder="プレイヤー名" />
        <button onclick="addPlayer()">追加</button>
    </div>
    
    <div class="card">
        <h2>👥 参加プレイヤー ({{ players|length }}名)</h2>
        <ul>
        {% for player in players %}
            <li>{{ player }}</li>
        {% endfor %}
        </ul>
    </div>
    
    <div class="card">
        <h2>⛳ スコア入力</h2>
        <select id="scorePlayer">
            <option value="">プレイヤー選択</option>
            {% for player in players %}
            <option value="{{ player }}">{{ player }}</option>
            {% endfor %}
        </select>
        <input type="number" id="scoreHole" placeholder="ホール (1-18)" min="1" max="18" />
        <input type="number" id="scoreValue" placeholder="スコア" />
        <button onclick="addScore()">スコア記録</button>
    </div>
    
    {% if scores %}
    <div class="card">
        <h2>📊 スコア履歴</h2>
        <table class="score-table">
            <tr><th>プレイヤー</th><th>ホール</th><th>スコア</th><th>時刻</th></tr>
            {% for score in scores[-10:] %}
            <tr>
                <td>{{ score.player }}</td>
                <td>{{ score.hole }}</td>
                <td>{{ score.score }}</td>
                <td>{{ score.time }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
    
    <script>
        function addPlayer() {
            const name = document.getElementById('playerName').value;
            if (!name) return alert('プレイヤー名を入力してください');
            
            fetch('/add_player', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name})
            }).then(() => location.reload());
        }
        
        function addScore() {
            const player = document.getElementById('scorePlayer').value;
            const hole = document.getElementById('scoreHole').value;
            const score = document.getElementById('scoreValue').value;
            
            if (!player || !hole || !score) return alert('すべて入力してください');
            
            fetch('/add_score', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({player: player, hole: parseInt(hole), score: parseInt(score)})
            }).then(() => location.reload());
        }
    </script>
</body>
</html>
    """
    
    return render_template_string(html, players=data['players'], scores=data['scores'])

@app.route('/add_player', methods=['POST'])
def add_player():
    """プレイヤー追加"""
    data = load_data()
    player_name = request.json['name']
    
    if player_name not in data['players']:
        data['players'].append(player_name)
        save_data(data)
    
    return jsonify({'status': 'success'})

@app.route('/add_score', methods=['POST'])
def add_score():
    """スコア追加"""
    data = load_data()
    score_data = request.json
    score_data['time'] = datetime.now().strftime('%H:%M:%S')
    
    data['scores'].append(score_data)
    save_data(data)
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"🚀 Flask緊急版起動 - ポート: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
