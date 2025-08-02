import os
import pandas as pd
import json
import shutil
from sqlalchemy import create_engine, text, inspect
from config import DB_CONNECTION_STRING
from data_cleaning import (
    clean_operation_data, clean_numeric_columns, drop_percentage_columns,
    match_store_id_for_single_cpc, process_cpc_dates, add_datetime_column
)
from column_mappings import COLUMN_MAPPING_CPC_HOURLY
from excel_header_finder import clean_and_load_excel
from database_importer import import_to_mysql, get_dtype_for_operation, get_dtype_for_cpc_hourly
import send2trash  # ✅ 添加回收站依赖

engine = create_engine(DB_CONNECTION_STRING)

CPC_HOURLY_FOLDER = r"D:\dianping_downloads\cpc_hourly_data"
OPERATION_FOLDER  = r"D:\dianping_downloads\operation_data"

def delete_old_cpc_for_store(start_date, end_date, store_ids):
    with engine.begin() as conn:
        for sid in store_ids:
            res = conn.execute(
                text("DELETE FROM cpc_hourly_data WHERE store_id = :sid AND DATE(date) BETWEEN :s AND :e"),
                {"sid": sid, "s": start_date, "e": end_date}
            )
            print(f"✅ 删除 cpc_hourly_data 中 门店ID={sid} {start_date}~{end_date} 共 {res.rowcount} 条。")

def delete_old_op_for_store(start_date, end_date, store_ids):
    with engine.begin() as conn:
        for sid in store_ids:
            res = conn.execute(
                text("DELETE FROM operation_data WHERE `美团门店ID` = :sid AND DATE(`日期`) BETWEEN :s AND :e"),
                {"sid": sid, "s": start_date, "e": end_date}
            )
            print(f"✅ 删除 operation_data 中 门店ID={sid} {start_date}~{end_date} 共 {res.rowcount} 条。")

def build_rankings_detail(row):
    city = str(row.get("城市", "")).strip()
    cols = {
        "美团人气榜榜单排名":   "meituan_popularity",
        "美团好评榜榜单排名":   "meituan_rating",
        "点评热门榜榜单排名":   "dianping_hot",
        "点评好评榜榜单排名":   "dianping_rating",
        "点评口味榜榜单排名":   "dianping_taste",
        "点评环境榜榜单排名":   "dianping_env",
        "点评服务榜榜单排名":   "dianping_service",
        "点评打卡人气榜榜单排名": "dianping_checkin",
    }
    detail = {}
    for src_col, key in cols.items():
        raw = row.get(src_col)
        if not raw or pd.isna(raw):
            continue
        tmp = {}
        for part in str(raw).split("|"):
            import re
            m = re.search(r'(.+?)第(\d+)名', part.strip())
            if not m:
                continue
            scope = m.group(1).strip()
            rank  = int(m.group(2))
            if city and city in scope:
                tmp['city'] = rank
            elif scope.endswith('区'):
                tmp['district'] = rank
            else:
                tmp['subdistrict'] = rank
        if tmp:
            detail[key] = tmp
    return json.dumps(detail, ensure_ascii=False)

