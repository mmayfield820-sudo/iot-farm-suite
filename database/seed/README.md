# 演示数据

- `001_demo_data.sql`：创建基础演示账号和兼容初始化数据。
- `002_orange_demo_reset.sql`：将演示业务数据统一重置为当前橙园产品数据。

这些文件由 `infra/docker-compose.yml` 按顺序执行，不再维护旧版 `smart_agriculture` 数据库的分片种子脚本。
