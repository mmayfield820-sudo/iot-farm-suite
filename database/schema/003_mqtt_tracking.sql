-- MQTT support migration. Safe to run against both existing and new databases.
SET @column_exists = (
  SELECT COUNT(*)
  FROM information_schema.columns
  WHERE table_schema = DATABASE()
    AND table_name = 'irrigation_record'
    AND column_name = 'command_id'
);
SET @statement = IF(
  @column_exists = 0,
  'ALTER TABLE irrigation_record ADD COLUMN command_id VARCHAR(64) NULL AFTER record_id',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

SET @index_exists = (
  SELECT COUNT(*)
  FROM information_schema.statistics
  WHERE table_schema = DATABASE()
    AND table_name = 'irrigation_record'
    AND index_name = 'uq_irrigation_command_id'
);
SET @statement = IF(
  @index_exists = 0,
  'ALTER TABLE irrigation_record ADD UNIQUE KEY uq_irrigation_command_id (command_id)',
  'SELECT 1'
);
PREPARE migration_statement FROM @statement;
EXECUTE migration_statement;
DEALLOCATE PREPARE migration_statement;

CREATE TABLE IF NOT EXISTS mqtt_telemetry_message (
  device_id BIGINT NOT NULL,
  message_id VARCHAR(100) NOT NULL,
  received_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (device_id, message_id),
  CONSTRAINT fk_mqtt_telemetry_device
    FOREIGN KEY (device_id) REFERENCES device (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
