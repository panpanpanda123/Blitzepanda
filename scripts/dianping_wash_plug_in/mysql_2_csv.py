from sqlalchemy import create_engine
import pandas as pd
import os

# 把 root:密码@ 改成实际的 root:您的密码@
engine = create_engine(
    "mysql+pymysql://root:xpxx1688@localhost:3306/dianping?charset=utf8mb4"
)

# 执行查询，获取 store_mapping 表
df = pd.read_sql(
    "SELECT 推广门店 AS store_name, 门店ID AS store_id FROM store_mapping",
    engine
)

# 确保输出目录存在
output_path = r"D:\pythonproject\pythonProject\config\store_mapping.csv"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# 将结果写入 CSV
df.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"✅ 导出完成 → {output_path}")
