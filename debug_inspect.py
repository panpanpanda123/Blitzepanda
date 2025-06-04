import json

def preview_ai_input(op_summary, cpc_summary, cpc_ratios, comparison, cpc_hour_df=None):
    print("\n🛠️【DEBUG】即将发送至 AI 的数据摘要：")

    print("\n📌【运营数据摘要 op_summary】")
    try:
        print(json.dumps(op_summary, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print("❌ 运营数据打印失败：", e)

    print("\n📌【CPC 数据摘要 cpc_summary】")
    try:
        print(json.dumps(cpc_summary, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print("❌ CPC 摘要打印失败：", e)

    print("\n📌【CPC 占比测算 cpc_ratios】")
    try:
        print(json.dumps(cpc_ratios, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print("❌ CPC 占比打印失败：", e)

    print("\n📌【环比变化 comparison】")
    try:
        print(json.dumps(comparison, indent=2, ensure_ascii=False, default=str))
    except Exception as e:
        print("❌ 环比变化打印失败：", e)

    if cpc_hour_df is not None:
        print("\n📌【分时段CPC原始数据（前10行）】")
        try:
            print(cpc_hour_df.head(10).to_string(index=False))
        except Exception as e:
            print("❌ 分时段数据打印失败：", e)
