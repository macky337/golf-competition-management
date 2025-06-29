#!/usr/bin/env python3
"""
緊急フォールバック: Flask版ゴルフスコア管理システム
"""
from flask import Flask, render_template_string, request, jsonify
import os
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # GUI不要
import matplotlib.pyplot as plt
import io
import base64
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

def create_score_chart(data):
    """スコアチャートを作成"""
    if not data['scores']:
        return None
    
    df = pd.DataFrame(data['scores'])
    
    # プレイヤー別の合計スコア
    player_totals = df.groupby('player')['score'].sum().sort_values()
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(player_totals.index, player_totals.values, color=['#4CAF50', '#2196F3', '#FF9800', '#E91E63'])
    plt.title('🏌️ プレイヤー別合計スコア', fontsize=16, pad=20)
    plt.xlabel('プレイヤー', fontsize=12)
    plt.ylabel('合計スコア', fontsize=12)
    plt.xticks(rotation=45)
    
    # バーの上に数値表示
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    # 画像をbase64エンコード
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=100, bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return plot_url

@app.route('/')
def home():
    """メインページ"""
    data = load_data()
    chart_data = create_score_chart(data)
    
    # 最新スコア履歴
    recent_scores = data['scores'][-10:] if data['scores'] else []
    
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>🏌️ 88会ゴルフコンペ・スコア管理</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; padding: 20px; background: #f5f5f5; 
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            background: linear-gradient(135deg, #2e7d32, #4caf50); 
            color: white; padding: 30px; border-radius: 15px; text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .card { 
            background: white; padding: 25px; margin: 20px 0; 
            border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h2 { color: #2e7d32; margin-top: 0; }
        .form-group { margin: 15px 0; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, button { 
            padding: 12px; margin: 5px; border-radius: 8px; 
            border: 2px solid #ddd; font-size: 16px;
        }
        input:focus, select:focus { border-color: #4caf50; outline: none; }
        button { 
            background: #4caf50; color: white; cursor: pointer; 
            border: none; font-weight: bold; transition: background 0.3s;
        }
        button:hover { background: #45a049; }
        .score-table { 
            width: 100%; border-collapse: collapse; margin: 20px 0; 
        }
        .score-table th, .score-table td { 
            border: 1px solid #ddd; padding: 12px; text-align: center; 
        }
        .score-table th { 
            background: #f8f9fa; font-weight: bold; color: #2e7d32;
        }
        .score-table tr:nth-child(even) { background: #f8f9fa; }
        .stats-grid { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; margin: 20px 0; 
        }
        .stat-card { 
            background: #e8f5e8; padding: 20px; border-radius: 10px; text-align: center; 
        }
        .stat-number { font-size: 2em; font-weight: bold; color: #2e7d32; }
        .stat-label { color: #666; margin-top: 5px; }
        .chart-container { text-align: center; margin: 20px 0; }
        .player-list { 
            display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; 
        }
        .player-tag { 
            background: #e3f2fd; color: #1976d2; padding: 8px 16px; 
            border-radius: 20px; font-size: 14px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏌️ 88会ゴルフコンペ・スコア管理システム</h1>
            <p>📱 Flask版 - Railway完全対応 | {{ datetime.now().strftime('%Y年%m月%d日 %H:%M') }}</p>
        </div>
        
        {% if players %}
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ players|length }}</div>
                <div class="stat-label">参加プレイヤー</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ scores|length }}</div>
                <div class="stat-label">記録スコア数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ (scores|map(attribute='hole')|list|unique|list|length) or 0 }}</div>
                <div class="stat-label">プレイホール数</div>
            </div>
        </div>
        {% endif %}
        
        <div class="card">
            <h2>🆕 プレイヤー追加</h2>
            <div class="form-group">
                <label for="playerName">プレイヤー名</label>
                <input type="text" id="playerName" placeholder="プレイヤー名を入力" />
                <button onclick="addPlayer()">プレイヤー追加</button>
            </div>
        </div>
        
        {% if players %}
        <div class="card">
            <h2>👥 参加プレイヤー ({{ players|length }}名)</h2>
            <div class="player-list">
                {% for player in players %}
                <div class="player-tag">{{ player }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% if players %}
        <div class="card">
            <h2>⛳ スコア入力</h2>
            <div class="form-group">
                <label for="scorePlayer">プレイヤー</label>
                <select id="scorePlayer">
                    <option value="">プレイヤーを選択</option>
                    {% for player in players %}
                    <option value="{{ player }}">{{ player }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="form-group">
                <label for="scoreHole">ホール番号</label>
                <input type="number" id="scoreHole" placeholder="1-18" min="1" max="18" />
            </div>
            <div class="form-group">
                <label for="scoreValue">スコア</label>
                <input type="number" id="scoreValue" placeholder="スコアを入力" />
            </div>
            <button onclick="addScore()">スコア記録</button>
        </div>
        {% endif %}
        
        {% if chart_data %}
        <div class="card">
            <h2>📊 スコアチャート</h2>
            <div class="chart-container">
                <img src="data:image/png;base64,{{ chart_data }}" style="max-width: 100%; height: auto;" />
            </div>
        </div>
        {% endif %}
        
        {% if recent_scores %}
        <div class="card">
            <h2>� 最新スコア履歴</h2>
            <table class="score-table">
                <tr>
                    <th>プレイヤー</th>
                    <th>ホール</th>
                    <th>スコア</th>
                    <th>記録時刻</th>
                </tr>
                {% for score in recent_scores|reverse %}
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
    </div>
    
    <script>
        function addPlayer() {
            const name = document.getElementById('playerName').value.trim();
            if (!name) return alert('プレイヤー名を入力してください');
            
            fetch('/add_player', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name})
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    location.reload();
                } else {
                    alert(data.message || 'エラーが発生しました');
                }
            });
        }
        
        function addScore() {
            const player = document.getElementById('scorePlayer').value;
            const hole = document.getElementById('scoreHole').value;
            const score = document.getElementById('scoreValue').value;
            
            if (!player || !hole || !score) {
                return alert('すべての項目を入力してください');
            }
            
            if (hole < 1 || hole > 18) {
                return alert('ホール番号は1-18の範囲で入力してください');
            }
            
            fetch('/add_score', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    player: player, 
                    hole: parseInt(hole), 
                    score: parseInt(score)
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById('scoreHole').value = '';
                    document.getElementById('scoreValue').value = '';
                    location.reload();
                } else {
                    alert(data.message || 'エラーが発生しました');
                }
            });
        }
        
        // 自動更新（30秒ごと）
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
    """
    
    return render_template_string(html, 
                                players=data['players'], 
                                scores=data['scores'], 
                                recent_scores=recent_scores,
                                chart_data=chart_data,
                                datetime=datetime)

@app.route('/add_player', methods=['POST'])
def add_player():
    """プレイヤー追加"""
    try:
        data = load_data()
        player_name = request.json['name'].strip()
        
        if not player_name:
            return jsonify({'status': 'error', 'message': 'プレイヤー名が空です'})
        
        if player_name in data['players']:
            return jsonify({'status': 'error', 'message': 'そのプレイヤーは既に登録されています'})
        
        data['players'].append(player_name)
        save_data(data)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/add_score', methods=['POST'])
def add_score():
    """スコア追加"""
    try:
        data = load_data()
        score_data = request.json
        score_data['time'] = datetime.now().strftime('%H:%M:%S')
        
        data['scores'].append(score_data)
        save_data(data)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/health')
def health():
    """ヘルスチェック"""
    return jsonify({'status': 'healthy', 'app': 'golf-score-management'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("🏌️ 88会ゴルフコンペ・スコア管理システム Flask版")
    print(f"🚀 起動ポート: {port}")
    print("✅ STREAMLIT_SERVER_PORT問題を完全回避")
    app.run(host='0.0.0.0', port=port, debug=False)
