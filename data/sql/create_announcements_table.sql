-- お知らせ・ブログ管理テーブル
-- 管理者が簡単にコンテンツを投稿・編集できる機能

CREATE TABLE IF NOT EXISTS announcements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    image_url VARCHAR(500),
    tournament_info JSONB,  -- 大会情報をJSON形式で保存
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- tournament_info の例:
-- {
--   "tournament_number": 52,
--   "date": "2025-12-06",
--   "start_time": "9:07",
--   "course_name": "本千葉カントリークラブ",
--   "course_url": "https://www.honchiba-cc.co.jp/",
--   "address": "千葉市緑区大金沢町311",
--   "phone": "043-292-0191",
--   "groups": 3,
--   "meeting_time": "8:30",
--   "fee": "18,000+昼食（少し引いてくれるかも）",
--   "organizers": "吉井.福澤"
-- }

-- インデックス作成
CREATE INDEX idx_announcements_display_order ON announcements(display_order DESC);
CREATE INDEX idx_announcements_is_active ON announcements(is_active);
CREATE INDEX idx_announcements_created_at ON announcements(created_at DESC);

-- 更新日時を自動更新するトリガー
CREATE OR REPLACE FUNCTION update_announcements_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_announcements_updated_at
    BEFORE UPDATE ON announcements
    FOR EACH ROW
    EXECUTE FUNCTION update_announcements_updated_at();

-- サンプルデータ挿入（第52回大会のお知らせ）
INSERT INTO announcements (title, content, display_order, is_active, tournament_info) VALUES
(
    '第52回88会ゴルフコンペのご案内',
    '次回の開催場所は前回同様本千葉カントリーとなりました。',
    1,
    true,
    '{
        "tournament_number": 52,
        "date": "2025-12-06",
        "start_time": "9:07",
        "course_name": "本千葉カントリークラブ",
        "course_url": "https://www.honchiba-cc.co.jp/",
        "address": "千葉市緑区大金沢町311",
        "phone": "043-292-0191",
        "groups": 3,
        "meeting_time": "8:30",
        "fee": "18,000+昼食（少し引いてくれるかも）",
        "organizers": "吉井.福澤"
    }'::jsonb
);

-- Row Level Security (RLS) の設定
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;

-- 全員が読み取り可能
CREATE POLICY "Anyone can read announcements"
    ON announcements FOR SELECT
    USING (true);

-- 管理者のみが作成・更新・削除可能（必要に応じて認証設定）
-- CREATE POLICY "Admins can manage announcements"
--     ON announcements FOR ALL
--     USING (auth.role() = 'admin');

COMMENT ON TABLE announcements IS '管理者が投稿するお知らせ・ブログ・大会案内を管理するテーブル';
COMMENT ON COLUMN announcements.tournament_info IS '大会情報（日時、場所、費用など）をJSON形式で保存';
COMMENT ON COLUMN announcements.display_order IS '表示順序（数字が大きいほど上に表示）';
