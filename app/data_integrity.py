"""Database reads and restore validation shared by administrative workflows."""

RESTORE_TABLES = ("competitions", "players", "participants", "scores", "announcements")


def validate_backup(payload):
    if not isinstance(payload, dict):
        raise ValueError("バックアップはJSONオブジェクトである必要があります。")
    for table in RESTORE_TABLES:
        if table not in payload or not isinstance(payload[table], list):
            raise ValueError(f"バックアップの {table} 配列がありません。復元を中止しました。")
        if any(not isinstance(row, dict) for row in payload[table]):
            raise ValueError(f"バックアップの {table} に不正な行があります。")
    if not any(payload[table] for table in RESTORE_TABLES):
        raise ValueError("全テーブルが空のバックアップは復元できません。")


def fetch_all_rows(client, table):
    """Read bounded pages with stable ordering, rejecting truncated snapshots."""
    key = "competition_id" if table == "competitions" else "id"
    rows = []
    expected = None
    while True:
        response = client.table(table).select("*", count="exact").order(key).range(len(rows), len(rows) + 499).execute()
        if response.count is None:
            raise ValueError(f"{table} の総件数を確認できません。")
        if expected is None:
            expected = response.count
        if response.count != expected:
            raise ValueError(f"{table} が取得中に更新されました。再実行してください。")
        page = response.data or []
        rows.extend(page)
        if len(rows) >= expected:
            break
        if not page:
            raise ValueError(f"{table} の全件取得に失敗しました。")
    if len(rows) != expected or len({row[key] for row in rows}) != expected:
        raise ValueError(f"{table} の取得件数が一致しません。")
    return rows
