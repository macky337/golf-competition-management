import streamlit as st
import sys
import os
import pandas as pd

# scriptsディレクトリをモジュール検索パスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))

from player_management import add_player, get_players, delete_player
from score_entry import add_score, get_scores, delete_score
from data_visualization import plot_score_distribution, plot_score_trends
from import_data import import_data

st.title('ゴルフ大会管理システム')

# プレイヤー管理
st.header('プレイヤー管理')
player_name = st.text_input('プレイヤー名')
if st.button('プレイヤー追加'):
    add_player(player_name)
    st.success(f'プレイヤー {player_name} を追加しました')

players = get_players()
st.write('プレイヤー一覧')
for player in players:
    st.write(f'{player[0]}: {player[1]}')
    if st.button(f'プレイヤー削除 {player[1]}', key=f'delete_{player[0]}'):
        delete_player(player[0])
        st.success(f'プレイヤー {player[1]} を削除しました')

# スコア入力
st.header('スコア入力')
competition_id = st.number_input('大会ID', min_value=1)
player_id = st.number_input('プレイヤーID', min_value=1)
out_score = st.number_input('アウトスコア', min_value=0)
in_score = st.number_input('インスコア', min_value=0)
handicap = st.number_input('ハンデキャップ', min_value=0)
if st.button('スコア追加'):
    add_score(competition_id, player_id, out_score, in_score, handicap)
    st.success('スコアを追加しました')

# スコア一覧
scores = get_scores()
st.header('スコア一覧')
if scores:
    # pandas DataFrame に変換して表示
    df_scores = pd.DataFrame(scores, columns=['id', 'competition_id', 'player_id', 'out_score', 'in_score', 'total_score', 'handicap', 'net_score', 'ranking'])
    st.dataframe(df_scores)
    # または、各スコアをループで表示
    # for score in scores:
    #     st.write(score)
    #     if st.button(f'スコア削除 {score[0]}', key=f'delete_score_{score[0]}'):
    #         delete_score(score[0])
    #         st.success('スコアを削除しました')
else:
    st.write('スコアがありません。')

# データ可視化
st.header('データ可視化')
if st.button('スコア分布を表示'):
    plot_score_distribution()

player_id_for_trends = st.number_input('スコア推移を表示するプレイヤーID', min_value=1, key='player_id_for_trends')
if st.button('スコア推移を表示'):
    plot_score_trends(player_id_for_trends)

# データインポート
st.header('データインポート')
uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
if uploaded_file is not None:
    try:
        # エンコーディングと区切り文字を指定
        df = pd.read_csv(uploaded_file, encoding='utf-8', sep=',')
        record_count = len(df)
        import_data(df)
        st.success(f'{record_count} 件のデータをインポートしました')
    except Exception as e:
        st.error(f"データのインポート中にエラーが発生しました: {e}")

def validate_data(df):
    required_columns = ['competition_id', 'player_id', 'out_score', 'in_score', 'total_score', 'handicap', 'net_score', 'ranking']
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"CSVファイルに必要な列 '{col}' が存在しません。")
    # 追加のバリデーション（例：数値であることの確認）
    numeric_columns = ['competition_id', 'player_id', 'out_score', 'in_score', 'total_score', 'handicap', 'net_score', 'ranking']
    for col in numeric_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"列 '{col}' は数値である必要があります。")