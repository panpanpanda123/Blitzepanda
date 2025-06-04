# ✅ 模块4：数据获取模块
import pandas as pd

def fetch_operation_data(mt_store_id, start_date, end_date, op_fields, engine):
    """获取运营数据（根据美团门店ID）"""
    base_fields = ["日期"]
    safe_fields = base_fields + [f"`{f}`" for f in op_fields]
    field_clause = ", ".join(safe_fields)

    query = f"""
    SELECT {field_clause}
    FROM operation_data
    WHERE 日期 BETWEEN '{start_date.date()}' AND '{end_date.date()}'
    AND 美团门店ID = '{mt_store_id}'
    """
    df = pd.read_sql(query, engine)
    return df

def fetch_cpc_data(store_id, start_date, end_date, cpc_fields, engine):
    """获取推广通数据（根据门店ID）"""
    base_fields = ["日期"]
    safe_fields = base_fields + [f"`{f}`" for f in cpc_fields]
    field_clause = ", ".join(safe_fields)

    query = f"""
        SELECT 
            date, cost, impressions, clicks, avg_cpc, orders, merchant_views,
            favorites, interests, shares
        FROM cpc_hourly_data
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        AND store_id = {store_id}
    """

    df = pd.read_sql(query, engine)
    return df


def fetch_cpc_hourly_data(store_id, start_date, end_date, engine):
    query = f"""
        SELECT 
            date,
            time_slot,
            cost,
            impressions,
            clicks,
            avg_cpc,
            view_images,
            view_reviews,
            view_address,
            favorites,
            shares,
            orders,
            merchant_views,
            interests,
            view_groupbuy
        FROM cpc_hourly_data
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        AND store_id = {store_id}
    """
    df = pd.read_sql(query, engine)

    # 汇总为每日级别数据（如果你希望按月分析）
    daily_df = df.groupby("date").sum(numeric_only=True).reset_index()
    return daily_df


def fetch_cpc_by_hour(store_id, start_date, end_date, engine):
    query = f"""
        SELECT time_slot,
               SUM(cost) AS cost,
               SUM(clicks) AS clicks,
               SUM(orders) AS orders
        FROM cpc_hourly_data
        WHERE store_id = '{store_id}'
        AND date BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY time_slot
        ORDER BY time_slot
    """
    return pd.read_sql(query, engine)

