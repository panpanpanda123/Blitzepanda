import os

def generate_boss_report(brand_name, start_date, end_date, ai_text, output_dir="."):
    """
    输出适合老板快速阅读的月报：只保留 TL;DR 和核心建议段落
    """
    filename = f"运营月报_老板版_{brand_name}_{start_date.date()}_{end_date.date()}.md"
    filepath = os.path.join(output_dir, filename)

    lines = [f"# {brand_name} 本月运营简报（老板版）",
             f"📅 时间：{start_date.date()} 至 {end_date.date()}\n",
             "## 🧠 运营概况 & 结论 TL;DR"]

    # 提取 TL;DR 段（从 AI 分析中抓取）
    if "TL;DR" in ai_text:
        tldr_block = ai_text.split("TL;DR")[-1].strip().split("\n")[0]
        lines.append(f"👉 {tldr_block.strip('：:')}\n")
    else:
        lines.append("👉 本月总体平稳，暂无重大异常。\n")

    lines.append("## ✅ 核心建议摘要（请拍板的内容）")

    if "机会建议" in ai_text:
        tips_block = ai_text.split("机会建议")[-1].strip()
        for line in tips_block.split("\n"):
            if line.startswith("- "):
                lines.append(line)
            elif line.startswith("##") or line.startswith("1."):
                break
    else:
        lines.append("- 无特别建议，维持当前策略观察即可")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"📄 老板版报告已生成：{filepath}")
