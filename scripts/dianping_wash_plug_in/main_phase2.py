import os
import json
import argparse
import yaml
import logging
import send2trash
import pandas as pd
from datetime import datetime
from logging.handlers import RotatingFileHandler
from sqlalchemy import create_engine, inspect, text
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from excel_header_finder import clean_and_load_excel
from data_cleaning import (
    clean_operation_data, clean_numeric_columns, drop_percentage_columns,
    process_cpc_dates, match_store_id_for_single_cpc, add_datetime_column
)
from database_importer import import_to_mysql, get_dtype_for_operation, get_dtype_for_cpc_hourly
from column_mappings import COLUMN_MAPPING_CPC_HOURLY

# 配置模型
class Settings(BaseModel):
    db_connection_string: str
    operation_folder: str
    cpc_hourly_folder: str
    log_dir: str = "logs"
    processed_list: str = "processed_files.json"
    retry_attempts: int = 3
    retry_backoff: int = 2
    notification: dict = Field(default_factory=dict)

def load_settings(path: str) -> Settings:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return Settings(**data)

def setup_logger(log_dir: str):
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger('import_logger')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        os.path.join(log_dir, 'import.log'),
        maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(handler)
    return logger

# 全局设置对象和 logger（将在 main 中初始化）
settings = None
logger = None

# 重试装饰器
def retryable(func):
    return retry(
        stop=stop_after_attempt(settings.retry_attempts),
        wait=wait_exponential(multiplier=settings.retry_backoff, min=settings.retry_backoff)
    )(func)

# 审计相关
def init_import_history_table(engine):
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS import_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            brand_name VARCHAR(255),
            file_name VARCHAR(512),
            table_name VARCHAR(255),
            row_count INT,
            status VARCHAR(50),
            error_msg TEXT,
            start_time DATETIME,
            end_time DATETIME
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))

def record_import(engine, brand, file_name, table, row_count, status, error_msg, start_time, end_time):
    with engine.begin() as conn:
        conn.execute(text("""
        INSERT INTO import_history
        (brand_name, file_name, table_name, row_count, status, error_msg, start_time, end_time)
        VALUES (:brand, :file_name, :table, :row_count, :status, :error_msg, :start_time, :end_time)
        """), {
            "brand": brand,
            "file_name": file_name,
            "table": table,
            "row_count": row_count,
            "status": status,
            "error_msg": error_msg,
            "start_time": start_time,
            "end_time": end_time
        })

def load_processed(path: str):
    if os.path.exists(path):
        return set(json.load(open(path, 'r', encoding='utf-8')))
    return set()

def save_processed(path: str, processed_set: set):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(list(processed_set), f, ensure_ascii=False, indent=2)

# 主处理逻辑示例
@retryable
def process_operation_file(path, engine, logger, processed, settings):
    logger.info(f"处理运营: {path}")
    df = clean_operation_data(clean_and_load_excel(path))
    df = drop_percentage_columns(df)
    df = clean_numeric_columns(df)
    df["日期"] = pd.to_datetime(df["日期"]).dt.date
    store_ids = df["美团门店ID"].astype(str).unique().tolist()
    with engine.begin() as conn:
        for sid in store_ids:
            conn.execute(text(
                "DELETE FROM operation_data WHERE `美团门店ID`=:sid AND DATE(`日期`)=:d"
            ), {"sid": sid, "d": df["日期"].min()})
    cnt = import_to_mysql(df, "operation_data", settings.db_connection_string, dtype=get_dtype_for_operation(df))
    record_import(engine, "brand", path, "operation_data", cnt, "success", "", datetime.now(), datetime.now())
    send2trash.send2trash(path)
    processed.add(path)
    save_processed(settings.processed_list, processed)
    logger.info(f"✅ 完成运营: {path} ({cnt} 行)")

def main():
    global settings, logger
    parser = argparse.ArgumentParser(description="Phase2: 支持 CLI & 配置文件")
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    args = parser.parse_args()

    settings = load_settings(args.config)
    logger = setup_logger(settings.log_dir)
    engine = create_engine(settings.db_connection_string)

    init_import_history_table(engine)
    processed = load_processed(settings.processed_list)

    # 示例：处理运营数据，后续可补充 process_cpc_folder
    op_files = [
        os.path.join(settings.operation_folder, f)
        for f in os.listdir(settings.operation_folder)
        if f.endswith('.xlsx')
    ]
    for fp in op_files:
        if fp in processed:
            continue
        try:
            process_operation_file(fp, engine, logger, processed, settings)
        except Exception as e:
            logger.error(f"失败: {fp} -> {e}", exc_info=True)

if __name__ == '__main__':
    main()
