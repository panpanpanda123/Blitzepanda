"""
app.pipelines

按目录批量导入“运营数据 / 小时级 CPC 数据”的轻量流水线。
与旧脚本的入库逻辑对齐，但抽离成可复用函数。
"""

from __future__ import annotations

import os
import json
from typing import Tuple

import pandas as pd
from sqlalchemy import text

from app.db import get_engine, import_to_mysql, reflect_existing_columns, get_dtype_for_operation, get_dtype_for_cpc_hourly
from app.excel import clean_and_load_excel
from app.cleaning import (
    clean_operation_data, drop_percentage_columns, clean_numeric_columns,
    match_store_id_for_single_cpc, process_cpc_dates, add_datetime_column,
)
from app.mappings import COLUMN_MAPPING_CPC_HOURLY


def _build_rankings_detail(row: pd.Series) -> str:
    # 与旧实现保持一致的简化版
    import re
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
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            continue
        tmp = {}
        for part in str(raw).split("|"):
            m = re.search(r"(.+?)第(\d+)名", part.strip())
            if not m:
                continue
            scope = m.group(1).strip()
            rank = int(m.group(2))
            if city and city in scope:
                tmp["city"] = rank
            elif scope.endswith("区"):
                tmp["district"] = rank
            else:
                tmp["subdistrict"] = rank
        if tmp:
            detail[key] = tmp
    return json.dumps(detail, ensure_ascii=False)


def import_operation_folder(folder: str) -> None:
    print(f"📂 正在读取运营数据路径：{folder}")
    os.makedirs(folder, exist_ok=True)
    dfs = []
    for fname in os.listdir(folder):
        if not fname.endswith(".xlsx"):
            continue
        fp = os.path.join(folder, fname)
        try:
            df = clean_operation_data(clean_and_load_excel(fp))
            df = drop_percentage_columns(df)
            df = clean_numeric_columns(df, key_col="美团门店ID")
            dfs.append(df)
        except Exception as e:
            print(f"❌ 运营数据文件 {fp} 处理失败: {e}")
    if not dfs:
        print("⚠️ 无运营数据文件导入"); return

    df_all = pd.concat(dfs, ignore_index=True)
    # 兜底：若仍不存在关键列，打印列名并报错提示
    required_cols = ["日期", "美团门店ID"]
    missing = [c for c in required_cols if c not in df_all.columns]
    if missing:
        print(f"❌ 运营数据缺少关键列：{missing}。当前列：{list(df_all.columns)}")
        raise KeyError(missing)
    df_all.drop_duplicates(subset=required_cols, keep="last", inplace=True)
    df_all["日期"] = pd.to_datetime(df_all["日期"]).dt.date
    min_date, max_date = df_all["日期"].min(), df_all["日期"].max()
    store_ids = df_all["美团门店ID"].astype(str).unique().tolist()

    engine = get_engine()
    with engine.begin() as conn:
        for sid in store_ids:
            res = conn.execute(
                text("DELETE FROM operation_data WHERE `美团门店ID` = :sid AND DATE(`日期`) BETWEEN :s AND :e"),
                {"sid": sid, "s": min_date, "e": max_date}
            )
            print(f"✅ 删除 operation_data 中 门店ID={sid} {min_date}~{max_date} 共 {res.rowcount} 条。")

    existing_cols = reflect_existing_columns("operation_data")
    flat_cols = [c for c in existing_cols if c in df_all.columns]
    df_basic = df_all[flat_cols].copy()
    dynamic_df = df_all.drop(columns=flat_cols, errors="ignore")
    dicts = dynamic_df.to_dict(orient="records")
    cleaned = [{k: (None if pd.isna(v) else v) for k, v in d.items()} for d in dicts]
    df_basic["extra_metrics"] = [json.dumps(d, ensure_ascii=False) for d in cleaned]
    if "ROS分" in df_all.columns:
        df_basic["ros_score"] = pd.to_numeric(df_all["ROS分"], errors="coerce").fillna(0).astype(int)
    df_basic["rankings_detail"] = df_all.apply(_build_rankings_detail, axis=1)

    dtype_op = get_dtype_for_operation(df_basic)
    import_to_mysql(df_basic, "operation_data", dtype=dtype_op)
    print(f"✅ 成功导入运营数据，共 {len(df_basic)} 行。")
    
    # 导入成功后清理文件
    print("🗑️ 开始清理已导入的运营数据文件...")
    for fp in [os.path.join(folder, fname) for fname in os.listdir(folder) if fname.endswith(".xlsx")]:
        try:
            # 尝试移动到回收站，如果失败则删除
            try:
                from send2trash import send2trash
                send2trash(fp)
                print(f"🗑️ 已移入回收站：{fp}")
            except ImportError:
                os.remove(fp)
                print(f"🗑️ 已删除：{fp}")
        except Exception as e:
            print(f"⚠️ 清理文件失败 {fp}: {e}")


