from structured_summarizer import structure_summary
from AI_prompt import safe_dumps  # 沿用已有的json格式化函数


def build_structured_ai_prompt(brand_name, brand_profile_text, op_summary_raw, cpc_summary_raw,
                                comparison_raw, start_date, end_date,
                                context_factors, cpc_ratios, notes_text,
                               last_start, last_end):
    """
    生成结构化AI Prompt，便于大模型聚焦核心问题与模块分析。
    """
    # 按模块划分的结构化摘要
    op_summary = structure_summary(op_summary_raw)
    cpc_summary = structure_summary(cpc_summary_raw)

    # Header
    prompt = f"""
你是「{brand_name}」的品牌运营顾问，请根据下列结构化数据撰写一份【商业理性】风格的运营分析报告，识别关键问题与机会，并提出明确建议。

【品牌画像】
{brand_profile_text or "暂无画像"}

【时间区间】
{start_date.date()} 至 {end_date.date()}

【本月运营指标（按模块分类）】
{safe_dumps(op_summary)}

【CPC 投放指标（按模块分类）】
{safe_dumps(cpc_summary)}

【系统标记的环比变化与异常】
（当前区间：{start_date.date()} ~ {end_date.date()}，对比区间：{last_start.date()} ~ {last_end.date()}）
{safe_dumps(comparison_raw)}

【推广通投放占比】
{safe_dumps(cpc_ratios)}

【运营期间事件记录】
{context_factors or "无"}

【用户补充说明】
{notes_text or "无"}

---

【任务要求】请严格遵循以下格式输出：
1. 本阶段运营概况（用 3~5 句描述关键变化，定性 + 数据点）
2. 关键问题拆解（从流量结构、转化路径、复购/口碑等角度列出 2~3 个问题）
3. 投放评估（清晰给出 CPC 效率与必要性判断，不重复解释）
4. 机会建议（仅保留与当前问题强相关的建议）
5. 总结汇报（一句话告诉老板“这月干得好不好、为什么、下月要干嘛”）

语气专业理性，允许假设分析，禁止套话与废话。
格式为 Markdown。
"""
    return prompt

def build_five_stage_prompts(brand, start_date, end_date, op_summary, cpc_summary,
                             comparison,
                             brand_baseline=None, brand_profile_text=None,
                             previous_outputs=None, user_feedback=None, factors=None):

    previous_outputs = previous_outputs or {}
    user_feedback = user_feedback or ""
    factors = factors or "无运营动作记录"

    # 第1轮：概况
    prompt1 = f"""
你是品牌「{brand}」的运营分析师，请根据以下数据输出一段简洁的运营概况摘要：

【时间区间】
{start_date.date()} 至 {end_date.date()}

【运营数据】
{op_summary}

【CPC 投放数据】
{cpc_summary}

【与上一周期对比】
{comparison}

【品牌画像（文字）】
{brand_profile_text or "暂无画像"}

【品牌基准数据（总计 & 日均）】
{safe_dumps(brand_baseline or {})}

请完成以下内容（Markdown格式）：
1. 概况总结（2~4 句话）
2. 本周期主要的整体变化趋势
3. 是否出现明显波动（如流量激增/订单骤降等）
""".strip()

    # 第2轮：问题
    prompt2 = f"""
你是品牌「{brand}」的策略分析师，请基于以下数据与上轮概况，识别本周期的 2~3 个关键问题：

【运营与CPC汇总】
{op_summary}
{cpc_summary}

【上轮概况摘要】
{previous_outputs.get('stage1', '')}

【环比变化】
{comparison}

【品牌画像（文字）】
{brand_profile_text or "暂无画像"}

【品牌基准数据（总计 & 日均）】
{safe_dumps(brand_baseline or {})}

输出每个问题包括：
- 问题描述（简洁）
- 所属模块（流量 / 转化 / 复购 / 投放 / 口碑）
- 受影响的关键指标
""".strip()

    # 第3轮：提问
    prompt3 = f"""
你是品牌「{brand}」的运营分析师。**仅基于以下运营动作与数据**，列出本周期最值得运营团队思考的现象，并提出运营师需要补充的背景信息。

要求：
- 每条内容包含：
  - 现象描述：结构化指标变化
  - 涉及模块
  - 建议向运营师提出的问题（以“该周期是否…”、“是否有…”开头）
  - **严禁自创原因或活动**
- 不要给出原因推测，仅列出应提问项

【运营动作记录】
{factors}

【问题清单】
{previous_outputs.get('stage2', '')}

【品牌画像（文字）】
{brand_profile_text or "暂无画像"}

【品牌基准数据（总计 & 日均）】
{safe_dumps(brand_baseline or {})}

""".strip()

    # 第4轮：建议
    prompt4 = f"""
你是品牌「{brand}」的资深策略顾问。**仅基于以下运营动作记录、阶段2问题清单与阶段3反馈**，给出 2~3 条具体可执行建议。

要求：
- 建议必须具体、可执行、针对性强
- **严禁引入未提供的事实**

【问题清单】
{previous_outputs.get('stage2', '')}

【运营动作记录】
{factors}

【运营师反馈】
{user_feedback}

【品牌画像（文字）】
{brand_profile_text or "暂无画像"}

【品牌基准数据（总计 & 日均）】
{safe_dumps(brand_baseline or {})}

【阶段2问题清单】
{previous_outputs.get('stage2', '')}

""".strip()

    # 第5轮：TL;DR
    prompt5 = f"""
你是高层汇报撰写人。请**严格基于前面产生的建议与以下运营动作记录**，输出简短的总结 和三条 bullet，不要编造新的活动或原因。

要求：
- 用一句话概括整体表现
- 用 3 条 bullet 点标出：亮点 / 问题 / 下周期方向
- 语气专业理性，适合复制到汇报PPT中

【运营动作记录】
{factors}

【建议摘要】
{previous_outputs.get('stage4', '')}
""".strip()

    return {
        "stage1": prompt1,
        "stage2": prompt2,
        "stage3": prompt3,
        "stage4": prompt4,
        "stage5": prompt5
    }

