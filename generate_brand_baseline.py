# 修改后的 generate_brand_baseline.py （请完整替换原文件）

import os
import json
from datetime import datetime
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from summarize import format_number, summarize
from config_and_brand import get_mysql_engine

# 时间区间配置
START_DATE = datetime(2025, 1, 1)
END_DATE   = datetime(2025, 5, 18)
OUTPUT_PATH = "brand_baseline.json"

# 指标字段
op_fields  = [
    "曝光人数", "访问人数", "购买人数",
    "成交金额(优惠后)", "成交客单价(优惠后)",
    "新好评数", "新评价数", "新客购买人数", "老客购买人数"
]
cpc_fields = [
    "cost", "impressions", "clicks", "orders",
    "merchant_views", "favorites", "interests", "shares"
]

# 建立数据库连接
engine = get_mysql_engine()

# 读取门店映射表
store_mapping = pd.read_sql("SELECT * FROM store_mapping", engine)
store_mapping = store_mapping.dropna(subset=["推广门店", "门店ID", "美团门店ID"])

brand_list = store_mapping["推广门店"].unique().tolist()
brand_baseline = {}

# 数据提取函数
def fetch_operation_data(mt_store_id, start_date, end_date):
    sql = f"""
        SELECT * 
        FROM operation_data
        WHERE 美团门店ID = '{mt_store_id}'
          AND 日期 BETWEEN '{start_date.date()}' AND '{end_date.date()}'
    """
    return pd.read_sql(sql, engine)

def fetch_cpc_data(store_id, start_date, end_date):
    sql = f"""
        SELECT * 
        FROM cpc_hourly_data
        WHERE store_id = '{store_id}'
          AND date BETWEEN '{start_date.date()}' AND '{end_date.date()}'
    """
    return pd.read_sql(sql, engine)

# 遍历每个品牌
for brand in brand_list:
    df_map = store_mapping[store_mapping["推广门店"] == brand]
    op_df_all  = pd.DataFrame()
    cpc_df_all = pd.DataFrame()

    # 汇总该品牌下所有门店的数据
    for _, row in df_map.iterrows():
        sid, mtid = row["门店ID"], row["美团门店ID"]
        op_part  = fetch_operation_data(mtid, START_DATE, END_DATE)
        cpc_part = fetch_cpc_data(sid,  START_DATE, END_DATE)
        op_df_all  = pd.concat([op_df_all,  op_part],  ignore_index=True)
        cpc_df_all = pd.concat([cpc_df_all, cpc_part], ignore_index=True)

    # 若完全无数据，跳过
    if op_df_all.empty and cpc_df_all.empty:
        continue

    # 1) 计算总计
    op_summary  = summarize(op_df_all,  op_fields)
    cpc_summary = summarize(cpc_df_all, cpc_fields)

    # 2) 计算日均值
    days = (END_DATE.date() - START_DATE.date()).days + 1
    op_daily  = {k: format_number(v / days)  for k, v in op_summary.items()}
    cpc_daily = {k: format_number(v / days) for k, v in cpc_summary.items()}

    # 写入画像
    brand_baseline[brand] = {
        "运营数据总计": op_summary,
        "运营数据日均": op_daily,
        "推广数据总计": cpc_summary,
        "推广数据日均": cpc_daily
    }

# 保存至 JSON，处理 numpy 类型
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(
        brand_baseline, f,
        ensure_ascii=False, indent=2,
        default=lambda o: int(o) if isinstance(o, np.integer)
                         else float(o) if isinstance(o, np.floating)
                         else str(o)
    )

print(f"✅ 基准画像已生成：{OUTPUT_PATH}")

