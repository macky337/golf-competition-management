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
            name TEXT NOT NULL
        );
    ''')
    
    # scores テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER,
            player_id INTEGER,
            out_score INTEGER,
            in_score INTEGER,
            total_score INTEGER,
            handicap INTEGER,
            net_score INTEGER,
            ranking INTEGER,
            FOREIGN KEY (competition_id) REFERENCES competitions(id),
            FOREIGN KEY (player_id) REFERENCES players(id)
        );
    ''')
    
    print("Tables created successfully.")

def import_data():
    # データベースに接続
    conn = sqlite3.connect(db_path)
    create_tables(conn)
    cursor = conn.cursor()

    print("Importing competitions data...")
    competitions_df = pd.read_csv(competitions_csv, encoding='utf-8', sep=',')
    competitions_df.to_sql('competitions', conn, if_exists='append', index=False)
    print(f"{len(competitions_df)} competitions imported.")

    print("Importing players data...")
    players_df = pd.read_csv(players_csv, encoding='utf-8', sep=',')
    
    # 列名をデータベースに合わせてリネーム
    if 'player_name' in players_df.columns:
        players_df.rename(columns={'player_name': 'name'}, inplace=True)
    
    players_df.to_sql('players', conn, if_exists='append', index=False)
    print(f"{len(players_df)} players imported.")

    print("Importing scores data...")
    scores_df = pd.read_csv(scores_csv, encoding='utf-8', sep=',')
    scores_df.to_sql('scores', conn, if_exists='append', index=False)
    print(f"{len(scores_df)} scores imported.")

    # コミットして接続を閉じる
    conn.commit()
    conn.close()
    print("Data import completed successfully.")

if __name__ == '__main__':
    import_data()