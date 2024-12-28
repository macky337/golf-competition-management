import pandas as pd
import os

# スクリプトのディレクトリを基準にファイルパスを設定
script_dir = os.path.dirname(os.path.abspath(__file__))
excel_file = os.path.join(script_dir, '..', 'golf_scores1.xlsx')
competitions_csv = os.path.join(script_dir, '..', 'competitions.csv')
players_csv = os.path.join(script_dir, '..', 'players.csv')
scores_csv = os.path.join(script_dir, '..', 'scores.csv')

# Excelファイルの読み込み
df = pd.read_excel(excel_file)

# competitions.csv の作成
competitions = df[['competition_id', 'date', 'course']].drop_duplicates().reset_index(drop=True)
competitions.to_csv(competitions_csv, index=False, encoding='utf-8-sig')

# players.csv の作成
players = df[['player']].drop_duplicates().reset_index(drop=True)
players = players.rename(columns={'player': 'name'})
players.insert(0, 'id', range(1, len(players) + 1))
players.to_csv(players_csv, index=False, encoding='utf-8-sig')

# scores.csv の作成
# players.csv からプレイヤーIDを取得
players_df = pd.read_csv(players_csv)
df = df.merge(players_df, left_on='player', right_on='name', how='left')
df = df.rename(columns={
    'competition_id': 'competition_id',
    'id_y': 'player_id',
    'score1': 'out_score',
    'score2': 'in_score',
    'total_score': 'total_score',
    'handicap': 'handicap',
    'net_score': 'net_score'
})

# scores.csv に必要なカラムを選択して保存
scores = df[['id_x', 'competition_id', 'player_id', 'out_score', 'in_score', 'total_score', 'handicap', 'net_score']]
scores = scores.rename(columns={'id_x': 'id'})
scores.to_csv(scores_csv, index=False, encoding='utf-8-sig')

print("CSVファイルのインポートが完了しました。")