# ✅ structured_summarizer.py

from collections import defaultdict

# ✅ 中英文映射（供报告用）
CPC_FIELD_ALIASES = {
    "cost": "推广总花费",
    "impressions": "广告曝光量",
    "clicks": "广告点击量",
    "avg_cpc": "平均点击单价",
    "orders": "广告订单数",
    "merchant_views": "商家页浏览量",
    "favorites": "收藏次数",
    "interests": "感兴趣行为数",
    "shares": "分享次数"
}

def format_number(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return round(value, 2)

# ✅ 定义字段归属模块
METRIC_GROUPS = {
    "流量类": ["曝光人数", "访问人数", "扫码人数", "扫码收藏人数", "扫码打卡人数"],
    "转化类": ["购买人数", "访问-购买转化率", "新客购买人数", "老客购买人数", "复购率"],
    "交易类": ["成交金额(优惠后)", "成交客单价(优惠后)", "用户实付金额", "成交订单数"],
    "口碑类": ["新好评数", "新评价数", "好评率", "新中差评数", "中差评率"],
    "CPC类": ["impressions", "clicks", "cost", "avg_cpc", "orders", "CTR", "CVR", "CPA"],
}

# ✅ 反向映射字段 -> 模块名
METRIC_TO_GROUP = {col: group for group, cols in METRIC_GROUPS.items() for col in cols}


def structure_summary(summary_dict):
    """
    将 summary_dict 转换为结构化模块形式：{"流量类": {...}, "交易类": {...}, ...}
    同时加入派生字段：中差评数、中差评率（若字段存在）
    """
    summary = dict(summary_dict)

    if "新评价数" in summary and "新好评数" in summary:
        summary["新中差评数"] = summary["新评价数"] - summary["新好评数"]
        if summary["新评价数"]:
            summary["中差评率"] = round(summary["新中差评数"] / summary["新评价数"], 4)

    grouped = defaultdict(dict)
    for k, v in summary.items():
        group = METRIC_TO_GROUP.get(k, "其他")
        grouped[group][k] = format_number(v)
    return dict(grouped)


def compare_with_last(current_summary, last_summary, threshold=10):
    """
    对比本月与上月，标记变化率与异常字段。
    返回格式：{
        字段名: {
            "current": 123,
            "last": 234,
            "change": "+xx%",
            "type": "模块名",
            "flag": "下降幅度显著" / "增长显著" / "正常"
        }, ...
    }
    """
    comparison = {}
    for key, curr in current_summary.items():
        last = last_summary.get(key)
        if last is None or last == 0:
            delta = None
            pct = "N/A"
            flag = "无上期数据"
        else:
            delta = (curr - last) / last * 100
            pct = f"{delta:+.1f}%"
            if abs(delta) >= threshold:
                flag = "增长显著" if delta > 0 else "下降幅度显著"
            else:
                flag = "正常"
        comparison[key] = {
            "current": format_number(curr),
            "last": format_number(last) if last is not None else None,
            "change": pct,
            "type": METRIC_TO_GROUP.get(key, "其他"),
            "flag": flag
        }
    return comparison
