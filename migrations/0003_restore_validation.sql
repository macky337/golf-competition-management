BEGIN;
ALTER FUNCTION restore_golf_database(JSONB) RENAME TO restore_golf_database_internal;
REVOKE ALL ON FUNCTION restore_golf_database_internal(JSONB) FROM PUBLIC, anon, authenticated, service_role;

CREATE FUNCTION restore_golf_database(backup_data JSONB)
RETURNS JSONB LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, pg_temp AS $$
DECLARE
    table_name TEXT;
    total_rows INTEGER := 0;
BEGIN
    IF backup_data IS NULL OR jsonb_typeof(backup_data) <> 'object' THEN
        RAISE EXCEPTION 'backup_data must be an object';
    END IF;
    FOREACH table_name IN ARRAY ARRAY['competitions','players','participants','scores','announcements'] LOOP
        IF NOT (backup_data ? table_name) OR jsonb_typeof(backup_data -> table_name) <> 'array' THEN
            RAISE EXCEPTION 'Missing or invalid table: %', table_name;
        END IF;
        IF EXISTS (SELECT 1 FROM jsonb_array_elements(backup_data -> table_name) AS item WHERE jsonb_typeof(item) <> 'object') THEN
            RAISE EXCEPTION 'Invalid row in %', table_name;
        END IF;
        total_rows := total_rows + jsonb_array_length(backup_data -> table_name);
    END LOOP;
    IF total_rows = 0 THEN
        RAISE EXCEPTION 'Empty backup cannot be restored';
    END IF;
    RETURN restore_golf_database_internal(backup_data);
END;
$$;
REVOKE ALL ON FUNCTION restore_golf_database(JSONB) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION restore_golf_database(JSONB) TO service_role;
COMMIT;
