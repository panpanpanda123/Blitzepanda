import pandas as pd
from datetime import datetime, date
from sqlalchemy import create_engine, text
from config.config import db_config

def test_monthly_report():
    """测试月报功能"""
    print("开始测试月报功能...")
    
    # 连接数据库
    engine = create_engine(
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"
    )
    
    # 测试商品数据查询
    start_date = date(2025, 7, 1)
    end_date = date(2025, 7, 31)
    brand = "朱桢"
    
    sql = """
    SELECT * FROM product_daily 
    WHERE date BETWEEN %(start_date)s AND %(end_date)s AND brand = %(brand)s
    """
    
    df = pd.read_sql(sql, engine, params={
        'start_date': start_date, 
        'end_date': end_date, 
        'brand': brand
    })
    
    print(f"查询到 {len(df)} 条商品数据")
    
    if not df.empty:
        # 计算商品指标
        product_summary = df.groupby('product_name').agg({
            'visitors': 'sum',
            'buyers': 'sum',
            'gmv_after_discount': 'sum'
        }).reset_index()
        
        total_visitors = df['visitors'].sum()
        total_buyers = df['buyers'].sum()
        total_gmv = df['gmv_after_discount'].sum()
        
        print(f"总商品访问人数: {total_visitors}")
        print(f"总商品购买人数: {total_buyers}")
        print(f"总商品成交金额: {total_gmv:,.2f}")
        
        if total_visitors > 0:
            conversion_rate = total_buyers / total_visitors
            print(f"商品购买转化率: {conversion_rate:.2%}")
        
        # Top 5 商品
        top_products = product_summary.nlargest(5, 'gmv_after_discount')
        print("\nTop 5 商品:")
        for _, row in top_products.iterrows():
            print(f"  {row['product_name']}: {row['gmv_after_discount']:,.2f}")
    
    print("✅ 月报功能测试完成")

if __name__ == '__main__':
    test_monthly_report() 