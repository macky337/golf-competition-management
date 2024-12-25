import sqlite3

def initialize_db():
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()

    # テーブル作成
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS competitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        venue TEXT NOT NULL,
        edition INTEGER NOT NULL
    )
    ''')

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

if __name__ == '__main__':
    initialize_db()