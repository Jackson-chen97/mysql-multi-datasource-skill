#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 多数据源客户端
支持配置多个数据源，并可控制DML操作权限
"""

import json
import re
import sys
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from contextlib import contextmanager

try:
    import pymysql
    from pymysql.cursors import DictCursor
except ImportError:
    print("请先安装依赖: pip install pymysql")
    sys.exit(1)


@dataclass
class DataSourceConfig:
    """数据源配置"""
    name: str
    host: str
    port: int
    database: str
    username: str
    password: str
    allow_insert: bool = True
    allow_update: bool = True
    allow_delete: bool = True
    allow_ddl: bool = True
    ssl_disabled: bool = True

    @classmethod
    def from_dict(cls, data: Dict) -> 'DataSourceConfig':
        return cls(
            name=data['name'],
            host=data['host'],
            port=data['port'],
            database=data['database'],
            username=data['username'],
            password=data['password'],
            allow_insert=data.get('allowInsert', True),
            allow_update=data.get('allowUpdate', True),
            allow_delete=data.get('allowDelete', True),
            allow_ddl=data.get('allowDdl', True),
            ssl_disabled=data.get('sslDisabled', True)
        )


class PermissionError(Exception):
    """权限不足异常"""
    pass


class TableNotFoundError(Exception):
    """表不存在异常"""
    pass


class MySQLConnectionManager:
    """MySQL连接管理器"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.datasources: Dict[str, DataSourceConfig] = {}
        self._connections: Dict[str, pymysql.Connection] = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            for ds_config in config.get('datasources', []):
                ds = DataSourceConfig.from_dict(ds_config)
                self.datasources[ds.name] = ds

            print(f"[OK] 已加载 {len(self.datasources)} 个数据源配置")
            for name in self.datasources.keys():
                print(f"   - {name}")

        except FileNotFoundError:
            print(f"[ERROR] 配置文件不存在: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"[ERROR] 配置文件格式错误: {e}")
            sys.exit(1)

    def _get_connection(self, datasource_name: str) -> pymysql.Connection:
        """获取数据库连接"""
        if datasource_name not in self.datasources:
            raise ValueError(f"数据源 '{datasource_name}' 不存在")

        # 检查是否已有连接
        if datasource_name in self._connections:
            conn = self._connections[datasource_name]
            if conn.open:
                return conn

        # 创建新连接
        config = self.datasources[datasource_name]
        try:
            conn = pymysql.connect(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.username,
                password=config.password,
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=False,
                ssl_disabled=config.ssl_disabled
            )
            self._connections[datasource_name] = conn
            return conn
        except pymysql.Error as e:
            raise ConnectionError(f"连接数据库失败: {e}")

    def _check_permission(self, datasource_name: str, sql: str) -> Tuple[bool, str]:
        """检查操作权限"""
        config = self.datasources[datasource_name]
        sql_upper = sql.strip().upper()

        # 检测SQL类型
        if sql_upper.startswith('INSERT'):
            if not config.allow_insert:
                return False, f"数据源 '{datasource_name}' 不允许执行 INSERT 操作"
        elif sql_upper.startswith('UPDATE'):
            if not config.allow_update:
                return False, f"数据源 '{datasource_name}' 不允许执行 UPDATE 操作"
        elif sql_upper.startswith('DELETE'):
            if not config.allow_delete:
                return False, f"数据源 '{datasource_name}' 不允许执行 DELETE 操作"
        elif self._is_ddl(sql_upper):
            if not config.allow_ddl:
                return False, f"数据源 '{datasource_name}' 不允许执行 DDL 操作 (CREATE/ALTER/DROP/TRUNCATE等)"

        return True, ""

    def _is_ddl(self, sql_upper: str) -> bool:
        """判断是否为DDL语句"""
        ddl_keywords = ['CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'RENAME']
        for keyword in ddl_keywords:
            if sql_upper.startswith(keyword):
                return True
        return False

    def _extract_table_names(self, sql: str) -> List[str]:
        """
        从SQL语句中提取表名
        支持: SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, TRUNCATE, JOIN等
        注意：保留原始大小写，因为MySQL表名可能区分大小写
        """
        tables = set()

        # 匹配 FROM 后面的表名 (包括 JOIN)
        from_pattern = r'\bFROM\s+(\w+)(?:\s+AS\s+\w+)?'
        join_pattern = r'\bJOIN\s+(\w+)(?:\s+AS\s+\w+)?'
        into_pattern = r'\bINTO\s+(\w+)'
        update_pattern = r'\bUPDATE\s+(\w+)'
        table_pattern = r'\bTABLE\s+(?:IF\s+EXISTS\s+)?(\w+)'

        for pattern in [from_pattern, join_pattern, into_pattern, update_pattern, table_pattern]:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.update(matches)

        return list(tables)

    def _check_tables_exist(self, datasource_name: str, sql: str) -> Tuple[bool, str]:
        """
        检查SQL中涉及的表是否存在于当前数据源
        对于DDL语句(CREATE TABLE)跳过检查
        """
        sql_upper = sql.strip().upper()

        # DDL创建表操作跳过表存在性检查
        if sql_upper.startswith('CREATE'):
            return True, ""

        table_names = self._extract_table_names(sql)
        if not table_names:
            return True, ""

        try:
            conn = self._get_connection(datasource_name)
            cursor = conn.cursor()

            for table_name in table_names:
                # 查询information_schema检查表是否存在
                check_sql = """
                    SELECT COUNT(*) as count
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE()
                    AND table_name = %s
                """
                cursor.execute(check_sql, (table_name,))
                result = cursor.fetchone()

                if result['count'] == 0:
                    cursor.close()
                    return False, f"表 '{table_name}' 不存在于数据源 '{datasource_name}' 中"

            cursor.close()
            return True, ""

        except Exception as e:
            return False, f"检查表存在性时出错: {e}"

    def execute_sql(self, datasource_name: str, sql: str, params: Optional[Tuple] = None) -> Dict[str, Any]:
        """
        执行SQL语句

        Args:
            datasource_name: 数据源名称
            sql: SQL语句
            params: SQL参数（可选）

        Returns:
            执行结果字典
        """
        # 检查权限
        has_permission, error_msg = self._check_permission(datasource_name, sql)
        if not has_permission:
            raise PermissionError(error_msg)

        # 检查表是否存在（CREATE语句除外）
        tables_exist, error_msg = self._check_tables_exist(datasource_name, sql)
        if not tables_exist:
            raise TableNotFoundError(error_msg)

        conn = None
        cursor = None
        try:
            conn = self._get_connection(datasource_name)
            cursor = conn.cursor()

            # 执行SQL
            cursor.execute(sql, params)

            # 判断SQL类型
            sql_upper = sql.strip().upper()

            if sql_upper.startswith('SELECT') or sql_upper.startswith('SHOW') or sql_upper.startswith('DESC'):
                # 查询操作，返回结果集
                results = cursor.fetchall()
                return {
                    'success': True,
                    'type': 'query',
                    'row_count': len(results),
                    'data': results
                }
            else:
                # DML/DDL操作，提交事务
                conn.commit()
                return {
                    'success': True,
                    'type': 'dml',
                    'affected_rows': cursor.rowcount,
                    'last_insert_id': cursor.lastrowid
                }

        except PermissionError:
            raise
        except TableNotFoundError:
            raise
        except pymysql.Error as e:
            if conn:
                conn.rollback()
            return {
                'success': False,
                'error': 'SQL_ERROR',
                'message': str(e)
            }
        except Exception as e:
            if conn:
                conn.rollback()
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': str(e)
            }
        finally:
            if cursor:
                cursor.close()

    def close_all(self):
        """关闭所有连接"""
        for name, conn in self._connections.items():
            if conn and conn.open:
                conn.close()
                print(f"[CLOSED] 已关闭连接: {name}")
        self._connections.clear()

    def get_datasource_info(self, datasource_name: str) -> Optional[Dict]:
        """获取数据源信息"""
        if datasource_name not in self.datasources:
            return None

        config = self.datasources[datasource_name]
        return {
            'name': config.name,
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'permissions': {
                'insert': config.allow_insert,
                'update': config.allow_update,
                'delete': config.allow_delete,
                'ddl': config.allow_ddl
            }
        }

    def list_datasources(self) -> List[str]:
        """列出所有数据源名称"""
        return list(self.datasources.keys())


def print_query_results(results: List[Dict]):
    """打印查询结果"""
    if not results:
        print("[EMPTY] 查询结果为空")
        return

    # 获取所有列名
    columns = list(results[0].keys())

    # 计算每列的最大宽度
    col_widths = {}
    for col in columns:
        header_len = len(str(col))
        max_data_len = max(len(str(row.get(col, ''))) for row in results)
        col_widths[col] = max(header_len, max_data_len) + 2

    # 打印表头
    header_line = "+" + "+".join("-" * (col_widths[col] + 2) for col in columns) + "+"
    print(header_line)
    header = "|" + "|".join(f" {str(col):^{col_widths[col]}} " for col in columns) + "|"
    print(header)
    print(header_line)

    # 打印数据行
    for row in results:
        row_str = "|" + "|".join(f" {str(row.get(col, '')):^{col_widths[col]}} " for col in columns) + "|"
        print(row_str)

    print(header_line)
    print(f"[INFO] 共 {len(results)} 条记录")


def interactive_mode(manager: MySQLConnectionManager):
    """交互式模式"""
    print("\n" + "=" * 50)
    print("MySQL 多数据源客户端 - 交互式模式")
    print("=" * 50)
    print("命令:")
    print("  /use <数据源名>  - 切换数据源")
    print("  /list           - 列出所有数据源")
    print("  /info           - 查看当前数据源信息")
    print("  /exit           - 退出程序")
    print("=" * 50 + "\n")

    current_datasource = None

    while True:
        try:
            # 显示提示符
            prompt = f"[{current_datasource or '未选择'}]> "
            user_input = input(prompt).strip()

            if not user_input:
                continue

            # 处理命令
            if user_input.startswith('/'):
                parts = user_input.split()
                cmd = parts[0].lower()

                if cmd == '/exit':
                    print("再见！")
                    break

                elif cmd == '/list':
                    print("\n可用数据源:")
                    for name in manager.list_datasources():
                        ds_info = manager.get_datasource_info(name)
                        perms = []
                        if ds_info['permissions']['insert']:
                            perms.append('I')
                        if ds_info['permissions']['update']:
                            perms.append('U')
                        if ds_info['permissions']['delete']:
                            perms.append('D')
                        if ds_info['permissions']['ddl']:
                            perms.append('DDL')
                        perm_str = f"[{','.join(perms) if perms else '只读'}]"
                        print(f"   • {name} {perm_str}")
                    print()

                elif cmd == '/use':
                    if len(parts) < 2:
                        print("[ERROR] 用法: /use <数据源名>")
                        continue

                    ds_name = parts[1]
                    if ds_name in manager.list_datasources():
                        current_datasource = ds_name
                        print(f"[OK] 已切换到数据源: {ds_name}")
                    else:
                        print(f"[ERROR] 数据源 '{ds_name}' 不存在")

                elif cmd == '/info':
                    if not current_datasource:
                        print("[ERROR] 请先选择数据源")
                        continue

                    info = manager.get_datasource_info(current_datasource)
                    print(f"\n数据源信息: {info['name']}")
                    print(f"   主机: {info['host']}:{info['port']}")
                    print(f"   数据库: {info['database']}")
                    print(f"   权限: INSERT={'[OK]' if info['permissions']['insert'] else '[NO]'} "
                          f"UPDATE={'[OK]' if info['permissions']['update'] else '[NO]'} "
                          f"DELETE={'[OK]' if info['permissions']['delete'] else '[NO]'} "
                          f"DDL={'[OK]' if info['permissions']['ddl'] else '[NO]'}")
                    print()

                else:
                    print(f"[ERROR] 未知命令: {cmd}")

            else:
                # 执行SQL
                if not current_datasource:
                    print("[ERROR] 请先使用 /use <数据源名> 选择数据源")
                    continue

                sql = user_input
                print(f"执行SQL: {sql}")

                try:
                    result = manager.execute_sql(current_datasource, sql)

                    if result['success']:
                        if result['type'] == 'query':
                            print_query_results(result['data'])
                        else:
                            print(f"执行成功")
                            print(f"   影响行数: {result['affected_rows']}")
                            if result['last_insert_id']:
                                print(f"   自增ID: {result['last_insert_id']}")
                    else:
                        print(f"执行失败: {result['message']}")

                except PermissionError as e:
                    print(f"权限错误: {e}")
                except TableNotFoundError as e:
                    print(f"表不存在: {e}")
                except Exception as e:
                    print(f"错误: {e}")

        except KeyboardInterrupt:
            print("\n再见！")
            break
        except EOFError:
            break


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='MySQL 多数据源客户端')
    parser.add_argument('--config', '-c', default='../config.json',
                        help='配置文件路径 (默认: ../config.json)')
    parser.add_argument('--datasource', '-d', help='数据源名称')
    parser.add_argument('--sql', '-s', help='要执行的SQL语句')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='进入交互式模式')

    args = parser.parse_args()

    # 初始化连接管理器
    manager = MySQLConnectionManager(args.config)

    try:
        if args.interactive or (not args.sql and not args.datasource):
            # 交互式模式
            interactive_mode(manager)
        elif args.sql and args.datasource:
            # 直接执行SQL
            print(f"在数据源 '{args.datasource}' 上执行SQL: {args.sql}")
            result = manager.execute_sql(args.datasource, args.sql)

            if result['success']:
                if result['type'] == 'query':
                    print_query_results(result['data'])
                else:
                    print(f"执行成功")
                    print(f"   影响行数: {result['affected_rows']}")
                    if result['last_insert_id']:
                        print(f"   自增ID: {result['last_insert_id']}")
            else:
                print(f"执行失败: {result['message']}")
                sys.exit(1)
        else:
            print("请提供 --sql 和 --datasource 参数，或使用 --interactive 进入交互式模式")
            sys.exit(1)

    finally:
        manager.close_all()


if __name__ == '__main__':
    main()
