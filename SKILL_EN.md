---
name: "mysql-multi-datasource"
description: "Multi-datasource MySQL database operation tool that supports configuring multiple database connections with controllable DML permissions (INSERT/UPDATE/DELETE) and DDL permissions (CREATE/ALTER/DROP etc.). Invoke when user needs to connect to multiple MySQL databases with configurable DML and DDL access permissions."
---

# MySQL Multi-Datasource Operation Tool

This Skill provides flexible multi-datasource MySQL database operation capabilities, supporting configuration of multiple database connections with fine-grained control over DML operation permissions (INSERT/UPDATE/DELETE) and DDL operation permissions (CREATE/ALTER/DROP/TRUNCATE etc.).
When using it, first check the `config.json` file in the same directory of the skill to understand the format and field meaning of the data source configuration.
## Features

- **Multi-Datasource Support**: Configure multiple MySQL database connections
- **DML Permission Control**: Individually configure whether to allow INSERT, UPDATE, DELETE operations
- **DDL Permission Control**: Individually configure whether to allow CREATE, ALTER, DROP, TRUNCATE and other DDL operations
- **Table Existence Check**: Automatically check if involved tables exist in current datasource before executing SQL (except CREATE statements)
- **SQL Execution**: Support queries, DML and DDL operations (based on permission configuration)
- **Connection Management**: Automatic database connection pool management

## Configuration

### Datasource Configuration File

Configure datasources in `./config.json`:

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

### Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Unique datasource identifier |
| host | string | Yes | Database host address |
| port | number | Yes | Database port |
| database | string | Yes | Database name |
| username | string | Yes | Username |
| password | string | Yes | Password |
| allowInsert | boolean | No | Allow INSERT operations, default true |
| allowUpdate | boolean | No | Allow UPDATE operations, default true |
| allowDelete | boolean | No | Allow DELETE operations, default true |
| allowDdl | boolean | No | Allow DDL operations (CREATE/ALTER/DROP etc.), default true |
| sslDisabled | boolean | No | Disable SSL connection, default true |

## Usage

### Python Script Mode

#### 1. Install Dependencies

```bash
cd ./scripts
pip install -r requirements.txt
```

#### 2. Interactive Mode (Recommended)

```bash
python mysql_client.py -i
```

Interactive Commands:

- `/list` - List all datasources
- `/use <datasource>` - Switch datasource
- `/info` - View current datasource info
- `/exit` - Exit

#### 3. Direct SQL Execution

```bash
# Query example
python mysql_client.py -d db1 -s "SELECT * FROM users LIMIT 10"

# Specify config file path
python mysql_client.py -c ../config.json -d db2 -s "SHOW TABLES"
```

### Use in Python Code

```python
from mysql_client import MySQLConnectionManager

# Initialize connection manager
manager = MySQLConnectionManager('config.json')

# Execute query
result = manager.execute_sql('db1', 'SELECT * FROM users LIMIT 10')
if result['success']:
    print(result['data'])

# Execute DML (subject to permission control)
result = manager.execute_sql('db1', 'UPDATE users SET status = 1 WHERE id = 1')
print(f"Affected rows: {result['affected_rows']}")

# Close connections
manager.close_all()
```

## Permission Control Rules

### Operation Type Detection

The system automatically detects SQL statement types and validates against permission configuration:

| SQL Prefix | Operation Type | Required Permission |
|------------|----------------|---------------------|
| SELECT | Query | No restriction |
| INSERT | Insert | allowInsert: true |
| UPDATE | Update | allowUpdate: true |
| DELETE | Delete | allowDelete: true |
| CREATE/ALTER/DROP/TRUNCATE/RENAME | DDL | allowDdl: true |

### Permission Denied Handling

When executing operations beyond permissions, the system returns an error:

```json
{
  "error": "PERMISSION_DENIED",
  "message": "Datasource 'db2' does not allow INSERT operations",
  "datasource": "db2",
  "operation": "INSERT"
}
```

When DDL operation is denied:

```json
{
  "error": "PERMISSION_DENIED",
  "message": "Datasource 'db2' does not allow DDL operations (CREATE/ALTER/DROP/TRUNCATE etc.)",
  "datasource": "db2",
  "operation": "DDL"
}
```

### Table Not Found Handling

When executing SQL, the system automatically checks if involved tables exist in the current datasource (except CREATE TABLE statements):

```json
{
  "error": "TABLE_NOT_FOUND",
  "message": "Table 'users' does not exist in datasource 'db1'",
  "datasource": "db1",
  "table": "users"
}
```

Supported SQL types for checking:
- SELECT ... FROM table_name [JOIN table_name]
- INSERT INTO table_name
- UPDATE table_name
- DELETE FROM table_name
- ALTER TABLE table_name
- DROP TABLE table_name
- TRUNCATE TABLE table_name

## Common SQL Examples

### List All Tables

```sql
SHOW TABLES;
```

### View Table Structure

```sql
DESC table_name;
-- or
SHOW CREATE TABLE table_name;
```

### Query Data

```sql
SELECT * FROM table_name WHERE condition LIMIT 100;
```

### Count Records

```sql
SELECT COUNT(*) FROM table_name WHERE condition;
```

### Paginated Query

```sql
SELECT * FROM table_name LIMIT 10 OFFSET 20;
```

## Best Practices

1. **Principle of Least Privilege**: Configure read-only datasources with `allowInsert: false, allowUpdate: false, allowDelete: false, allowDdl: false`
2. **Production Environment Protection**: Production databases should restrict DML and DDL permissions to avoid accidental operations
3. **DDL Caution**: DDL operations (CREATE/ALTER/DROP etc.) modify database structure, validate in development environment before applying to production
4. **Sensitive Data**: Pay attention to data masking when querying sensitive data
5. **Query Before Modify**: Use SELECT to confirm impact range before executing UPDATE/DELETE

## Error Handling

### Common Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| CONNECTION_ERROR | Connection failed | Check network, host address, port |
| AUTHENTICATION_ERROR | Authentication failed | Check username and password |
| PERMISSION_DENIED | Insufficient permissions | Check datasource permission configuration |
| TABLE_NOT_FOUND | Table does not exist | Check if table name is correct, or create table first |
| SQL_ERROR | SQL execution error | Check SQL syntax |
| DATASOURCE_NOT_FOUND | Datasource does not exist | Check datasource name configuration |

## Security Reminders

⚠️ **Important**:

- Passwords in configuration files are stored in plaintext, ensure file permissions are secure
- Do not commit configuration files to version control
- Regularly rotate database passwords
- Always validate in test environment before production operations
