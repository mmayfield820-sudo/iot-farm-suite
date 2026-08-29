# 智慧农业监测平台（前端）

智慧农业监测平台的 Web 前端，面向农户、农场管理员和系统管理员三类用户。项目使用 Vue 3 构建，支持模拟数据独立演示，也可以切换到真实后端接口。

## 技术栈

- Vue 3：页面和组件
- Vite：开发服务器和构建工具
- Vue Router：路由和角色访问控制
- Pinia：用户、地块、设备、告警等共享状态
- Element Plus：表单、表格、按钮、弹窗等界面组件
- ECharts：温湿度趋势图
- Axios：调用后端 HTTP 接口
- ExcelJS：设备信息批量导入

## 功能模块

### 农户端

- 农场首页：地块、在线设备、当前告警和今日灌溉统计
- 地块管理：实时温湿度、地块信息、设备状态、历史趋势和阈值设置
- 智慧灌溉：灌溉建议、控制确认、指令执行进度和灌溉记录
- 告警中心：按地块、类型、状态和时间查询告警
- AI 农业助手：结合当前地块农情数据提供辅助建议

### 农场管理员端

- 多地块总览
- 设备运行状态与控制
- 设备录入、Excel 批量导入、绑定、换绑和解绑
- 农场范围内的告警日志

### 系统管理员端

- 平台运行概况
- 全局告警
- 用户、角色和授权范围管理
- 注册申请审核
- 系统参数和操作日志（真实环境需要后端及数据库提供相应接口）

## 环境要求

- Node.js `^20.19.0` 或 `>=22.12.0`
- npm 10 或兼容版本
- 推荐使用 Chrome、Edge 等现代浏览器

检查环境：

```powershell
node --version
npm --version
```

## 安装与启动

进入前端目录：

```powershell
cd E:\sm\codex\iot-farm-suite\frontend
```

首次运行先安装依赖：

```powershell
npm install
```

启动开发服务器：

```powershell
npm run dev
```

终端显示启动成功后，在浏览器打开：

```text
http://localhost:5173
```

结束运行时，在启动服务器的终端中按 `Ctrl + C`。

## 模拟数据模式

开发环境默认配置为：

```env
VITE_API_BASE_URL=/api
VITE_USE_MOCK=true
```

该模式不需要启动 Java 后端、MySQL 或 MQTT 服务

内置演示账号：

| 用户名 | 密码 | 角色和权限范围 |
| --- | --- | --- |
| `zhangsan` | `123456` | 农户、农场管理员、系统管理员；拥有多个地块和农场 |
| `lisi` | `123456` | 农户；仅能访问一个授权地块 |

登录页面不选择角色。账号登录后自动进入其第一个角色；拥有多个角色时，可以在页面右上角切换工作视角。

模拟模式下还可以体验注册流程：

1. 在登录页点击注册；
2. 填写账号资料；
3. 选择农户、农场管理员或同时选择两种身份；
4. 申请农户身份时选择地块；
5. 申请农场管理员身份时选择农场；
6. 使用系统管理员视角审核申请；
7. 审核通过后使用注册账号登录。

系统管理员身份不开放自行注册。

## 连接真实后端

真实数据必须通过后端接口获取，浏览器前端不应直接连接 MySQL，也不应直接向设备发送灌溉指令。推荐链路为：

```text
Vue 前端 → HTTP 后端 → MySQL
                    └→ MQTT Broker → 灌溉设备
```

修改 `.env.development`：

```env
VITE_API_BASE_URL=/api
VITE_USE_MOCK=false
```

修改环境变量后必须停止并重新执行：

```powershell
npm run dev
```

开发服务器会按照 `vite.config.js` 将 `/api` 转发到：

```text
http://localhost:8080
```

因此使用真实接口时，需要先启动监听 `8080` 端口的后端服务。如果后端端口不同，请修改 `vite.config.js` 中的 `server.proxy['/api'].target`。

前后端接口定义请参考：

- `openapi.yaml`：完整接口契约和字段格式
- `API接口使用说明.md`：接口接入说明
- `src/api/`：前端实际使用的接口封装

后端返回字段如果与页面模型不同，应在后端 DTO 中统一，或在 `src/utils/dataAdapters.js` 中转换。设备状态、设备类型、灌溉状态、告警状态和时间字段尤其需要保持一致。

