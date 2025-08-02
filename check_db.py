from sqlalchemy import create_engine, text
from config.config import db_config

engine = create_engine(f'mysql+pymysql://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}?charset={db_config["charset"]}')

with engine.connect() as conn:
    result = conn.execute(text('SHOW TABLES'))
    tables = [row[0] for row in result]
    print('Existing tables:', tables)
    
    # Check structure of existing tables
    for table in tables:
        print(f"\nTable: {table}")
        result = conn.execute(text(f'DESCRIBE {table}'))
        columns = [row for row in result]
        for col in columns:
            print(f"  {col[0]} - {col[1]}") 