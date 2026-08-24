USE smart_agriculture;

-- 1.用户表
INSERT IGNORE INTO users
    (user_id, username, password_hash, email, phone, user_status)
VALUES
    (1, 'admin', '$2b$10$N9qo8uLOickGXa2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhW', 'admin@example.com', '13800000001', 'ACTIVE'),
    (2, 'farm_manager', '$2b$10$N9qo8uLOickGXa2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhW', 'manager@example.com', '13800000002', 'ACTIVE'),
    (3, 'farmer', '$2b$10$N9qo8uLOickGXa2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhW', 'farmer@example.com', '13800000003', 'ACTIVE'),
    (4, 'viewer', '$2b$10$N9qo8uLOickGXa2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhW', 'viewer@example.com', NULL, 'ACTIVE');



-- 2. 角色表
INSERT IGNORE INTO roles
    (role_id, role_code, scope_type)
VALUES
    (1, 'SYSTEM_ADMIN', 'SYSTEM'),
    (2, 'FARM_MANAGER', 'FARM'),
    (3, 'FARMER', 'PLOT'),
    (4, 'VIEWER', 'FARM');



-- 4. 权限定义表
INSERT IGNORE INTO permissions
    (permission_id, permission_code, resource_type, action_type)
VALUES
    (1, 'FARM_VIEW', 'FARM', 'VIEW'),
    (2, 'FARM_MANAGE', 'FARM', 'MANAGE'),
    (3, 'PLOT_VIEW', 'PLOT', 'VIEW'),
    (4, 'PLOT_MANAGE', 'PLOT', 'MANAGE'),
    (5, 'DEVICE_VIEW', 'DEVICE', 'VIEW'),
    (6, 'DEVICE_CONTROL', 'DEVICE', 'CONTROL'),
    (7, 'THRESHOLD_CONFIG_MANAGE', 'THRESHOLD_CONFIG', 'MANAGE'),
    (8, 'REPORT_VIEW', 'REPORT', 'VIEW'),
    (9, 'IRRIGATION_CONTROL', 'IRRIGATION', 'CONTROL'),
    (10, 'ALERT_MANAGE', 'ALERT', 'MANAGE'),
    (11, 'USER_MANAGE', 'USER', 'MANAGE'),
    (12, 'SYSTEM_MANAGE', 'SYSTEM', 'MANAGE');



-- 3. 用户-角色中间表
INSERT IGNORE INTO user_roles (user_id, role_id, status)
VALUES
    (1, 1, 'ACTIVE'),
    (2, 2, 'ACTIVE'),
    (3, 3, 'ACTIVE'),
    (4, 4, 'ACTIVE');



-- 5. 角色—权限关联表
INSERT IGNORE INTO role_permission_rel (role_id, permission_id)
VALUES
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
    (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12),
    (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),
    (2, 7), (2, 8), (2, 9), (2, 10),
    (3, 3), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9),
    (4, 1), (4, 3), (4, 5), (4, 8);