# filepath: c:\Users\user\Documents\GitHub\golf-competition-management\data\migrate_sqlite_to_supabase.py
# filepath: C:\Users\user\Documents\GitHub\golf-competition-management\migrate_sqlite_to_supabase.py
import os
import sqlite3
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import sys
import json

# .envファイルから環境変数を読み込む
load_dotenv()

# Supabase接続情報
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("エラー: 環境変数が設定されていません。.envファイルを確認してください。")
    sys.exit(1)

# Supabaseクライアントを作成
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# データ移行前にRLSを無効化するSQL
def disable_rls():
    try:
        supabase.rpc('disable_rls').execute()
        print("RLSを一時的に無効化しました")
    except Exception as e:
        print(f"RLS無効化中にエラーが発生しました: {e}")

# データ移行後にRLSを再度有効化するSQL
def enable_rls():
    try:
        supabase.rpc('enable_rls').execute()
        print("RLSを再度有効化しました")
    except Exception as e:
        print(f"RLS有効化中にエラーが発生しました: {e}")

def migrate_from_sqlite():
    # 修正後: 正確なパスを追加
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'data', 'golf_competition.db'))
    
    if not os.path.exists(db_path):
        print(f"エラー: SQLiteデータベースが存在しません: {db_path}")
        # 追加のパスを試す
        possible_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'golf_competition.db')),  # プロジェクトルートのdata
            os.path.abspath(os.path.join(os.path.dirname(__file__), 'golf_competition.db')),  # 現在のディレクトリ
            os.path.abspath('golf_competition.db'),  # 実行ディレクトリ
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                print(f"データベースが見つかりました: {db_path}")
                break
        else:
            print("いずれのパスにもSQLiteデータベースが見つかりませんでした。")
            # 実際のデータベースファイルの場所を確認するためのデバッグ情報
            print("\n現在の作業ディレクトリ: " + os.getcwd())
            
            # プロジェクト内のすべてのDBファイルを探す
            for root, dirs, files in os.walk(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))):
                for file in files:
                    if file.endswith('.db'):
                        print(f"見つかったDBファイル: {os.path.join(root, file)}")
            
            return
    
    print(f"SQLiteデータベースを開いています: {db_path}")
    conn = sqlite3.connect(db_path)
    
    # playersテーブルのデータを取得
    players_df = pd.read_sql_query("SELECT * FROM players", conn)
    print(f"プレイヤーデータ: {len(players_df)}行読み込みました")
    
    # competitionsテーブルのデータを取得（存在する場合）
    try:
        competitions_df = pd.read_sql_query("SELECT * FROM competitions", conn)
        print(f"競技データ: {len(competitions_df)}行読み込みました")
        has_competitions_table = True
    except sqlite3.OperationalError:
        print("競技テーブルが見つかりません。CSVファイルから読み込みます。")
        competitions_path = os.path.join(os.path.dirname(__file__), 'data', 'competitions.csv')
        if os.path.exists(competitions_path):
            competitions_df = pd.read_csv(competitions_path)
            print(f"競技データ(CSV): {len(competitions_df)}行読み込みました")
            has_competitions_table = True
        else:
            print("競技CSVファイルが見つかりません。")
            has_competitions_table = False
    
    # scoresテーブルのデータを取得
    scores_df = pd.read_sql_query("SELECT * FROM scores", conn)
    print(f"スコアデータ: {len(scores_df)}行読み込みました")

    # NaN値とデータ型の処理
    scores_df = scores_df.fillna({
        'id': 0,
        'competition_id': 0,
        'player_id': 0,
        'date': '',
        'course': '',
        'out_score': 0.0,
        'in_score': 0.0,
        'handicap': 0.0,
        'net_score': 0.0,
        'ranking': 0
    })

    # 各カラムのデータ型を明示的に設定
    numeric_columns = ['id', 'competition_id', 'player_id', 'out_score', 'in_score', 'handicap', 'net_score', 'ranking']
    for col in numeric_columns:
        if col in scores_df.columns:
            # 整数型に変換（可能な場合）
            if col in ['id', 'competition_id', 'player_id', 'ranking']:
                scores_df[col] = scores_df[col].astype('Int64')  # null値を許容する整数型
            else:
                scores_df[col] = scores_df[col].astype(float)

    # 文字列カラムの処理
    string_columns = ['date', 'course']
    for col in string_columns:
        if col in scores_df.columns:
            scores_df[col] = scores_df[col].astype(str)
            # 'nan'という文字列を空文字列に置換
            scores_df[col] = scores_df[col].replace('nan', '')

    # NaNチェック（デバッグ用）
    nan_check = scores_df.isna().sum()
    if nan_check.sum() > 0:
        print("警告: データにまだNaN値が含まれています:")
        print(nan_check)
    
    conn.close()
    
    # JSONシリアライズ可能かチェックする関数
    def check_json_serializable(df, name="データフレーム"):
        """データフレームがJSONシリアライズ可能かチェックする"""
        try:
            records = df.to_dict('records')
            for i, record in enumerate(records):
                try:
                    json.dumps(record)
                except TypeError as e:
                    print(f"行 {i} はJSON互換性がありません: {e}")
                    print(f"問題の行: {record}")
                    for k, v in record.items():
                        if pd.isna(v) or str(v) == 'nan':
                            print(f"  NaN値を含むカラム: {k}, 値: {v}, 型: {type(v)}")
                    return False
            print(f"{name}はJSON互換性があります。")
            return True
        except Exception as e:
            print(f"{name}のJSON互換性チェック中にエラー: {e}")
            return False

    # 各データフレームをチェック
    check_json_serializable(players_df, "プレイヤーデータ")
    check_json_serializable(competitions_df, "競技データ")
    check_json_serializable(scores_df, "スコアデータ")

    # Supabaseにデータを挿入
    try:
        # RLSを無効化
        disable_rls()

        # 既存データを削除 - トランケートクエリを使用
        try:
            # テーブルを空にするSQLを実行
            result = supabase.rpc('truncate_tables', {'tables': ['scores', 'players', 'competitions']}).execute()
            print("既存のテーブルデータを削除しました")
        except Exception as e:
            print(f"テーブルのクリア中にエラーが発生しました: {e}")
            print("SQLを使用してテーブルをクリアします...")
            try:
                # 代替方法: RPC関数がない場合はWHERE TRUEを使用
                supabase.table('scores').delete().eq('id', 'id').execute()
                supabase.table('players').delete().eq('id', 'id').execute()
                if has_competitions_table:
                    supabase.table('competitions').delete().eq('competition_id', 'competition_id').execute()
                print("SQLでテーブルを空にしました")
            except Exception as e:
                print(f"代替クリア方法も失敗しました: {e}")
                print("既存データは削除せずに継続します...")
        
        # playersテーブルのデータをインサート
        supabase.table('players').insert(players_df.to_dict('records')).execute()
        print(f"プレイヤーデータ: {len(players_df)}行挿入しました")
        
        # competitionsテーブルのデータをインサート
        if has_competitions_table:
            supabase.table('competitions').insert(competitions_df.to_dict('records')).execute()
            print(f"競技データ: {len(competitions_df)}行挿入しました")
        
        # NaN値を適切に処理するコードを追加
        # scoresテーブルのデータをインサート（チャンクに分割）
        # NaN値をNULLに変換
        scores_df = scores_df.replace({pd.NA: None, float('nan'): None})  # NaN値をNoneに置換

        # スコアデータのインサート前にカラム確認と調整
        try:
            # 代替方法: スキーマチェックをスキップして、必要なカラムのみを保持
            try:
                # scores テーブルで必要なカラムを明示的に指定
                required_columns = ['id', 'competition_id', 'player_id', 'date', 'course', 
                                'out_score', 'in_score', 'handicap', 'net_score', 'ranking']
                
                # 現在のデータフレームカラムを確認
                df_columns = scores_df.columns.tolist()
                print(f"DataFrameのカラム: {df_columns}")
                
                # 余分なカラムを削除
                for col in df_columns:
                    if col not in required_columns:
                        scores_df = scores_df.drop(columns=[col])
                        print(f"余分なカラムを削除: {col}")
                
                # 不足しているカラムを追加
                for col in required_columns:
                    if col not in scores_df.columns:
                        print(f"不足しているカラム: {col}")
                        # 適切なデフォルト値を設定
                        if col in ['id', 'competition_id', 'player_id', 'ranking']:
                            scores_df[col] = 0
                        elif col in ['out_score', 'in_score', 'handicap', 'net_score']:
                            scores_df[col] = 0.0
                        else:
                            scores_df[col] = ''
                            
                # スコアデータのインサート
                # カラム調整後のスコアデータインサート部分（既存コードの続きとして追加）
                try:
                    # データをJSON経由で変換してNaN問題を回避
                    json_str = scores_df.to_json(orient='records')
                    records = json.loads(json_str)
                    
                    # チャンクに分割してインサート
                    chunk_size = 100
                    total_inserted = 0
                    
                    for i in range(0, len(records), chunk_size):
                        chunk = records[i:i+chunk_size]
                        supabase.table('scores').insert(chunk).execute()
                        total_inserted += len(chunk)
                        print(f"スコアデータ: {i}から{i+len(chunk)}行までを挿入しました")
                    
                    print(f"スコアデータ: 全{total_inserted}行の挿入が完了しました")
                except Exception as e:
                    print(f"スコアデータのインサート中にエラーが発生しました: {e}")
                    import traceback
                    print(traceback.format_exc())

            except Exception as e:
                print(f"スコアデータのインサート中にエラーが発生しました: {e}")
                # 詳細なエラー情報を表示
                import traceback
                print(traceback.format_exc())

            # RLSを再度有効化
            enable_rls()
        
        except Exception as e:
            print(f"スコアデータのインサート中にエラーが発生しました: {e}")
            # 詳細なエラー情報を表示
            import traceback
            print(traceback.format_exc())

        # RLSを再度有効化
        enable_rls()
        
    except Exception as e:
        print(f"データ移行中にエラーが発生しました: {e}")

if __name__ == "__main__":
    print("SQLiteからSupabaseへのデータ移行を開始します...")
    migrate_from_sqlite()
    print("データ移行が完了しました。")

# データ確認用のクイックスクリプト
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 各テーブルのレコード数を確認
players = supabase.table('players').select('*').execute()
competitions = supabase.table('competitions').select('*').execute()
scores = supabase.table('scores').select('*').execute()

print(f"プレイヤー数: {len(players.data)}")
print(f"競技数: {len(competitions.data)}")
print(f"スコア数: {len(scores.data)}")