"""
app.cleaning

用途：集中放置清洗函数，兼容老版本命名，减少跨文件依赖。
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import pandas as pd


def drop_percentage_columns(df: pd.DataFrame) -> pd.DataFrame:
    """沿用老代码：删除任何列内包含 % 的列。"""
    percent_columns = [col for col in df.columns if df[col].astype(str).str.contains('%').any()]
    return df.drop(columns=percent_columns)


def clean_numeric_columns(df: pd.DataFrame, key_col: Optional[str] = None) -> pd.DataFrame:
    """沿用老代码的数值清洗逻辑。"""
    import numpy as np
    bad_set = set()
    skip = {
        '日期', '时段', '推广门店', '推广名称',
        '门店名称', '门店ID', '美团门店ID', '平台', '城市', '门店所在城市'
    }
    for col in df.columns:
        if df[col].dtype != 'object' or col in skip:
            continue
        s = df[col].astype(str).str.replace(',', '', regex=False).str.strip()
        cleaned = []
        for idx, raw in enumerate(s):
            if raw == '/':
                brand = df.at[idx, key_col] if key_col and key_col in df.columns else None
                bad_set.add((brand, col))
                num = np.nan
            else:
                try:
                    num = float(raw)
                except Exception:
                    num = raw
            cleaned.append(num)
        df[col] = pd.Series(cleaned, index=df.index).replace({np.nan: 0})
    if bad_set:
        print("⚠️ 以下品牌/列在某些行出现“/”，已设为 0，请人工核对：")
        for brand, col in sorted(bad_set, key=lambda x: (str(x[0]), x[1])):
            if brand:
                print(f"  • 品牌 “{brand}” 的列 “{col}”")
            else:
                print(f"  • 列 “{col}”")
    return df


def clean_operation_data(df: pd.DataFrame) -> pd.DataFrame:
    """沿用老代码：去空格，并将“日期”宽松解析为 yyyy-MM-dd 字符串。"""
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce').dt.strftime('%Y-%m-%d')
    return df


def normalize_operation_columns(df: pd.DataFrame) -> pd.DataFrame:
    """将运营数据中的常见列名变体统一为标准列："日期"、"美团门店ID"。

    兼容的候选：
    - 日期列候选：["日期", "统计日期", "报表日期", "date", "Date"]
    - 门店ID列候选：["美团门店ID", "门店ID", "店铺ID", "美团门店Id", "美团门店id", "门店id", "店铺id"]
    """
    df = df.copy()
    # 统一列名两端空白
    df.columns = [str(c).strip() for c in df.columns]

    def _norm(s: str) -> str:
        s = str(s).strip().lower()
        # 去除常见分隔符与括号
        for ch in [" ", "-", "_", ":", "/", "\\", "[", "]", "(", ")", "（", "）"]:
            s = s.replace(ch, "")
        # 统一 id 大小写
        s = s.replace("Id", "id").replace("ID", "id")
        return s

    norm_map = {_norm(c): c for c in df.columns}

    def _find_date_col() -> Optional[str]:
        # 直接匹配
        for key in ["日期", "统计日期", "报表日期", "date", "Date"]:
            k = _norm(key)
            if k in norm_map:
                return norm_map[k]
        # 包含式匹配（包含“日期”或“date”）
        for n, orig in norm_map.items():
            if "日期" in n or n.endswith("date") or n == "date":
                return orig
        return None

    def _find_store_col() -> Optional[str]:
        # 直接匹配
        direct = ["美团门店id", "门店id", "店铺id", "shopid", "poiid", "wm_poi_id", "wm_poiid"]
        for key in direct:
            if key in norm_map:
                return norm_map[key]
        # 组合式匹配：包含“门店/店铺”且包含“id”，或包含“美团门店”
        for n, orig in norm_map.items():
            if ("门店" in n or "店铺" in n) and "id" in n:
                return orig
            if "美团门店" in n:
                return orig
        return None

    date_col = _find_date_col()
    store_col = _find_store_col()

    if date_col and date_col != "日期":
        df.rename(columns={date_col: "日期"}, inplace=True)
    if store_col and store_col != "美团门店ID":
        df.rename(columns={store_col: "美团门店ID"}, inplace=True)

    return df


def match_store_id_for_single_cpc(df: pd.DataFrame, store_mapping: pd.DataFrame) -> pd.DataFrame:
    """按“推广门店/门店ID”在映射表中补齐标准 store_id。"""
    mapping = store_mapping.copy()
    mapping["推广门店"] = mapping["推广门店"].astype(str).str.strip()
    mapping["门店ID"] = mapping["门店ID"].astype(str).str.strip()
    df = df.copy()
    if "门店ID" in df.columns:
        df["门店ID"] = df["门店ID"].astype(str).str.strip()
    if "推广门店" in df.columns and "门店ID" not in df.columns:
        df = df.merge(mapping[["推广门店", "门店ID"]], on="推广门店", how="left")
    return df


def process_cpc_dates(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """按老代码逻辑：从文件名推断年份，将“MM-DD”补全年份，直接回写到 df['日期']。

    - 文件名包含 _YYYYMMDD_YYYYMMDD_，用起始日期推断年份；
    - 对每个 MM-DD 先拼起始年份；若早于起始日期则跨到下一年；
    - 结果写回 '日期' 列（字符串 yyyy-MM-dd），供后续映射为 'date'。
    """
    import re
    from datetime import datetime
    df = df.copy()

    m = re.search(r"_(\d{8})_(\d{8})_", filename)
    if not m or '日期' not in df.columns:
        return df

    start_date = datetime.strptime(m.group(1), "%Y%m%d")
    completed = []
    for raw in df['日期'].astype(str).tolist():
        try:
            parts = raw.strip().split('-')
            if len(parts) != 2:
                completed.append(None)
                continue
            month = int(parts[0])
            day = int(parts[1])
            candidate = datetime(year=start_date.year, month=month, day=day)
            if candidate < start_date:
                candidate = candidate.replace(year=start_date.year + 1)
            completed.append(candidate.strftime('%Y-%m-%d'))
        except Exception:
            completed.append(None)
    df['日期'] = completed
    df = df.dropna(subset=['日期'])
    return df


def add_datetime_column(df: pd.DataFrame) -> pd.DataFrame:
    """沿用老代码：从 '日期' + '时段' 构造 '起始时间'（datetime）。"""
    if "起始时间" in df.columns:
        return df
    if "日期" not in df.columns or "时段" not in df.columns:
        return df
    def extract_start_time(row):
        try:
            date_part = str(row["日期"]).strip()
            time_range = str(row["时段"]).strip()
            start_time = time_range.split("~")[0].strip()
            full = f"{date_part} {start_time}"
            return pd.to_datetime(full, format="%Y-%m-%d %H:%M", errors="coerce")
        except Exception:
            return pd.NaT
    df["起始时间"] = df.apply(extract_start_time, axis=1)
    return df


