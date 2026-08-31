# 智慧农业项目

这是一个由设备采集、后端业务服务、网页前端和农业智能问答组成的智慧农业平台。

## 目录入口

- `docs/`：需求、架构和部署资料
- `contracts/`：前后端和设备端共同遵守的接口契约
- `frontend/`：网页前端
- `backend/`：后端服务
- `device-simulator/`：模拟温度、湿度和灌溉设备
- `ai-service/`：RAG 智能问答服务
- `database/`：数据库脚本和演示数据
- `infra/`：Docker、EMQX 等运行环境
- `tests/`：跨模块联调测试

## 开发顺序

1. 阅读 `docs/requirements/01_智慧农业_基本功能清单.md`。
2. 阅读 `contracts/` 中的接口约定。
3. 复制 `.env.example` 为 `.env`，填写本地配置。
4. 各成员只在自己负责的目录中开发。

接口有变化时，先修改 `contracts/` 并通知团队，再修改代码。详细规则见 `CONTRIBUTING.md`。

## 二期迭代能力（阶段 0～9）

- 种植档案：脐橙品种模板、定植日期、土壤类型、树龄和当前生长阶段，支持有原因的人工阶段修正。
- 管理计划：按模板预览、生成和重新生成计划；旧的未完成任务会标记为 `SUPERSEDED`，已完成历史不会丢失。
- 农事执行：今日、逾期、未来 7 天任务，临时任务、完成记录和月历。
- 决策辅助：天气 Mock/API/缓存/降级，规则化灌溉建议，低湿、降雨、设备离线等计划调整提醒。系统不会自动执行真实灌溉。
- 地块时间轴：聚合农事任务、灌溉记录、提醒和关键审计事件。
- 管理端：橙园与地块档案、员工 Excel 预校验和确认导入、员工激活、农场统计、分页审计日志。
- 账号入口：默认关闭公开注册，员工必须由系统管理员导入后使用一次性凭证激活；确有兼容需要时可显式设置 `PUBLIC_REGISTRATION_ENABLED=true`。

## 一键启动

在项目根目录双击 `start-all.cmd`，或在 PowerShell 中执行：

```powershell
.\start-all.ps1
```

仅检查本机依赖和配置，不启动服务：

```powershell
.\start-all.ps1 -ValidateOnly
```

默认端口为 MySQL `3306`、MQTT `2883`、Ollama `11434`、业务后端 `8080`、AI 服务 `8000`、前端 `5173`。所有服务端时间写入 UTC，前端统一显示北京时间。

## 数据库升级

- 全新环境依次执行 `database/schema/001_schema.sql` 与 `database/seed/001_demo_data.sql`。
- 一期已有库按 `database/migrations/README.md` 的编号顺序执行迁移，不能通过删除数据库代替升级。
- 当前二期迁移截至 `008_phase2_seed_template_tasks.sql`。

## 验证

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests\unit -p "test_*.py"
cd frontend
npm run build
```
