# 数据库结构

本目录是面向交付的最终结构定义，不包含历史迁移或旧字段兼容脚本。

- `001_schema.sql`：创建当前项目的 20 张表、主键、索引、外键与检查约束。
- `002_reference_data.sql`：按当前数据库快照写入角色、权限及角色权限关系。

全新环境按文件名顺序执行本目录脚本，再执行 `../seed/001_demo_data.sql`。Docker Compose 已完成相同顺序的挂载配置。

所有时间字段按 UTC 保存；服务端负责转换为界面时区。`cultivation_template.template_content` 中的农业墒情参考采用田间持水量口径，设备告警与灌溉控制仍以 `threshold_config.soil_moisture_threshold` 和传感器实测口径为准，两者不能直接比较。
