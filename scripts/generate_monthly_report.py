# -*- coding: utf-8 -*-
"""
月报生成主入口脚本
功能：从数据库拉取运营数据、CPC数据、商品数据，生成综合月报并输出Excel
基于PDF模板格式，包含环比分析
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import REPORT_OUTPUT_DIR, db_config
from utils.logger import get_logger

def get_database_connection():
    """获取数据库连接"""
    engine = create_engine(
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"
    )
    return engine

def fetch_operation_data(engine, start_date, end_date, brand=None):
    """获取运营数据"""
    sql = """
    SELECT * FROM operation_data 
    WHERE 日期 BETWEEN %(start_date)s AND %(end_date)s
    """
    params = {'start_date': start_date, 'end_date': end_date}
    
    if brand:
        sql += " AND 门店名称 LIKE %(brand)s"
        params['brand'] = f'%{brand}%'
    
    df = pd.read_sql(sql, engine, params=params)
    return df

def fetch_cpc_data(engine, start_date, end_date, brand=None):
    """获取CPC数据"""
    sql = """
    SELECT * FROM cpc_hourly_data 
    WHERE date BETWEEN %(start_date)s AND %(end_date)s
    """
    params = {'start_date': start_date, 'end_date': end_date}
    
    if brand:
        sql += " AND store_name LIKE %(brand)s"
        params['brand'] = f'%{brand}%'
    
    df = pd.read_sql(sql, engine, params=params)
    return df

def fetch_product_data(engine, start_date, end_date, brand=None):
    """获取商品数据"""
    sql = """
    SELECT * FROM product_daily 
    WHERE date BETWEEN %(start_date)s AND %(end_date)s
    """
    params = {'start_date': start_date, 'end_date': end_date}
    
    if brand:
        sql += " AND brand = %(brand)s"
        params['brand'] = brand
    
    df = pd.read_sql(sql, engine, params=params)
    return df

def calculate_period_metrics(df_op, df_cpc, df_prod, period_name):
    """计算指定时期的指标"""
    metrics = {}
    
    if not df_op.empty:
        # 运营指标
        metrics['消费金额'] = df_op['成交金额(优惠后)'].sum()
        metrics['访问人数'] = df_op['访问人数'].sum()
        metrics['购买人数'] = df_op['购买人数'].sum()
        metrics['打卡人数'] = df_op['打卡人数'].sum()
        metrics['收藏人数'] = df_op['累计收藏人数'].sum()
        metrics['曝光次数'] = df_op['曝光次数'].sum()
        
        # 转化率
        if metrics['曝光次数'] > 0:
            metrics['曝光-访问转化率'] = metrics['访问人数'] / metrics['曝光次数']
        if metrics['访问人数'] > 0:
            metrics['访问-购买转化率'] = metrics['购买人数'] / metrics['访问人数']
        if metrics['购买人数'] > 0:
            metrics['打卡转化率'] = metrics['打卡人数'] / metrics['购买人数']
            metrics['收藏转化率'] = metrics['收藏人数'] / metrics['购买人数']
    
    if not df_cpc.empty:
        # CPC指标
        metrics['推广花费'] = df_cpc['cost'].sum()
        metrics['CPC展示次数'] = df_cpc['impressions'].sum()
        metrics['CPC点击次数'] = df_cpc['clicks'].sum()
        
        if metrics['CPC展示次数'] > 0:
            metrics['CPC点击率'] = metrics['CPC点击次数'] / metrics['CPC展示次数']
        if metrics['CPC点击次数'] > 0:
            metrics['CPC平均点击成本'] = metrics['推广花费'] / metrics['CPC点击次数']
    
    if not df_prod.empty:
        # 商品指标
        metrics['商品访问人数'] = df_prod['visitors'].sum()
        metrics['商品购买人数'] = df_prod['buyers'].sum()
        metrics['商品成交金额'] = df_prod['gmv_after_discount'].sum()
        
        if metrics['商品访问人数'] > 0:
            metrics['商品购买转化率'] = metrics['商品购买人数'] / metrics['商品访问人数']
    
    return metrics

def calculate_comparison_metrics(current_metrics, previous_metrics):
    """计算环比指标"""
    comparison = {}
    
    for key in current_metrics:
        if key in previous_metrics and previous_metrics[key] != 0:
            current_val = current_metrics[key]
            previous_val = previous_metrics[key]
            
            # 计算绝对变化
            abs_change = current_val - previous_val
            
            # 计算相对变化
            rel_change = (abs_change / previous_val) * 100
            
            comparison[f'{key}_环比变化'] = abs_change
            comparison[f'{key}_环比变化率'] = rel_change
    
    return comparison

def analyze_product_performance(df_prod):
    """分析商品表现"""
    if df_prod.empty:
        return pd.DataFrame()
    
    # 按商品汇总
    product_summary = df_prod.groupby('product_name').agg({
        'visitors': 'sum',
        'buyers': 'sum',
        'gmv_after_discount': 'sum'
    }).reset_index()
    
    # 计算转化率
    product_summary['访问-购买转化率'] = (product_summary['buyers'] / product_summary['visitors'] * 100).fillna(0)
    
    # 按成交金额排序
    product_summary = product_summary.sort_values('gmv_after_discount', ascending=False)
    
    return product_summary

def generate_comprehensive_monthly_report(start_date, end_date, brand=None, output_dir=None):
    """生成综合月报"""
    logger = get_logger('generate_monthly_report')
    logger.info(f"开始生成 {start_date} 至 {end_date} 的综合月报")
    
    if output_dir is None:
        output_dir = REPORT_OUTPUT_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 连接数据库
    engine = get_database_connection()
    
    # 计算对比期间（上个月）
    current_start = start_date
    current_end = end_date
    
    # 计算上个月的时间范围
    if start_date.month == 1:
        prev_start = date(start_date.year - 1, 12, 1)
        prev_end = date(start_date.year - 1, 12, 31)
    else:
        prev_start = date(start_date.year, start_date.month - 1, 1)
        prev_end = date(start_date.year, start_date.month - 1, 28)  # 简化处理
    
    logger.info(f"当前期间: {current_start} 至 {current_end}")
    logger.info(f"对比期间: {prev_start} 至 {prev_end}")
    
    # 获取当前期间数据
    logger.info("获取当前期间数据...")
    df_op_current = fetch_operation_data(engine, current_start, current_end, brand)
    df_cpc_current = fetch_cpc_data(engine, current_start, current_end, brand)
    df_prod_current = fetch_product_data(engine, current_start, current_end, brand)
    
    # 获取对比期间数据
    logger.info("获取对比期间数据...")
    df_op_prev = fetch_operation_data(engine, prev_start, prev_end, brand)
    df_cpc_prev = fetch_cpc_data(engine, prev_start, prev_end, brand)
    df_prod_prev = fetch_product_data(engine, prev_start, prev_end, brand)
    
    # 计算指标
    logger.info("计算当前期间指标...")
    current_metrics = calculate_period_metrics(df_op_current, df_cpc_current, df_prod_current, "当前")
    
    logger.info("计算对比期间指标...")
    previous_metrics = calculate_period_metrics(df_op_prev, df_cpc_prev, df_prod_prev, "对比")
    
    # 计算环比
    logger.info("计算环比指标...")
    comparison_metrics = calculate_comparison_metrics(current_metrics, previous_metrics)
    
    # 分析商品表现
    logger.info("分析商品表现...")
    product_analysis = analyze_product_performance(df_prod_current)
    
    # 生成报告文件
    report_date = f"{start_date.strftime('%Y-%m')}"
    excel_path = os.path.join(output_dir, f'{brand or "所有品牌"}_{report_date}_综合月报.xlsx')
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # 1. 经营分析概览
        overview_data = []
        for key, value in current_metrics.items():
            if key in previous_metrics:
                change = value - previous_metrics[key]
                change_pct = (change / previous_metrics[key] * 100) if previous_metrics[key] != 0 else 0
                overview_data.append([key, f"{value:,.0f}", f"{previous_metrics[key]:,.0f}", 
                                   f"{change:+,.0f}", f"{change_pct:+.1f}%"])
            else:
                overview_data.append([key, f"{value:,.0f}", "-", "-", "-"])
        
        overview_df = pd.DataFrame(overview_data, 
                                 columns=['指标', '本期', '上期', '环比变化', '环比变化率'])
        overview_df.to_excel(writer, sheet_name='经营分析概览', index=False)
        
        # 2. 详细指标对比
        detailed_data = []
        for key in current_metrics:
            current_val = current_metrics[key]
            prev_val = previous_metrics.get(key, 0)
            change = current_val - prev_val
            change_pct = (change / prev_val * 100) if prev_val != 0 else 0
            detailed_data.append([key, current_val, prev_val, change, change_pct])
        
        detailed_df = pd.DataFrame(detailed_data, 
                                 columns=['指标', '本期值', '上期值', '变化量', '变化率(%)'])
        detailed_df.to_excel(writer, sheet_name='详细指标对比', index=False)
        
        # 3. 商品分析
        if not product_analysis.empty:
            product_analysis.to_excel(writer, sheet_name='商品分析', index=False)
        
        # 4. 转化率分析
        conversion_data = []
        conversion_metrics = ['曝光-访问转化率', '访问-购买转化率', '打卡转化率', '收藏转化率', '商品购买转化率']
        for metric in conversion_metrics:
            if metric in current_metrics and metric in previous_metrics:
                current_pct = current_metrics[metric] * 100
                prev_pct = previous_metrics[metric] * 100
                change_pct = current_pct - prev_pct
                conversion_data.append([metric, f"{current_pct:.2f}%", f"{prev_pct:.2f}%", f"{change_pct:+.2f}%"])
        
        if conversion_data:
            conversion_df = pd.DataFrame(conversion_data, 
                                       columns=['转化率指标', '本期', '上期', '变化'])
            conversion_df.to_excel(writer, sheet_name='转化率分析', index=False)
        
        # 5. CPC推广分析
        cpc_data = []
        cpc_metrics = ['推广花费', 'CPC展示次数', 'CPC点击次数', 'CPC点击率', 'CPC平均点击成本']
        for metric in cpc_metrics:
            if metric in current_metrics and metric in previous_metrics:
                current_val = current_metrics[metric]
                prev_val = previous_metrics[metric]
                change = current_val - prev_val
                change_pct = (change / prev_val * 100) if prev_val != 0 else 0
                cpc_data.append([metric, f"{current_val:,.2f}", f"{prev_val:,.2f}", 
                               f"{change:+,.2f}", f"{change_pct:+.1f}%"])
        
        if cpc_data:
            cpc_df = pd.DataFrame(cpc_data, 
                                 columns=['CPC指标', '本期', '上期', '变化', '变化率'])
            cpc_df.to_excel(writer, sheet_name='CPC推广分析', index=False)
    
    logger.info(f"综合月报生成完成：{excel_path}")
    return excel_path

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='生成综合月度运营报告')
    parser.add_argument('--start', required=True, help='起始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--brand', help='品牌名称（可选）')
    parser.add_argument('--output', help='输出目录（可选）')
    
    args = parser.parse_args()
    
    # 解析日期
    start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
    end_date = datetime.strptime(args.end, '%Y-%m-%d').date()
    
    # 生成报告
    excel_path = generate_comprehensive_monthly_report(start_date, end_date, args.brand, args.output)
    print(f"✅ 综合月报已生成：{excel_path}")

if __name__ == '__main__':
    main()