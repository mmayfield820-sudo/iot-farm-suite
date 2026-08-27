# 本地部署 SQL 数据库

## 1. 安装 MySQL Server 8.4

下载地址：

[MySQL 8.4 Installer](https://dev.mysql.com/downloads/file/?id=556212)

安装过程中请记录以下信息：

- MySQL 用户名，开发环境可以使用 `root`；
- 设置的 MySQL 密码；
- 端口，默认是 `3306`；
- Windows 服务是否设置为自动启动。

MySQL Server 是真正运行数据库的服务。安装完成后可以在 PowerShell 中确认客户端是否可用：

```powershell
mysql --version
```

如果提示找不到 `mysql`，将类似下面的目录加入 Windows PATH：

```text
C:\Program Files\MySQL\MySQL Server 8.4\bin
```

重新打开 VS Code 终端后再次运行 `mysql --version`。

## 2. 安装 MySQL Workbench

下载地址：

[MySQL Workbench](https://dev.mysql.com/downloads/file/?id=552199)

Workbench 是 MySQL 的图形化管理工具，不是数据库服务本身。它可以连接 MySQL Server、执行 SQL、查看表和检查数据。

以管理员身份打开 PowerShell，确认 MySQL 服务状态：

```powershell
Get-Service -Name MySQL84
```

如果服务没有运行，启动服务：

```powershell
Start-Service -Name MySQL84
```

将 MySQL 设置为 Windows 开机自动启动：

```powershell
Set-Service -Name MySQL84 -StartupType Automatic
```

workbench主页下面已经会有默认sql连接，可以直接用这个。

或者新创建一个连接：

```text
Connection Name: local-smart-agriculture
Hostname: 127.0.0.1
Port: 3306
Username: 你的 MySQL 用户
```

点击 Test Connection，确认可以连接。

## 3. 建库

最方便就是在mysql workbench打开连接之后在上面栏目 file->new query tab，然后把iot-farm-suite/database/schema/smart_agriculture.sql的内容复制到空sql file。最后按⚡的图标来执行建库的sql。（其他方法比较麻烦）

新建用户：

```SQL
CREATE USER 'smart_app'@'localhost'
IDENTIFIED BY '12345678';

GRANT SELECT, INSERT, UPDATE, DELETE
ON smart_agriculture.*
TO 'smart_app'@'localhost';

GRANT CREATE, ALTER, INDEX, DROP
ON smart_agriculture.*
TO 'smart_app'@'localhost';

FLUSH PRIVILEGES;
```

## 4. 导入seed数据

目前最方便的方法是把4个 iot-farm-suite/database/seed 01, 02, 03, 04的代码复制到sql workbench空sql文件一个个执行。（其他方法比较麻烦）

然后在sql workbench可以测试：

```SQL
USE smart_agriculture;
SELECT * FROM users;
```

结果该显示四个users实体

## 5. python环境

首先在项目vsc终端执行：

```PowerShell
pip install -r backend/requirements.txt
```

来安装python和数据库连接需要的依赖

接着在iot-farm-suite/.env文件添加：

```
# Database configuration for MySQL
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=smart_agriculture
DB_USER=smart_app
DB_PASSWORD=12345678
```

配置项目和数据库的连接地址。若密码不是12345678，请使用你之前输入的密码。

## 6. 测试python后端能连接到数据库

在项目vsc终端执行：

```PowerShell
$env:PYTHONPATH="$PWD\backend"
python -m unittest discover -s backend\tests -p "test_*.py" -v
```

结果该输出数据库12表
