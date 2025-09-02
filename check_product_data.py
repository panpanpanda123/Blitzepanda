from sqlalchemy import create_engine, text
from config.config import db_config

engine = create_engine(f'mysql+pymysql://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}?charset={db_config["charset"]}')

with engine.connect() as conn:
    # Check if product_daily table exists
    result = conn.execute(text('SHOW TABLES LIKE "product_daily"'))
    tables = [row[0] for row in result]
    
    if 'product_daily' in tables:
        print("✅ product_daily 表存在")
        
        # Check data count
        result = conn.execute(text('SELECT COUNT(*) FROM product_daily'))
        count = result.fetchone()[0]
        print(f"商品数据条数: {count}")
        
        # Check sample data
        result = conn.execute(text('SELECT * FROM product_daily LIMIT 3'))
        rows = result.fetchall()
        print("样本数据:")
        for row in rows:
            print(f"  {row}")
    else:
        print("❌ product_daily 表不存在") 