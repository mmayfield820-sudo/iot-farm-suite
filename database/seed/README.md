# 演示数据

这里存放本地开发和演示所需的初始化数据。文件按照外键依赖和业务域拆分，统一入口为 `seed_all.sql`。

## 文件顺序

1. `01_identity.sql`：用户、角色、权限及关联关系
2. `02_farms_and_plots.sql`：农场和地块
3. `03_devices.sql`：设备
4. `04_monitoring_and_operations.sql`：阈值、监测报告、灌溉记录和告警

## 执行方式

先执行 `database/schema/建库.sql` 创建表，再从项目根目录执行：

```sql
SOURCE database/seed/seed_all.sql;
```

各个 seed 文件使用固定主键和 `INSERT IGNORE`，可重复执行。示例账号的密码哈希均为占位演示值，生产环境不得使用。
