import pandas as pd
import os
import csv

# filepath: /c:/Users/user/Documents/GitHub/golf-competition-management/scripts/clean_scores.py
def clean_scores(input_file, output_file):
    try:
        # CSVファイルを読み込む（引用符を保持）
        df = pd.read_csv(input_file, quotechar='"')

        # 'id' カラムを削除
        if 'id' in df.columns:
            df = df.drop(columns=['id'])

        # 引用符なしでCSVを保存
        df.to_csv(output_file, index=False, quoting=csv.QUOTE_NONE, escapechar='\\')
        
        print(f"\'{input_file}\' から \'id\' カラムと引用符を削除しました。\n出力ファイル: {output_file}")
    except Exception as e:
        print(f"処理中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # 入力ファイルと出力ファイルのパスを設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, '..', 'data', 'scores.csv')
    output_path = os.path.join(script_dir, '..', 'data', 'scores_clean.csv')

    clean_scores(input_path, output_path)