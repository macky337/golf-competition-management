-- バックアップからの復元を単一トランザクションで実行する。
-- PostgreSQL の関数呼び出しは成功時にまとめてコミットされ、例外時は全変更がロールバックされる。

BEGIN;

-- 旧0001を適用済みの環境（competitions.id）を、アプリの契約へ移行する。
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'competitions' AND column_name = 'id'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'competitions' AND column_name = 'competition_id'
    ) THEN
        ALTER TABLE competitions RENAME COLUMN id TO competition_id;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'competitions' AND column_name = 'name'
    ) THEN
        ALTER TABLE competitions ALTER COLUMN name DROP NOT NULL;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION restore_golf_database(backup_data JSONB)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    table_name TEXT;
    sequence_name TEXT;
    required_tables CONSTANT TEXT[] := ARRAY[
        'competitions', 'players', 'participants', 'scores', 'announcements'
    ];
BEGIN
    IF backup_data IS NULL OR jsonb_typeof(backup_data) <> 'object' THEN
        RAISE EXCEPTION 'backup_data must be a JSON object';
    END IF;

    FOREACH table_name IN ARRAY required_tables LOOP
        IF backup_data ? table_name
           AND jsonb_typeof(backup_data -> table_name) <> 'array' THEN
            RAISE EXCEPTION 'backup_data.% must be a JSON array', table_name;
        END IF;
    END LOOP;

    DELETE FROM scores;
    DELETE FROM participants;
    DELETE FROM announcements;
    DELETE FROM competitions;
    DELETE FROM players;

    INSERT INTO competitions
    SELECT record.*
    FROM jsonb_populate_recordset(
        NULL::competitions,
        COALESCE(backup_data -> 'competitions', '[]'::JSONB)
    ) AS record;

    INSERT INTO players
    SELECT record.*
    FROM jsonb_populate_recordset(
        NULL::players,
        COALESCE(backup_data -> 'players', '[]'::JSONB)
    ) AS record;

    INSERT INTO announcements
    SELECT record.*
    FROM jsonb_populate_recordset(
        NULL::announcements,
        COALESCE(backup_data -> 'announcements', '[]'::JSONB)
    ) AS record;

    INSERT INTO participants
    SELECT record.*
    FROM jsonb_populate_recordset(
        NULL::participants,
        COALESCE(backup_data -> 'participants', '[]'::JSONB)
    ) AS record;

    INSERT INTO scores
    SELECT record.*
    FROM jsonb_populate_recordset(
        NULL::scores,
        COALESCE(backup_data -> 'scores', '[]'::JSONB)
    ) AS record;

    sequence_name := pg_get_serial_sequence('competitions', 'competition_id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(competition_id) FROM competitions), 1), EXISTS (SELECT 1 FROM competitions));
    END IF;
    sequence_name := pg_get_serial_sequence('players', 'id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(id) FROM players), 1), EXISTS (SELECT 1 FROM players));
    END IF;
    sequence_name := pg_get_serial_sequence('participants', 'id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(id) FROM participants), 1), EXISTS (SELECT 1 FROM participants));
    END IF;
    sequence_name := pg_get_serial_sequence('scores', 'id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(id) FROM scores), 1), EXISTS (SELECT 1 FROM scores));
    END IF;
    sequence_name := pg_get_serial_sequence('announcements', 'id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(id) FROM announcements), 1), EXISTS (SELECT 1 FROM announcements));
    END IF;

    RETURN jsonb_build_object(
        'competitions', (SELECT COUNT(*) FROM competitions),
        'players', (SELECT COUNT(*) FROM players),
        'participants', (SELECT COUNT(*) FROM participants),
        'scores', (SELECT COUNT(*) FROM scores),
        'announcements', (SELECT COUNT(*) FROM announcements)
    );
END;
$$;

REVOKE ALL ON FUNCTION restore_golf_database(JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION restore_golf_database(JSONB) FROM anon;
REVOKE ALL ON FUNCTION restore_golf_database(JSONB) FROM authenticated;
GRANT EXECUTE ON FUNCTION restore_golf_database(JSONB) TO service_role;

COMMIT;
