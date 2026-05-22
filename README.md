# MySQL 多数据源操作工具

一个灵活的 MySQL 多数据源客户端，支持配置多个数据库连接，提供细粒度的权限控制和表存在性检查。

## 功能特性

- **多数据源支持** - 同时管理多个 MySQL 数据库连接
- **DML 权限控制** - 可配置 INSERT/UPDATE/DELETE 操作权限
- **DDL 权限控制** - 可配置 CREATE/ALTER/DROP/TRUNCATE 等 DDL 操作权限
- **表存在性检查** - 执行 SQL 前自动验证表是否存在于当前数据源
- **交互式操作** - 提供友好的命令行交互界面
- **程序化调用** - 支持在 Python 代码中直接调用

## 快速开始

### 1. 安装依赖

```bash
cd scripts
pip install -r requirements.txt
```

### 2. 配置数据源

编辑 `config.json` 文件，添加你的数据库连接信息：

```json
{
  "datasources": [
    {
      "name": "db1",
      "host": "localhost",
      "port": 3306,
      "database": "mydb",
      "username": "root",
      "password": "password",
      "allowInsert": true,
      "allowUpdate": true,
      "allowDelete": false,
      "allowDdl": false
    }
  ]
}
```

### 3. 启动交互式客户端

```bash
python mysql_client.py -i
```

## 使用方式

### 交互式模式（推荐）

```bash
python mysql_client.py -i
```

交互式命令：

| 命令 | 说明 |
|------|------|
| `/list` | 列出所有配置的数据源 |
| `/use <数据源名>` | 切换到指定数据源 |
| `/info` | 查看当前数据源信息和权限 |
| `/exit` | 退出程序 |

示例会话：

```
[未选择]> /list
📋 可用数据源:
   • db1 [I,U]
   • db2 [只读]

[未选择]> /use db1
✅ 已切换到数据源: db1

[db1]> SELECT * FROM users LIMIT 5;
🚀 执行SQL: SELECT * FROM users LIMIT 5
+----+--------+-------+
| id | name   | email |
+----+--------+-------+
|  1 | Alice  | a@... |
|  2 | Bob    | b@... |
+----+--------+-------+
📊 共 5 条记录

[db1]> /exit
👋 再见！
```

### 命令行直接执行

```bash
# 执行查询
python mysql_client.py -d db1 -s "SELECT * FROM users LIMIT 10"

# 指定配置文件路径
python mysql_client.py -c /path/to/config.json -d db1 -s "SHOW TABLES"
```

### Python 代码中使用

```python
from mysql_client import MySQLConnectionManager

# 初始化连接管理器
manager = MySQLConnectionManager('config.json')

try:
    # 执行查询
    result = manager.execute_sql('db1', 'SELECT * FROM users LIMIT 10')
    if result['success']:
        print(result['data'])

    # 执行 DML（受权限控制）
    result = manager.execute_sql('db1', 'UPDATE users SET status = 1 WHERE id = 1')
    print(f"影响行数: {result['affected_rows']}")
finally:
    manager.close_all()
```

## 配置说明

### 配置字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 数据源唯一标识名 |
| host | string | 是 | 数据库主机地址 |
| port | number | 是 | 数据库端口 |
| database | string | 是 | 数据库名 |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |
| allowInsert | boolean | 否 | 是否允许 INSERT，默认 true |
| allowUpdate | boolean | 否 | 是否允许 UPDATE，默认 true |
| allowDelete | boolean | 否 | 是否允许 DELETE，默认 true |
| allowDdl | boolean | 否 | 是否允许 DDL，默认 true |
| sslDisabled | boolean | 否 | 是否禁用 SSL，默认 true |

### 权限控制示例

**只读数据源配置：**

```json
{
  "name": "readonly-db",
  "host": "localhost",
  "port": 3306,
  "database": "production",
  "username": "readonly",
  "password": "secret",
  "allowInsert": false,
  "allowUpdate": false,
  "allowDelete": false,
  "allowDdl": false
}
```

## 权限控制规则

系统会自动检测 SQL 语句类型并进行权限校验：

| SQL 类型 | 需要的权限 |
|----------|-----------|
| SELECT | 无限制 |
| INSERT | allowInsert: true |
| UPDATE | allowUpdate: true |
| DELETE | allowDelete: true |
| CREATE/ALTER/DROP/TRUNCATE | allowDdl: true |

## 表存在性检查

执行 SQL 前，系统会自动检查涉及的表是否存在于当前数据源（CREATE TABLE 除外）：

```
❌ 表不存在: 表 'users' 不存在于数据源 'db1' 中
```

支持的 SQL 类型检查：
- SELECT ... FROM table_name [JOIN table_name]
- INSERT INTO table_name
- UPDATE table_name
- DELETE FROM table_name
- ALTER/DROP/TRUNCATE TABLE table_name

## 项目结构

```
mysql-multi-datasource-skill/
├── README.md              # 项目说明文档
├── SKILL.md               # Skill 详细文档
├── config.json            # 数据源配置文件
└── scripts/
    ├── mysql_client.py    # MySQL 客户端主程序
    └── requirements.txt   # Python 依赖
```

## 错误处理

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| CONNECTION_ERROR | 连接失败 | 检查网络、主机地址、端口 |
| AUTHENTICATION_ERROR | 认证失败 | 检查用户名密码 |
| PERMISSION_DENIED | 权限不足 | 检查数据源权限配置 |
| TABLE_NOT_FOUND | 表不存在 | 检查表名是否正确 |
| SQL_ERROR | SQL 执行错误 | 检查 SQL 语法 |
| DATASOURCE_NOT_FOUND | 数据源不存在 | 检查数据源名称配置 |

## 最佳实践

1. **最小权限原则** - 为只读数据源关闭所有写权限
2. **生产环境保护** - 限制 DML 和 DDL 权限，避免误操作
3. **DDL 谨慎使用** - 在开发环境验证后再应用到生产环境
4. **敏感数据处理** - 查询敏感数据时注意脱敏
5. **先查后改** - UPDATE/DELETE 前先用 SELECT 确认影响范围

## 安全提醒

⚠️ **重要提示：**

- 配置文件中的密码以明文存储，请确保文件权限安全（建议设置为 600）
- 不要将配置文件提交到版本控制，建议添加到 `.gitignore`
- 定期更换数据库密码
- 生产环境操作前务必在测试环境验证

## License

MIT
