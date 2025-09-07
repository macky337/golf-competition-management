import os

def remove_quotes(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            for line in infile:
                # 各行の先頭と末尾の引用符を削除
                cleaned_line = line.strip().strip('"')
                outfile.write(cleaned_line + '\n')
        
        print(f"引用符の削除が成功しました。\n出力ファイル: {output_file}")
    except Exception as e:
        print(f"引用符の削除中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # 入力ファイルと出力ファイルのパスを設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, '..', 'data', 'scores.csv')
    output_path = os.path.join(script_dir, '..', 'data', 'scores_clean.csv')

    remove_quotes(input_path, output_path)