import sqlite3
import pandas as pd
import os

# スクリプトのディレクトリを取得
script_dir = os.path.dirname(os.path.abspath(__file__))

# データベースとCSVファイルの絶対パスを作成
db_path = os.path.join(script_dir, '../data/golf_competition.db')
competitions_csv = os.path.join(script_dir, '../data/competitions.csv')
players_csv = os.path.join(script_dir, '../data/players.csv')
scores_csv = os.path.join(script_dir, '../data/scores.csv')

print("Database Path:", db_path)
print("Competitions CSV Path:", competitions_csv)
print("Players CSV Path:", players_csv)
print("Scores CSV Path:", scores_csv)

def create_tables(conn):
    cursor = conn.cursor()
    
    print("Creating tables...")
    
    # competitions テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_number INTEGER NOT NULL,
            date TEXT NOT NULL,
            venue TEXT NOT NULL
        );
    ''')
    
    # players テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL
        );
    ''')
    
    # scores テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            out_score INTEGER NOT NULL,
            in_score INTEGER NOT NULL,
            total_score INTEGER NOT NULL,
            handicap INTEGER NOT NULL,
            net_score INTEGER NOT NULL,
            ranking INTEGER NOT NULL,
            FOREIGN KEY (competition_id) REFERENCES competitions(id),
            FOREIGN KEY (player_id) REFERENCES players(id)
        );
    ''')
    
    conn.commit()
    print("Tables created successfully.")

def import_competitions(conn, df):
    cursor = conn.cursor()
    print("Importing competitions data...")
    
    # 必要な列が存在するか確認
    required_columns = ['id', 'competition_number', 'date', 'venue']
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"CSVファイルに必要な列 '{col}' が存在しません。")
    
    # データを挿入
    for index, row in df.iterrows():
        cursor.execute('''
            INSERT INTO competitions (id, competition_number, date, venue)
            VALUES (?, ?, ?, ?)
        ''', (
            int(row['id']),
            int(row['competition_number']),
            row['date'],
            row['venue']
        ))
    
    conn.commit()
    print("Competitions data imported successfully.")

def import_players(conn, df):
    cursor = conn.cursor()
    print("Importing players data...")
    
    # 必要な列が存在するか確認
    required_columns = ['id', 'player_name']
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"CSVファイルに必要な列 '{col}' が存在しません。")
    
    # データを挿入
    for index, row in df.iterrows():
        cursor.execute('''
            INSERT INTO players (id, player_name)
            VALUES (?, ?)
        ''', (
            int(row['id']),
            row['player_name']
        ))  # ← ここに閉じ括弧を追加
    
    conn.commit()
    print("Players data imported successfully.")

def import_scores(conn, df):
    cursor = conn.cursor()
    print("Importing scores data...")
    
    # 必要な列が存在するか確認
    required_columns = ['id', 'competition_id', 'player_id', 'out_score', 'in_score', 'total_score', 'handicap', 'net_score', 'ranking']
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"CSVファイルに必要な列 '{col}' が存在しません。")
    
    # データを挿入
    for index, row in df.iterrows():
        cursor.execute('''
            INSERT INTO scores (id, competition_id, player_id, out_score, in_score, total_score, handicap, net_score, ranking)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(row['id']),
            int(row['competition_id']),
            int(row['player_id']),
            int(row['out_score']),
            int(row['in_score']),
            int(row['total_score']),
            int(row['handicap']),
            int(row['net_score']),
            int(row['ranking'])
        ))
    
    conn.commit()
    print("Scores data imported successfully.")

if __name__ == '__main__':
    # データベースに接続
    conn = sqlite3.connect(db_path)
    print("Connected to the database.")
    
    # テーブルを作成
    create_tables(conn)
    
    # CSVファイルの存在を確認
    for csv_path in [competitions_csv, players_csv, scores_csv]:
        if not os.path.isfile(csv_path):
            raise FileNotFoundError(f"CSVファイルが見つかりません: {csv_path}")
    print("All CSV files exist.")
    
    # CSVファイルの読み込み
    competitions_df = pd.read_csv(competitions_csv, encoding='utf-8', sep=',')
    players_df = pd.read_csv(players_csv, encoding='utf-8', sep=',')
    scores_df = pd.read_csv(scores_csv, encoding='utf-8', sep=',')
    print("CSV files loaded successfully.")
    
    # データのインポート
    import_competitions(conn, competitions_df)
    import_players(conn, players_df)
    import_scores(conn, scores_df)
    
    # 接続を閉じる
    conn.close()
    print("Database connection closed. All data imported successfully.")