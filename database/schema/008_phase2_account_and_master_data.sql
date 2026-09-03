-- Phase 2: pre-provisioned accounts, master data, and import staging.
-- Execute after 007_localize_demo_data.sql. All timestamps are UTC.
SET NAMES utf8mb4;

-- Existing active accounts remain usable. New accounts start as pending_activation.
ALTER TABLE users
  MODIFY username VARCHAR(50) NULL,
  MODIFY password_hash VARCHAR(255) NULL,
  ADD COLUMN employee_no VARCHAR(50) NULL AFTER username,
  ADD COLUMN activation_code_hash VARCHAR(255) NULL AFTER password_hash,
  ADD COLUMN activation_expires_at DATETIME(6) NULL AFTER activation_code_hash,
  ADD COLUMN activated_at DATETIME(6) NULL AFTER activation_expires_at;

ALTER TABLE users DROP CHECK chk_users_status;
ALTER TABLE users
  MODIFY user_status VARCHAR(20) NOT NULL DEFAULT 'active',
  ADD UNIQUE KEY uq_users_employee_no (employee_no),
  ADD CONSTRAINT chk_users_status
    CHECK (user_status IN ('pending_activation', 'active', 'disabled'));

-- The one-time token is stored separately from the administrator-issued code.
CREATE TABLE account_activation_token (
  activation_token_id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  token_hash CHAR(64) NOT NULL,
  expires_at DATETIME(6) NOT NULL,
  consumed_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (activation_token_id),
  UNIQUE KEY uq_activation_token_hash (token_hash),
  KEY idx_activation_token_user_expiry (user_id, expires_at),
  CONSTRAINT fk_activation_token_user FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Employee import is parsed and validated before any account is created.
CREATE TABLE user_import_job (
  import_job_id BIGINT NOT NULL AUTO_INCREMENT,
  original_filename VARCHAR(255) NOT NULL,
  job_status VARCHAR(20) NOT NULL DEFAULT 'validating',
  total_rows INT NOT NULL DEFAULT 0,
  valid_rows INT NOT NULL DEFAULT 0,
  invalid_rows INT NOT NULL DEFAULT 0,
  created_by BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  committed_by BIGINT NULL,
  committed_at DATETIME(6) NULL,
  PRIMARY KEY (import_job_id),
  KEY idx_user_import_job_status_created (job_status, created_at),
  CONSTRAINT fk_user_import_job_creator FOREIGN KEY (created_by) REFERENCES users (user_id),
  CONSTRAINT fk_user_import_job_committer FOREIGN KEY (committed_by) REFERENCES users (user_id),
  CONSTRAINT chk_user_import_job_status
    CHECK (job_status IN ('validating', 'ready', 'committed', 'failed')),
  CONSTRAINT chk_user_import_job_counts
    CHECK (total_rows >= 0 AND valid_rows >= 0 AND invalid_rows >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE user_import_row (
  import_row_id BIGINT NOT NULL AUTO_INCREMENT,
  import_job_id BIGINT NOT NULL,
  source_row_number INT NOT NULL,
  source_data JSON NOT NULL,
  validation_errors JSON NULL,
  row_status VARCHAR(20) NOT NULL DEFAULT 'valid',
  imported_user_id BIGINT NULL,
  PRIMARY KEY (import_row_id),
  UNIQUE KEY uq_user_import_row_number (import_job_id, source_row_number),
  KEY idx_user_import_row_status (import_job_id, row_status),
  CONSTRAINT fk_user_import_row_job FOREIGN KEY (import_job_id) REFERENCES user_import_job (import_job_id),
  CONSTRAINT fk_user_import_row_user FOREIGN KEY (imported_user_id) REFERENCES users (user_id),
  CONSTRAINT chk_user_import_row_number CHECK (source_row_number >= 2),
  CONSTRAINT chk_user_import_row_status
    CHECK (row_status IN ('valid', 'invalid', 'imported'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE farm
  ADD COLUMN province VARCHAR(50) NULL AFTER farm_name,
  ADD COLUMN area_mu DECIMAL(10,2) NULL AFTER address,
  ADD COLUMN manager_name VARCHAR(50) NULL AFTER area_mu,
  ADD COLUMN note VARCHAR(500) NULL AFTER manager_name,
  ADD COLUMN farm_status VARCHAR(20) NOT NULL DEFAULT 'active' AFTER note,
  ADD COLUMN created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) AFTER farm_status,
  ADD COLUMN updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6) AFTER created_at,
  ADD CONSTRAINT chk_farm_status CHECK (farm_status IN ('active', 'inactive')),
  ADD CONSTRAINT chk_farm_area_mu CHECK (area_mu IS NULL OR area_mu >= 0);

ALTER TABLE plot
  ADD COLUMN plot_code VARCHAR(50) NULL AFTER farm_id,
  ADD COLUMN area_mu DECIMAL(10,2) NULL AFTER plot_name,
  ADD COLUMN irrigation_method VARCHAR(20) NULL AFTER area_mu,
  ADD COLUMN plot_status VARCHAR(20) NOT NULL DEFAULT 'active' AFTER irrigation_method,
  ADD COLUMN created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) AFTER description,
  ADD COLUMN updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ON UPDATE CURRENT_TIMESTAMP(6) AFTER created_at;

-- Existing plots receive stable codes before the uniqueness constraint is added.
UPDATE plot
SET plot_code = CONCAT('P', LPAD(plot_id, 6, '0'))
WHERE plot_code IS NULL OR plot_code = '';

ALTER TABLE plot
  MODIFY plot_code VARCHAR(50) NOT NULL,
  ADD UNIQUE KEY uq_plot_code (plot_code),
  ADD CONSTRAINT chk_plot_status CHECK (plot_status IN ('active', 'inactive')),
  ADD CONSTRAINT chk_plot_area_mu CHECK (area_mu IS NULL OR area_mu >= 0),
  ADD CONSTRAINT chk_plot_irrigation_method
    CHECK (irrigation_method IS NULL OR irrigation_method IN ('drip', 'sprinkler', 'flood', 'manual', 'other'));

-- A farmer may be responsible for several plots; a plot has exactly one farmer.
ALTER TABLE farmer_plot_scope
  ADD UNIQUE KEY uq_farmer_plot_scope_plot (plot_id);
