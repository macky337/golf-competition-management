import sqlite3

def add_score(competition_id, player_id, out_score, in_score, handicap):
    total_score = out_score + in_score
    net_score = total_score - handicap
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scores (competition_id, player_id, out_score, in_score, total_score, handicap, net_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (competition_id, player_id, out_score, in_score, total_score, handicap, net_score))
    conn.commit()
    conn.close()

def get_scores():
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scores")
    rows = cursor.fetchall()
    conn.close()

    # バイト列をデコード（もし存在する場合）
    decoded_rows = []
    for row in rows:
        decoded_row = []
        for item in row:
            if isinstance(item, bytes):
                decoded_item = item.decode('utf-8')
                decoded_row.append(decoded_item)
            else:
                decoded_row.append(item)
        decoded_rows.append(decoded_row)

    return decoded_rows

def delete_score(score_id):
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scores WHERE id = ?', (score_id,))
    conn.commit()
    conn.close()