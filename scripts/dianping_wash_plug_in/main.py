# main.py（自动读取固定路径 + 去重处理）
import os
import pandas as pd
import json, math, re
from sqlalchemy import create_engine, text, inspect
from column_mappings import COLUMN_MAPPING_CPC_HOURLY
from excel_header_finder import clean_and_load_excel
from data_cleaning import (
    clean_operation_data,
    clean_numeric_columns,
    drop_percentage_columns,
    match_store_id_for_single_cpc,
    process_cpc_dates,add_datetime_column,
)
from database_importer import import_to_mysql, get_dtype_for_cpc_hourly
from config import DB_CONNECTION_STRING
import shutil
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='openpyxl')
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(message)s')

# 引入点评清洗函数 & MySQL 写入
from review_cleaner import clean_review_file
from sqlalchemy import types as sqltypes

engine = create_engine(DB_CONNECTION_STRING)

def build_rankings_detail(row):
    """
    直接用当前行的 '城市' 列判定 city 级，
    以 '区' 结尾判定 district 级，
    其余当 subdistrict 级。
    """
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
            m = re.search(r'(.+?)第(\d+)名', part.strip())
            if not m:
                continue
            scope = m.group(1).strip()
            rank  = int(m.group(2))
            # 判定层级
            if city and city in scope:
                tmp['city'] = rank
            elif scope.endswith('区'):
                tmp['district'] = rank
            else:
                tmp['subdistrict'] = rank
        if tmp:
            detail[key] = tmp
    return json.dumps(detail, ensure_ascii=False)
# —— END 简化版 build_rankings_detail ——

def bulk_import_excels_to_table(folder_path: str, table_name: str):
    """
    扫描 folder_path 下所有 .xlsx，把每个文件读成 DataFrame，
    自动对齐 table_name 里已有的列，剩下的丢弃，
    然后 append 到该表中。
    """
    engine = create_engine(DB_CONNECTION_STRING)
    inspector = inspect(engine)
    # 1. 反射表结构，拿到表里所有列名
    existing_cols = [c['name'] for c in inspector.get_columns(table_name)]

    for fname in os.listdir(folder_path):
        if not fname.endswith(".xlsx"):
            continue
        full_path = os.path.join(folder_path, fname)
        # 2. 读 Excel（默认第一张表）
        df = pd.read_excel(full_path)
        # 3. 重命名映射（如需），否则注释掉下一行
        # df = df.rename(columns=COLUMN_MAPPING_OPERATION)
        # 4. 只保留表里已有的列
        df = df[[c for c in df.columns if c in existing_cols]]
        if df.empty:
            continue
        # 5. 写入 MySQL
        df.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"✅ {fname} 导入表 {table_name} 完成，{len(df)} 行。")

# ✅ 固定数据路径（自动读取）
FIXED_FOLDER_PATH = r"D:\橡皮信息科技\橡皮客户运营\大众点评运营数据\raw_data"

# 1) 定义清理函数，替代旧 delete_data_by_date.py
def delete_old_cpc_for_store(start_date, end_date, store_ids):
    """只删除指定门店在日期范围内的推广通（cpc_hourly_data）旧数据"""
    engine = create_engine(DB_CONNECTION_STRING)
    with engine.begin() as conn:
        for sid in store_ids:
            res = conn.execute(
                text("DELETE FROM cpc_hourly_data WHERE store_id = :sid AND DATE(date) BETWEEN :s AND :e"),
                {"sid": sid, "s": start_date, "e": end_date}
            )
            print(f"✅ 删除 cpc_hourly_data 中 门店ID={sid} {start_date}~{end_date} 共 {res.rowcount} 条。")

def delete_old_op_for_store(start_date, end_date, store_ids):
    """只删除指定门店在日期范围内的运营数据（operation_data）旧记录"""
    engine = create_engine(DB_CONNECTION_STRING)
    with engine.begin() as conn:
        for sid in store_ids:
            res = conn.execute(
                text("DELETE FROM operation_data WHERE `美团门店ID` = :sid AND DATE(`日期`) BETWEEN :s AND :e"),
                {"sid": sid, "s": start_date, "e": end_date}
            )
            print(f"✅ 删除 operation_data 中 门店ID={sid} {start_date}~{end_date} 共 {res.rowcount} 条。")


# 2) 定义已处理目录常量
PROCESSED_ROOT_PATH = r"D:\橡皮信息科技\橡皮客户运营\大众点评运营数据\processed_data"

