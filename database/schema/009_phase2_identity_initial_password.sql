-- Phase 2: employee identity attributes and first-login password setup.
-- Execute after 008_phase2_account_and_master_data.sql. All timestamps are UTC.
SET NAMES utf8mb4;

-- Never store an ID card number in plaintext. The keyed digest enforces uniqueness;
-- the masked value is the only form exposed by the business API.
ALTER TABLE users
  ADD COLUMN id_card_hash CHAR(64) NULL AFTER employee_no,
  ADD COLUMN id_card_masked VARCHAR(24) NULL AFTER id_card_hash,
  ADD COLUMN initial_password_hash VARCHAR(255) NULL AFTER password_hash,
  ADD UNIQUE KEY uq_users_id_card_hash (id_card_hash);

-- Existing phase-1 accounts remain active. New phase-2 accounts use employee_no as
-- username and keep this bcrypt hash only for administrator-initiated password reset.
