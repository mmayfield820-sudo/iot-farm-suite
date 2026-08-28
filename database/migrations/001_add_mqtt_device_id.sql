USE smart_agriculture;

ALTER TABLE devices
    ADD COLUMN mqtt_device_id VARCHAR(100) NULL AFTER device_code;

UPDATE devices
SET mqtt_device_id = CONCAT('device_', LPAD(device_id, 3, '0'))
WHERE mqtt_device_id IS NULL;

ALTER TABLE devices
    MODIFY COLUMN mqtt_device_id VARCHAR(100) NOT NULL,
    ADD CONSTRAINT uk_devices_mqtt_device_id UNIQUE (mqtt_device_id);