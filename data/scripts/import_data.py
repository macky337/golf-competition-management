# このスクリプトは、Excelファイルからゴルフスコアデータを読み込み、
# それを competitions.csv、players.csv、および scores.csv に変換して保存します。
# スクリプトのディレクトリを基準にファイルパスを設定し、
# 各CSVファイルを作成するために必要なデータを抽出および変換します。
# 既存のCSVファイルが存在する場合は、新しいデータを追加して更新します。
# このスクリプトは、データのインポート処理を自動化するために使用されます。

import pandas as pd
import os

# スクリプトのディレクトリを基準にファイルパスを設定
script_dir = os.path.dirname(os.path.abspath(__file__))
excel_file = os.path.join(script_dir, '..', 'data', 'golf_scores1.xlsx')
competitions_csv = os.path.join(script_dir, '..', 'data', 'competitions.csv')
players_csv = os.path.join(script_dir, '..', 'data', 'players.csv')
scores_csv = os.path.join(script_dir, '..', 'data', 'scores.csv')

# ファイルの存在確認
if not os.path.exists(excel_file):
    print(f"エラー: {excel_file} が存在しません。")
    exit(1)

# Excelファイルの読み込み
df = pd.read_excel(excel_file)
df = df.rename(columns={'score1': 'out_score', 'score2': 'in_score'})
print("Excelファイルの読み込み成功")

# competitions.csv の読み込みと新規データの登録
if os.path.exists(competitions_csv):
    existing_competitions = pd.read_csv(competitions_csv)
else:
    existing_competitions = pd.DataFrame(columns=['competition_id', 'date', 'course'])

new_competitions = df[['competition_id', 'date', 'course']].drop_duplicates()
competitions_to_add = new_competitions[~new_competitions['competition_id'].isin(existing_competitions['competition_id'])]
all_competitions = pd.concat([existing_competitions, competitions_to_add]).drop_duplicates()
all_competitions.to_csv(competitions_csv, index=False, encoding='utf-8-sig')
print("competitions.csv の更新成功")

# players.csv の読み込みと新規データの登録
if os.path.exists(players_csv):
    existing_players = pd.read_csv(players_csv)
else:
    existing_players = pd.DataFrame(columns=['id', 'name'])

new_players = df[['player']].drop_duplicates().rename(columns={'player': 'name'})
new_players['id'] = range(existing_players['id'].max() + 1 if not existing_players.empty else 1,
                          len(new_players) + (existing_players['id'].max() if not existing_players.empty else 0) + 1)
players_to_add = new_players[~new_players['name'].isin(existing_players['name'])]
all_players = pd.concat([existing_players, players_to_add]).drop_duplicates()
all_players.to_csv(players_csv, index=False, encoding='utf-8-sig')
print("players.csv の更新成功")

# scores.csv の読み込みと新規データの登録
if os.path.exists(scores_csv):
    existing_scores = pd.read_csv(scores_csv)

    # カラム名のリネームが必要な場合
    if 'on_id' in existing_scores.columns:
        existing_scores.rename(columns={'on_id': 'competition_id'}, inplace=True)
else:
    existing_scores = pd.DataFrame(columns=['id', 'competition_id', 'date', 'course', 'player', 'out_score', 'in_score', 'total_score', 'handicap', 'net_score', 'player_id', 'name'])

df = df.merge(all_players, left_on='player', right_on='name', how='left')
scores_to_add = df[~df[['competition_id', 'player']].apply(tuple, axis=1).isin(existing_scores[['competition_id', 'player']].apply(tuple, axis=1))]
all_scores = pd.concat([existing_scores, scores_to_add]).drop_duplicates()
all_scores.to_csv(scores_csv, index=False, encoding='utf-8-sig')
print("scores.csv の更新成功")
