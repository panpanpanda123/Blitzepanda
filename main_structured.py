import sys
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import simpledialog
from config_and_brand import engine, brand_profile, API_URL, API_KEY, MODEL
from brand_and_data_input import get_user_selected_brand_and_dates
from mysql_data_mapping import get_store_ids
from data_fetch import fetch_operation_data, fetch_cpc_hourly_data, fetch_cpc_by_hour
from summarize import summarize
from last_month_compare import get_previous_period_range, compare_months
from cpc_analysis import compute_cpc_contribution_ratios
from structured_summarizer import structure_summary, compare_with_last
from multi_stage_analysis import run_multi_stage_analysis
from tkinter import messagebox
import json


# ⏳ 动态提示动画
def spinning_cursor(stop_flag):
    while not stop_flag[0]:
        for cursor in '|/-\\':
            sys.stdout.write(f'\r🤖 正在连接 AI 分析中... {cursor}')
            sys.stdout.flush()
            time.sleep(0.15)

def main():
    root = tk.Tk()
    root.withdraw()

    brand, start_date, end_date = get_user_selected_brand_and_dates(root, engine)
    start_date = datetime.strptime(start_date, "%m/%d/%y")
    end_date = datetime.strptime(end_date, "%m/%d/%y")
    store_id, mt_store_id = get_store_ids(brand, engine)

    op_fields = [
        "曝光人数", "访问人数", "购买人数",
        "成交金额(优惠后)", "成交客单价(优惠后)",
        "新好评数", "新评价数", "新客购买人数", "老客购买人数"
    ]

    cpc_fields = [
        "cost", "impressions", "clicks", "orders",
        "merchant_views", "favorites", "interests", "shares"
    ]

    # 当前数据
    op_df = fetch_operation_data(mt_store_id, start_date, end_date, op_fields, engine)
    cpc_df = fetch_cpc_hourly_data(store_id, start_date, end_date, engine)
    op_summary_raw = summarize(op_df, op_fields)
    cpc_summary_raw = summarize(cpc_df, cpc_fields)
    cpc_ratios = compute_cpc_contribution_ratios(op_summary_raw, cpc_summary_raw)

    # 上期数据
    last_start, last_end = get_previous_period_range(start_date, end_date)
    op_df_last = fetch_operation_data(mt_store_id, last_start, last_end, op_fields, engine)
    op_summary_last = summarize(op_df_last, op_fields)
    comparison = compare_with_last(op_summary_raw, op_summary_last)

    # 用户输入
    # 更清晰的格式指引 + 多行输入窗口
    def get_structured_event_input():
        hint = (
            "请粘贴上周的运营事件（支持多条，推荐格式如下）：\n\n"
            "5月13日 | 功能上线：「一键买单功能」，目标：提升转化率（适用：全时段）\n"
            "5月14日 | 产品上新：「啤酒套餐」，目标：提升夜场消费（适用：夜间）\n"
            "5月17日 | 菜单调整：「午市3-4人餐」，目标：提升工作日午餐转化率\n\n"
            "如果无重大事件，请输入“无”"
        )
        messagebox.showinfo("提示", hint)  # 弹窗提示格式

        input_text = simpledialog.askstring(
            "运营期间事件记录",
            "请输入运营事件记录（可直接粘贴多条）",
        )
        return input_text.strip() if input_text else "无"

    # 调用
    factors = get_structured_event_input()
    notes = simpledialog.askstring("补充说明", "请填写您对运营或数据的补充信息（可选）") or "无"

    # —— 多轮 AI 分析 ——
    import json
    from config_and_brand import API_KEY, MODEL, brand_profile
    from multi_stage_analysis import run_multi_stage_analysis

    # 读取品牌基准画像（仅供对比，不展示）
    with open("brand_baseline.json", "r", encoding="utf-8") as f:
        brand_baseline = json.load(f)
    text_profile = brand_profile.get(brand, "")

    # 启动多轮分析，一次完成五份报告
    run_multi_stage_analysis(
        brand=brand,
        start_date=start_date,
        end_date=end_date,
        op_summary=op_summary_raw,
        cpc_summary=cpc_summary_raw,
        comparison=comparison,
        brand_baseline=brand_baseline.get(brand, {}),
        brand_profile_text=text_profile,
        factors=factors,
        api_key=API_KEY,
        model=MODEL,
        output_dir="./multi_report"
    )
if __name__ == "__main__":
    main()
