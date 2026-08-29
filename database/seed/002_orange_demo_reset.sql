-- 橙心如意本地演示数据。仅用于开发环境，可重复执行。
-- 目标：3 个演示账号、2 个橙园、4 个农户地块、前三个地块绑定真实鸿蒙模拟器 UUID。
SET NAMES utf8mb4;
START TRANSACTION;

SET @admin_user_id = (SELECT user_id FROM users WHERE username = 'demo_admin' LIMIT 1);
SET @farmer_user_id = (SELECT user_id FROM users WHERE username = 'demo_farmer' LIMIT 1);
SET @system_user_id = (SELECT user_id FROM users WHERE username = 'demo_system' LIMIT 1);

-- 清理业务数据和授权关系，保留数据库结构、角色与权限定义。
DELETE FROM mqtt_telemetry_message;
DELETE FROM alert;
DELETE FROM irrigation_record;
DELETE FROM plot_report;
DELETE FROM threshold_config;
DELETE FROM registration_application;
DELETE FROM farm_admin_scope;
DELETE FROM farmer_plot_scope;
DELETE FROM device;
DELETE FROM plot;
DELETE FROM farm;
DELETE FROM user_role_rel;
DELETE FROM users WHERE username NOT IN ('demo_admin', 'demo_farmer', 'demo_system');

ALTER TABLE farm AUTO_INCREMENT = 1;
ALTER TABLE plot AUTO_INCREMENT = 1;
ALTER TABLE device AUTO_INCREMENT = 1;
ALTER TABLE threshold_config AUTO_INCREMENT = 1;
ALTER TABLE plot_report AUTO_INCREMENT = 1;
ALTER TABLE irrigation_record AUTO_INCREMENT = 1;
ALTER TABLE alert AUTO_INCREMENT = 1;
ALTER TABLE registration_application AUTO_INCREMENT = 1;

UPDATE users SET real_name = '张园长', email = 'orchard-admin@example.invalid', phone = '13800000001', user_status = 'active' WHERE user_id = @admin_user_id;
UPDATE users SET real_name = '李果农', email = 'orange-farmer@example.invalid', phone = '13800000002', user_status = 'active' WHERE user_id = @farmer_user_id;
UPDATE users SET real_name = '王管理员', email = 'system-admin@example.invalid', phone = '13800000003', user_status = 'active' WHERE user_id = @system_user_id;

INSERT INTO user_role_rel (user_id, role_id, status)
SELECT @admin_user_id, role_id, 'active' FROM roles WHERE role_code = 'farm_admin';
INSERT INTO user_role_rel (user_id, role_id, status)
SELECT @farmer_user_id, role_id, 'active' FROM roles WHERE role_code = 'farmer';
INSERT INTO user_role_rel (user_id, role_id, status)
SELECT @system_user_id, role_id, 'active' FROM roles WHERE role_code = 'system_admin';

INSERT INTO farm (admin_user_id, farm_name, city, address) VALUES
  (@admin_user_id, '奉节县朱衣橙园', '重庆市奉节县', '重庆市奉节县朱衣镇砚瓦村'),
  (@admin_user_id, '奉节县安坪橙园', '重庆市奉节县', '重庆市奉节县安坪镇三沱村');
SET @farm1_id = 1;
SET @farm2_id = 2;

INSERT INTO plot (farmer_user_id, farm_id, plot_name, location, crop_name, description) VALUES
  (@farmer_user_id, @farm1_id, '朱衣一号果园', '朱衣镇东坡 A 区', '奉园72-1脐橙', '果实膨大期'),
  (@farmer_user_id, @farm1_id, '朱衣二号果园', '朱衣镇河谷 B 区', '奉园91脐橙', '果实转色期'),
  (@farmer_user_id, @farm1_id, '朱衣晚熟果园', '朱衣镇南坡 C 区', '奉节晚橙', '秋梢生长期'),
  (@farmer_user_id, @farm2_id, '安坪红翠果园', '安坪镇临江 D 区', '红翠2号', '幼树整形期');
SET @plot1_id = 1;
SET @plot2_id = 2;
SET @plot3_id = 3;
SET @plot4_id = 4;

INSERT INTO farm_admin_scope (user_id, farm_id) VALUES
  (@admin_user_id, @farm1_id), (@admin_user_id, @farm2_id);
INSERT INTO farmer_plot_scope (user_id, plot_id) VALUES
  (@farmer_user_id, @plot1_id), (@farmer_user_id, @plot2_id),
  (@farmer_user_id, @plot3_id), (@farmer_user_id, @plot4_id);

