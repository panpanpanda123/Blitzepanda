#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quarterly_analysis.py

功能：
1. 自动获取指定品牌门店的服务起始日期和服务结束日期
2. 按自然季度（Q1/Q2/Q3/Q4）切分服务期内的数据
3. 分别汇总每个完整季度的运营数据和推广数据
4. 计算最后两个完整季度的环比（QoQ）和同比（YoY）指标
5. 将结果导出到 Excel（包含“季度汇总”表、“完整季度数据”表、“最后两季度”表、“同比_环比结果”表）

使用方法：
    1. 在脚本顶部修改以下常量：
       BRAND：要分析的品牌名称（与 store_mapping 表中的 “推广门店” 字段保持一致）
       SERVICE_END：服务到期日期，格式 YYYY-MM-DD
       OUTPUT_PATH：导出 Excel 的完整路径（例如 "./output/韩味岛_季度分析.xlsx"）
    2. 直接在 PyCharm 中运行，无需传入命令行参数。

依赖：
    - Python 3.7+
    - pandas
    - SQLAlchemy + PyMySQL（请确保在当前虚拟环境中已安装）
    - config_and_brand.py（包含数据库 engine 配置）
    - mysql_data_mapping.get_store_ids(brand, engine) → 返回 (store_id, mt_store_id)
    - data_fetch.fetch_operation_data(...)
    - data_fetch.fetch_cpc_hourly_data(...)
    - summarize.summarize(...)
