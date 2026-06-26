---
name: "mysql-multi-datasource"
description: "多数据源MySQL数据库操作工具，支持配置多个数据库连接，可控制DML操作权限（INSERT/UPDATE/DELETE）和DDL操作权限（CREATE/ALTER/DROP等）。Invoke when user needs to connect to multiple MySQL databases with configurable DML and DDL access permissions."
---

# MySQL 多数据源操作工具

本Skill提供灵活的多数据源MySQL数据库操作能力，支持配置多个数据库连接，并可细粒度控制DML操作权限（INSERT/UPDATE/DELETE）和DDL操作权限（CREATE/ALTER/DROP/TRUNCATE等）。
使用时首先查看该skill的同级目录下的`config.json`文件，了解数据源配置的格式和字段含义。

### 环境检测与命令语法

**必须根据用户环境生成对应的命令格式：**

| 环境 | 特征 | 命令分隔符 | 示例 |
|------|------|-----------|------|
| PowerShell | 用户OS为Windows | 分号 `;` | `cd ./scripts; python mysql_client.py -d db1 -s "SELECT 1"` |
| CMD | 用户OS为Windows | `&&` 或 `&` | `cd ./scripts && python mysql_client.py -d db1 -s "SELECT 1"` |
| Bash/Zsh | 用户OS为Linux/Mac | `&&` 或 `;` | `cd ./scripts && python mysql_client.py -d db1 -s "SELECT 1"` |

**PowerShell严禁使用 `&&` 作为命令分隔符**，会导致语法错误。

### UTF-8 编码设置

**防止中文乱码，执行命令前需设置UTF-8环境变量：**

| 环境 | 设置方式 | 示例 |
|------|---------|------|
| PowerShell | `$env:PYTHONIOENCODING="utf-8"` | `$env:PYTHONIOENCODING="utf-8"; cd ./scripts; python mysql_client.py -d db1 -s "SELECT * FROM users"` |
| CMD | `set PYTHONIOENCODING=utf-8` | `set PYTHONIOENCODING=utf-8 && cd ./scripts && python mysql_client.py -d db1 -s "SELECT * FROM users"` |
| Bash/Zsh | `export PYTHONIOENCODING=utf-8` | `export PYTHONIOENCODING=utf-8 && cd ./scripts && python mysql_client.py -d db1 -s "SELECT * FROM users"` |

**Windows环境建议在命令开头添加UTF-8设置**，避免查询结果中文字段显示乱码。

## 功能特性

- **多数据源支持**: 可配置多个MySQL数据库连接
- **DML权限控制**: 可单独配置是否允许执行 INSERT、UPDATE、DELETE 操作
- **DDL权限控制**: 可单独配置是否允许执行 CREATE、ALTER、DROP、TRUNCATE 等DDL操作
- **表存在性检查**: 执行SQL前自动检查涉及的表是否存在于当前数据源（CREATE语句除外）
- **SQL执行**: 支持查询、DML和DDL操作（根据权限配置）
- **连接管理**: 自动管理数据库连接池

## 配置说明

### 数据源配置文件

在 `./config.json` 中配置数据源：

```json
{
  "datasources": [
    {
      "name": "db1",
      "host": "localhost",
      "port": 3306,
      "database": "database1",
      "username": "user1",
      "password": "pass1",
      "allowInsert": true,
      "allowUpdate": true,
      "allowDelete": false,
      "allowDdl": true,
      "sslDisabled": true
    },
    {
      "name": "db2",
      "host": "192.168.1.100",
      "port": 3306,
      "database": "database2",
      "username": "user2",
      "password": "pass2",
      "allowInsert": false,
      "allowUpdate": false,
      "allowDelete": false,
      "allowDdl": false,
      "sslDisabled": true
    }
  ]
}
```

### 配置字段说明

| 字段          | 类型      | 必填 | 说明                          |
| ----------- | ------- | -- | --------------------------- |
| name        | string  | 是  | 数据源唯一标识名                    |
| host        | string  | 是  | 数据库主机地址                     |
| port        | number  | 是  | 数据库端口                       |
| database    | string  | 是  | 数据库名                        |
| username    | string  | 是  | 用户名                         |
| password    | string  | 是  | 密码                          |
| allowInsert | boolean | 否  | 是否允许INSERT操作，默认true         |
| allowUpdate | boolean | 否  | 是否允许UPDATE操作，默认true         |
| allowDelete | boolean | 否  | 是否允许DELETE操作，默认true         |
| allowDdl    | boolean | 否  | 是否允许DDL操作(CREATE/ALTER/DROP等)，默认true |
| sslDisabled | boolean | 否  | 是否禁用SSL连接，默认true            |

## 使用方法

### Python脚本方式

#### 1. 安装依赖

```bash
cd ./scripts
pip install -r requirements.txt
```

