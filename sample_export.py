import pandas as pd
from config_and_brand import engine

# 当前数据库中真实存在的表（来自你截图）
table_list = [
    "cpc_data",
    "cpc_hourly_data",
    "operation_data",
    "operation_metrics",
    "review_ai_summary",
    "review_ai_tag",
    "review_data",
    "review_raw",
    "store_mapping"
]

# 循环导出每个表的前 10 条记录
for table in table_list:
    try:
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 10", engine)
        df.to_csv(f"{table}_样本数据.csv", index=False, encoding="utf-8-sig")
        print(f"✅ 成功导出：{table}_样本数据.csv")
    except Exception as e:
        print(f"❌ 表 {table} 导出失败：{e}")
