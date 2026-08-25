-- Replace the former project-only communication_id with the UUID used by the
-- HarmonyOS simulator. Safe to run on an existing development database.
SET @has_uuid = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'device' AND column_name = 'device_uuid'
);
SET @sql = IF(@has_uuid = 0,
  'ALTER TABLE device ADD COLUMN device_uuid CHAR(36) NULL AFTER device_code',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE device SET device_uuid = UUID() WHERE device_uuid IS NULL OR device_uuid = '';

-- Keep the existing three-row demo database aligned with the UUIDs registered
-- in the HarmonyOS integration document. This only touches the old demo codes.
UPDATE device
SET device_code = 'P001-TEMP',
    device_uuid = '3b8dcefd-3a51-4adc-b452-47c184c0951d'
WHERE device_code = 'SENSOR-001'
;
UPDATE device
SET device_code = 'P001-MOIST',
    device_uuid = '814621f7-2561-49ad-9766-72d3fcd18d86'
WHERE device_code = 'SENSOR-002'
;
UPDATE device
SET device_code = 'P001-IRRIG',
    device_uuid = '435106ba-01e7-4745-9646-3907d15b28df'
WHERE device_code = 'SENSOR-003'
;

SET @has_comm = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'device' AND column_name = 'communication_id'
);
SET @has_old_index = (
  SELECT COUNT(*) FROM information_schema.statistics
  WHERE table_schema = DATABASE() AND table_name = 'device' AND index_name = 'uq_device_communication_id'
);
SET @sql = IF(@has_old_index > 0,
  'ALTER TABLE device DROP INDEX uq_device_communication_id',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql = IF(@has_comm > 0,
  'ALTER TABLE device DROP COLUMN communication_id',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_uuid_index = (
  SELECT COUNT(*) FROM information_schema.statistics
  WHERE table_schema = DATABASE() AND table_name = 'device' AND index_name = 'uq_device_uuid'
);
SET @sql = IF(@has_uuid_index = 0,
  'ALTER TABLE device ADD UNIQUE KEY uq_device_uuid (device_uuid)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

ALTER TABLE device MODIFY device_uuid CHAR(36) NOT NULL;
