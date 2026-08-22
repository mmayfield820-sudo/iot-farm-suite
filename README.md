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
