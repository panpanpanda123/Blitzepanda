import os
import json
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from config import DB_CONNECTION_STRING
from excel_header_finder import clean_and_load_excel
from data_cleaning import clean_operation_data, drop_percentage_columns, clean_numeric_columns
from database_importer import import_to_mysql, get_dtype_for_operation
from main import build_rankings_detail

engine = create_engine(DB_CONNECTION_STRING)
OP_FOLDER = r"D:\dianping_downloads\operation_data"

def delete_old_op_for_store(start_date, end_date, store_ids):
    with engine.begin() as conn:
        for sid in store_ids:
            res = conn.execute(
                text("DELETE FROM operation_data WHERE `美团门店ID` = :sid AND DATE(`日期`) BETWEEN :s AND :e"),
                {"sid": sid, "s": start_date, "e": end_date}
            )
            print(f"✅ 删除 operation_data 中 门店ID={sid} {start_date}~{end_date} 共 {res.rowcount} 条。")

def process_operation_folder():
    dfs = []
    for fname in os.listdir(OP_FOLDER):
        if not fname.endswith(".xlsx"):
            continue
        fp = os.path.join(OP_FOLDER, fname)
        df = clean_operation_data(clean_and_load_excel(fp))
        df = drop_percentage_columns(df)
        df = clean_numeric_columns(df)
        dfs.append(df)

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

if __name__ == "__main__":
    process_operation_folder()
