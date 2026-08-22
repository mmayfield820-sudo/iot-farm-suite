# 团队协作规则

## 目录边界

每位成员优先只修改自己负责的目录。跨目录修改前先在群里说明原因，避免覆盖他人的工作。

## 接口优先

- REST 接口以 `contracts/openapi.yaml` 为准。
- 实时推送以 `contracts/websocket-events.md` 为准。
- MQTT 主题以 `contracts/mqtt-topics.md` 为准。
- 字段名称、单位和状态值以 `contracts/data-dictionary.md` 为准。
- 修改接口时先改契约，再同步前端、后端和设备端。

## 提交代码

提交信息尽量说明模块和动作，例如 `feat: add device list api`、`fix: handle command timeout`。

提交前至少确认：自己负责的模块可以启动，接口字段与契约一致，没有提交密码或本地 `.env` 文件。
