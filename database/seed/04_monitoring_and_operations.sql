USE smart_agriculture;

-- 9. 地块阈值配置表
INSERT IGNORE INTO threshold_configs
    (config_id, plot_id, soil_moisture_threshold, irrigation_length, irrigation_interval, updated_by)
VALUES
    (1, 1, 35.00, 10, 60, 2),
    (2, 2, 40.00, 8, 90, 2),
    (3, 3, 30.00, 15, 120, 2);



-- 10. 地块监测报告表
INSERT IGNORE INTO plot_reports
    (report_id, plot_id, soil_moisture_device_id, temperature_device_id, plot_moisture, temperature, report_datetime)
VALUES
    (1, 1, 1, 2, 42.50, 26.80, '2026-08-24 09:00:00'),
    (2, 1, 1, 2, 38.20, 27.10, '2026-08-24 09:30:00'),
    (3, 2, 4, 5, 24.80, 29.40, '2026-08-24 09:30:00'),
    (4, 3, 7, 8, 56.00, 25.20, '2026-08-24 09:30:00');



-- 11. 灌溉控制记录表
INSERT IGNORE INTO irrigation_records
    (record_id, plot_id, device_id, action_type, activation_type, operator_id, requested_at, executed_at, status)
VALUES
    (1, 1, 3, 'ON', 'AUTO', NULL, '2026-08-24 09:31:00', '2026-08-24 09:31:03', 'SUCCESS'),
    (2, 1, 3, 'OFF', 'AUTO', NULL, '2026-08-24 09:41:00', '2026-08-24 09:41:02', 'SUCCESS'),
    (3, 2, 6, 'ON', 'MANUAL', 3, '2026-08-24 09:45:00', NULL, 'PENDING'),
    (4, 2, 6, 'OFF', 'AUTO', NULL, '2026-08-23 18:00:00', '2026-08-23 18:00:30', 'FAILED');



-- 12. 告警表
INSERT IGNORE INTO alerts
    (alert_id, plot_id, device_id, alert_type, alert_description, alert_value, alert_threshold, alert_datetime, alert_status, handled_by, handled_at)
VALUES
    (1, 2, 4, 'LOW_MOISTURE', '二号温室土壤湿度低于设定阈值', 24.80, 40.00, '2026-08-24 09:30:00', 'UNHANDLED', NULL, NULL),
    (2, 2, 4, 'DEVICE_OFFLINE', '土壤湿度传感器超过心跳时间', NULL, NULL, '2026-08-24 09:35:00', 'HANDLING', 2, NULL),
    (3, 2, 6, 'IRRIGATION_FAILED', '自动灌溉指令执行失败', NULL, NULL, '2026-08-23 18:00:30', 'HANDLED', 2, '2026-08-23 18:20:00');