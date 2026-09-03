-- Registration and multi-scope authorization.
-- This migration is additive: farm.admin_user_id and plot.farmer_user_id
-- continue to represent the original responsible user.
SET NAMES utf8mb4;

SET @has_real_name = (
  SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'users' AND column_name = 'real_name'
);
SET @sql = IF(@has_real_name = 0,
  'ALTER TABLE users ADD COLUMN real_name VARCHAR(50) NULL AFTER username',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS farm_admin_scope (
  user_id BIGINT NOT NULL,
  farm_id BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id, farm_id),
  KEY idx_farm_admin_scope_farm (farm_id),
  CONSTRAINT fk_farm_admin_scope_user FOREIGN KEY (user_id) REFERENCES users (user_id),
  CONSTRAINT fk_farm_admin_scope_farm FOREIGN KEY (farm_id) REFERENCES farm (farm_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS farmer_plot_scope (
  user_id BIGINT NOT NULL,
  plot_id BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id, plot_id),
  KEY idx_farmer_plot_scope_plot (plot_id),
  CONSTRAINT fk_farmer_plot_scope_user FOREIGN KEY (user_id) REFERENCES users (user_id),
  CONSTRAINT fk_farmer_plot_scope_plot FOREIGN KEY (plot_id) REFERENCES plot (plot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS registration_application (
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

-- Existing responsible users retain their access after the authorization
-- checks begin consulting the new scope tables.
INSERT IGNORE INTO farm_admin_scope (user_id, farm_id)
SELECT admin_user_id, farm_id FROM farm WHERE admin_user_id IS NOT NULL;

INSERT IGNORE INTO farmer_plot_scope (user_id, plot_id)
SELECT farmer_user_id, plot_id FROM plot WHERE farmer_user_id IS NOT NULL;

INSERT IGNORE INTO user_role_rel (user_id, role_id, status)
SELECT DISTINCT s.user_id, r.role_id, 'active'
FROM farm_admin_scope AS s
JOIN roles AS r ON r.role_code = 'farm_admin';

INSERT IGNORE INTO user_role_rel (user_id, role_id, status)
SELECT DISTINCT s.user_id, r.role_id, 'active'
FROM farmer_plot_scope AS s
JOIN roles AS r ON r.role_code = 'farmer';
