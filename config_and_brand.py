# ✅ 模块1：数据库连接与品牌画像配置

from sqlalchemy import create_engine

# 数据库连接字符串
DB_CONNECTION_STRING = 'mysql+pymysql://root:xpxx1688@localhost:3306/dianping'
engine = create_engine(DB_CONNECTION_STRING)

HORLY_CPC_TABLE_NAME = 'cpc_hourly_data'

# 大模型 API 配置
API_URL = 'https://api.moonshot.cn/v1/chat/completions'
API_KEY = 'sk-6BEaBQDqxNRofpO8PjNgbFFzppxZH1u8NIVGg84zmkVZWq1D'
MODEL = 'kimi-latest'

# 品牌画像（可继续添加其他品牌）
brand_profile = {
    "流杯酒肆": {
        "基本定位": "位于上海静安寺，定位为社交型中餐酒馆，客单价约300元，融合定制调酒和中式小吃。",
        "目标人群": "25-35岁都市白领女性，重视社交体验、审美氛围与互动感。",
        "关键场景": "朋友聚会、女生小聚、夜间约会、节日送杯活动。",
        "核心亮点": "“留杯玩法”制造复购仪式感，调酒互动增强社交记忆点。",
        "当前阶段目标": "提升老客复购率与到店频次，辅助引导线上传播提升自然流量。",
        "潜在问题": "门店位置在二楼，进店率低；调酒环节依赖服务质量。",
        "品牌调性": "中式雅致+潮流打卡+地道台州菜，希望客人能轻松愉快地玩起来。",
        "是否投放 CPC": "是",
        "是否售卖线上代金券/团购": "是",
        "是否主打线下转化": "否",
        "策略备注": "品牌重视大众点评，会引导客人尽量购买使用线上交易产品及优惠活动"
    },
    "椿野里": {
        "基本定位": "位于上海徐家汇，定位为中餐餐厅，客单价约120元，菜品融合传统云贵本地特色和现代创意",
        "目标人群": "25-35岁都市白领女性，重视社交体验、审美氛围与互动感。",
        "关键场景": "朋友聚会、女生小聚、同事聚餐。",
        "核心亮点": "暂无",
        "当前阶段目标": "提升消费吸引力",
        "潜在问题": "周边竞对进店目的明确，本店缺少核心竞争力，导致消费吸引力不足，无明确进店理由，并且门店过度依赖站内流量，推广通花费过大，完全无站外流量补充；用餐时长较长，且很少排队，翻台率低",
        "品牌调性": "没什么特色，性价比挺高的",
        "是否投放 CPC": "是",
        "是否售卖线上代金券/团购": "是",
        "是否主打线下转化": "否",
        "策略备注": "品牌重视大众点评，会引导客人尽量购买使用线上交易产品及优惠活动"
    },
    "进士食堂": {
        "基本定位": "位于上海闵行区，定位为韩式烤肉自助，客单价约100元，菜品主要为烤肉和正宗韩料",
        "目标人群": "20-30岁中低消费的年轻群体，重视性价比、品牌和趣味体验。",
        "关键场景": "学生聚餐、朋友小聚、同事聚餐。",
        "核心亮点": "性价比高",
        "当前阶段目标": "提升新客吸引力",
        "潜在问题": "周边竞对走低价竞争，吸走较多客流",
        "品牌调性": "全球600+的百元自助烤肉连锁",
        "是否投放 CPC": "是",
        "是否售卖线上代金券/团购": "是",
        "是否主打线下转化": "否",
        "策略备注": "品牌重视大众点评，会引导客人尽量购买使用线上交易产品及优惠活动"
    }
    # 其他品牌可追加
}

def get_mysql_engine():
    return engine
