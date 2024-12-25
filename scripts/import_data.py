import sqlite3

def import_data(df):
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()

    # 必要な列が存在するか確認
    required_columns = ['competition_id', 'player_id', 'out_score', 'in_score', 'total_score', 'handicap', 'net_score', 'ranking']
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"CSVファイルに必要な列 '{col}' が存在しません。")

    # データを挿入
    for index, row in df.iterrows():
        cursor.execute('''
            INSERT INTO scores (competition_id, player_id, out_score, in_score, total_score, handicap, net_score, ranking)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
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
    conn.close()

if __name__ == '__main__':
    import pandas as pd
    df = pd.read_csv('../data/sample_data.csv', encoding='utf-8', sep=',')
    import_data(df)
