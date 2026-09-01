USE smart_agriculture;

UPDATE devices
SET mqtt_device_id = CONCAT('device_', LPAD(device_id, 3, '0'))
WHERE mqtt_device_id IS NULL;