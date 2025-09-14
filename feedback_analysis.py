import pandas as pd
import re
from openai import OpenAI


# 设置Moonshot API客户端
def setup_api_client(api_key="sk-lo5a5fud41oV6gcAVAheB5DyinSVh5PiGdmY5pdJaEuIXJa1", base_url="https://api.moonshot.cn/v1"):
    return OpenAI(api_key=api_key, base_url=base_url)


# 读取并筛选评论
def read_and_filter_reviews(file_path, score_column='评分', review_column='评价', threshold=4.0):
    df = pd.read_excel(file_path)
    return df[df[score_column] < threshold][review_column].dropna().tolist()


# 提取关键词和分类
def extract_keywords_and_classify(client, model, review):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 Kimi，由 Moonshot AI 提供的人工智能助手。"
                    "你的任务是阅读用户评价，并将评价内容按服务、口味、环境、性价比、"
                    "偶发事件和情绪价值等多个方面进行拆解。请提取关键词并进行分类，"
                    "最后总结出该评价的优点和问题。"
                )
            },
            {
                "role": "user",
                "content": (
                    "请阅读以下用户评价，并按服务、口味、环境、性价比、"
                    "偶发事件和情绪价值等多个方面进行拆解。"
                    "提取关键词并进行分类，总结评价的优点和问题。"
                    "评价内容：{review}"
                )
            },
            {
                "role": "system",
                "content": (
                    "示例：\n"
                    "评价内容：这家餐厅的服务非常差，菜品质量一般。\n"
                    "分类结果：\n"
                    "服务：差\n"
                    "口味：一般\n"
                    "环境：无\n"
                    "性价比：无\n"
                    "偶发事件：无\n"
                    "情绪价值：负面"
                )
            }
        ],
        temperature=0.3,
    )
    return completion.choices[0].message.content


# 统计关键词频率
def count_keywords(keywords):
    return pd.Series(keywords).value_counts()


# 保存结果到Excel文件
def save_results_to_excel(keyword_freq, categories, keyword_file='关键词频率.xlsx', category_file='分类结果.xlsx'):
    keyword_freq_df = pd.DataFrame(list(keyword_freq.items()), columns=['关键词', '频率']).sort_values(by='频率',
                                                                                                       ascending=False)
    categories_df = pd.DataFrame(categories, columns=['分类结果'])
    keyword_freq_df.to_excel(keyword_file, index=False)
    categories_df.to_excel(category_file, index=False)


# 主程序
def main(file_path, api_key):
    # 读取并筛选评论
    reviews = read_and_filter_reviews(file_path)

    # 设置API客户端
    client = setup_api_client(api_key)

    # 提取关键词和分类
    all_keywords = []
    categories = []
    for review in reviews:
        result = extract_keywords_and_classify(client, "moonshot-v1-8k", review)
        keywords = re.findall(r'\b\w+\b', result)
        if keywords:
            all_keywords.extend(keywords)
            categories.append(result)

    # 统计关键词频率
    keyword_freq = count_keywords(all_keywords)

    # 保存结果到Excel文件
    save_results_to_excel(keyword_freq, categories)

    print("关键词统计和分类整理完成。")


# 运行主程序
if __name__ == "__main__":
    main('C:/Users/豆豆/Downloads/856b4b963d004b5696dcae00ba4622f7.xlsx', 'sk-lo5a5fud41oV6gcAVAheB5DyinSVh5PiGdmY5pdJaEuIXJa1')
