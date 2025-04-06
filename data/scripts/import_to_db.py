# このスクリプトは、CSVファイルからデータを読み込み、SQLiteデータベースにインポートします。
# スクリプトのディレクトリを基準にファイルパスを設定し、データベース接続を確立します。
# CSVファイルからデータを読み込み、必要に応じてランキングを計算し、
# データベースに competitions、players、および scores テーブルを作成してデータを保存します。
# 最後に、データベース接続を閉じます。
# このスクリプトを実行すると、データベースにデータがインポートされます。

import pandas as pd
import sqlite3
import os

print("スクリプト開始")

# スクリプトのディレクトリを基準にファイルパスを設定
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, '..', 'data', 'golf_competition.db')
competitions_csv = os.path.join(script_dir, '..', 'data', 'competitions.csv')
players_csv = os.path.join(script_dir, '..', 'data', 'players.csv')
scores_csv = os.path.join(script_dir, '..', 'data', 'scores.csv')

print("ファイルパス設定完了")
print(f"DB Path: {db_path}")
print(f"Competitions CSV Path: {competitions_csv}")
print(f"Players CSV Path: {players_csv}")
print(f"Scores CSV Path: {scores_csv}")

# データベース接続の確立
conn = sqlite3.connect(db_path)
print("データベース接続完了")

# CSVファイルの読み込み
competitions_df = pd.read_csv(competitions_csv)
players_df = pd.read_csv(players_csv)
scores_df = pd.read_csv(scores_csv)
print("CSVファイル読み込み完了")

# ranking を net_score から計算
scores_df['ranking'] = scores_df.groupby('competition_id')['net_score'].rank(method='min')

# その回が1行の場合、ランキングを1に設定
scores_df.loc[scores_df.groupby('competition_id')['competition_id'].transform('count') == 1, 'ranking'] = 1

# データベースにテーブルを作成
competitions_df.to_sql('competitions', conn, if_exists='replace', index=False)
players_df.to_sql('players', conn, if_exists='replace', index=False)
scores_df.to_sql('scores', conn, if_exists='replace', index=False)
print("データベースへの書き出し完了")

# データベース接続を閉じる
conn.close()
print("データベース接続を閉じました")