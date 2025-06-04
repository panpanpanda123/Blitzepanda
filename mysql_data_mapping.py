# ✅ 模块3：门店信息匹配

import pandas as pd

def get_store_ids(brand_name, engine):
    """
    根据品牌名（推广门店）从数据库获取对应的 门店ID 和 美团门店ID
    """
    df = pd.read_sql("SELECT * FROM store_mapping", engine)
    df["推广门店"] = df["推广门店"].str.strip()

    match = df[df["推广门店"] == brand_name]
    if match.empty:
        raise ValueError(f"❌ 未找到品牌名“{brand_name}”的对应门店信息，请检查 store_mapping 表。")

    store_id = match.iloc[0]["门店ID"]
    mt_store_id = match.iloc[0]["美团门店ID"]

    print(f"✅ 已获取门店ID：{store_id}，美团门店ID：{mt_store_id}")
    return store_id, mt_store_id
