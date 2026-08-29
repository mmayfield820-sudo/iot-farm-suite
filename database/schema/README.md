# 数据库结构

这里存放 MySQL 8 建表和数据库升级脚本。文件按数字前缀排序执行，所有成员使用同一套脚本初始化本地数据库。

001_schema.sql 创建表、外键、唯一约束、索引和检查约束；002_reference_data.sql 写入角色和权限基础数据。演示数据位于 database/seed/001_demo_data.sql。

脚本也可以手动执行：

mysql -h 127.0.0.1 -P 3306 -u farm -p farm < database/schema/001_schema.sql

003_mqtt_tracking.sql adds persistent MQTT message deduplication and the command_id field needed to match device command-result messages.

008_device_runtime_status.sql separates device communication and collection/work states.

009_irrigation_duration.sql stores the planned duration for irrigation-on commands; actual duration is calculated from the paired on/off execution times.
