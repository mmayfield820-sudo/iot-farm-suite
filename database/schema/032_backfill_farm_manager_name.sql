-- Preserve the legacy farm administrator as the initial archive owner.
UPDATE farm AS f
JOIN users AS u ON u.user_id = f.admin_user_id
SET f.manager_name = u.real_name
WHERE (f.manager_name IS NULL OR TRIM(f.manager_name) = '')
  AND u.real_name IS NOT NULL
  AND TRIM(u.real_name) <> '';
