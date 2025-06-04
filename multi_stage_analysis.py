from pathlib import Path
from AI_prompt import call_kimi_api
from prompt_builder_refactor import build_five_stage_prompts

def build_output_paths(base_dir, brand, start_date, end_date):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    prefix = f"{brand}_{start_date.date()}_{end_date.date()}"
    return {
        "stage1": base / f"{prefix}_stage1_summary.txt",
        "stage2": base / f"{prefix}_stage2_problems.txt",
        "stage3": base / f"{prefix}_stage3_questions.txt",
        "stage4": base / f"{prefix}_stage4_solutions.txt",
        "stage5": base / f"{prefix}_stage5_tldr.md"
    }

def run_multi_stage_analysis(brand, start_date, end_date, op_summary, cpc_summary,
                             comparison, brand_baseline, brand_profile_text,
                             factors, api_key, model, output_dir="./multi_report"):
    paths = build_output_paths(output_dir, brand, start_date, end_date)
    results = {}

    # 第1轮：概况
    print("🧠 第1轮：概况分析")
    prompts = build_five_stage_prompts(
        brand, start_date, end_date,
        op_summary, cpc_summary, comparison,
        brand_baseline=brand_baseline,
        brand_profile_text=brand_profile_text,
        factors=factors
    )
    messages1 = [
        {"role":"system", "content":"仅基于后续提供的事实与数据，不要编造任何不存在的事件或原因。"},
        {"role":"user",   "content": prompts["stage1"]}
    ]
    results["stage1"] = call_kimi_api(messages1, api_key, model)
    paths["stage1"].write_text(results["stage1"], encoding="utf-8")

    # 第2轮：问题识别
    print("🔍 第2轮：问题识别")
    prompts2 = build_five_stage_prompts(
        brand, start_date, end_date,
        op_summary, cpc_summary, comparison,
        brand_baseline=brand_baseline,
        brand_profile_text=brand_profile_text,
        previous_outputs={"stage1": results["stage1"]},
        factors=factors
    )
    messages2 = [
        {"role":"system", "content":"仅基于以下数据与上轮概况，不要捏造事实。"},
        {"role":"user",   "content": prompts2["stage2"]}
    ]
    results["stage2"] = call_kimi_api(messages2, api_key, model)
    paths["stage2"].write_text(results["stage2"], encoding="utf-8")

    # 第3轮：运营师提问
    print("📣 第3轮：生成提问")
    prompts3 = build_five_stage_prompts(
        brand, start_date, end_date,
        op_summary, cpc_summary, comparison,
        brand_baseline=brand_baseline,
        brand_profile_text=brand_profile_text,
        previous_outputs={"stage2": results["stage2"]},
        factors=factors
    )
    messages3 = [
        {"role":"system", "content":"仅基于以下运营动作与阶段2问题清单，不要编造额外事件。"},
        {"role":"user",   "content": prompts3["stage3"]}
    ]
    results["stage3"] = call_kimi_api(messages3, api_key, model)
    paths["stage3"].write_text(results["stage3"], encoding="utf-8")

    print(f"\n✅ 完成1~3轮，请复制运营师反馈↓\n")
    feedback = input("📥 运营师反馈：\n").strip()

    # 第4轮：策略建议
    print("🛠️ 第4轮：策略建议")
    prompts4 = build_five_stage_prompts(
        brand, start_date, end_date,
        op_summary, cpc_summary, comparison,
        brand_baseline=brand_baseline,
        brand_profile_text=brand_profile_text,
        previous_outputs={"stage2": results["stage2"]},
        user_feedback=feedback,
        factors=factors
    )
    messages4 = [
        {"role":"system", "content":"仅基于以下运营动作、问题清单与反馈，不要凭空添加信息。"},
        {"role":"user",   "content": prompts4["stage4"]}
    ]
    results["stage4"] = call_kimi_api(messages4, api_key, model)
    paths["stage4"].write_text(results["stage4"], encoding="utf-8")

    # 第5轮：TL;DR
    print("📢 第5轮：TL;DR 汇报")
    prompts5 = build_five_stage_prompts(
        brand, start_date, end_date,
        op_summary, cpc_summary, comparison,
        brand_baseline=brand_baseline,
        brand_profile_text=brand_profile_text,
        previous_outputs={"stage4": results["stage4"]},
        factors=factors
    )
    messages5 = [
        {"role":"system", "content":"仅基于以下运营动作与建议摘要，不要自创事实。"},
        {"role":"user",   "content": prompts5["stage5"]}
    ]
    results["stage5"] = call_kimi_api(messages5, api_key, model)
    paths["stage5"].write_text(results["stage5"], encoding="utf-8")

    print("\n🎉 五轮分析完成，报告保存在", output_dir)
    return results
