from sqlalchemy import create_engine, text
from config.config import db_config

engine = create_engine(f'mysql+pymysql://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}?charset={db_config["charset"]}')

with engine.connect() as conn:
    # Check operation_data table
    result = conn.execute(text('SELECT COUNT(*) FROM operation_data'))
    count = result.fetchone()[0]
    print(f"运营数据条数: {count}")
    
    if count > 0:
        # Check sample data
        result = conn.execute(text('SELECT * FROM operation_data LIMIT 3'))
        rows = result.fetchall()
        print("样本运营数据:")
        for row in rows:
            print(f"  {row}")
        
        # Check columns
        result = conn.execute(text('DESCRIBE operation_data'))
        columns = result.fetchall()
        print("\n运营数据表结构:")
        for col in columns:
            print(f"  {col[0]} - {col[1]}")
    else:
        print("❌ 运营数据表为空") 