-- MySQL 8.0 schema for the smart agriculture platform.
-- All timestamps use UTC. The database is selected by Docker or mysql client.
SET NAMES utf8mb4;

CREATE TABLE users (
  user_id BIGINT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  real_name VARCHAR(50) NULL,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(100) NULL,
  phone VARCHAR(20) NULL,
  user_status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_users_username (username),
  UNIQUE KEY uq_users_email (email),
  CONSTRAINT chk_users_status CHECK (user_status IN ('active', 'disabled'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE roles (
  role_id BIGINT NOT NULL AUTO_INCREMENT,
  role_code VARCHAR(50) NOT NULL,
  scope_type VARCHAR(20) NOT NULL,
  PRIMARY KEY (role_id),
  UNIQUE KEY uq_roles_code (role_code),
  CONSTRAINT chk_roles_scope CHECK (scope_type IN ('system', 'farm', 'plot'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE permissions (
  permission_id BIGINT NOT NULL AUTO_INCREMENT,
  permission_code VARCHAR(80) NOT NULL,
  resource_type VARCHAR(30) NOT NULL,
  action_type VARCHAR(30) NOT NULL,
  PRIMARY KEY (permission_id),
  UNIQUE KEY uq_permissions_code (permission_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE user_role_rel (
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  PRIMARY KEY (user_id, role_id),
  CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES users (user_id),
  CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES roles (role_id),
  CONSTRAINT chk_user_role_status CHECK (status IN ('active', 'disabled'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE role_permission_rel (
  role_id BIGINT NOT NULL,
  permission_id BIGINT NOT NULL,
  PRIMARY KEY (role_id, permission_id),
  CONSTRAINT fk_role_permission_role FOREIGN KEY (role_id) REFERENCES roles (role_id),
  CONSTRAINT fk_role_permission_permission FOREIGN KEY (permission_id) REFERENCES permissions (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- One farm has at most one administrator, represented by admin_user_id.
CREATE TABLE farm (
  farm_id BIGINT NOT NULL AUTO_INCREMENT,
  admin_user_id BIGINT NULL,
  farm_name VARCHAR(100) NOT NULL,
  city VARCHAR(50) NULL,
  address VARCHAR(255) NULL,
  PRIMARY KEY (farm_id),
  KEY idx_farm_admin_user (admin_user_id),
  CONSTRAINT fk_farm_admin FOREIGN KEY (admin_user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- One plot has at most one farmer, represented by farmer_user_id.
CREATE TABLE plot (
  plot_id BIGINT NOT NULL AUTO_INCREMENT,
  farmer_user_id BIGINT NULL,
  farm_id BIGINT NOT NULL,
  plot_name VARCHAR(100) NOT NULL,
  location VARCHAR(255) NULL,
  crop_name VARCHAR(50) NULL,
  description VARCHAR(255) NULL,
  PRIMARY KEY (plot_id),
  UNIQUE KEY uq_plot_farm_name (farm_id, plot_name),
  KEY idx_plot_farmer_user (farmer_user_id),
  CONSTRAINT fk_plot_farmer FOREIGN KEY (farmer_user_id) REFERENCES users (user_id),
  CONSTRAINT fk_plot_farm FOREIGN KEY (farm_id) REFERENCES farm (farm_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE device (
  device_id BIGINT NOT NULL AUTO_INCREMENT,
  device_code VARCHAR(100) NOT NULL,
  device_uuid CHAR(36) NOT NULL,
  device_type VARCHAR(30) NOT NULL,
  plot_id BIGINT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'offline',
  work_status VARCHAR(20) NOT NULL DEFAULT 'stopped',
  last_heartbeat DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (device_id),
  UNIQUE KEY uq_device_code (device_code),
  UNIQUE KEY uq_device_uuid (device_uuid),
  UNIQUE KEY uq_device_plot_type (plot_id, device_type),
  UNIQUE KEY uq_device_id_plot (device_id, plot_id),
  CONSTRAINT fk_device_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id),
  CONSTRAINT chk_device_type CHECK (device_type IN ('temperature', 'humidity', 'irrigation')),
  CONSTRAINT chk_device_status CHECK (status IN ('online', 'offline')),
  CONSTRAINT chk_device_work_status CHECK (work_status IN ('running', 'stopped'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE threshold_config (
  config_id BIGINT NOT NULL AUTO_INCREMENT,
  plot_id BIGINT NOT NULL,
  soil_moisture_threshold DECIMAL(5,2) NOT NULL,
  irrigation_length INT NOT NULL DEFAULT 0,
  irrigation_interval INT NOT NULL DEFAULT 0,
  updated_by BIGINT NULL,
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (config_id),
  UNIQUE KEY uq_threshold_plot (plot_id),
  KEY idx_threshold_updated_by (updated_by),
  CONSTRAINT fk_threshold_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id),
  CONSTRAINT fk_threshold_user FOREIGN KEY (updated_by) REFERENCES users (user_id),
  CONSTRAINT chk_threshold_moisture CHECK (soil_moisture_threshold BETWEEN 0 AND 100),
  CONSTRAINT chk_threshold_length CHECK (irrigation_length >= 0),
  CONSTRAINT chk_threshold_interval CHECK (irrigation_interval >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- A report is a complete plot snapshot; both sensors and values are mandatory.
CREATE TABLE plot_report (
  report_id BIGINT NOT NULL AUTO_INCREMENT,
  plot_id BIGINT NOT NULL,
  soil_moisture_device_id BIGINT NOT NULL,
  temperature_device_id BIGINT NOT NULL,
  plot_moisture DECIMAL(5,2) NOT NULL,
  temperature DECIMAL(5,2) NOT NULL,
  report_datetime DATETIME(6) NOT NULL,
  PRIMARY KEY (report_id),
  KEY idx_report_plot_datetime (plot_id, report_datetime),
  CONSTRAINT fk_report_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id),
  CONSTRAINT fk_report_moisture_device FOREIGN KEY (soil_moisture_device_id, plot_id)
    REFERENCES device (device_id, plot_id),
  CONSTRAINT fk_report_temperature_device FOREIGN KEY (temperature_device_id, plot_id)
    REFERENCES device (device_id, plot_id),
  CONSTRAINT chk_report_moisture CHECK (plot_moisture BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE irrigation_record (
  record_id BIGINT NOT NULL AUTO_INCREMENT,
  command_id VARCHAR(64) NULL,
  plot_id BIGINT NOT NULL,
  device_id BIGINT NOT NULL,
  action_type VARCHAR(10) NOT NULL,
  activation_type VARCHAR(10) NOT NULL,
  operator_id BIGINT NULL,
  planned_duration_minutes INT NULL,
  requested_at DATETIME(6) NOT NULL,
  executed_at DATETIME(6) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  PRIMARY KEY (record_id),
  UNIQUE KEY uq_irrigation_command_id (command_id),
  KEY idx_irrigation_plot_requested (plot_id, requested_at),
  KEY idx_irrigation_operator (operator_id),
  CONSTRAINT fk_irrigation_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id),
  CONSTRAINT fk_irrigation_device FOREIGN KEY (device_id, plot_id)
    REFERENCES device (device_id, plot_id),
  CONSTRAINT fk_irrigation_operator FOREIGN KEY (operator_id) REFERENCES users (user_id),
  CONSTRAINT chk_irrigation_action CHECK (action_type IN ('on', 'off')),
  CONSTRAINT chk_irrigation_activation CHECK (activation_type IN ('manual', 'auto')),
  CONSTRAINT chk_irrigation_planned_duration CHECK (planned_duration_minutes IS NULL OR planned_duration_minutes BETWEEN 1 AND 240),
  CONSTRAINT chk_irrigation_status CHECK (status IN ('pending', 'success', 'failed', 'timeout'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE alert (
  alert_id BIGINT NOT NULL AUTO_INCREMENT,
  plot_id BIGINT NOT NULL,
  device_id BIGINT NULL,
  alert_type VARCHAR(30) NOT NULL,
  alert_description VARCHAR(255) NOT NULL,
  alert_value DECIMAL(10,2) NULL,
  alert_threshold DECIMAL(10,2) NULL,
  alert_datetime DATETIME(6) NOT NULL,
  alert_status VARCHAR(20) NOT NULL DEFAULT 'active',
  handled_by BIGINT NULL,
  handled_at DATETIME(6) NULL,
  PRIMARY KEY (alert_id),
  KEY idx_alert_plot_datetime (plot_id, alert_datetime),
  KEY idx_alert_status (alert_status),
  KEY idx_alert_handler (handled_by),
  CONSTRAINT fk_alert_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id),
  CONSTRAINT fk_alert_device FOREIGN KEY (device_id, plot_id)
    REFERENCES device (device_id, plot_id),
  CONSTRAINT fk_alert_handler FOREIGN KEY (handled_by) REFERENCES users (user_id),
  CONSTRAINT chk_alert_type CHECK (alert_type IN ('low_moisture', 'device_offline', 'device_fault', 'irrigation_failed')),
  CONSTRAINT chk_alert_status CHECK (alert_status IN ('active', 'acknowledged', 'recovered'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE mqtt_telemetry_message (
  device_id BIGINT NOT NULL,
  message_id VARCHAR(100) NOT NULL,
  received_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (device_id, message_id),
  CONSTRAINT fk_mqtt_telemetry_device FOREIGN KEY (device_id) REFERENCES device (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE farm_admin_scope (
  user_id BIGINT NOT NULL,
  farm_id BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id, farm_id),
  KEY idx_farm_admin_scope_farm (farm_id),
  CONSTRAINT fk_farm_admin_scope_user FOREIGN KEY (user_id) REFERENCES users (user_id),
  CONSTRAINT fk_farm_admin_scope_farm FOREIGN KEY (farm_id) REFERENCES farm (farm_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE farmer_plot_scope (
  user_id BIGINT NOT NULL,
  plot_id BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id, plot_id),
  KEY idx_farmer_plot_scope_plot (plot_id),
  CONSTRAINT fk_farmer_plot_scope_user FOREIGN KEY (user_id) REFERENCES users (user_id),
  CONSTRAINT fk_farmer_plot_scope_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE registration_application (
  application_id BIGINT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  real_name VARCHAR(50) NOT NULL,
  email VARCHAR(100) NULL,
  phone VARCHAR(20) NULL,
  role_codes JSON NOT NULL,
  farm_ids JSON NOT NULL,
  plot_ids JSON NOT NULL,
  application_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  reject_reason VARCHAR(255) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  reviewed_at DATETIME(6) NULL,
  reviewed_by BIGINT NULL,
  PRIMARY KEY (application_id),
  UNIQUE KEY uq_registration_application_username (username),
  KEY idx_registration_application_status (application_status),
  CONSTRAINT fk_registration_application_reviewer FOREIGN KEY (reviewed_by) REFERENCES users (user_id),
  CONSTRAINT chk_registration_application_status CHECK (application_status IN ('pending', 'approved', 'rejected'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
