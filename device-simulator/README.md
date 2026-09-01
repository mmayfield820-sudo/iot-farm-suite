# 模拟设备

`simulator.py` 同时模拟土壤湿度传感器（`device_001`）、温度传感器（`device_002`）和灌溉控制器（`device_003`）。主题和 JSON 格式以 `../contracts/mqtt-topics.md` 为准，并与 `database/seed/03_devices.sql` 对齐。

启动前先运行数据库迁移 `database/migrations/003_add_device_telemetry.sql`，启动后端和 EMQX，再在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe .\device-simulator\simulator.py
```

模拟器每 5 秒上报温湿度和心跳；后端下发给 `farm/command/device_003` 的灌溉命令会被自动回传为 `success`。可用环境变量 `SIMULATOR_INTERVAL_SECONDS` 调整上报间隔。
