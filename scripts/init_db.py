import sqlite3
import os

def initialize_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'golf_competition.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # players テーブル作成
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    # competitions テーブル作成
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS competitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        venue TEXT NOT NULL,
        edition INTEGER NOT NULL
    )
    ''')

    # scores テーブル作成
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
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS winners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        competition_id INTEGER,
        FOREIGN KEY (player_id) REFERENCES players(id),
        FOREIGN KEY (competition_id) REFERENCES competitions(id)
    )
    ''')

    conn.commit()
    conn.close()
    print("データベースとテーブルが初期化されました。")

def fetch_players():
    conn = sqlite3.connect('data/golf_competition.db')
    cursor = conn.cursor()

    # playersテーブルのデータを取得
    cursor.execute('SELECT * FROM players')
    players = cursor.fetchall()

    print("Playersテーブルのデータ:")
    for player in players:
        print(player)

    conn.close()

if __name__ == '__main__':
    initialize_db()
    fetch_players()