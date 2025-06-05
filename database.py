import pymysql
from contextlib import contextmanager
import config

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
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset='utf8mb4'
    )
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """
    测试数据库连接是否成功。
    在首次运行前，请确保已在 MySQL 中执行 schema.sql 创建数据库与表结构。
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
    print('数据库连接正常。') 