"""

import os
from pathlib import Path
import pandas as pd
from pandas.tseries.offsets import QuarterEnd

# ========== ▶ 在这里填写品牌、结束日期和输出路径（无需动其它地方） ==========

# 品牌名称，必须与数据库中 store_mapping 表的 “推广门店” 字段一致
BRAND = "韩味岛"

# 服务结束日期（合同到期当天或最后一次拉取数据的日期），格式 YYYY-MM-DD
SERVICE_END = "2025-05-31"

# 导出结果的 Excel 路径，可以写相对路径或绝对路径
OUTPUT_PATH = "./output/韩味岛_季度分析.xlsx"

# ==========================================================================

from config_and_brand import engine
from mysql_data_mapping import get_store_ids
from data_fetch import fetch_operation_data, fetch_cpc_hourly_data
from summarize import summarize

def split_quarters(start: pd.Timestamp, end: pd.Timestamp):
    """
    把 [start, end] 区间切成所有完整的自然季度（Q1/Q2/Q3/Q4）
    返回 [(q_start, q_end), ...] 列表，不包含不完整的头尾季度
    """
    start = pd.Timestamp(start).normalize()
    first_q_end = (start + QuarterEnd(0))
    first_q_begin = first_q_end - QuarterEnd(1) + pd.Timedelta(days=1)

    # 如果 start 在季度中间，则下一个完整季度从 first_q_end+1 天开始
    if start > first_q_begin:
        first_q_begin = first_q_end + pd.Timedelta(days=1)
        first_q_end = (first_q_begin + QuarterEnd(0)) - pd.Timedelta(days=1)

    end = pd.Timestamp(end).normalize()
    last_q_end = (end - QuarterEnd(1)) + QuarterEnd(0)
    if end < last_q_end:
        last_q_end = last_q_end - QuarterEnd(1)

    if first_q_end > last_q_end:
        return []

    q_ends = pd.date_range(first_q_end, last_q_end, freq="Q-DEC")
    spans = []
    for q_end in q_ends:
        q_begin = q_end - QuarterEnd(1) + pd.Timedelta(days=1)
        spans.append((q_begin, q_end))
    return spans

def collect_quarter_summaries(mt_store_id, store_id, quarters, op_fields, cpc_fields):
    """
    对每个季度（q_start, q_end）：
      - 拉取运营数据(fetch_operation_data)
      - 拉取推广数据(fetch_cpc_hourly_data)
      - 对两个 DataFrame 分别调用 summarize，得到 dict
      - 合并两个 dict，加上 '季度'、'q_start'、'q_end' 字段，返回列表
    """
    rows = []
    for q_start, q_end in quarters:
        op_df = fetch_operation_data(mt_store_id, q_start, q_end, op_fields, engine)
        cpc_df = fetch_cpc_hourly_data(store_id, q_start, q_end, engine)

        op_sum = summarize(op_df, op_fields)        # dict，例如 {'曝光人数': 382000, '访问人数': 5873, ...}
        cpc_sum = summarize(cpc_df, cpc_fields)      # dict，例如 {'cost': 1234.5, 'clicks': 678, ...}

        # 构造行字典
        row = {"季度": f"{q_start.to_period('Q')}"}  # 例如 "2025Q1"
        # 将 op_sum 的每个 key/value 加入 row，列名前加 "op_"
        for k, v in op_sum.items():
            row[f"op_{k}"] = v
        # 将 cpc_sum 加入 row，列名前加 "cpc_"
        for k, v in cpc_sum.items():
            row[f"cpc_{k}"] = v
        # 存储季度起止，便于排序和检查
        row["q_start"] = q_start
        row["q_end"]   = q_end
        rows.append(row)

    return rows

def compute_qoq_yoy(df: pd.DataFrame):
    """
    在 df（已按 q_start 升序排序）上，取最后两个完整季度进行对比，计算环比QoQ和同比YoY。
    自动根据 df 中以 "op_" 和 "cpc_" 开头的列来进行对比，避免 KeyError。
    返回：
      - df_sorted: 按季度升序排列的原始 df
      - compare_df: 行是指标名，列为 ['前一季度', '当前季度', 'QoQ(%)', '上一年同季度', 'YoY(%)']
    """
    df_sorted = df.sort_values("q_start").reset_index(drop=True)
    if len(df_sorted) < 2:
        raise ValueError("不足两个完整季度，无法计算环比。")

    last_two = df_sorted.tail(2).reset_index(drop=True)
    prev_q = last_two.loc[0, "季度"]
    curr_q = last_two.loc[1, "季度"]

    # 提取所有要比较的指标列：以 "op_" 或 "cpc_" 开头，但不包含 q_start、q_end
    metric_cols = [col for col in df_sorted.columns if col.startswith("op_") or col.startswith("cpc_")]

    # 找到上一年同季度的行
    def find_same_q_year(q_label):
        # q_label 示例："2025Q1"
        year = int(q_label[:4])
        quarter_label = q_label[4:]  # "Q1"、"Q2" 等
        last_year_label = f"{year - 1}{quarter_label}"
        # df_sorted 中 "季度" 列以 f"{q_start.to_period('Q')}" 形式保存
        candidate = df_sorted[df_sorted["季度"] == last_year_label]
        return candidate.iloc[0] if not candidate.empty else None

    same_prev_year_prev = find_same_q_year(prev_q)
    same_prev_year_curr = find_same_q_year(curr_q)

    records = []
    for col in metric_cols:
        prev_val = last_two.loc[0, col]
        curr_val = last_two.loc[1, col]

        # 计算 QoQ
        if isinstance(prev_val, (int, float)) and prev_val != 0:
            try:
                qoq = (curr_val - prev_val) / prev_val * 100
                qoq_str = f"{qoq:+.2f}%"
            except Exception:
                qoq_str = "N/A"
        else:
            qoq_str = "N/A"

        # 计算 YoY
        if same_prev_year_curr is not None and col in same_prev_year_curr:
            same_val = same_prev_year_curr[col]
            if isinstance(same_val, (int, float)) and same_val != 0:
                try:
                    yoy = (curr_val - same_val) / same_val * 100
                    yoy_str = f"{yoy:+.2f}%"
                except Exception:
                    yoy_str = "N/A"
                same_display = same_val
            else:
                yoy_str = "N/A"
                same_display = "N/A"
        else:
            yoy_str = "N/A"
            same_display = "N/A"

        records.append({
            "指标": col,
            "前一季度": prev_val,
            "当前季度": curr_val,
            "QoQ(%)": qoq_str,
            "上一年同季度": same_display,
            "YoY(%)": yoy_str
        })

    compare_df = pd.DataFrame(records).set_index("指标")
    return df_sorted, compare_df

def main():
    # ─────────── 1. 参数处理（BRAND、SERVICE_END、OUTPUT_PATH 已在顶部定义） ───────────
    brand = BRAND
    try:
        service_end = pd.to_datetime(SERVICE_END).normalize()
    except Exception:
        print(f"❌ 日期格式不正确：{SERVICE_END}。请使用 YYYY-MM-DD。")
        return

    # ─────────── 2. 获取 store_id 和 mt_store_id ───────────
    try:
        store_id, mt_store_id = get_store_ids(brand, engine)
        print(f"✅ 已获取门店ID：{store_id}，美团门店ID：{mt_store_id}")
    except Exception as e:
        print(f"❌ 无法获取品牌“{brand}”的门店信息：{e}")
        return

    # ─────────── 3. 查询服务开始日期 ───────────
    sql = f"""
        SELECT MIN(日期) AS min_dt
        FROM operation_data
        WHERE 美团门店ID = '{mt_store_id}'
    """
    try:
        df_min = pd.read_sql(sql, engine)
        service_start = pd.to_datetime(df_min["min_dt"].iat[0])
    except Exception as e:
        print(f"❌ 查询服务起始日期失败：{e}")
        return

    if pd.isna(service_start):
        print(f"❌ 品牌“{brand}”在 operation_data 表中没有数据，无法分析。")
        return

    # ─────────── 4. 切分完整自然季度 ───────────
    quarters = split_quarters(service_start, service_end)
    if not quarters:
        print("❌ 在指定服务区间内没有找到任何完整自然季度，无法继续。")
        return

    # ─────────── 5. 定义需要汇总的字段（可按需调整） ───────────
    op_fields  = [
        "曝光人数", "访问人数", "购买人数", "成交金额(优惠后)",
        "成交客单价(优惠后)", "新好评数", "新评价数",
        "新客购买人数", "老客购买人数"
    ]
    cpc_fields = ["cost", "impressions", "clicks", "orders", "merchant_views", "favorites", "interests", "shares"]

    # ─────────── 6. 按季度拉取并汇总数据 ───────────
    rows = collect_quarter_summaries(mt_store_id, store_id, quarters, op_fields, cpc_fields)
    if not rows:
        print("❌ 没有任何季度数据，rows 为空。")
        return

    df_quarters = pd.DataFrame(rows)
    df_quarters = df_quarters.sort_values("q_start").reset_index(drop=True)

    # ─────────── 7. 计算最后两个季度的环比 + 同比 ───────────
    try:
        df_all, df_compare = compute_qoq_yoy(df_quarters)
    except ValueError as ve:
        print(f"❌ {ve}")
        return

    # ─────────── 8. 导出到 Excel ───────────
    output_path = Path(OUTPUT_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(str(output_path), engine="xlsxwriter") as writer:
        # “季度汇总” sheet：去掉 q_start、q_end，仅保留汇总指标
        df_quarters.drop(columns=["q_start", "q_end"]).to_excel(
            writer, sheet_name="季度汇总", index=False
        )

        # “完整季度数据” sheet：包含 q_start、q_end，方便检查
        df_quarters.to_excel(writer, sheet_name="完整季度数据", index=False)

        # “最后两季度” sheet：只保留最后两个季度（并去掉 q_start、q_end）
        df_quarters.tail(2).drop(columns=["q_start", "q_end"]).to_excel(
            writer, sheet_name="最后两季度", index=False
        )

        # “同比_环比结果” sheet：输出 compute_qoq_yoy 返回的 compare_df
        df_compare.to_excel(writer, sheet_name="同比_环比结果")

    print(f"✅ 已成功导出季度分析到：{output_path}")

if __name__ == "__main__":
    main()
