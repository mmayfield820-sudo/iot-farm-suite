# 智慧农业监测平台（前端）

Vue 3 + Vite + Element Plus + Pinia + Vue Router + Axios + ECharts。

## 启动

```powershell
npm install
npm run dev
```

当前使用模拟登录。账号由系统分配角色，登录前无需选择身份；拥有多个角色的账号可在页面右上角切换当前工作视角。演示账号为 `E000001 / 123456`，同时拥有以下三个角色：

- 农户：`/farmer/dashboard`
- 农场管理员：`/farm/dashboard`
- 系统管理员：`/admin/archives`

农户模块位于 `src/views/farmer`，按需求2采用单地块视角，包含实时监测、历史趋势、阈值告警、远程灌溉、天气预报和智能问答；农场管理员模块位于 `src/views/farmAdmin`，包含多地块总览、设备控制、设备录入/绑定和告警日志；系统管理员模块位于 `src/views/systemAdmin`，包含基础档案、全局告警、用户账号、品种模板和审计日志。MQTT 主题和 JSON 构造集中在 `src/services/mqttProtocol.js`。后端完成后，将 `.env.development` 中的 `VITE_USE_MOCK` 改为 `false`，并按 `src/api` 中的接口接入。
