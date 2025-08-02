"""
数据库操作工具
"""
import pymysql
from config.config import db_config

def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**db_config)

def insert_dataframe(df, table_name):
    """将DataFrame批量插入数据库表"""
    conn = get_connection()
    try:
        df.to_sql(table_name, conn, if_exists='append', index=False)
    finally:
        conn.close()
