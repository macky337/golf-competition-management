import sqlite3

def import_data(df):
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()

    # デバッグ用にデータフレームの列名を表示
    print(df.columns)

    # データを挿入
    for index, row in df.iterrows():
        cursor.execute('''
            INSERT INTO scores (competition_id, player_id, out_score, in_score, total_score, handicap, net_score, ranking)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row['competition_id'], row['player_id'], row['out_score'], row['in_score'], row['total_score'], row['handicap'], row['net_score'], row['ranking']))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    import pandas as pd
    df = pd.read_csv('../data/sample_data.csv')
    import_data(df)
