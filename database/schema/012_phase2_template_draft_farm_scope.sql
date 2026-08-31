-- Phase 2: drafts are private to one farm's next production cycle.
SET NAMES utf8mb4;

ALTER TABLE crop_template_version
  ADD COLUMN farm_id BIGINT NULL AFTER template_id,
  ADD KEY idx_template_version_farm_status (farm_id, version_status),
  ADD CONSTRAINT fk_template_version_farm FOREIGN KEY (farm_id) REFERENCES farm(farm_id);

-- Existing published versions are immutable global history, so farm_id remains NULL.
-- Every newly created draft and the published next-cycle version derived from it are
-- associated with the farm that owns that maintenance window.
