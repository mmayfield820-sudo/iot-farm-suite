-- Refine local demo names and profiles for the Fengjie navel orange showcase.
SET NAMES utf8mb4;

UPDATE users AS source_user
LEFT JOIN users AS target_user ON target_user.employee_no = 'E000004'
SET source_user.employee_no = 'E000004'
WHERE source_user.employee_no = 'TEST0902'
  AND target_user.user_id IS NULL;

UPDATE users
SET real_name = CASE employee_no
  WHEN 'E000001' THEN '林致远'
  WHEN 'E000002' THEN '陈明远'
  WHEN 'E000003' THEN '许文澜'
  WHEN 'E000004' THEN '周晓梅'
  ELSE real_name
END
WHERE employee_no IN ('E000001', 'E000002', 'E000003', 'E000004');

UPDATE farm
SET admin_user_id = (SELECT user_id FROM users WHERE employee_no = 'E000001'),
    farm_name = '奉节朱衣脐橙示范园',
    province = '重庆市',
    city = '奉节县',
    address = '重庆市奉节县朱衣镇双碾村脐橙产业园',
    area_mu = 126.50,
    manager_name = '林致远',
    note = '奉节脐橙标准化种植与智慧农业示范基地'
WHERE farm_id = 1;

UPDATE plot
SET farmer_user_id = (SELECT user_id FROM users WHERE employee_no = 'E000002'),
    plot_name = '东坡一号果园',
    area_mu = 42.50,
    location = '示范园东区缓坡梯田',
    crop_name = '脐橙',
    description = '东坡标准化脐橙种植区'
WHERE plot_id = 1;

UPDATE plot
SET farmer_user_id = (SELECT user_id FROM users WHERE employee_no = 'E000002'),
    plot_name = '河谷二号果园',
    area_mu = 38.00,
    location = '示范园西区临河台地',
    crop_name = '脐橙',
    description = '河谷水肥一体化脐橙种植区'
WHERE plot_id = 3;

UPDATE plot
SET farmer_user_id = (SELECT user_id FROM users WHERE employee_no = 'E000004'),
    plot_name = '高坡试验果园',
    area_mu = 46.00,
    location = '示范园北区高坡水肥试验区',
    crop_name = '脐橙',
    description = '高坡智慧水肥试验区'
WHERE plot_id = 4;
