def extract_keywords_and_classify(client, model, review):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 Kimi，由 Moonshot AI 提供的人工智能助手。"
                    "你的任务是阅读以下用户评价，并将评价内容按服务、口味、环境、性价比、"
                    "偶发事件和情绪价值等多个方面进行拆解。请提取关键词并进行分类，"
                    "最后总结出该评价的优点和问题。"
                )
            },
            {"role": "user", "content": f"评价内容：{review}"}
        ],
        temperature=0.3,
    )
    return completion.choices[0].message.content
