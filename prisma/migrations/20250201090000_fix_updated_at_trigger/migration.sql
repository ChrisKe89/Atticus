-- Align update_updated_at trigger with snake_case and camelCase columns
CREATE OR REPLACE FUNCTION app_private.update_updated_at()
RETURNS trigger AS $$
DECLARE
    payload jsonb := to_jsonb(NEW);
BEGIN
    IF payload ? 'updatedAt' THEN
        NEW."updatedAt" = CURRENT_TIMESTAMP;
    ELSIF payload ? 'updated_at' THEN
        NEW.updated_at = CURRENT_TIMESTAMP;
    ELSE
        RAISE EXCEPTION 'update_updated_at() called for table % without updated timestamp column', TG_TABLE_NAME;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
