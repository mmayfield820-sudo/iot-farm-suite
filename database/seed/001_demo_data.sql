-- Development-only demo data. Safe to execute repeatedly.
-- All demo accounts use a bcrypt hash of the local development password documented in backend/README.md.
START TRANSACTION;

INSERT INTO users (username, password_hash, email, phone)
VALUES
  ('demo_admin', '$2b$12$.qlye5L1Opp5Ng9ydn36nOzw8bhmQ2J8AHdXmmPv4KLWCRvC2Bxh6', 'demo-admin@example.invalid', NULL),
  ('demo_farmer', '$2b$12$.qlye5L1Opp5Ng9ydn36nOzw8bhmQ2J8AHdXmmPv4KLWCRvC2Bxh6', 'demo-farmer@example.invalid', NULL),
  ('demo_system', '$2b$12$.qlye5L1Opp5Ng9ydn36nOzw8bhmQ2J8AHdXmmPv4KLWCRvC2Bxh6', 'demo-system@example.invalid', NULL)
ON DUPLICATE KEY UPDATE
  password_hash = VALUES(password_hash),
  email = VALUES(email),
  phone = VALUES(phone),
  user_status = 'active';

SET @admin_user_id = (SELECT user_id FROM users WHERE username = 'demo_admin');
SET @farmer_user_id = (SELECT user_id FROM users WHERE username = 'demo_farmer');
SET @system_user_id = (SELECT user_id FROM users WHERE username = 'demo_system');

INSERT IGNORE INTO user_role_rel (user_id, role_id, status)
SELECT @system_user_id, role_id, 'active'
FROM roles
WHERE role_code = 'system_admin';

INSERT INTO farm (admin_user_id, farm_name, city, address)
SELECT @admin_user_id, '演示农场', '杭州市', '浙江省杭州市演示农业园'
WHERE NOT EXISTS (SELECT 1 FROM farm WHERE admin_user_id = @admin_user_id);

SET @farm_id = (
  SELECT farm_id FROM farm
  WHERE admin_user_id = @admin_user_id
  ORDER BY farm_id LIMIT 1
);

UPDATE farm
SET admin_user_id = @admin_user_id,
    farm_name = '演示农场',
    city = '杭州市',
    address = '浙江省杭州市演示农业园'
WHERE farm_id = @farm_id;

INSERT INTO plot (farmer_user_id, farm_id, plot_name, location, crop_name, description)
SELECT @farmer_user_id, @farm_id, '一号田地', '东区温室', '番茄', '演示用一号田地'
WHERE NOT EXISTS (
  SELECT 1 FROM plot WHERE farm_id = @farm_id AND farmer_user_id = @farmer_user_id
);

SET @plot_id = (
  SELECT plot_id FROM plot
  WHERE farm_id = @farm_id AND farmer_user_id = @farmer_user_id
  ORDER BY plot_id LIMIT 1
);

UPDATE plot
SET farmer_user_id = @farmer_user_id,
    plot_name = '一号田地',
    location = '东区温室',
    crop_name = '番茄',
    description = '演示用一号田地'
WHERE plot_id = @plot_id;

INSERT INTO plot (farmer_user_id, farm_id, plot_name, location, crop_name, description)
SELECT @farmer_user_id, @farm_id, '二号田地', '西区温室', '黄瓜', '演示用二号田地'
WHERE NOT EXISTS (SELECT 1 FROM plot WHERE farm_id = @farm_id AND plot_name = '二号田地');

SET @plot2_id = (
  SELECT plot_id FROM plot
WHERE farm_id = @farm_id AND plot_name = '二号田地'
ORDER BY plot_id LIMIT 1
);

UPDATE plot
SET farmer_user_id = @farmer_user_id,
    plot_name = '二号田地',
    location = '西区温室',
    crop_name = '黄瓜',
    description = '演示用二号田地'
WHERE plot_id = @plot2_id;

INSERT INTO plot (farmer_user_id, farm_id, plot_name, location, crop_name, description)
SELECT NULL, @farm_id, '三号田地', '北区温室', '生菜', '演示用三号田地'
WHERE NOT EXISTS (SELECT 1 FROM plot WHERE farm_id = @farm_id AND plot_name = '三号田地');

SET @plot3_id = (
  SELECT plot_id FROM plot
WHERE farm_id = @farm_id AND plot_name = '三号田地'
ORDER BY plot_id LIMIT 1
);

UPDATE plot
SET farmer_user_id = NULL,
    plot_name = '三号田地',
    location = '北区温室',
    crop_name = '生菜',
    description = '演示用三号田地'
WHERE plot_id = @plot3_id;

SET @has_farmer_plot_scope = (
  SELECT COUNT(*) FROM information_schema.tables
  WHERE table_schema = DATABASE() AND table_name = 'farmer_plot_scope'
);
SET @cleanup_plot3_scope_sql = IF(
  @has_farmer_plot_scope > 0,
  'DELETE FROM farmer_plot_scope WHERE user_id = @farmer_user_id AND plot_id = @plot3_id',
  'SELECT 1'
);
PREPARE cleanup_plot3_scope_stmt FROM @cleanup_plot3_scope_sql;
EXECUTE cleanup_plot3_scope_stmt;
DEALLOCATE PREPARE cleanup_plot3_scope_stmt;

