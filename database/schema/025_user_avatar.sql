-- Store the user's optional profile image as a validated data URL.
SET NAMES utf8mb4;

SET @column_exists = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'users'
    AND column_name = 'avatar_data'
);
SET @statement = IF(
  @column_exists = 0,
  'ALTER TABLE users ADD COLUMN avatar_data MEDIUMTEXT NULL AFTER phone',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;
