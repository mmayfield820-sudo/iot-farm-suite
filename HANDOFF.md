# Handoff

## 当前分支

- `further`
- 生成日期：2026-09-03

## 本次完成

- 新增农场管理员菜单“设备监测与管理”。
- 新增合并页面 `frontend/src/views/farmAdmin/DeviceMonitoringManagement.vue`。
- 完成页面标题、数据更新时间、手动刷新和四张设备统计卡。
- 完成设备状态分布圆环图、设备类型统计及设备告警跳转。
- 迁移设备搜索、筛选、分页、录入、Excel 批量导入、绑定、换绑和解绑功能。
- 删除旧页面 `DeviceControl.vue` 和 `Devices.vue`。
- 删除旧菜单入口，旧路径 `/farm/status`、`/farm/control`、`/farm/devices` 保留重定向兼容。
- Dashboard 中的设备查看入口已改为跳转新页面。

## 数据与权限

- 页面复用现有 `platform` store 和 `/api/devices` 接口，未新增后端接口。
- 设备数据按农场管理员授权农场过滤，未绑定设备保留为可绑定设备。
- 在线、异常、未绑定采用互斥统计口径，避免重复计数。

## 验证

- `npm.cmd run build`：通过。
- `git diff --check`：通过。
- 旧组件及旧命名路由引用检查：通过，无残留引用。
- 本地预览：`http://127.0.0.1:5175/farm/device-monitoring-management`。
- 当前环境无可连接浏览器实例，未完成截图级视觉回归。

## 后续建议

- 在可用浏览器环境下对照设计稿检查桌面端卡片尺寸、表格密度及移动端换行。
- 根据真实设备数据确认“其他设备”分类和未绑定设备的业务归属规则。
