-- Link legacy farm manager text to the single employee already authorized for the farm.
SET NAMES utf8mb4;

UPDATE farm AS f
JOIN (
  SELECT farm_id, MIN(user_id) AS user_id
  FROM farm_admin_scope
  GROUP BY farm_id
  HAVING COUNT(DISTINCT user_id) = 1
) AS scope_owner ON scope_owner.farm_id = f.farm_id
JOIN users AS u ON u.user_id = scope_owner.user_id
SET f.admin_user_id = u.user_id,
    f.manager_name = COALESCE(NULLIF(TRIM(u.real_name), ''), u.employee_no)
WHERE f.admin_user_id IS NULL;
