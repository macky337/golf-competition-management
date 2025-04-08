# このスクリプトは、SQLiteデータベースの内容を確認するためのものです。
# スクリプトのディレクトリを基準にファイルパスを設定し、データベース接続を確立します。
# データベース内のテーブル一覧を取得し、各テーブルの内容を表示します。
# 最後に、データベース接続を閉じます。
# このスクリプトを実行すると、データベース内のテーブルとその内容がコンソールに表示されます。

import sqlite3
import os

def check_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'golf_competition.db')
    if not os.path.exists(db_path):
        print(f"データベースファイルが存在しません: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # テーブル一覧を取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("テーブル一覧:")
    for table in tables:
        print(f"- {table[0]}")

    # 各テーブルの内容を表示
    for table in tables:
        table_name = table[0]
        print(f"\n{table_name} テーブルの内容:")

        # カラム名を取得して表示
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        print(f"カラム名: {', '.join(column_names)}")

        # テーブルの内容を取得して表示
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        for row in rows:
            print(row)

    conn.close()

if __name__ == "__main__":
    check_db()