-- UUID 与当前鸿蒙模拟器一致；第四地块暂不绑定虚构设备。
INSERT INTO device (device_code, device_uuid, device_type, plot_id, status) VALUES
  ('P001-TEMP',  '3b8dcefd-3a51-4adc-b452-47c184c0951d', 'temperature', @plot1_id, 'offline'),
  ('P001-MOIST', '814621f7-2561-49ad-9766-72d3fcd18d86', 'humidity',    @plot1_id, 'offline'),
  ('P001-IRRIG', '435106ba-01e7-4745-9646-3907d15b28df', 'irrigation', @plot1_id, 'offline'),
  ('P002-TEMP',  '77448f68-baa9-46f1-b380-d835d4e2dda6', 'temperature', @plot2_id, 'offline'),
  ('P002-MOIST', '8e52cfa5-9106-45c2-8645-2a26f9d0e554', 'humidity',    @plot2_id, 'offline'),
  ('P002-IRRIG', 'b0242636-5e56-4c0f-9b82-5a407e6e23ea', 'irrigation', @plot2_id, 'offline'),
  ('P003-TEMP',  '4ae3704f-4ef1-42f2-9301-4af74fcf6454', 'temperature', @plot3_id, 'offline'),
  ('P003-MOIST', 'ff8706d0-2058-48fa-aa90-b95a4f61553c', 'humidity',    @plot3_id, 'offline'),
  ('P003-IRRIG', '1b8a4d7c-5e9c-4788-b8d1-3c02b0505664', 'irrigation', @plot3_id, 'offline');

SET @p1_temp = (SELECT device_id FROM device WHERE device_code = 'P001-TEMP');
SET @p1_moist = (SELECT device_id FROM device WHERE device_code = 'P001-MOIST');
SET @p1_irrig = (SELECT device_id FROM device WHERE device_code = 'P001-IRRIG');
SET @p2_temp = (SELECT device_id FROM device WHERE device_code = 'P002-TEMP');
SET @p2_moist = (SELECT device_id FROM device WHERE device_code = 'P002-MOIST');
SET @p2_irrig = (SELECT device_id FROM device WHERE device_code = 'P002-IRRIG');
SET @p3_temp = (SELECT device_id FROM device WHERE device_code = 'P003-TEMP');
SET @p3_moist = (SELECT device_id FROM device WHERE device_code = 'P003-MOIST');
SET @p3_irrig = (SELECT device_id FROM device WHERE device_code = 'P003-IRRIG');

INSERT INTO threshold_config (plot_id, soil_moisture_threshold, irrigation_length, irrigation_interval, updated_by) VALUES
  (@plot1_id, 35.00, 25, 90, @admin_user_id),
  (@plot2_id, 35.00, 20, 90, @admin_user_id),
  (@plot3_id, 35.00, 20, 120, @admin_user_id),
  (@plot4_id, 40.00, 15, 120, @admin_user_id);

-- 12 条趋势数据，便于核对，同时不会形成过长的演示历史。
INSERT INTO plot_report (plot_id, soil_moisture_device_id, temperature_device_id, plot_moisture, temperature, report_datetime) VALUES
  (@plot1_id,@p1_moist,@p1_temp,48.20,24.60,UTC_TIMESTAMP(6)-INTERVAL 12 HOUR),
  (@plot1_id,@p1_moist,@p1_temp,45.80,25.30,UTC_TIMESTAMP(6)-INTERVAL 8 HOUR),
  (@plot1_id,@p1_moist,@p1_temp,43.60,26.10,UTC_TIMESTAMP(6)-INTERVAL 4 HOUR),
  (@plot1_id,@p1_moist,@p1_temp,46.40,25.70,UTC_TIMESTAMP(6)-INTERVAL 10 MINUTE),
  (@plot2_id,@p2_moist,@p2_temp,44.10,23.90,UTC_TIMESTAMP(6)-INTERVAL 12 HOUR),
  (@plot2_id,@p2_moist,@p2_temp,41.70,24.80,UTC_TIMESTAMP(6)-INTERVAL 8 HOUR),
  (@plot2_id,@p2_moist,@p2_temp,39.60,25.60,UTC_TIMESTAMP(6)-INTERVAL 4 HOUR),
  (@plot2_id,@p2_moist,@p2_temp,42.30,25.10,UTC_TIMESTAMP(6)-INTERVAL 9 MINUTE),
  (@plot3_id,@p3_moist,@p3_temp,41.30,22.80,UTC_TIMESTAMP(6)-INTERVAL 12 HOUR),
  (@plot3_id,@p3_moist,@p3_temp,39.90,23.70,UTC_TIMESTAMP(6)-INTERVAL 8 HOUR),
  (@plot3_id,@p3_moist,@p3_temp,37.50,24.50,UTC_TIMESTAMP(6)-INTERVAL 4 HOUR),
  (@plot3_id,@p3_moist,@p3_temp,40.60,24.20,UTC_TIMESTAMP(6)-INTERVAL 8 MINUTE);