def process_brand(brand_path, store_mapping):
    """
    读取 brand_path 下所有推广报表文件，清洗、合并并返回 DataFrame
    """
    hourly_cpc = []
    for fname in os.listdir(brand_path):
        if not (fname.endswith(".xlsx") and "推广报表" in fname):
            continue
        fp = os.path.join(brand_path, fname)
        df = clean_and_load_excel(fp)
        df = process_cpc_dates(df, fname)
        df = match_store_id_for_single_cpc(df, store_mapping)
        df = drop_percentage_columns(df)
        df = clean_numeric_columns(df)
        df = add_datetime_column(df)
        hourly_cpc.append(df)
    if not hourly_cpc:
        return pd.DataFrame()  # 没有报表则返回空 DF
    df_all = pd.concat(hourly_cpc, ignore_index=True)
    # 生成唯一标识 plan_key
    df_all['plan_key'] = (
        df_all['门店ID'].astype(str).str.strip()
        + "_"
        + df_all['推广名称'].astype(str).str.strip()
        + "_"
        + df_all['平台'].astype(str).str.strip()
    )
    # 重命名为英文列
    df_all.rename(columns=COLUMN_MAPPING_CPC_HOURLY, inplace=True)
    # 去重：同一个 plan_key + 同一个时段 只保留最后一条
    df_all.drop_duplicates(subset=['plan_key', 'start_time'], inplace=True)
    return df_all

