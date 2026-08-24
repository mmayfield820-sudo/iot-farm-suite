-- 在 MySQL 客户端中从项目根目录执行：
-- SOURCE database/seed/seed_all.sql;
-- 各文件按外键依赖顺序执行，可重复执行。

SOURCE database/seed/01_identity.sql;
SOURCE database/seed/02_farms_and_plots.sql;
SOURCE database/seed/03_devices.sql;
SOURCE database/seed/04_monitoring_and_operations.sql;