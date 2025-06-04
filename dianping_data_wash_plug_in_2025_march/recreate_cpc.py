from sqlalchemy import create_engine, Table, MetaData, Column, DateTime, Float, Integer, String, Date, text
from config import DB_CONNECTION_STRING

def get_engine():
    return create_engine(DB_CONNECTION_STRING)

def recreate_cpc_table():
    engine = get_engine()
    metadata = MetaData()

    # 如果表已存在则先删除
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS cpc_data"))

    # 定义新的表结构
    cpc_data = Table(
        'cpc_data', metadata,
        Column('date', Date),                      # 日期
        Column('start_time', DateTime),            # 起始时间
        Column('time_slot', String(50)),           # 时段
        Column('cost', Float),                     # 花费（元）
        Column('impressions', Integer),            # 曝光（次）
        Column('clicks', Integer),                 # 点击（次）
        Column('avg_cpc', Float),                  # 点击均价（元）
        Column('view_images', Integer),            # 查看图片（次）
        Column('view_reviews', Integer),           # 查看评论（次）
        Column('view_address', Integer),           # 查看地址（次）
        Column('favorites', Integer),              # 收藏（次）
        Column('shares', Integer),                 # 分享（次）
        Column('orders', Integer),                 # 订单量（个）
        Column('merchant_views', Integer),         # 商户浏览量（次）
        Column('interests', Integer),              # 感兴趣（次）
        Column('store_name', String(255)),  # 推广门店
        Column('store_id', String(50)),  # 门店ID
    )

    metadata.create_all(engine)
    print("✅ MySQL 中的 cpc_data 表已重建成功。")

if __name__ == "__main__":
    recreate_cpc_table()
