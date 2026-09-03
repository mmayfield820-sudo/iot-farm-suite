-- Use the employee number as the only employee login identifier.
-- Execute after 032_backfill_farm_manager_name.sql. Existing user_id values stay unchanged.
SET NAMES utf8mb4;

UPDATE users
SET employee_no = CASE username
  WHEN 'demo_admin' THEN 'E000001'
  WHEN 'demo_farmer' THEN 'E000002'
  WHEN 'demo_system' THEN 'E000003'
  ELSE username
END
WHERE employee_no IS NULL OR employee_no = '';

ALTER TABLE users
  DROP INDEX uq_users_username,
  MODIFY employee_no VARCHAR(50) NOT NULL,
  DROP COLUMN username;
