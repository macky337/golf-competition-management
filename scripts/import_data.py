import sqlite3
import pandas as pd

def import_competitions(df):
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()

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
    conn.close()

def import_players(df):
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()

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
        ))

    conn.commit()
    conn.close()

def import_scores(df):
    conn = sqlite3.connect('../data/golf_competition.db')
    cursor = conn.cursor()

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
    conn.close()

if __name__ == '__main__':
    # CSVファイルの読み込み
    competitions_df = pd.read_csv('../data/competitions.csv', encoding='utf-8', sep=',')
    players_df = pd.read_csv('../data/players.csv', encoding='utf-8', sep=',')
    scores_df = pd.read_csv('../data/scores.csv', encoding='utf-8', sep=',')

    # データのインポート
    import_competitions(competitions_df)
    import_players(players_df)
    import_scores(scores_df)