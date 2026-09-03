-- Stage-based annual management workflow and independent production milestones.
SET NAMES utf8mb4;

ALTER TABLE farm_production_profile
  ADD COLUMN harvest_completed_at DATETIME(6) NULL AFTER tree_age_years;

ALTER TABLE plot
  ADD COLUMN production_date_offset_days SMALLINT NOT NULL DEFAULT 0
    COMMENT 'Date offset from the farm annual management plan';

ALTER TABLE management_plan
  ADD COLUMN production_year SMALLINT NULL AFTER template_version_id,
  ADD COLUMN stage_code VARCHAR(50) NULL AFTER production_year,
  ADD KEY idx_plan_plot_year_stage (plot_id, production_year, stage_code, plan_status);

CREATE TABLE farm_annual_stage_state (
  farm_id BIGINT NOT NULL,
  production_year SMALLINT NOT NULL,
  stage_code VARCHAR(50) NOT NULL,
  sort_order INT NOT NULL,
  planned_start_date DATE NOT NULL,
  planned_end_date DATE NOT NULL,
  stage_status VARCHAR(20) NOT NULL DEFAULT 'planned',
  actual_started_at DATETIME(6) NULL,
  completed_at DATETIME(6) NULL,
  started_by BIGINT NULL,
  locked_template_version_id BIGINT NULL,
  dispatched_template_version_id BIGINT NULL,
  dispatched_at DATETIME(6) NULL,
  non_dispatch_reason VARCHAR(500) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (farm_id, production_year, stage_code),
  UNIQUE KEY uq_farm_year_stage_order (farm_id, production_year, sort_order),
  KEY idx_farm_stage_status (farm_id, production_year, stage_status),
  CONSTRAINT chk_farm_stage_status CHECK (stage_status IN ('planned', 'active', 'completed', 'not_dispatched')),
  CONSTRAINT chk_farm_stage_dates CHECK (planned_start_date <= planned_end_date),
  CONSTRAINT fk_farm_stage_farm FOREIGN KEY (farm_id) REFERENCES farm(farm_id),
  CONSTRAINT fk_farm_stage_starter FOREIGN KEY (started_by) REFERENCES users(user_id),
  CONSTRAINT fk_farm_stage_locked_version FOREIGN KEY (locked_template_version_id) REFERENCES crop_template_version(template_version_id),
  CONSTRAINT fk_farm_stage_dispatched_version FOREIGN KEY (dispatched_template_version_id) REFERENCES crop_template_version(template_version_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