INSERT INTO irrigation_record (command_id, plot_id, device_id, action_type, activation_type, operator_id, requested_at, executed_at, status) VALUES
  ('ORANGE-DEMO-001',@plot1_id,@p1_irrig,'on','manual',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 11 HOUR,UTC_TIMESTAMP(6)-INTERVAL 11 HOUR+INTERVAL 5 SECOND,'success'),
  ('ORANGE-DEMO-002',@plot1_id,@p1_irrig,'off','manual',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 10 HOUR,UTC_TIMESTAMP(6)-INTERVAL 10 HOUR+INTERVAL 5 SECOND,'success'),
  ('ORANGE-DEMO-003',@plot2_id,@p2_irrig,'on','auto',@admin_user_id,UTC_TIMESTAMP(6)-INTERVAL 9 HOUR,UTC_TIMESTAMP(6)-INTERVAL 9 HOUR+INTERVAL 4 SECOND,'success'),
  ('ORANGE-DEMO-004',@plot2_id,@p2_irrig,'off','auto',@admin_user_id,UTC_TIMESTAMP(6)-INTERVAL 8 HOUR,UTC_TIMESTAMP(6)-INTERVAL 8 HOUR+INTERVAL 4 SECOND,'success'),
  ('ORANGE-DEMO-005',@plot3_id,@p3_irrig,'on','manual',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 7 HOUR,UTC_TIMESTAMP(6)-INTERVAL 7 HOUR+INTERVAL 6 SECOND,'success'),
  ('ORANGE-DEMO-006',@plot3_id,@p3_irrig,'off','manual',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 6 HOUR,UTC_TIMESTAMP(6)-INTERVAL 6 HOUR+INTERVAL 6 SECOND,'success'),
  ('ORANGE-DEMO-007',@plot1_id,@p1_irrig,'on','manual',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 5 HOUR,UTC_TIMESTAMP(6)-INTERVAL 5 HOUR+INTERVAL 5 SECOND,'success'),
  ('ORANGE-DEMO-008',@plot1_id,@p1_irrig,'off','manual',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 4 HOUR,UTC_TIMESTAMP(6)-INTERVAL 4 HOUR+INTERVAL 5 SECOND,'success'),
  ('ORANGE-DEMO-009',@plot2_id,@p2_irrig,'on','manual',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 3 HOUR,UTC_TIMESTAMP(6)-INTERVAL 3 HOUR+INTERVAL 5 SECOND,'success'),
  ('ORANGE-DEMO-010',@plot2_id,@p2_irrig,'off','manual',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 2 HOUR,UTC_TIMESTAMP(6)-INTERVAL 2 HOUR+INTERVAL 5 SECOND,'success');

INSERT INTO alert (plot_id, device_id, alert_type, alert_description, alert_value, alert_threshold, alert_datetime, alert_status, handled_by, handled_at) VALUES
  (@plot1_id,@p1_moist,'low_moisture','果实膨大期墒情低于目标阈值',39.20,42.00,UTC_TIMESTAMP(6)-INTERVAL 30 HOUR,'recovered',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 29 HOUR),
  (@plot2_id,@p2_moist,'low_moisture','果实转色期墒情短时偏低',37.80,40.00,UTC_TIMESTAMP(6)-INTERVAL 26 HOUR,'acknowledged',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 25 HOUR),
  (@plot3_id,@p3_irrig,'irrigation_failed','晚熟果园灌溉指令曾出现超时',NULL,NULL,UTC_TIMESTAMP(6)-INTERVAL 22 HOUR,'recovered',@admin_user_id,UTC_TIMESTAMP(6)-INTERVAL 21 HOUR),
  (@plot1_id,@p1_temp,'device_offline','东坡温度传感器短时离线',NULL,NULL,UTC_TIMESTAMP(6)-INTERVAL 18 HOUR,'recovered',@admin_user_id,UTC_TIMESTAMP(6)-INTERVAL 17 HOUR),
  (@plot2_id,@p2_moist,'device_fault','河谷湿度数据配对异常',NULL,NULL,UTC_TIMESTAMP(6)-INTERVAL 14 HOUR,'recovered',@admin_user_id,UTC_TIMESTAMP(6)-INTERVAL 13 HOUR),
  (@plot3_id,@p3_moist,'low_moisture','秋梢生长期墒情接近下限',37.50,38.00,UTC_TIMESTAMP(6)-INTERVAL 10 HOUR,'acknowledged',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 9 HOUR),
  (@plot1_id,@p1_irrig,'device_offline','灌溉控制器心跳延迟',NULL,NULL,UTC_TIMESTAMP(6)-INTERVAL 8 HOUR,'recovered',@admin_user_id,UTC_TIMESTAMP(6)-INTERVAL 7 HOUR),
  (@plot2_id,@p2_temp,'device_fault','温度数据出现短时波动',31.20,30.00,UTC_TIMESTAMP(6)-INTERVAL 6 HOUR,'acknowledged',@admin_user_id,UTC_TIMESTAMP(6)-INTERVAL 5 HOUR),
  (@plot3_id,@p3_moist,'device_offline','南坡湿度传感器通信中断',NULL,NULL,UTC_TIMESTAMP(6)-INTERVAL 4 HOUR,'recovered',@farmer_user_id,UTC_TIMESTAMP(6)-INTERVAL 3 HOUR),
  (@plot1_id,@p1_moist,'low_moisture','当前墒情接近果实膨大期下限',41.60,42.00,UTC_TIMESTAMP(6)-INTERVAL 1 HOUR,'active',NULL,NULL);

COMMIT;
