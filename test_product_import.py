import pandas as pd
import re
from sqlalchemy import create_engine, text
from config.config import db_config

def extract_brand_from_filename(filename):
    """从文件名中提取品牌名称"""
    match = re.match(r'^(.+?)_\d{4}_\d{2}_\d{2}-\d{4}_\d{2}_\d{2}', filename)
    if match:
        return match.group(1)
    return None

def create_product_table(engine):
    """创建商品数据表"""
    sql = """
    CREATE TABLE IF NOT EXISTS product_daily (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        date DATE NOT NULL,
        product_id VARCHAR(100) NOT NULL,
        product_name VARCHAR(255) NOT NULL,
        visits INT DEFAULT 0,
        visitors INT DEFAULT 0,
        buyers INT DEFAULT 0,
        gmv_after_discount DECIMAL(12,2) DEFAULT 0,
        brand VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_date (date),
        INDEX idx_brand (brand)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
        print("✅ 商品数据表已创建")

def import_product_data():
    """导入商品数据"""
    # 连接数据库
    engine = create_engine(f'mysql+pymysql://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}?charset={db_config["charset"]}')
    
    # 创建表
    create_product_table(engine)
    
    # 读取数据
    filename = "朱桢_2025_07_01-2025_07_31商品数据导出_2025_08_01.xlsx"
    brand = extract_brand_from_filename(filename)
    print(f"品牌: {brand}")
    
    df = pd.read_excel(f"data/product_data/{filename}")
    print(f"数据行数: {len(df)}")
    print(f"列名: {df.columns.tolist()}")
    
    # 清理数据
    df['brand'] = brand
    df['date'] = pd.to_datetime(df['日期']).dt.date
    
    # 选择关键列
    mapping = {
        '商品ID': 'product_id',
        '商品名称': 'product_name',
        '商品访问人数': 'visitors',
        '商品购买人数': 'buyers',
        '商品成交金额(优惠后)': 'gmv_after_discount'
    }
    
    df_clean = df[['date', 'brand'] + list(mapping.keys())].copy()
    df_clean = df_clean.rename(columns=mapping)
    
    # 插入数据库
    with engine.begin() as conn:
        for _, row in df_clean.iterrows():
            sql = """
            INSERT INTO product_daily (date, product_id, product_name, visitors, buyers, gmv_after_discount, brand)
            VALUES (:date, :product_id, :product_name, :visitors, :buyers, :gmv_after_discount, :brand)
            ON DUPLICATE KEY UPDATE
            visitors = VALUES(visitors),
            buyers = VALUES(buyers),
            gmv_after_discount = VALUES(gmv_after_discount)
            """
            conn.execute(text(sql), row.to_dict())
    
    print("✅ 商品数据导入完成")

if __name__ == '__main__':
    import_product_data() 