## 页面入口

| 页面 | 地址 |
| --- | --- |
| 登录 | `/login` |
| 注册 | `/register` |
| 农户首页 | `/farmer/dashboard` |
| 农户地块管理 | `/farmer/management` |
| 智慧灌溉 | `/farmer/irrigation` |
| 农户告警中心 | `/farmer/alarm` |
| AI 农业助手 | `/farmer/ai` |
| 农场管理员总览 | `/farm/dashboard` |
| 农场管理员设备状态 | `/farm/status` |
| 农场管理员设备管理 | `/farm/devices` |
| 系统管理员首页 | `/admin/dashboard` |
| 系统用户管理 | `/admin/users` |

页面受登录状态和角色权限保护，不能依靠手动修改网址访问未授权模块。

## 项目结构

```text
frontend/
├─ src/
│  ├─ api/           后端接口封装
│  ├─ assets/        全局样式和作物图片
│  ├─ components/    通用组件
│  ├─ layout/        三种角色的页面布局
│  ├─ mock/          模拟数据
│  ├─ router/        页面路由和角色守卫
│  ├─ services/      MQTT 主题和消息协议
│  ├─ stores/        Pinia 状态仓库及业务逻辑
│  ├─ utils/         后端数据转换和状态计算
│  ├─ views/         登录及三种角色的业务页面
│  ├─ App.vue        根组件
│  └─ main.js        应用启动入口
├─ .env.development  开发环境变量
├─ .env.production   生产环境变量
├─ openapi.yaml      前后端接口契约
├─ vite.config.js    Vite、别名和接口代理配置
└─ package.json      依赖及运行命令
```

主要数据调用路径：

```text
views 页面 → stores 状态与业务逻辑 → api 接口封装 → request.js → 后端
```

模拟模式的数据调用路径：

```text
views 页面 → stores 状态与业务逻辑 → mock 模拟数据
```

## 构建与部署

生成生产环境文件：

```powershell
npm run build
```

构建结果位于：

```text
dist/
```

在本地预览构建结果：

```powershell
npm run preview
```

正式部署时应将 `dist` 放到 Nginx 等静态服务器，并完成两项配置：

1. 将前端路由回退到 `index.html`，避免刷新子页面时出现 404；
2. 将 `/api` 反向代理到后端服务。

## 开发约定

- 页面组件放在 `src/views`，并按角色分目录。
- 多个页面共用的界面放在 `src/components`。
- 多页面共享数据和业务操作放在 `src/stores`。
- HTTP 请求统一放在 `src/api`，不要在页面中重复创建 Axios 实例。
- 数据库字段和接口字段的兼容转换集中放在 `src/utils/dataAdapters.js`。
- 前端不保存明文密码，不直接连接数据库，不直接发布真实设备控制消息。
- 新增页面后，同时在 `src/router/index.js` 和对应角色的布局菜单中登记。

## 常见问题

### 1. `npm install` 失败

先确认 Node.js 版本满足要求，再重新安装依赖。不要手动修改 `node_modules` 中的文件。

### 2. 页面能够打开，但一直显示模拟数据

检查 `.env.development`：

```env
VITE_USE_MOCK=false
```

修改后重新启动开发服务器。

### 3. 请求接口返回 404 或连接失败

检查：

- 后端是否已经启动；
- 后端是否监听 `8080`；
- 请求地址是否以 `/api` 开头；
- `vite.config.js` 的代理目标是否与后端一致。

### 4. 登录后立即返回登录页

通常是后端返回了 `401`，或者登录响应中没有有效 Token、角色和授权范围。可以退出账号或清理本站 Local Storage 后重新登录。

### 5. 设备明明在线，页面却显示离线

检查后端返回的设备状态和最后心跳时间。前端分别显示通信状态 `status` 与采集状态 `workStatus`，并把接口中的 UTC 时间统一转换为北京时间。

### 6. 刷新 `/farmer/...` 等页面出现 404

开发环境通常不会出现该问题；生产服务器需要配置 Vue Router history 模式回退，将未知静态路径交给 `index.html` 处理。

## 相关资料

- 前后端接口契约：`openapi.yaml`
- 接口使用说明：`API接口使用说明.md`
- 数据库建表文件：`../database/schema/建库.sql`
