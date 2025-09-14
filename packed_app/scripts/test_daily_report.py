"""
测试日报生成功能的基本组件
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
from config.config import db_config
from utils.logger import get_logger

def test_database_connection():
    """测试数据库连接"""
    logger = get_logger('test_daily_report')
    
    try:
        # 创建数据库连接
        DB_CONNECTION_STRING = f'mysql+pymysql://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}'
        engine = create_engine(DB_CONNECTION_STRING)
        
        # 测试连接
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("数据库连接成功")
        
        return engine
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

def test_store_mapping():
    """测试门店映射数据获取"""
    logger = get_logger('test_daily_report')
    
    engine = test_database_connection()
    if not engine:
        return None
    
    try:
        # 获取门店映射
        store_map = pd.read_sql(
            "SELECT 门店ID AS store_id, 美团门店ID, 推广门店 AS brand_name, 运营师 AS operator FROM store_mapping",
            engine
        )
        logger.info(f"成功获取门店映射数据，共 {len(store_map)} 条记录")
        logger.info(f"运营师列表: {store_map['operator'].unique().tolist()}")
        return store_map
    except Exception as e:
        logger.error(f"获取门店映射失败: {e}")
        return None

def test_data_availability():
    """测试数据可用性"""
    logger = get_logger('test_daily_report')
    
    engine = test_database_connection()
    if not engine:
        return
    
    # 测试日期
    test_date = datetime.now() - timedelta(days=1)
    
    try:
        # 检查运营数据
        op_count = pd.read_sql(
            f"SELECT COUNT(*) as count FROM operation_data WHERE 日期 = '{test_date.date()}'",
            engine
        ).iloc[0]['count']
        logger.info(f"运营数据记录数: {op_count}")
        
        # 检查CPC数据
        cpc_count = pd.read_sql(
            f"SELECT COUNT(*) as count FROM cpc_hourly_data WHERE date = '{test_date.date()}'",
            engine
        ).iloc[0]['count']
        logger.info(f"CPC数据记录数: {cpc_count}")
        
        # 检查最近7天数据
        week_count = pd.read_sql(
            f"SELECT COUNT(*) as count FROM operation_data WHERE 日期 BETWEEN '{(test_date - timedelta(days=7)).date()}' AND '{test_date.date()}'",
            engine
        ).iloc[0]['count']
        logger.info(f"最近7天运营数据记录数: {week_count}")
        
    except Exception as e:
        logger.error(f"数据可用性检查失败: {e}")

def main():
    """主测试函数"""
    logger = get_logger('test_daily_report')
    logger.info("开始测试日报生成功能")
    
    # 测试数据库连接
    test_database_connection()
    
    # 测试门店映射
    test_store_mapping()
    
    # 测试数据可用性
    test_data_availability()
    
    logger.info("测试完成")

if __name__ == '__main__':
    main() 