def import_cpc_folder(folder: str) -> None:
    print(f"📂 正在读取小时级CPC数据路径：{folder}")
    os.makedirs(folder, exist_ok=True)

    engine = get_engine()
    store_mapping = pd.read_sql("SELECT * FROM store_mapping", con=engine)
    dfs = []
    for fname in os.listdir(folder):
        if not fname.endswith(".xlsx"):
            continue
        fp = os.path.join(folder, fname)
        try:
            df = clean_and_load_excel(fp)
            df = process_cpc_dates(df, fname)
            df = match_store_id_for_single_cpc(df, store_mapping)
            df = drop_percentage_columns(df)
            df = clean_numeric_columns(df, key_col='门店名称')
            df = add_datetime_column(df)
            dfs.append(df)
        except Exception as e:
            print(f"❌ CPC数据文件 {fp} 处理失败: {e}")
    if not dfs:
        print("⚠️ 无CPC数据文件导入"); return

    df_all = pd.concat(dfs, ignore_index=True)
    df_all['plan_key'] = (
        df_all['门店ID'].astype(str).str.strip()
        + "_"
        + df_all['推广名称'].astype(str).str.strip()
        + "_"
        + df_all['平台'].astype(str).str.strip()
    )
    # 与老代码一致：重命名后包含 'start_time' 列
    df_all.rename(columns=COLUMN_MAPPING_CPC_HOURLY, inplace=True)
    # 去重键使用 'plan_key' + 'start_time'
    if 'start_time' not in df_all.columns:
        print("⚠️ CPC数据缺少 start_time 列，检查原始表头是否包含‘时段’并已成功解析为‘起始时间’ → start_time。")
    df_all.drop_duplicates(subset=['plan_key', 'start_time'], inplace=True)
    # 老代码在重命名后仍将 'date' 解析为日期
    if 'date' in df_all.columns:
        df_all['date'] = pd.to_datetime(df_all['date']).dt.date
    min_date, max_date = df_all['date'].min(), df_all['date'].max()
    store_ids = df_all['store_id'].astype(str).unique().tolist()

    with engine.begin() as conn:
        for sid in store_ids:
            res = conn.execute(
                text("DELETE FROM cpc_hourly_data WHERE store_id = :sid AND DATE(date) BETWEEN :s AND :e"),
                {"sid": sid, "s": min_date, "e": max_date}
            )
            print(f"✅ 删除 cpc_hourly_data 中 门店ID={sid} {min_date}~{max_date} 共 {res.rowcount} 条。")

    dtype_cpc = get_dtype_for_cpc_hourly(df_all)
    import_to_mysql(df_all, "cpc_hourly_data", dtype=dtype_cpc)
    print(f"✅ 成功导入小时级CPC数据，共 {len(df_all)} 行。")
    
    # 导入成功后清理文件
    print("🗑️ 开始清理已导入的CPC数据文件...")
    for fp in [os.path.join(folder, fname) for fname in os.listdir(folder) if fname.endswith(".xlsx")]:
        try:
            # 尝试移动到回收站，如果失败则删除
            try:
                from send2trash import send2trash
                send2trash(fp)
                print(f"🗑️ 已移入回收站：{fp}")
            except ImportError:
                os.remove(fp)
                print(f"🗑️ 已删除：{fp}")
        except Exception as e:
            print(f"⚠️ 清理文件失败 {fp}: {e}")


