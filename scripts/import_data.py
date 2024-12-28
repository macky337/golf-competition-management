import pandas as pd
import os

# スクリプトのディレクトリを基準にファイルパスを設定
script_dir = os.path.dirname(os.path.abspath(__file__))
excel_file = os.path.join(script_dir, '..', 'data', 'golf_scores1.xlsx')  # 修正
competitions_csv = os.path.join(script_dir, '..', 'data', 'competitions.csv')  # 修正
players_csv = os.path.join(script_dir, '..', 'data', 'players.csv')  # 修正
scores_csv = os.path.join(script_dir, '..', 'data', 'scores.csv')  # 修正

# デバッグ: ファイルパスを表示
print(f"Excel ファイルのパス: {excel_file}")
print(f"Competitions CSV のパス: {competitions_csv}")
print(f"Players CSV のパス: {players_csv}")
print(f"Scores CSV のパス: {scores_csv}")

# ファイルの存在確認
if not os.path.exists(excel_file):
    print(f"エラー: {excel_file} が存在しません。")
    exit(1)

# Excelファイルの読み込み
df = pd.read_excel(excel_file)
print("Excelファイルの読み込み成功")

# competitions.csv の作成
competitions = df[['competition_id', 'date', 'course']].drop_duplicates().reset_index(drop=True)
competitions.to_csv(competitions_csv, index=False, encoding='utf-8-sig')
print("competitions.csv の作成成功")

# players.csv の作成
players = df[['player']].drop_duplicates().reset_index(drop=True)
players = players.rename(columns={'player': 'name'})
players.insert(0, 'id', range(1, len(players) + 1))
players.to_csv(players_csv, index=False, encoding='utf-8-sig')
print("players.csv の作成成功")

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

# scores.csv に保存
df.to_csv(scores_csv, index=False, encoding='utf-8-sig')
print("scores.csv の作成成功")