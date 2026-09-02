-- Persist the device-reported switch as the real-time source of truth.
SET @column_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'device'
    AND column_name = 'switch_state'
);
SET @statement = IF(
  @column_exists = 0,
  'ALTER TABLE device ADD COLUMN switch_state VARCHAR(10) NULL AFTER status',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

SET @column_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'device'
    AND column_name = 'switch_changed_at'
);
SET @statement = IF(
  @column_exists = 0,
  'ALTER TABLE device ADD COLUMN switch_changed_at DATETIME(6) NULL AFTER switch_state',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;
