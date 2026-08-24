USE smart_agriculture;


-- 6. 农场表
INSERT IGNORE INTO farms
    (farm_id, admin_user_id, farm_name, city, address)
VALUES
    (1, 2, '绿野示范农场', '北京市', '北京市顺义区农业科技园 1 号'),
    (2, 2, '清源实验农场', '上海市', '上海市崇明区东滩现代农业园 2 号');



-- 7. 地块表
INSERT IGNORE INTO plots
    (plot_id, farmer_user_id, farm_id, plot_name, location, crop_name, description)
VALUES
    (1, 3, 1, '一号温室', '绿野农场东区', '番茄', '温室种植区，配备自动灌溉'),
    (2, 3, 1, '二号温室', '绿野农场西区', '黄瓜', '温室种植区'),
    (3, NULL, 2, '露天试验田', '清源农场北区', '水稻', '用于环境监测演示');