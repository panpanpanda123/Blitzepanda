import json
import pandas as pd
import requests
from datetime import date
from config_and_brand import engine, API_URL, API_KEY, MODEL


def fetch_review_data(store_id: str, start_date: date, end_date: date) -> pd.DataFrame:
    """
    从 review_data 表中拉取指定门店、指定时间段的评价数据。
    返回 DataFrame 包含 rating_label 和 key_topics 两列。
    """
    sql = f"""
    SELECT rating_label, key_topics
    FROM review_data
    WHERE store_id = '{store_id}'
      AND review_date BETWEEN '{start_date}' AND '{end_date}'
    """
    df = pd.read_sql(sql, engine)
    return df


def aggregate_reviews(df: pd.DataFrame) -> dict:
    """
    对评价数据做聚合，统计：
    - 不同评价类别的数量及占比
    - 各类别下最常见的关键词（前5）
    返回结构化字典。
    """
    total = len(df)
    counts = df['rating_label'].value_counts().to_dict()
    pct = {k: round(v / total, 4) for k, v in counts.items()}

    # 解析关键词 JSON 列并展开
    df_topics = df.copy()
    df_topics['topic'] = df_topics['key_topics'].apply(lambda s: json.loads(s))
    df_topics = df_topics.explode('topic')

    topic_counts = (
        df_topics.groupby(['rating_label', 'topic'])
                 .size()
                 .reset_index(name='count')
    )

    top_topics = {}
    for label in ['好评', '中评', '差评']:
        subset = topic_counts[topic_counts['rating_label'] == label]
        top = subset.nlargest(5, 'count')[['topic', 'count']]
        top_topics[label] = top.to_dict(orient='records')

    return {
        'total_reviews': total,
        'counts': counts,
        'percentages': pct,
        'top_topics': top_topics
    }


def prepare_review_payload(store_id: str, start_date: date, end_date: date) -> dict:
    """
    拉取并聚合后返回给 AI 的 payload。
    """
    df = fetch_review_data(store_id, start_date, end_date)
    agg = aggregate_reviews(df)

    payload = {
        'store_id': store_id,
        'period': f"{start_date} to {end_date}",
        **agg
    }
    return payload


def call_ai_review_analysis(payload: dict) -> str:
    """
    调用 KIMI API 对评价数据进行优势/痛点分析，并给出建议。
    返回 AI 的文本输出。
    """
    prompt = f"""
基于以下门店评价数据，分析：
1) 当前门店做得最好的3个方面（给出出现次数与占比）；
2) 持续被消费者批评的3个痛点（给出出现次数与占比）；
3) 针对以上分别给出具体可执行的改进建议。

数据：
{json.dumps(payload, ensure_ascii=False, indent=2)}
"""
    messages = [
        {'role': 'system', 'content': '你是餐饮门店运营分析专家，请基于提供数据给出结构化分析。'},
        {'role': 'user', 'content': prompt}
    ]
    headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
    body = {'model': MODEL, 'messages': messages, 'temperature': 0.4}
    response = requests.post(API_URL, headers=headers, json=body)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']


# 测试示例
if __name__ == '__main__':
    # 示例参数，请根据实际调用替换
    test_store = '1539873707'
    test_start = date(2025, 5, 1)
    test_end = date(2025, 5, 28)

    payload = prepare_review_payload(test_store, test_start, test_end)
    print('🛠 Test payload:')
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    print('\n🛠 Calling AI for review analysis...')
    result = call_ai_review_analysis(payload)
    print('\n🤖 AI Analysis Result:')
    print(result)
