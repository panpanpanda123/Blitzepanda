import calendar
from datetime import timedelta

def get_previous_period_range(start_date, end_date):
    """
    自动获取前一段等长时间区间，适配自定义时间范围对比需求。
    例如选中10天，则自动返回前10天。
    """
    delta = end_date - start_date
    last_end = start_date - timedelta(days=1)
    last_start = last_end - delta
    return last_start, last_end

def compare_months(current_summary, last_summary):
    """计算环比变化，返回结构清晰的比较结果"""
    comparison = {}
    for key in current_summary:
        curr = current_summary[key]
        last = last_summary.get(key)
        if last is None or last == 0:
            delta = None
        else:
            delta = (curr - last) / last * 100
        comparison[key] = {
            "current": round(curr, 2),
            "last": round(last, 2) if last else None,
            "change": f"{delta:+.1f}%" if delta is not None else "N/A"
        }
    return comparison