def process_files():
    base = FIXED_FOLDER_PATH
    print(f"📂 正在读取固定路径：{base}")

    engine = create_engine(DB_CONNECTION_STRING)
    store_mapping = pd.read_sql("SELECT * FROM store_mapping", con=engine)
    store_mapping["推广门店"] = store_mapping["推广门店"].str.strip()
    store_mapping["门店ID"] = store_mapping["门店ID"].astype(str).str.strip()

    cpc_successes, op_successes, failures = [], [], []

    for brand in os.listdir(base):
        brand_dir = os.path.join(base, brand)
        if not os.path.isdir(brand_dir):
            continue

        try:
            # —— 1) 处理推广通 ——
            # 只处理包含“推广报表”、“账号报表”或“门店报表”的文件，避免将其他 Excel 当作 CPC 导入
            cpc_files = [
                f for f in os.listdir(brand_dir)
                if f.endswith(".xlsx") and any(k in f for k in ["推广报表", "账号报表", "门店报表"])
            ]
            if cpc_files:
                hourly_list = []
                for fname in cpc_files:
                    fp = os.path.join(brand_dir, fname)
                    df = clean_and_load_excel(fp)
                    df = process_cpc_dates(df, fname)
                    df = match_store_id_for_single_cpc(df, store_mapping)
                    df = drop_percentage_columns(df)
                    df = clean_numeric_columns(df)
                    df = add_datetime_column(df)
                    hourly_list.append(df)
                df_cpc = pd.concat(hourly_list, ignore_index=True)

                # 生成唯一标识并重命名、去重
                df_cpc['plan_key'] = (
                    df_cpc['门店ID'].astype(str).str.strip()
                    + "_"
                    + df_cpc['推广名称'].astype(str).str.strip()
                    + "_"
                    + df_cpc['平台'].astype(str).str.strip()
                )
                df_cpc.rename(columns=COLUMN_MAPPING_CPC_HOURLY, inplace=True)
                df_cpc.drop_duplicates(subset=['plan_key', 'start_time'], inplace=True)

                # 删除历史同店同日期数据
                df_cpc['date'] = pd.to_datetime(df_cpc['date']).dt.date
                min_date, max_date = df_cpc['date'].min(), df_cpc['date'].max()
                store_ids_cpc = df_cpc['store_id'].astype(str).unique().tolist()
                delete_old_cpc_for_store(min_date, max_date, store_ids_cpc)

                # 写入新数据
                dtype_cpc = get_dtype_for_cpc_hourly(df_cpc)
                import_to_mysql(
                    df_cpc,
                    "cpc_hourly_data",
                    DB_CONNECTION_STRING,
                    dtype=dtype_cpc,
                    if_exists="append"
                )
                cpc_successes.append(brand)
            else:
                logging.info(f"品牌 {brand} 下无 CPC 相关报表，跳过。")

            # —— 2) 处理运营数据 ——
            op_dfs = []
            for fname in os.listdir(brand_dir):
                # 只处理运营表，跳过所有带“推广报表”或“评价”关键字的 .xlsx
                if (not fname.endswith(".xlsx")
                        or "推广报表" in fname
                        or "评价" in fname
                ):
                    continue
                fp = os.path.join(brand_dir, fname)
                df_op = clean_operation_data(clean_and_load_excel(fp))
                df_op = drop_percentage_columns(df_op)
                df_op = clean_numeric_columns(df_op)
                op_dfs.append(df_op)

            if op_dfs:
                # 合并去重
                df_op_all = pd.concat(op_dfs, ignore_index=True)
                df_op_all.drop_duplicates(subset=["日期", "美团门店ID"], keep="last", inplace=True)

                # 转 datetime 并取区间
                df_op_all["日期"] = pd.to_datetime(df_op_all["日期"]).dt.date
                min_op, max_op = df_op_all["日期"].min(), df_op_all["日期"].max()
                store_ids_op = df_op_all["美团门店ID"].astype(str).unique().tolist()

                # 删除旧记录
                delete_old_op_for_store(min_op, max_op, store_ids_op)

                # 反射表结构，取已存在的列作为 flat 列
                inspector     = inspect(engine)
                existing_cols = [c["name"] for c in inspector.get_columns("operation_data")]
                flat_cols     = [c for c in existing_cols if c in df_op_all.columns]
                df_basic      = df_op_all[flat_cols].copy()

                # —— dynamic extra_metrics ——
                dynamic_df = df_op_all.drop(columns=flat_cols, errors="ignore")
                dicts = dynamic_df.to_dict(orient="records")
                if not dicts:
                    dicts = [{} for _ in range(len(df_basic))]
                cleaned = []
                for d in dicts:
                    cleaned.append({
                        k: (None if isinstance(v, float) and math.isnan(v) else v)
                        for k, v in d.items()
                    })
                df_basic["extra_metrics"] = [json.dumps(d, ensure_ascii=False) for d in cleaned]

                # —— ROS 分 ——
                if "ROS分" in df_op_all.columns:
                    df_basic["ros_score"] = pd.to_numeric(
                        df_op_all["ROS分"], errors="coerce"
                    ).fillna(0).astype(int)

                # —— 排行榜详情 JSON ——
                df_basic["rankings_detail"] = df_op_all.apply(build_rankings_detail, axis=1)

                # —— 唯一一次写入 operation_data ——
                from database_importer import get_dtype_for_operation
                dtype_op = get_dtype_for_operation(df_basic)
                import_to_mysql(
                    df_basic,
                    "operation_data",
                    DB_CONNECTION_STRING,
                    dtype=dtype_op,
                    if_exists="append"
                )
                op_successes.append(brand)
            else:
                logging.info(f"品牌 {brand} 下无运营数据，跳过。")

            # —— 3) 处理评价数据 ——  <— 与上面 if/else 同级
            review_files = [
                f for f in os.listdir(brand_dir)
                if f.endswith(".xlsx") and "评价" in f
            ]
            if review_files:
                for fname in review_files:
                    fp = os.path.join(brand_dir, fname)
                    df_rev = clean_review_file(fp, store_mapping)
                    dtype_review = {
                        "store_id": sqltypes.String(50),
                        "review_date": sqltypes.Date,
                        "rating_raw": sqltypes.Numeric(3, 1),
                        "rating_label": sqltypes.String(2),
                        "review_text": sqltypes.Text,
                        "senti_score": sqltypes.Float,
                        "senti_label": sqltypes.String(2),
                        "key_topics": sqltypes.JSON,
                    }
                    import_to_mysql(
                        df_rev,
                        "review_data",
                        DB_CONNECTION_STRING,
                        dtype=dtype_review,
                        if_exists="append"
                    )
                    print(f"✅ {brand} 的评价文件 {fname} 已写入 review_data，共 {len(df_rev)} 行。")
            else:
                logging.info(f"品牌 {brand} 下无评价文件，跳过。")
            # —— 4) 全部成功后搬目录 ——
            move_processed_files(brand_dir, PROCESSED_ROOT_PATH)

        except Exception as e:
            logging.error(f"品牌 {brand} 处理失败：{e}")
            failures.append((brand, str(e)))

    # 最终结果
    print(f"✅ 推广通成功品牌：{cpc_successes}")
    print(f"✅ 运营数据成功品牌：{op_successes}")
    if failures:
        print("❌ 以下品牌处理失败，请人工介入：")
        for b, err in failures:
            print(f"  - {b}: {err}")



def move_processed_files(src_root, dst_root):
    for root, dirs, files in os.walk(src_root):
        for file in files:
            if file.startswith("~$") or not file.endswith(".xlsx"):
                continue
            src_file_path = os.path.join(root, file)

            # 计算相对子路径
            relative_subdir = os.path.relpath(root, src_root)
            dst_subdir_path = os.path.join(dst_root, relative_subdir)

            os.makedirs(dst_subdir_path, exist_ok=True)  # 自动创建目标子目录

            dst_file_path = os.path.join(dst_subdir_path, file)
            shutil.move(src_file_path, dst_file_path)
            print(f"📦 已移动文件到：{dst_file_path}")

if __name__ == "__main__":
    process_files()
