import pymysql
from contextlib import contextmanager
import enhanced_config as config
import os

@contextmanager
def get_connection():
    """
    上下文管理器：获取并自动关闭数据库连接。
    """
    conn = pymysql.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
        port=config.PORT,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset=config.CHARSET
    )
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """
    初始化数据库：
    1. 确保数据库存在（如果不存在则尝试创建）。
    2. 执行 enhanced_schema.sql 文件以创建所有必要的表。
    """
    try:
        # 步骤1: 尝试连接到数据库，如果不存在则尝试创建数据库
        conn_no_db = pymysql.connect(
            host=config.HOST,
            user=config.USER,
            password=config.PASSWORD,
            port=config.PORT,
            cursorclass=pymysql.cursors.DictCursor,
            charset=config.CHARSET
        )
        with conn_no_db.cursor() as cur_no_db:
            cur_no_db.execute(f"CREATE DATABASE IF NOT EXISTS {config.DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn_no_db.close()
        print(f"数据库 '{config.DATABASE}' 已确认或创建。")

        # 步骤2: 连接到指定数据库并执行 schema 文件
        with get_connection() as conn: # get_connection 会连接到 config.DATABASE
            print(f"正在连接到数据库 '{config.DATABASE}' 以执行 schema...")
            # 假设 enhanced_schema.sql 与此文件在同一目录或可访问路径
            # 为确保路径正确，最好使用绝对路径或相对于脚本的路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            schema_file_path = os.path.join(script_dir, "enhanced_schema.sql")
            
            if not os.path.exists(schema_file_path):
                print(f"错误: SQL schema 文件未找到于 '{schema_file_path}'")
                print("请确保 enhanced_schema.sql 文件与 enhanced_database.py 在同一目录。")
                return

            print(f"正在执行 SQL schema 文件: {schema_file_path}...")
            execute_sql_file(schema_file_path, conn) # 传递连接对象
            print("数据库表结构初始化完成。")

    except pymysql.Error as e:
        print(f"数据库初始化失败: {e}")
        # 可以考虑在这里抛出异常，让调用方处理
        raise # 重新抛出异常，以便 create_admin.py 可以捕获并停止
    except FileNotFoundError:
        print(f"错误: SQL schema 文件 'enhanced_schema.sql' 未找到。")
        raise
    except Exception as e:
        print(f"数据库初始化过程中发生未知错误: {e}")
        raise

def execute_sql_file(file_path, connection):
    """
    执行SQL文件
    :param file_path: SQL文件的路径
    :param connection: 已建立的数据库连接对象
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 分割SQL语句 (更稳健的方式是处理注释和空语句)
    statements = []
    current_statement = ""
    in_delimiter_block = False
    delimiter = ";"

    for line in sql_content.splitlines():
        line = line.strip()
        if not line or line.startswith('--'): # 跳过空行和单行注释
            continue
        
        if line.upper().startswith("DELIMITER "):
            delimiter = line.split()[1]
            current_statement = "" # 重置当前语句
            continue

        current_statement += line + "\n"
        
        if current_statement.rstrip().endswith(delimiter):
            # 去掉末尾的 delimiter 和可能的多余换行
            statement_to_execute = current_statement[:current_statement.rfind(delimiter)].strip()
            if statement_to_execute: # 确保不是空语句
                 statements.append(statement_to_execute)
            current_statement = ""
            if delimiter != ";": # 如果是自定义的 delimiter 块结束，则恢复默认
                # 这个逻辑假设 DELIMITER // ... END //; 结构
                # 对于简单的 DELIMITER // ... END //，下次循环会自动重置 delimiter
                # 如果SQL文件严格遵循 DELIMITER ; 来恢复，这里可以不用动
                # 但更稳健的做法是，如果 DELIMITER // 后面是 END //; 则在END // 后恢复
                if statement_to_execute.upper().startswith("END"):
                    delimiter = ";" # 恢复默认 delimiter
    
    # 处理最后一个可能的语句（如果没有以 delimiter 结尾）
    if current_statement.strip():
        statements.append(current_statement.strip())

    with connection.cursor() as cur:
        for i, statement in enumerate(statements):
            if statement:
                try:
                    # print(f"Executing: {statement[:100]}...") # 用于调试
                    cur.execute(statement)
                except pymysql.Error as e:
                    # 检查错误是否与索引创建相关，如果是则忽略
                    error_str = str(e)
                    if "CREATE INDEX" in statement and ("already exists" in error_str or "Duplicate key name" in error_str):
                        print(f"索引可能已存在，忽略错误: {statement[:100]}...")
                    else:
                        print(f"执行SQL语句时出错 (语句 {i+1}): {statement[:100]}...")
                        print(f"错误信息: {e}")
                        # 对于非索引错误，回滚并抛出异常
                        connection.rollback()
                        raise
                except Exception as e:
                    print(f"执行SQL语句时发生非pymysql错误 (语句 {i+1}): {statement[:100]}...")
                    print(f"错误信息: {e}")
                    connection.rollback()
                    raise
        connection.commit()
    print('SQL文件执行完成。') 