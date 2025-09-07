import pandas as pd
import os

def convert_tab_to_comma(input_file, output_file):
    try:
        # タブ区切りのCSVを読み込む（コメント行を無視）
        df = pd.read_csv(input_file, sep='\t', comment='/')
        
        # カンマ区切りで保存
        df.to_csv(output_file, index=False)
        
        print(f"変換が成功しました。\n出力ファイル: {output_file}")
    except Exception as e:
        print(f"変換中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # 入力ファイルと出力ファイルのパスを設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, '..', 'data', 'scores.csv')
    output_path = os.path.join(script_dir, '..', 'data', 'scores_comma.csv')

    convert_tab_to_comma(input_path, output_path)