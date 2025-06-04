def compute_cpc_contribution_ratios(op_summary, cpc_summary):
    def safe_div(n, d, precision=2):
        return round(n / d * 100, precision) if d else None

    clicks = cpc_summary.get("clicks", 0)
    impressions = cpc_summary.get("impressions", 0)
    cost = cpc_summary.get("cost", 0)
    orders = cpc_summary.get("orders", 0)

    avg_cpc = round(cost / clicks, 4) if clicks else 0
    cpa = round(cost / orders, 2) if orders else None
    ctr = safe_div(clicks, impressions)
    cvr = safe_div(orders, clicks)

    ratios = {
        "曝光占比": safe_div(impressions, op_summary.get("曝光人数", 0)),
        "点击占比": safe_div(clicks, op_summary.get("访问人数", 0)),
        "花费与成交金额占比": safe_div(cost, op_summary.get("成交金额(优惠后)", 0)),
        "平均点击单价": avg_cpc,
        "CPA": cpa,
        "CTR": ctr,
        "CVR": cvr
    }

    return ratios
