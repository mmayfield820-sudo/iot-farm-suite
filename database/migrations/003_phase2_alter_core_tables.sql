-- Stage 1: extend the four existing core tables without deleting history.
SET NAMES utf8mb4;

ALTER TABLE users
  ADD COLUMN employee_no VARCHAR(50) NULL AFTER phone,
  ADD COLUMN activation_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' AFTER employee_no,
  ADD COLUMN activation_token_hash VARCHAR(255) NULL AFTER activation_status,
  ADD COLUMN activated_at DATETIME(6) NULL AFTER activation_token_hash,
  ADD UNIQUE KEY uq_users_employee_no (employee_no),
  ADD CONSTRAINT chk_users_activation_status
    CHECK (activation_status IN ('PENDING', 'ACTIVATED', 'DISABLED'));

ALTER TABLE farm
  ADD COLUMN province VARCHAR(50) NULL AFTER farm_name,
  ADD COLUMN area_mu DECIMAL(10,2) NULL AFTER address,
  ADD COLUMN farm_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' AFTER area_mu,
  ADD COLUMN remark VARCHAR(255) NULL AFTER farm_status,
  ADD CONSTRAINT chk_farm_area CHECK (area_mu IS NULL OR area_mu >= 0),
  ADD CONSTRAINT chk_farm_status CHECK (farm_status IN ('ACTIVE', 'INACTIVE'));

ALTER TABLE plot
  ADD COLUMN plot_code VARCHAR(50) NULL AFTER farm_id,
  ADD COLUMN area_mu DECIMAL(10,2) NULL AFTER description,
  ADD COLUMN irrigation_method VARCHAR(50) NULL AFTER area_mu,
  ADD COLUMN plot_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' AFTER irrigation_method,
  ADD COLUMN template_id BIGINT NULL AFTER plot_status,
  ADD COLUMN planting_date DATE NULL AFTER template_id,
  ADD COLUMN soil_type VARCHAR(50) NULL AFTER planting_date,
  ADD COLUMN planting_remark VARCHAR(255) NULL AFTER soil_type,
  ADD COLUMN stage_override_code VARCHAR(50) NULL AFTER planting_remark,
  ADD COLUMN stage_override_reason VARCHAR(255) NULL AFTER stage_override_code,
  ADD COLUMN stage_override_by BIGINT NULL AFTER stage_override_reason,
  ADD COLUMN stage_override_at DATETIME(6) NULL AFTER stage_override_by,
  ADD UNIQUE KEY uq_plot_code (plot_code),
  ADD KEY idx_plot_template (template_id),
  ADD KEY idx_plot_stage_override_by (stage_override_by),
  ADD CONSTRAINT fk_plot_stage_override_by FOREIGN KEY (stage_override_by) REFERENCES users (user_id),
  ADD CONSTRAINT chk_plot_area CHECK (area_mu IS NULL OR area_mu >= 0),
  ADD CONSTRAINT chk_plot_status CHECK (plot_status IN ('ACTIVE', 'INACTIVE'));

ALTER TABLE alert
  DROP CHECK chk_alert_type,
  ADD COLUMN related_task_id BIGINT NULL AFTER handled_at,
  ADD COLUMN resolution_action VARCHAR(30) NULL AFTER related_task_id,
  ADD COLUMN resolution_remark VARCHAR(255) NULL AFTER resolution_action,
  ADD KEY idx_alert_related_task (related_task_id),
  ADD CONSTRAINT chk_alert_type
    CHECK (alert_type IN ('low_moisture', 'device_offline', 'device_fault', 'irrigation_failed', 'plan_adjustment', 'continuous_rain')),
  ADD CONSTRAINT chk_alert_resolution_action
    CHECK (resolution_action IS NULL OR resolution_action IN ('ADJUST', 'KEEP_PLAN', 'HANDLED', 'ROLLED_BACK'));
