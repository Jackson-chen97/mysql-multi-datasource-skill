# MySQL Multi-Datasource Tool

A flexible MySQL multi-datasource client that supports configuring multiple database connections with fine-grained permission control and table existence checking.

## Features

- **Multi-Datasource Support** - Manage multiple MySQL database connections simultaneously
- **DML Permission Control** - Configurable INSERT/UPDATE/DELETE operation permissions
- **DDL Permission Control** - Configurable CREATE/ALTER/DROP/TRUNCATE and other DDL operation permissions
- **Table Existence Check** - Automatically verify table existence in current datasource before executing SQL (except CREATE TABLE)
- **Interactive Operation** - Friendly command-line interactive interface
- **Programmatic Usage** - Direct invocation in Python code

## Quick Start

### 1. Install Dependencies

```bash
cd scripts
pip install -r requirements.txt
```

### 2. Configure Datasources

Edit the `config.json` file and add your database connection information:

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

### 3. Start Interactive Client

```bash
python mysql_client.py -i
```

## Usage

### Interactive Mode (Recommended)

```bash
python mysql_client.py -i
```

Interactive Commands:

| Command | Description |
|---------|-------------|
| `/list` | List all configured datasources |
| `/use <datasource>` | Switch to specified datasource |
| `/info` | View current datasource info and permissions |
| `/exit` | Exit the program |

Example Session:

```
[none]> /list
📋 Available datasources:
   • db1 [I,U]
   • db2 [Read-only]

[none]> /use db1
✅ Switched to datasource: db1

[db1]> SELECT * FROM users LIMIT 5;
🚀 Executing SQL: SELECT * FROM users LIMIT 5
+----+--------+-------+
| id | name   | email |
+----+--------+-------+
|  1 | Alice  | a@... |
|  2 | Bob    | b@... |
+----+--------+-------+
📊 5 rows in total

[db1]> /exit
👋 Goodbye!
```

### Direct Command Line Execution

```bash
# Execute query
python mysql_client.py -d db1 -s "SELECT * FROM users LIMIT 10"

# Specify config file path
python mysql_client.py -c /path/to/config.json -d db1 -s "SHOW TABLES"
```

### Use in Python Code

```python
from mysql_client import MySQLConnectionManager

# Initialize connection manager
manager = MySQLConnectionManager('config.json')

try:
    # Execute query
    result = manager.execute_sql('db1', 'SELECT * FROM users LIMIT 10')
    if result['success']:
        print(result['data'])

    # Execute DML (subject to permission control)
    result = manager.execute_sql('db1', 'UPDATE users SET status = 1 WHERE id = 1')
    print(f"Affected rows: {result['affected_rows']}")
finally:
    manager.close_all()
```

## Configuration

### Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Unique datasource identifier |
| host | string | Yes | Database host address |
| port | number | Yes | Database port |
| database | string | Yes | Database name |
| username | string | Yes | Username |
| password | string | Yes | Password |
| allowInsert | boolean | No | Allow INSERT, default true |
| allowUpdate | boolean | No | Allow UPDATE, default true |
| allowDelete | boolean | No | Allow DELETE, default true |
| allowDdl | boolean | No | Allow DDL, default true |
| sslDisabled | boolean | No | Disable SSL, default true |

### Permission Control Example

**Read-only Datasource Configuration:**

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

## Permission Control Rules

The system automatically detects SQL statement types and performs permission validation:

| SQL Type | Required Permission |
|----------|---------------------|
| SELECT | No restriction |
| INSERT | allowInsert: true |
| UPDATE | allowUpdate: true |
| DELETE | allowDelete: true |
| CREATE/ALTER/DROP/TRUNCATE | allowDdl: true |

## Table Existence Check

Before executing SQL, the system automatically checks whether the involved tables exist in the current datasource (except for CREATE TABLE):

```
❌ Table not found: Table 'users' does not exist in datasource 'db1'
```

Supported SQL types for checking:
- SELECT ... FROM table_name [JOIN table_name]
- INSERT INTO table_name
- UPDATE table_name
- DELETE FROM table_name
- ALTER/DROP/TRUNCATE TABLE table_name

## Project Structure

```
mysql-multi-datasource-skill/
├── README.md              # Project documentation (Chinese)
├── README_EN.md           # Project documentation (English)
├── SKILL.md               # Skill detailed documentation (Chinese)
├── SKILL_EN.md            # Skill detailed documentation (English)
├── config.json            # Datasource configuration file
└── scripts/
    ├── mysql_client.py    # MySQL client main program
    └── requirements.txt   # Python dependencies
```

## Error Handling

| Error Code | Description | Solution |
|------------|-------------|----------|
| CONNECTION_ERROR | Connection failed | Check network, host address, port |
| AUTHENTICATION_ERROR | Authentication failed | Check username and password |
| PERMISSION_DENIED | Insufficient permissions | Check datasource permission configuration |
| TABLE_NOT_FOUND | Table does not exist | Check if table name is correct |
| SQL_ERROR | SQL execution error | Check SQL syntax |
| DATASOURCE_NOT_FOUND | Datasource does not exist | Check datasource name configuration |

## Best Practices

1. **Principle of Least Privilege** - Disable all write permissions for read-only datasources
2. **Production Environment Protection** - Restrict DML and DDL permissions to avoid accidental operations
3. **DDL Caution** - Validate in development environment before applying to production
4. **Sensitive Data Handling** - Pay attention to data masking when querying sensitive data
5. **Query Before Modify** - Use SELECT to confirm impact range before UPDATE/DELETE

## Security Reminders

⚠️ **Important:**

- Passwords in configuration files are stored in plaintext, ensure file permissions are secure (recommended: chmod 600)
- Do not commit configuration files to version control, add to `.gitignore`
- Regularly rotate database passwords
- Always validate in test environment before production operations

## License

MIT
