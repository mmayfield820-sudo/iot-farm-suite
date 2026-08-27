-- mysql建库

CREATE DATABASE IF NOT EXISTS smart_agriculture
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE smart_agriculture;


-- pk= primary key, 主键
-- uk= unique key, 唯一键
-- chk= check constraint, 检查约束


-- 1. 用户表
CREATE TABLE users (
    user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,    -- 加密之后的密码
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NULL,
    user_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_email UNIQUE (email),
    CONSTRAINT chk_users_status
        CHECK (user_status IN ('ACTIVE', 'DISABLED'))
) 
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COMMENT = '用户表';


-- 2. 角色表
CREATE TABLE roles (
    role_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    role_code VARCHAR(50) NOT NULL,
    scope_type VARCHAR(20) NOT NULL,

    CONSTRAINT pk_roles PRIMARY KEY (role_id),
    CONSTRAINT uk_roles_role_code UNIQUE (role_code),
    CONSTRAINT chk_roles_scope_type
        CHECK (scope_type IN ('SYSTEM', 'FARM', 'PLOT'))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '角色表';


-- 3. 用户-角色中间表
CREATE TABLE user_roles (
    user_id BIGINT UNSIGNED NOT NULL,
    role_id BIGINT UNSIGNED NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    CONSTRAINT pk_user_roles PRIMARY KEY (user_id, role_id),

    CONSTRAINT fk_user_roles_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_user_roles_role
        FOREIGN KEY (role_id)
        REFERENCES roles(role_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_user_roles_status
        CHECK (status IN ('ACTIVE', 'DISABLED'))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '用户-角色中间表';




-- 4. 权限定义表
CREATE TABLE permissions (
    permission_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    permission_code VARCHAR(80) NOT NULL,
    resource_type VARCHAR(30) NOT NULL,
    action_type VARCHAR(30) NOT NULL,

    CONSTRAINT pk_permissions PRIMARY KEY (permission_id),
    CONSTRAINT uk_permissions_code UNIQUE (permission_code),

    CONSTRAINT chk_permissions_resource_type
        CHECK (
            resource_type IN (
                'FARM', 'PLOT', 'DEVICE', 'THRESHOLD_CONFIG',
                'REPORT', 'IRRIGATION', 'ALERT', 'USER', 'SYSTEM'
            )
        ),

    CONSTRAINT chk_permissions_action_type
        CHECK (
            action_type IN (
                'VIEW', 'CREATE', 'UPDATE',
                'DELETE', 'CONTROL', 'MANAGE'
            )
        ),

    CONSTRAINT uk_permissions_resource_action
        UNIQUE (resource_type, action_type)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '权限定义表';





-- 5. 角色—权限关联表
CREATE TABLE role_permission_rel (
    role_id BIGINT UNSIGNED NOT NULL,
    permission_id BIGINT UNSIGNED NOT NULL,

    CONSTRAINT pk_role_permission_rel
        PRIMARY KEY (role_id, permission_id),

    CONSTRAINT fk_role_permission_role
        FOREIGN KEY (role_id)
        REFERENCES roles(role_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_role_permission_permission
        FOREIGN KEY (permission_id)
        REFERENCES permissions(permission_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '角色与权限关联表';




-- 6. 农场表
CREATE TABLE farms (
    farm_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    admin_user_id BIGINT UNSIGNED NULL,
    farm_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    address VARCHAR(255) NOT NULL,

    CONSTRAINT pk_farms PRIMARY KEY (farm_id),

    CONSTRAINT fk_farms_admin_user
        FOREIGN KEY (admin_user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT uk_farms_name_city
        UNIQUE (farm_name, city)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '农场表';



-- 7. 地块表
CREATE TABLE plots (
    plot_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    farmer_user_id BIGINT UNSIGNED NULL,
    farm_id BIGINT UNSIGNED NOT NULL,
    plot_name VARCHAR(100) NOT NULL,
    location VARCHAR(255) NOT NULL,
    crop_name VARCHAR(50) NOT NULL,
    description VARCHAR(255) NULL,

    CONSTRAINT pk_plots PRIMARY KEY (plot_id),

    CONSTRAINT fk_plots_farmer_user
        FOREIGN KEY (farmer_user_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_plots_farm
        FOREIGN KEY (farm_id)
        REFERENCES farms(farm_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uk_plots_farm_name
        UNIQUE (farm_id, plot_name)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '地块表';


-- 8. 设备表
CREATE TABLE devices (
    device_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    device_code VARCHAR(100) NOT NULL,
    device_type VARCHAR(30) NOT NULL,
    plot_id BIGINT UNSIGNED NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OFFLINE',
    last_heartbeat DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_devices PRIMARY KEY (device_id),

    CONSTRAINT uk_devices_code
        UNIQUE (device_code),

    -- 供后续 irrigation_record 的复合外键引用
    CONSTRAINT uk_devices_id_plot
        UNIQUE (device_id, plot_id),

    -- 每个地块每种设备最多一台
    CONSTRAINT uk_devices_plot_type
        UNIQUE (plot_id, device_type),

    CONSTRAINT fk_devices_plot
        FOREIGN KEY (plot_id)
        REFERENCES plots(plot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_devices_type
        CHECK (
            device_type IN (
                'SOIL_MOISTURE_SENSOR',
                'TEMPERATURE_SENSOR',
                'IRRIGATION_CONTROLLER'
            )
        ),

    CONSTRAINT chk_devices_status
        CHECK (status IN ('ONLINE', 'OFFLINE'))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '设备表';




-- 9. 地块阈值配置表
CREATE TABLE threshold_configs (
    config_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    plot_id BIGINT UNSIGNED NOT NULL,
    soil_moisture_threshold DECIMAL(5,2) NOT NULL,
    irrigation_length INT UNSIGNED NOT NULL DEFAULT 0,
    irrigation_interval INT UNSIGNED NOT NULL DEFAULT 0,
    updated_by BIGINT UNSIGNED NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT pk_threshold_configs PRIMARY KEY (config_id),

    -- 一个地块仅保留一份当前阈值配置
    CONSTRAINT uk_threshold_configs_plot
        UNIQUE (plot_id),

    CONSTRAINT fk_threshold_configs_plot
        FOREIGN KEY (plot_id)
        REFERENCES plots(plot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_threshold_configs_updated_by
        FOREIGN KEY (updated_by)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT chk_threshold_configs_moisture
        CHECK (
            soil_moisture_threshold >= 0.00
            AND soil_moisture_threshold <= 100.00
        )
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '地块阈值配置表';



-- 10. 地块监测报告表
CREATE TABLE plot_reports (
    report_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    plot_id BIGINT UNSIGNED NOT NULL,
    soil_moisture_device_id BIGINT UNSIGNED NOT NULL,
    temperature_device_id BIGINT UNSIGNED NOT NULL,
    plot_moisture DECIMAL(5,2) NOT NULL,
    temperature DECIMAL(5,2) NOT NULL,
    report_datetime DATETIME NOT NULL,

    CONSTRAINT pk_plot_reports PRIMARY KEY (report_id),

    CONSTRAINT fk_plot_reports_plot
        FOREIGN KEY (plot_id)
        REFERENCES plots(plot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- 保证湿度设备属于填写的地块
    CONSTRAINT fk_plot_reports_moisture_device
        FOREIGN KEY (soil_moisture_device_id, plot_id)
        REFERENCES devices(device_id, plot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- 保证温度设备属于填写的地块
    CONSTRAINT fk_plot_reports_temperature_device
        FOREIGN KEY (temperature_device_id, plot_id)
        REFERENCES devices(device_id, plot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT chk_plot_reports_moisture
        CHECK (
            plot_moisture >= 0.00
            AND plot_moisture <= 100.00
        )
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '地块温湿度监测报告表';



-- 11. 灌溉控制记录表
CREATE TABLE irrigation_records (
    record_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    plot_id BIGINT UNSIGNED NOT NULL,
    device_id BIGINT UNSIGNED NOT NULL,
    action_type VARCHAR(10) NOT NULL,
    activation_type VARCHAR(10) NOT NULL,
    operator_id BIGINT UNSIGNED NULL,
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    executed_at DATETIME NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',

    CONSTRAINT pk_irrigation_records PRIMARY KEY (record_id),

    CONSTRAINT fk_irrigation_records_plot
        FOREIGN KEY (plot_id)
        REFERENCES plots(plot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- 保证灌溉设备属于目标地块
    CONSTRAINT fk_irrigation_records_device_plot
        FOREIGN KEY (device_id, plot_id)
        REFERENCES devices(device_id, plot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_irrigation_records_operator
        FOREIGN KEY (operator_id)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT chk_irrigation_records_action
        CHECK (action_type IN ('ON', 'OFF')),

    CONSTRAINT chk_irrigation_records_activation
        CHECK (activation_type IN ('MANUAL', 'AUTO')),

    CONSTRAINT chk_irrigation_records_status
        CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED', 'TIMEOUT'))
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '灌溉控制指令与执行记录表';




-- 12. 告警表
CREATE TABLE alerts (
    alert_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    plot_id BIGINT UNSIGNED NOT NULL,
    device_id BIGINT UNSIGNED NULL,
    alert_type VARCHAR(30) NOT NULL,
    alert_description VARCHAR(255) NOT NULL,
    alert_value DECIMAL(10,2) NULL,
    alert_threshold DECIMAL(10,2) NULL,
    alert_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    alert_status VARCHAR(20) NOT NULL DEFAULT 'UNHANDLED',
    handled_by BIGINT UNSIGNED NULL,
    handled_at DATETIME NULL,

    CONSTRAINT pk_alerts PRIMARY KEY (alert_id),

    CONSTRAINT fk_alerts_plot
        FOREIGN KEY (plot_id)
        REFERENCES plots(plot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- 设备不为空时，保证其属于该告警地块
    CONSTRAINT fk_alerts_device_plot
        FOREIGN KEY (device_id, plot_id)
        REFERENCES devices(device_id, plot_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_alerts_handled_by
        FOREIGN KEY (handled_by)
        REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT chk_alerts_type
        CHECK (
            alert_type IN (
                'LOW_MOISTURE',
                'DEVICE_OFFLINE',
                'DEVICE_FAULT',
                'IRRIGATION_FAILED'
            )
        ),

    CONSTRAINT chk_alerts_status
        CHECK (
            alert_status IN (
                'UNHANDLED',
                'HANDLING',
                'HANDLED'
            )
        )
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COMMENT = '告警表';