def process_operation_folder():
    print(f"📂 正在读取运营数据路径：{OPERATION_FOLDER}")
    dfs = []
    filepaths = []

    for fname in os.listdir(OPERATION_FOLDER):
        if not fname.endswith(".xlsx"):
            continue
        fp = os.path.join(OPERATION_FOLDER, fname)
        df = clean_operation_data(clean_and_load_excel(fp))
        df = drop_percentage_columns(df)
        # 清洗数值列，遇到异常项会打印出美团门店ID
        df = clean_numeric_columns(df, key_col='美团门店ID')
        dfs.append(df)
        filepaths.append(fp)

    if not dfs:
        print("⚠️ 无运营数据文件导入")
        return

    df_all = pd.concat(dfs, ignore_index=True)
    df_all.drop_duplicates(subset=["日期", "美团门店ID"], keep="last", inplace=True)
    df_all["日期"] = pd.to_datetime(df_all["日期"]).dt.date
    min_date, max_date = df_all["日期"].min(), df_all["日期"].max()
    store_ids = df_all["美团门店ID"].astype(str).unique().tolist()

    delete_old_op_for_store(min_date, max_date, store_ids)

    inspector = inspect(engine)
    existing_cols = [c["name"] for c in inspector.get_columns("operation_data")]
    flat_cols = [c for c in existing_cols if c in df_all.columns]
    df_basic = df_all[flat_cols].copy()

    dynamic_df = df_all.drop(columns=flat_cols, errors="ignore")
    dicts = dynamic_df.to_dict(orient="records")
    cleaned = [{k: (None if pd.isna(v) else v) for k, v in d.items()} for d in dicts]
    df_basic["extra_metrics"] = [json.dumps(d, ensure_ascii=False) for d in cleaned]

    if "ROS分" in df_all.columns:
        df_basic["ros_score"] = pd.to_numeric(df_all["ROS分"], errors="coerce").fillna(0).astype(int)

    df_basic["rankings_detail"] = df_all.apply(build_rankings_detail, axis=1)

    dtype_op = get_dtype_for_operation(df_basic)
    import_to_mysql(df_basic, "operation_data", DB_CONNECTION_STRING, dtype=dtype_op)
    print(f"✅ 成功导入运营数据，共 {len(df_basic)} 行。")

    for fp in filepaths:
        send2trash.send2trash(fp)
        print(f"🗑️ 已移入回收站：{fp}")

def process_cpc_folder():
    print(f"📂 正在读取小时级CPC数据路径：{CPC_HOURLY_FOLDER}")
    store_mapping = pd.read_sql("SELECT * FROM store_mapping", con=engine)
    dfs = []
    filepaths = []

    for fname in os.listdir(CPC_HOURLY_FOLDER):
        if not fname.endswith(".xlsx"):
            continue
        fp = os.path.join(CPC_HOURLY_FOLDER, fname)
        df = clean_and_load_excel(fp)
        df = process_cpc_dates(df, fname)
        df = match_store_id_for_single_cpc(df, store_mapping)
        df = drop_percentage_columns(df)
        # 清洗数值列，遇到异常项会打印出门店名称
        df = clean_numeric_columns(df, key_col='门店名称')
        df = add_datetime_column(df)
        dfs.append(df)
        filepaths.append(fp)

    if not dfs:
        print("⚠️ 无CPC数据文件导入")
        return

    df_all = pd.concat(dfs, ignore_index=True)
    df_all['plan_key'] = (
        df_all['门店ID'].astype(str).str.strip()
        + "_"
        + df_all['推广名称'].astype(str).str.strip()
        + "_"
        + df_all['平台'].astype(str).str.strip()
    )
    df_all.rename(columns=COLUMN_MAPPING_CPC_HOURLY, inplace=True)
    df_all.drop_duplicates(subset=['plan_key', 'start_time'], inplace=True)

    df_all['date'] = pd.to_datetime(df_all['date']).dt.date
    min_date, max_date = df_all['date'].min(), df_all['date'].max()
    store_ids = df_all['store_id'].astype(str).unique().tolist()
    delete_old_cpc_for_store(min_date, max_date, store_ids)

    dtype_cpc = get_dtype_for_cpc_hourly(df_all)
    import_to_mysql(df_all, "cpc_hourly_data", DB_CONNECTION_STRING, dtype=dtype_cpc)
    print(f"✅ 成功导入小时级CPC数据，共 {len(df_all)} 行。")

    for fp in filepaths:
        send2trash.send2trash(fp)
        print(f"🗑️ 已移入回收站：{fp}")

if __name__ == "__main__":
    process_operation_folder()
    process_cpc_folder()
