import pandas as pd
from sqlalchemy import text
from config_and_brand import engine  # 你项目里真实存在

# 获取当前数据库名
with engine.connect() as conn:
    result = conn.execute(text("SELECT DATABASE();"))
    db_name = result.scalar()

# 字段结构查询
sql = f"""
SELECT 
    TABLE_NAME AS 表名, 
    COLUMN_NAME AS 字段名, 
    COLUMN_TYPE AS 类型, 
    IS_NULLABLE AS 是否可为空, 
    COLUMN_DEFAULT AS 默认值, 
    COLUMN_COMMENT AS 字段说明
FROM 
    information_schema.COLUMNS
WHERE 
    TABLE_SCHEMA = '{db_name}'
ORDER BY 
    TABLE_NAME, ORDINAL_POSITION;
"""

# 查询 + 导出
df = pd.read_sql(sql, engine)
df.to_csv("字段结构_导出.csv", index=False, encoding='utf-8-sig')
print("✅ 成功导出字段结构：字段结构_导出.csv")
