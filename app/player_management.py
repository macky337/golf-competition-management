import sqlite3

def add_player(name):
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO players (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()

def get_players():
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM players')
    players = cursor.fetchall()
    conn.close()
    return players

def delete_player(player_id):
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM players WHERE id = ?', (player_id,))
    conn.commit()
    conn.close()