INSERT INTO device (device_code, device_uuid, device_type, plot_id, status)
SELECT 'P001-TEMP', '3b8dcefd-3a51-4adc-b452-47c184c0951d', 'temperature', @plot_id, 'online'
WHERE NOT EXISTS (SELECT 1 FROM device WHERE device_code = 'P001-TEMP');

INSERT INTO device (device_code, device_uuid, device_type, plot_id, status)
SELECT 'P001-MOIST', '814621f7-2561-49ad-9766-72d3fcd18d86', 'humidity', @plot_id, 'online'
WHERE NOT EXISTS (SELECT 1 FROM device WHERE device_code = 'P001-MOIST');

INSERT INTO device (device_code, device_uuid, device_type, plot_id, status)
SELECT 'P001-IRRIG', '435106ba-01e7-4745-9646-3907d15b28df', 'irrigation', @plot_id, 'offline'
WHERE NOT EXISTS (SELECT 1 FROM device WHERE device_code = 'P001-IRRIG');

SET @temperature_device_id = (SELECT device_id FROM device WHERE device_code = 'P001-TEMP');
SET @humidity_device_id = (SELECT device_id FROM device WHERE device_code = 'P001-MOIST');
SET @irrigation_device_id = (SELECT device_id FROM device WHERE device_code = 'P001-IRRIG');

UPDATE device SET plot_id = @plot_id, device_type = 'temperature', status = 'online'
 , device_uuid = '3b8dcefd-3a51-4adc-b452-47c184c0951d'
WHERE device_id = @temperature_device_id;
UPDATE device SET plot_id = @plot_id, device_type = 'humidity', status = 'online'
 , device_uuid = '814621f7-2561-49ad-9766-72d3fcd18d86'
WHERE device_id = @humidity_device_id;
UPDATE device SET plot_id = @plot_id, device_type = 'irrigation', status = 'offline'
 , device_uuid = '435106ba-01e7-4745-9646-3907d15b28df'
WHERE device_id = @irrigation_device_id;

INSERT INTO device (device_code, device_uuid, device_type, plot_id, status)
SELECT 'P002-TEMP', '77448f68-baa9-46f1-b380-d835d4e2dda6', 'temperature', @plot2_id, 'offline'
WHERE NOT EXISTS (SELECT 1 FROM device WHERE device_code = 'P002-TEMP');
INSERT INTO device (device_code, device_uuid, device_type, plot_id, status)
SELECT 'P002-MOIST', '8e52cfa5-9106-45c2-8645-2a26f9d0e554', 'humidity', @plot2_id, 'offline'
WHERE NOT EXISTS (SELECT 1 FROM device WHERE device_code = 'P002-MOIST');
INSERT INTO device (device_code, device_uuid, device_type, plot_id, status)
SELECT 'P002-IRRIG', 'b0242636-5e56-4c0f-9b82-5a407e6e23ea', 'irrigation', @plot2_id, 'offline'
WHERE NOT EXISTS (SELECT 1 FROM device WHERE device_code = 'P002-IRRIG');

INSERT INTO threshold_config (
  plot_id, soil_moisture_threshold, irrigation_length, irrigation_interval, updated_by
)
VALUES (@plot2_id, 35.00, 60, 30, @admin_user_id)
ON DUPLICATE KEY UPDATE
  soil_moisture_threshold = VALUES(soil_moisture_threshold),
  irrigation_length = VALUES(irrigation_length),
  irrigation_interval = VALUES(irrigation_interval),
  updated_by = VALUES(updated_by);

INSERT INTO threshold_config (
  plot_id, soil_moisture_threshold, irrigation_length, irrigation_interval, updated_by
)
VALUES (@plot3_id, 35.00, 60, 30, @admin_user_id)
ON DUPLICATE KEY UPDATE
  soil_moisture_threshold = VALUES(soil_moisture_threshold),
  irrigation_length = VALUES(irrigation_length),
  irrigation_interval = VALUES(irrigation_interval),
  updated_by = VALUES(updated_by);

INSERT INTO threshold_config (
  plot_id, soil_moisture_threshold, irrigation_length, irrigation_interval, updated_by
)
VALUES (@plot_id, 35.00, 60, 30, @admin_user_id)
ON DUPLICATE KEY UPDATE
  soil_moisture_threshold = VALUES(soil_moisture_threshold),
  irrigation_length = VALUES(irrigation_length),
  irrigation_interval = VALUES(irrigation_interval),
  updated_by = VALUES(updated_by);

INSERT INTO plot_report (
  plot_id, soil_moisture_device_id, temperature_device_id,
  plot_moisture, temperature, report_datetime
)
-- DATETIME values in the project are UTC.
SELECT @plot_id, @humidity_device_id, @temperature_device_id,
       62.50, 25.60, '2026-08-24 00:00:00'
WHERE NOT EXISTS (
  SELECT 1 FROM plot_report
  WHERE plot_id = @plot_id AND report_datetime = '2026-08-24 00:00:00'
);

COMMIT;
