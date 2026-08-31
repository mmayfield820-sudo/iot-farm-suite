-- Phase 2: versioned crop templates, planting profiles, and plan snapshots.
SET NAMES utf8mb4;

CREATE TABLE crop_template (
  template_id BIGINT NOT NULL AUTO_INCREMENT,
  template_name VARCHAR(100) NOT NULL,
  crop_name VARCHAR(50) NOT NULL,
  province VARCHAR(50) NULL,
  city VARCHAR(50) NULL,
  template_status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_by BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (template_id),
  KEY idx_crop_template_match (crop_name, province, city, template_status),
  CONSTRAINT chk_crop_template_status CHECK (template_status IN ('active', 'inactive')),
  CONSTRAINT fk_crop_template_creator FOREIGN KEY (created_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE crop_template_version (
  template_version_id BIGINT NOT NULL AUTO_INCREMENT,
  template_id BIGINT NOT NULL,
  version_no INT NOT NULL,
  version_status VARCHAR(20) NOT NULL DEFAULT 'draft',
  change_note VARCHAR(500) NULL,
  published_at DATETIME(6) NULL,
  published_by BIGINT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (template_version_id),
  UNIQUE KEY uq_template_version_no (template_id, version_no),
  KEY idx_template_version_status (template_id, version_status),
  CONSTRAINT chk_template_version_status CHECK (version_status IN ('draft', 'published', 'archived')),
  CONSTRAINT fk_template_version_template FOREIGN KEY (template_id) REFERENCES crop_template(template_id),
  CONSTRAINT fk_template_version_publisher FOREIGN KEY (published_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE growth_stage_template (
  stage_template_id BIGINT NOT NULL AUTO_INCREMENT,
  template_version_id BIGINT NOT NULL,
  stage_code VARCHAR(50) NOT NULL,
  stage_name VARCHAR(100) NOT NULL,
  sort_order INT NOT NULL,
  duration_days INT NOT NULL,
  moisture_min DECIMAL(5,2) NULL,
  moisture_max DECIMAL(5,2) NULL,
  management_focus TEXT NULL,
  PRIMARY KEY (stage_template_id),
  UNIQUE KEY uq_stage_template_code (template_version_id, stage_code),
  UNIQUE KEY uq_stage_template_order (template_version_id, sort_order),
  CONSTRAINT chk_stage_duration CHECK (duration_days > 0),
  CONSTRAINT chk_stage_moisture CHECK (moisture_min IS NULL OR moisture_max IS NULL OR moisture_min <= moisture_max),
  CONSTRAINT fk_stage_template_version FOREIGN KEY (template_version_id) REFERENCES crop_template_version(template_version_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE management_task_template (
  task_template_id BIGINT NOT NULL AUTO_INCREMENT,
  stage_template_id BIGINT NOT NULL,
  task_type VARCHAR(50) NOT NULL,
  title VARCHAR(150) NOT NULL,
  offset_days INT NOT NULL DEFAULT 0,
  suggested_time TIME NULL,
  note VARCHAR(1000) NULL,
  PRIMARY KEY (task_template_id),
  KEY idx_task_template_stage (stage_template_id, offset_days),
  CONSTRAINT fk_task_template_stage FOREIGN KEY (stage_template_id) REFERENCES growth_stage_template(stage_template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE planting_profile (
  plot_id BIGINT NOT NULL,
  template_version_id BIGINT NOT NULL,
  planting_date DATE NOT NULL,
  tree_age_years DECIMAL(5,2) NULL,
  soil_type VARCHAR(100) NULL,
  note VARCHAR(1000) NULL,
  updated_by BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (plot_id),
  CONSTRAINT chk_tree_age CHECK (tree_age_years IS NULL OR tree_age_years >= 0),
  CONSTRAINT fk_planting_plot FOREIGN KEY (plot_id) REFERENCES plot(plot_id),
  CONSTRAINT fk_planting_version FOREIGN KEY (template_version_id) REFERENCES crop_template_version(template_version_id),
  CONSTRAINT fk_planting_user FOREIGN KEY (updated_by) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE management_plan (
  plan_id BIGINT NOT NULL AUTO_INCREMENT,
  plot_id BIGINT NOT NULL,
  template_version_id BIGINT NOT NULL,
  plan_status VARCHAR(20) NOT NULL DEFAULT 'active',
  generated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  generated_by BIGINT NOT NULL,
  superseded_by BIGINT NULL,
  PRIMARY KEY (plan_id),
  KEY idx_plan_plot_status (plot_id, plan_status),
  CONSTRAINT chk_plan_status CHECK (plan_status IN ('active', 'superseded', 'completed')),
  CONSTRAINT fk_plan_plot FOREIGN KEY (plot_id) REFERENCES plot(plot_id),
  CONSTRAINT fk_plan_version FOREIGN KEY (template_version_id) REFERENCES crop_template_version(template_version_id),
  CONSTRAINT fk_plan_generator FOREIGN KEY (generated_by) REFERENCES users(user_id),
  CONSTRAINT fk_plan_superseded_by FOREIGN KEY (superseded_by) REFERENCES management_plan(plan_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE management_task (
  task_id BIGINT NOT NULL AUTO_INCREMENT,
  plan_id BIGINT NULL,
  plot_id BIGINT NOT NULL,
  stage_code VARCHAR(50) NULL,
  task_type VARCHAR(50) NOT NULL,
  title VARCHAR(150) NOT NULL,
  source VARCHAR(20) NOT NULL DEFAULT 'template',
  scheduled_date DATE NOT NULL,
  task_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  note VARCHAR(1000) NULL,
  PRIMARY KEY (task_id),
  KEY idx_task_plot_date (plot_id, scheduled_date, task_status),
  CONSTRAINT chk_task_source CHECK (source IN ('template', 'ad_hoc')),
  CONSTRAINT chk_task_status CHECK (task_status IN ('pending', 'in_progress', 'completed', 'overdue', 'cancelled')),
  CONSTRAINT fk_task_plan FOREIGN KEY (plan_id) REFERENCES management_plan(plan_id),
  CONSTRAINT fk_task_plot FOREIGN KEY (plot_id) REFERENCES plot(plot_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
