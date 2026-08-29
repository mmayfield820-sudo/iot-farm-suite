-- Stable roles and permissions required by the application.
SET NAMES utf8mb4;

INSERT INTO roles (role_code, scope_type) VALUES
  ('farmer', 'plot'),
  ('farm_admin', 'farm'),
  ('system_admin', 'system');

INSERT INTO permissions (permission_code, resource_type, action_type) VALUES
  ('farm_view', 'farm', 'view'),
  ('farm_manage', 'farm', 'manage'),
  ('plot_view', 'plot', 'view'),
  ('plot_manage', 'plot', 'manage'),
  ('device_view', 'device', 'view'),
  ('device_manage', 'device', 'manage'),
  ('irrigation_control', 'irrigation', 'control'),
  ('threshold_view', 'threshold_config', 'view'),
  ('threshold_update', 'threshold_config', 'update'),
  ('report_view', 'report', 'view'),
  ('alert_view', 'alert', 'view'),
  ('alert_manage', 'alert', 'manage');

INSERT INTO role_permission_rel (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles AS r
CROSS JOIN permissions AS p
WHERE r.role_code = 'system_admin'
   OR (r.role_code = 'farm_admin' AND p.permission_code IN (
     'farm_view', 'farm_manage', 'plot_view', 'plot_manage', 'device_view',
     'device_manage', 'irrigation_control', 'threshold_view',
     'threshold_update', 'report_view', 'alert_view', 'alert_manage'
   ))
   OR (r.role_code = 'farmer' AND p.permission_code IN (
     'plot_view', 'device_view', 'irrigation_control', 'threshold_view',
     'threshold_update', 'report_view', 'alert_view'
   ));
