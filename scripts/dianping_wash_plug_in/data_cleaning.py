# data_cleaning.py（修正版）
import pandas as pd
import re

def clean_operation_data(df):
    # 去除字符串型数据两端的空格
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip()

    # 处理日期格式
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce').dt.strftime('%Y-%m-%d')

    return df

def drop_percentage_columns(df):
    percent_columns = [col for col in df.columns if df[col].astype(str).str.contains('%').any()]
    return df.drop(columns=percent_columns)

def clean_numeric_columns(df):
    for col in df.columns[1:]:
        if df[col].dtype == 'object':
            df[col] = df[col].str.replace(',', '').astype(float, errors='ignore')
    return df

def match_store_id_for_single_cpc(df, store_mapping):
    if '推广门店' in df.columns and '门店ID' not in df.columns:
        df = df.dropna(subset=['推广门店'])

        # 统一字段名：store_mapping 应该有“推广门店” 和 “门店ID”
        latest_mapping = store_mapping[['推广门店', '门店ID']].drop_duplicates('推广门店', keep='last')

        df = df.merge(latest_mapping, how='left', on='推广门店')
    return df

def add_datetime_column(df):
    """
    从 '日期' + '时段' 构造起始时间 datetime 列
    示例：'03-31' + '09:00~10:00' → '2025-03-31 09:00:00'
    """
    if "日期" not in df.columns or "时段" not in df.columns:
        return df

    def extract_start_time(row):
        try:
            date_part = row["日期"]
            time_range = row["时段"]
            start_time = time_range.split("~")[0].strip()
            full = f"{date_part} {start_time}"
            return pd.to_datetime(full, format="%Y-%m-%d %H:%M", errors="coerce")
        except:
            return pd.NaT

    df["起始时间"] = df.apply(extract_start_time, axis=1)
    return df


def process_cpc_dates(df, filename):
    import re
    from datetime import datetime

    # 1. 从文件名提取起止日期（YYYYMMDD），用于确定“本文件数据的起始年份”
    match = re.search(r'_(\d{8})_(\d{8})_', filename)
    if not match:
        raise ValueError(f"文件名 {filename} 中不包含有效的起止日期格式")
    start_date_str = match.group(1)  # 例如 "20241230"
    # end_date_str = match.group(2)  # 实际上无需用到 end_date 进行跨年判断，只需要起始年份
    start_date = datetime.strptime(start_date_str, "%Y%m%d")

    # 2. 读取原始“月-日”字符串（类似 "12-30"、"01-05"），去重后生成列表
    raw_dates = df['日期'].dropna().unique()

    # 3. 针对每个 "MM-DD"，先尝试把它拼到“start_date.year”那一年：
    #    - 若拼出的日期 candidate >= start_date，说明这些就是当年（year = start_year）；
    #    - 否则说明它实际跨年到了下一年（year = start_year + 1）。
    date_candidates = []
    for ds in raw_dates:
        try:
            m_str, d_str = ds.strip().split('-')
            month = int(m_str)
            day = int(d_str)
        except Exception:
            # 如果无法拆分成 MM-DD，直接跳过
            continue

        # attempt 拼成年初候选日期
        try:
            candidate = datetime(year=start_date.year, month=month, day=day)
        except ValueError:
            # 如果拼不成合法日期（比如“02-30”），跳过
            continue

        # 如果 candidate 比 start_date 还小，说明它要跨年到下一年
        if candidate < start_date:
            candidate = candidate.replace(year=start_date.year + 1)

        # 收集 (candidate_datetime, 原始字符串) 以便后面排序
        date_candidates.append((candidate, ds))

    # 4. 把上述 (candidate, ds) 按 candidate 从早到晚排序，这样得到的顺序即为 文件内部的真实时间线
    date_candidates.sort(key=lambda x: x[0])

    # 5. 生成一个从“原始字符串”到“带年份完整日期”的映射
    completed_map = {
        ds: candidate.strftime("%Y-%m-%d")
        for candidate, ds in date_candidates
    }

    # （可选）调试用：打印一下本文件的映射关系，确认是不是符合预期
    # print(f"[DEBUG] process_cpc_dates 映射 for {filename}:")
    # for cand, ds in date_candidates:
    #     print(f"    {ds} → {cand.strftime('%Y-%m-%d')}")

    # 6. 最后替换 DataFrame 中的 df['日期']
    df['日期'] = df['日期'].map(completed_map)

    # 7. 彻底去除掉仍然是 NaN 的行（如果有非法“月-日”格式，就会在映射后变成 NaN，被 drop）
    return df.dropna(subset=['日期'])
