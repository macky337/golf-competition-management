-- Review in Supabase SQL Editor. This preview always ROLLS BACK.
-- After reviewing the result and explicitly authorizing production changes,
-- replace only the final ROLLBACK with COMMIT to apply the same transaction.
-- No names or score values are returned by this script.
BEGIN;
SET LOCAL lock_timeout = '5s';
LOCK TABLE public.scores IN SHARE ROW EXCLUSIVE MODE;

-- Abort if the target tournament or the audited duplicate pattern has changed.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.competitions
        WHERE competition_id = 55 AND date = DATE '2026-11-14'
    ) THEN
        RAISE EXCEPTION 'Competition does not match the reviewed target';
    END IF;
    IF EXISTS (
        SELECT player_id FROM public.scores s
        WHERE competition_id = 55
        GROUP BY player_id
        HAVING count(DISTINCT (to_jsonb(s) - ARRAY['id','created_at','updated_at'])) > 1
    ) THEN
        RAISE EXCEPTION 'Conflicting scores exist; no records were changed';
    END IF;
    IF (SELECT count(*) - count(DISTINCT player_id)
        FROM public.scores WHERE competition_id = 55) <> 2 THEN
        RAISE EXCEPTION 'Duplicate count changed; repeat the read-only audit';
    END IF;
END $$;

-- Preserve every row in the affected groups, including the retained originals.
CREATE TABLE IF NOT EXISTS public.score_duplicate_repair_archive (
    original_id BIGINT PRIMARY KEY,
    original_record JSONB NOT NULL,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE public.score_duplicate_repair_archive ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.score_duplicate_repair_archive FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.score_duplicate_repair_archive TO service_role;

INSERT INTO public.score_duplicate_repair_archive (original_id, original_record)
SELECT id, to_jsonb(s) FROM public.scores s
WHERE competition_id = 55 AND player_id IN (
    SELECT player_id FROM public.scores WHERE competition_id = 55
    GROUP BY player_id HAVING count(*) > 1
);

-- The full records are identical apart from IDs/timestamps; retain the lowest ID.
WITH duplicates AS (
    SELECT id, row_number() OVER (PARTITION BY player_id ORDER BY id) AS position
    FROM public.scores WHERE competition_id = 55
), removed AS (
    DELETE FROM public.scores s USING duplicates d
    WHERE s.id = d.id AND d.position > 1
    RETURNING s.id
)
SELECT count(*) AS preview_removed_rows FROM removed;

-- Prevent another duplicate in this tournament without altering other history.
CREATE UNIQUE INDEX scores_competition_55_player_unique
ON public.scores (competition_id, player_id) WHERE competition_id = 55;

SELECT count(*) AS remaining_rows, count(DISTINCT player_id) AS remaining_players
FROM public.scores WHERE competition_id = 55;

ROLLBACK;
