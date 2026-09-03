-- Localize the development demo records without changing stable IDs or codes.
SET NAMES utf8mb4;

START TRANSACTION;

UPDATE users
SET real_name = CASE username
  WHEN 'demo_admin' THEN '张三'
  WHEN 'demo_farmer' THEN '李四'
  WHEN 'demo_system' THEN '王五'
  ELSE real_name
END
WHERE username IN ('demo_admin', 'demo_farmer', 'demo_system');

UPDATE farm AS f
JOIN users AS u ON u.user_id = f.admin_user_id
SET f.farm_name = '演示农场',
    f.city = '杭州市',
    f.address = '浙江省杭州市演示农业园'
WHERE u.username = 'demo_admin'
  AND f.farm_name IN ('Demo Farm', '演示农场');

UPDATE plot AS p
JOIN farm AS f ON f.farm_id = p.farm_id
JOIN users AS u ON u.user_id = f.admin_user_id
SET p.plot_name = '一号田地',
    p.location = '东区温室',
    p.crop_name = '番茄',
    p.description = '演示用一号田地'
WHERE u.username = 'demo_admin'
  AND p.plot_name IN ('Plot 1', '一号田地');

UPDATE plot AS p
JOIN farm AS f ON f.farm_id = p.farm_id
JOIN users AS u ON u.user_id = f.admin_user_id
SET p.plot_name = '二号田地',
    p.location = '西区温室',
    p.crop_name = '黄瓜',
    p.description = '演示用二号田地'
WHERE u.username = 'demo_admin'
  AND p.plot_name IN ('Plot 2', '二号田地');

UPDATE plot AS p
JOIN farm AS f ON f.farm_id = p.farm_id
JOIN users AS u ON u.user_id = f.admin_user_id
SET p.plot_name = '三号田地',
    p.location = '北区温室',
    p.crop_name = '生菜',
    p.description = '演示用三号田地'
WHERE u.username = 'demo_admin'
  AND p.plot_name IN ('Plot 3', '三号田地');

UPDATE alert
SET alert_description = CASE alert_type
  WHEN 'low_moisture' THEN '土壤湿度低于设定阈值'
  WHEN 'device_fault' THEN '缺少配对的传感器数据'
  WHEN 'irrigation_failed' THEN '灌溉指令执行超时'
  ELSE alert_description
END
WHERE alert_description IN (
  'Soil moisture is below the configured threshold',
  'Missing paired humidity reading',
  'Missing paired temperature reading'
)
   OR alert_description LIKE 'Irrigation command % timed out';

COMMIT;
