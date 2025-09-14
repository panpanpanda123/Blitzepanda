import os
from structured_summarizer import METRIC_GROUPS, METRIC_TO_GROUP, CPC_FIELD_ALIASES

def generate_markdown_report(brand_name, start_date, end_date,
                              op_summary, cpc_summary, comparison, ai_text,
                              output_dir="."):
    """
    输出结构化 Markdown 报告，偏向分析师复盘场景
    """
    filename = f"运营月报_分析师版_{brand_name}_{start_date.date()}_{end_date.date()}.md"
    filepath = os.path.join(output_dir, filename)

    def format_number(v):
        return f"{v:.2f}" if isinstance(v, float) else str(v)

    lines = [f"# {brand_name} 运营月报（分析师复盘）",
             f"📅 时间段：{start_date.date()} - {end_date.date()}",
             "\n## 1. 核心运营指标汇总（按模块划分）"]

    # 输出 op_summary，按模块分组
    group_to_keys = {v: k for k, vs in METRIC_GROUPS.items() for v in vs}
    grouped = {}
    for k, v in op_summary.items():
        group = group_to_keys.get(k, "其他")
        grouped.setdefault(group, []).append((k, v))

    for group in sorted(grouped):
        lines.append(f"\n### 📌 {group}")
        for k, v in sorted(grouped[group]):
            lines.append(f"- {k}：{format_number(v)}")

    lines.append("\n## 2. 推广通数据摘要")
    for k, v in cpc_summary.items():
        k_alias = CPC_FIELD_ALIASES.get(k, k)
        lines.append(f"- {k_alias}：{format_number(v)}")

    lines.append("\n## 3. 环比变化与异常标注")
    for k, info in comparison.items():
        tag = "🚨" if info.get("flag", "") in ["增长显著", "下降幅度显著"] else "✅"
        lines.append(f"- {tag} {k}：本期 {info['current']}，上期 {info['last']}，环比 {info['change']}（{info['flag']}）")

    lines.append("\n## 4. AI 分析建议")
    lines.append(ai_text)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ 分析师报告已生成：{filepath}")