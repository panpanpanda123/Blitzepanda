# ✅ 模块5：字段缺失处理 + 自动补全

# 顶部加上字段白名单（推荐使用 set 提升查找效率）
FORCE_SUM_FIELDS = {
    "新好评数", "新评价数", "曝光人数", "访问人数", "购买人数", "新客购买人数", "老客购买人数",
    "成交金额(优惠后)", "成交订单数",
    "impressions", "clicks", "cost", "orders", "merchant_views",
    "favorites", "interests", "shares"
}

def format_number(value):
    # 如果是 float 且小数点后为 .00，则转为 int 显示
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return round(value, 2)




def summarize(df, fields, derived_fields=None):
    """
    根据字段汇总数据，如果字段缺失则跳过。支持推导字段的自动计算。
    """

    always_sum = {"新好评数", "新评价数"}

    summary = {}

    for col in fields:
        if col not in df.columns:
            print(f"⚠️ 字段缺失：{col}，已跳过")
            continue
        value = df[col].sum() if col in FORCE_SUM_FIELDS or any(x in col for x in ['金额', '人数', '次数', '笔数']) else \
        df[col].mean()
        summary[col] = format_number(value)

    # ✅ 自动推导指标（如转化率）
    if derived_fields:
        for derived in derived_fields:
            name, numerator, denominator = derived["name"], derived["numerator"], derived["denominator"]
            if numerator in df.columns and denominator in df.columns:
                num_sum = df[numerator].sum()
                den_sum = df[denominator].sum()
                summary[name] = float(num_sum) / float(den_sum) if den_sum != 0 else 0.0
                print(f"✅ 已自动计算字段：{name} = {numerator} / {denominator}")
            else:
                print(f"⚠️ 派生字段跳过（缺原始列）：{name} ← {numerator}/{denominator}")

    if "新好评数" in df.columns and "新评价数" in df.columns:
        good = df["新好评数"].sum()
        all_reviews = df["新评价数"].sum()
        if all_reviews > 0:
            summary["好评率"] = round(good / all_reviews, 4) # 保留4位

    if "新客购买人数" in df.columns and "老客购买人数" in df.columns:
        new = df["新客购买人数"].sum()
        old = df["老客购买人数"].sum()
        total = new + old
        if total > 0:
            summary["复购率"] = round(old / total, 4)

    return summary

# ✅ 添加派生字段的定义
derived_fields = [
    {"name": "访问-购买转化率", "numerator": "购买人数", "denominator": "访问人数"},
    {"name": "点击率", "numerator": "点击（次）", "denominator": "曝光（次）"}
]

__all__ = ["summarize", "derived_fields"]

