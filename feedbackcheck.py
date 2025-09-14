import pandas as pd
import re
from openai import OpenAI

# 设置Moonshot API客户端
client = OpenAI(
    api_key="sk-lo5a5fud41oV6gcAVAheB5DyinSVh5PiGdmY5pdJaEuIXJa1",  # 替换为您的Moonshot API密钥
    base_url="https://api.moonshot.cn/v1",
)

# 读取Excel文件
file_path = 'C:/Users/豆豆/Downloads/856b4b963d004b5696dcae00ba4622f7.xlsx'
df = pd.read_excel(file_path)

# 假设评分在'评分'列，评论内容在'评价'列
reviews = df[df['评分'] < 4.0]['评价'].dropna().tolist()

# 定义一个函数来使用Moonshot提取关键词和分类
def extract_keywords_and_classify(review):
    completion = client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "system", "content": "你是 Kimi，由 Moonshot AI 提供的人工智能助手。"},
            {"role": "user", "content": f"提取以下评论中的关键词并进行分类：{review}"}
        ],
        temperature=0.3,
    )
    return completion.choices[0].message.content

# 处理每条评论，提取关键词和分类
all_keywords = []
categories = []

for review in reviews:
    result = extract_keywords_and_classify(review)
    keywords = re.findall(r'\b\w+\b', result)
    if keywords:
        all_keywords.extend(keywords)
        categories.append(result)

# 将关键词频率和分类结果保存到Excel文件
word_freq = pd.Series(all_keywords).value_counts()
word_freq_df = pd.DataFrame(list(word_freq.items()), columns=['关键词', '频率']).sort_values(by='频率', ascending=False)
categories_df = pd.DataFrame(categories, columns=['分类结果'])
word_freq_df.to_excel('关键词频率.xlsx', index=False)
categories_df.to_excel('分类结果.xlsx', index=False)

print("关键词统计和分类整理完成。")