#### 2. 交互式模式（推荐）

```bash
python mysql_client.py -i
```

交互式命令：

- `/list` - 列出所有数据源
- `/use <数据源名>` - 切换数据源
- `/info` - 查看当前数据源信息
- `/exit` - 退出

#### 3. 直接执行SQL

```bash
# 查询示例
python mysql_client.py -d db1 -s "SELECT * FROM users LIMIT 10"

# 指定配置文件路径
python mysql_client.py -c ../config.json -d lsztc-product -s "SHOW TABLES"
```

### 在Python代码中使用

```python
from mysql_client import MySQLConnectionManager

# 初始化连接管理器
manager = MySQLConnectionManager('config.json')

# 执行查询
result = manager.execute_sql('db1', 'SELECT * FROM users LIMIT 10')
if result['success']:
    print(result['data'])

# 执行DML（受权限控制）
result = manager.execute_sql('db1', 'UPDATE users SET status = 1 WHERE id = 1')
print(f"影响行数: {result['affected_rows']}")

# 关闭连接
manager.close_all()
```

## 权限控制规则

### 操作类型检测

系统会自动检测SQL语句类型，并与权限配置进行校验：

| SQL前缀             | 操作类型 | 需要的权限             |
| ----------------- | ---- | ----------------- |
| SELECT            | 查询   | 无限制               |
| INSERT            | 插入   | allowInsert: true |
| UPDATE            | 更新   | allowUpdate: true |
| DELETE            | 删除   | allowDelete: true |
| CREATE/ALTER/DROP/TRUNCATE/RENAME | DDL  | allowDdl: true    |

### 权限不足处理

当执行超出权限的操作时，系统会返回错误：

```json
{
  "error": "PERMISSION_DENIED",
  "message": "Datasource 'db2' does not allow INSERT operations",
  "datasource": "db2",
  "operation": "INSERT"
}
```

DDL操作被拒绝时：

```json
{
  "error": "PERMISSION_DENIED",
  "message": "Datasource 'db2' does not allow DDL operations (CREATE/ALTER/DROP/TRUNCATE etc.)",
  "datasource": "db2",
  "operation": "DDL"
}
```

### 表不存在处理

当执行SQL时，系统会自动检查涉及的表是否存在于当前数据源（CREATE TABLE语句除外）：

```json
{
  "error": "TABLE_NOT_FOUND",
  "message": "表 'users' 不存在于数据源 'db1' 中",
  "datasource": "db1",
  "table": "users"
}
```

支持的SQL类型检查：
- SELECT ... FROM table_name [JOIN table_name]
- INSERT INTO table_name
- UPDATE table_name
- DELETE FROM table_name
- ALTER TABLE table_name
- DROP TABLE table_name
- TRUNCATE TABLE table_name

## 常用SQL示例

### 查看所有表

```sql
SHOW TABLES;
```

### 查看表结构

```sql
DESC table_name;
-- 或
SHOW CREATE TABLE table_name;
```

### 查询数据

```sql
SELECT * FROM table_name WHERE condition LIMIT 100;
```

### 统计数量

```sql
SELECT COUNT(*) FROM table_name WHERE condition;
```

### 分页查询

```sql
SELECT * FROM table_name LIMIT 10 OFFSET 20;
```

## 最佳实践

1. **最小权限原则**: 为只读数据源配置 `allowInsert: false, allowUpdate: false, allowDelete: false, allowDdl: false`
2. **生产环境保护**: 生产数据库建议限制DML和DDL权限，避免误操作
3. **DDL谨慎使用**: DDL操作（CREATE/ALTER/DROP等）会修改数据库结构，建议在开发环境验证后再应用到生产环境
4. **敏感数据**: 查询敏感数据时注意数据脱敏
5. **先查后改**: 执行UPDATE/DELETE前，先用SELECT确认影响范围

## 错误处理

### 常见错误

| 错误码                    | 说明      | 解决方案         |
| ---------------------- | ------- | ------------ |
| CONNECTION\_ERROR      | 连接失败    | 检查网络、主机地址、端口 |
| AUTHENTICATION\_ERROR  | 认证失败    | 检查用户名密码      |
| PERMISSION\_DENIED     | 权限不足    | 检查数据源权限配置    |
| TABLE\_NOT\_FOUND      | 表不存在    | 检查表名是否正确，或先创建表 |
| SQL\_ERROR             | SQL执行错误 | 检查SQL语法      |
| DATASOURCE\_NOT\_FOUND | 数据源不存在  | 检查数据源名称配置    |

## 安全提醒

⚠️ **重要**:

- 配置文件中的密码以明文存储，请确保文件权限安全
- 不要将配置文件提交到版本控制
- 定期更换数据库密码
- 生产环境操作前务必在测试环境验证

