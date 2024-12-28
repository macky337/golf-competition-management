import sqlite3

db_path = "golf_competition.db"  # ファイルパスを正確に指定
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# テーブル一覧を確認
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print("Tables:", tables)

# 例: playersテーブルの内容を見たい場合
cur.execute("SELECT * FROM players;")
rows = cur.fetchall()
for row in rows:
    print(row)

conn.close()
