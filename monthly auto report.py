#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monthly_auto_report.py

自动生成月度运营报告：
- 拉取运营数据、CPC 推广数据、商品日明细
- 汇总关键指标并计算环比/趋势
- 导出 Excel 报告（多工作表）和 Markdown 文本报告
"""
import os
import argparse
from datetime import datetime, date
import pandas as pd
from sqlalchemy import text
from config_and_brand import get_mysql_engine, DB_CONNECTION_STRING
from data_fetch import fetch_operation_data, fetch_cpc_hourly_data
from cpc_analysis import compute_cpc_contribution_ratios
from summarize import summarize
import openpyxl


def fetch_product_data(engine, start_date: date, end_date: date) -> pd.DataFrame:
    """
    从 product_daily 表中拉取指定时间段的商品日明细。
    返回包含商品名称、访问人数、购买人数、成交金额的 DataFrame。
    """
    sql = text(
        """
        SELECT `日期` AS date,
               `商品ID`     AS product_id,
               `商品名称`   AS product_name,
               `商品访问人数` AS visits,
               `商品购买人数` AS buys,
               `商品成交金额(优惠后)` AS gmv
        FROM product_daily
        WHERE date BETWEEN :start AND :end
        """
    )
    return pd.read_sql(sql, engine, params={"start": start_date, "end": end_date})


def summarize_top_products(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    汇总商品数据，按购买人数排序，返回 Top N 商品表。
    包括商品名称、总访问、总购买、总 GMV、转化率。
    """
    if df.empty:
        return pd.DataFrame()
    # 聚合
    grp = df.groupby('product_name').agg(
        total_visits=('visits', 'sum'),
        total_buys=('buys', 'sum'),
        total_gmv=('gmv', 'sum')
    )
    # 计算转化率
    grp['conv_rate'] = (grp['total_buys'] / grp['total_visits']).fillna(0)
    # 排序并取前 N
    top = grp.sort_values('total_buys', ascending=False).head(top_n)
    # 重置索引，便于写入 Excel
    return top.reset_index()


def build_report(brand: str, start_date: date, end_date: date, output_dir: str):
    """
    核心函数：拉取数据、汇总指标、生成报告文件。
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    engine = get_mysql_engine()

    # 1. 读取运营数据
    print(f"📊 拉取运营数据：{start_date} 至 {end_date}")
    op_df = fetch_operation_data(brand, start_date, end_date, None, engine)
    op_summary = summarize(op_df, list(op_df.columns.drop('日期')))

    # 2. 读取 CPC 数据
    print(f"💰 拉取CPC推广数据：{start_date} 至 {end_date}")
    cpc_df = fetch_cpc_hourly_data(brand, start_date, end_date, engine)
    cpc_summary = summarize(cpc_df, list(cpc_df.columns.drop('date')))
    cpc_ratios = compute_cpc_contribution_ratios(op_summary, cpc_summary)

    # 3. 读取商品数据
    print(f"🛍️ 拉取商品日明细：{start_date} 至 {end_date}")
    prod_df = fetch_product_data(engine, start_date, end_date)
    top_products = summarize_top_products(prod_df)

    # 4. 生成 Excel 报告
    excel_path = os.path.join(output_dir, f"{brand}_{start_date}_{end_date}_月度报告.xlsx")
    print(f"💾 写入 Excel：{excel_path}")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # 4.1 经营概览
        pd.DataFrame.from_dict(
            {k: [v] for k, v in op_summary.items()}
        ).to_excel(writer, sheet_name='经营概览', index=False)

        # 4.2 推广分析
        df_cpc = pd.DataFrame.from_dict({**cpc_summary, **cpc_ratios}, orient='index', columns=['value'])
        df_cpc.to_excel(writer, sheet_name='推广分析')

        # 4.3 商品分析 Top N
        if not top_products.empty:
            top_products.rename(
                columns={
                    'product_name': '商品名称',
                    'total_visits': '访问总数',
                    'total_buys': '购买总数',
                    'total_gmv': '成交金额(优惠后)',
                    'conv_rate': '访问-购买转化率'
                }, inplace=True
            )
            top_products.to_excel(writer, sheet_name='商品分析', index=False)
        else:
            pd.DataFrame({'提示': ['无商品数据']}).to_excel(writer, sheet_name='商品分析', index=False)

    # 5. 生成 Markdown 文本报告
    md_path = os.path.join(output_dir, f"{brand}_{start_date}_{end_date}_报告.md")
    print(f"✍️ 写入 Markdown：{md_path}")
    with open(md_path, 'w', encoding='utf-8') as md:
        md.write(f"# {brand} 月度运营报告 ({start_date} 至 {end_date})\n\n")
        # 5.1 概览
        md.write("## 一、经营概览\n")
        for k, v in op_summary.items():
            md.write(f"- **{k}**: {v}\n")
        md.write("\n")
        # 5.2 推广
        md.write("## 二、推广分析\n")
        for k, v in cpc_summary.items():
            md.write(f"- **{k}**: {v}\n")
        for k, v in cpc_ratios.items():
            md.write(f"- **{k}**: {v}\n")
        md.write("\n")
        # 5.3 商品
        md.write("## 三、商品分析 Top N\n")
        if not top_products.empty:
            md.write(top_products.to_markdown(index=False, floatfmt=".2f"))
        else:
            md.write("无商品数据可分析。\n")
        md.write("\n")
        # 5.4 建议占位
        md.write("## 四、总结与建议\n")
        md.write("- 待补充运营洞察与建议。\n")

    print("🎉 月度报告生成完成！")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生成月度运营报告')
    parser.add_argument('--brand', required=True, help='推广门店品牌名称')
    parser.add_argument('--start', required=False, help='起始日期 (YYYY-MM-DD)',
                        default=(datetime.today().replace(day=1).strftime('%Y-%m-%d')))
    parser.add_argument('--end', required=False, help='结束日期 (YYYY-MM-DD)',
                        default=(datetime.today().strftime('%Y-%m-%d')))
    parser.add_argument('--out', required=False, help='输出目录', default='./monthly_report')
    args = parser.parse_args()

    # 解析日期
    sd = datetime.strptime(args.start, '%Y-%m-%d').date()
    ed = datetime.strptime(args.end, '%Y-%m-%d').date()

    build_report(args.brand, sd, ed, args.out)
