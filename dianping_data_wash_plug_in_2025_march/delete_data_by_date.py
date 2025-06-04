from sqlalchemy import create_engine, text

# ✅ 替换为你要删除的日期
target_date = '2025-04-21'

# ✅ 数据库连接配置（从 config.py 读取）
from config import DB_CONNECTION_STRING

engine = create_engine(DB_CONNECTION_STRING)

tables_to_clean = [
    ("cpc_hourly_data", "date"),
    ("operation_data", "日期"),
]

with engine.begin() as conn:
    for table_name, date_col in tables_to_clean:
        stmt = text(f"DELETE FROM {table_name} WHERE DATE({date_col}) = :target_date")
        result = conn.execute(stmt, {"target_date": target_date})
        print(f"✅ 已删除表 {table_name} 中 {target_date} 的记录，共 {result.rowcount} 条。")
