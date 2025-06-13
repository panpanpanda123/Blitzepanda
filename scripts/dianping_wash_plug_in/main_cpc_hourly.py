import os
import pandas as pd
from sqlalchemy import create_engine, text
from config import DB_CONNECTION_STRING
from data_cleaning import (
    clean_numeric_columns, drop_percentage_columns, match_store_id_for_single_cpc,
    process_cpc_dates, add_datetime_column
)
from column_mappings import COLUMN_MAPPING_CPC_HOURLY
from excel_header_finder import clean_and_load_excel
from database_importer import import_to_mysql, get_dtype_for_cpc_hourly

engine = create_engine(DB_CONNECTION_STRING)

CPC_HOURLY_FOLDER = r"D:\dianping_downloads\cpc_hourly_data"

def delete_old_cpc_for_store(start_date, end_date, store_ids):
    with engine.begin() as conn:
        for sid in store_ids:
            res = conn.execute(
                text("DELETE FROM cpc_hourly_data WHERE store_id = :sid AND DATE(date) BETWEEN :s AND :e"),
                {"sid": sid, "s": start_date, "e": end_date}
            )
            print(f"✅ 删除 cpc_hourly_data 中 门店ID={sid} {start_date}~{end_date} 共 {res.rowcount} 条。")

def process_cpc_folder():
    store_mapping = pd.read_sql("SELECT * FROM store_mapping", con=engine)
    dfs = []
    for fname in os.listdir(CPC_HOURLY_FOLDER):
        if not fname.endswith(".xlsx"):
            continue
        fp = os.path.join(CPC_HOURLY_FOLDER, fname)
        df = clean_and_load_excel(fp)
        df = process_cpc_dates(df, fname)
        df = match_store_id_for_single_cpc(df, store_mapping)
        df = drop_percentage_columns(df)
        df = clean_numeric_columns(df)
        df = add_datetime_column(df)
        dfs.append(df)

    if not dfs:
        print("⚠️ 无有效文件导入")
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

if __name__ == "__main__":
    process_cpc_folder()
