#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
summary_tool.py

按 store_id 和 日期区间，基于已打标的 review_ai_tag 数据，
调用 Kimi AI 生成区间评价分析，并写入 review_ai_summary 表。

已内置测试参数，直接运行即可，不再需要命令行参数。
"""

import os
import json
import pymysql
from pymysql.cursors import DictCursor
import requests

# ====== 配置区，请根据您的环境修改 ======
DB_PARAMS = {
    'host':       'localhost',
    'user':       'root',
    'password':   'xpxx1688',
    'db':         'dianping',
    'charset':    'utf8mb4',
    'cursorclass': DictCursor
}
from config_and_brand import API_URL, API_KEY, MODEL
# 测试时使用的门店和时间区间
TEST_STORE_ID = "1539873707"
TEST_START    = "2025-05-01"
TEST_END      = "2025-05-28"
# =======================================

def get_connection():
    return pymysql.connect(**DB_PARAMS)

def fetch_tag_records(store_id: str, start_date: str, end_date: str) -> list:
    sql = """
        SELECT t.raw_id AS id,
               JSON_UNQUOTE(JSON_EXTRACT(t.tag_json, '$.sentiment')) AS sentiment,
               JSON_EXTRACT(t.tag_json, '$.topics')             AS topics,
               JSON_UNQUOTE(JSON_EXTRACT(t.tag_json, '$.severity'))    AS severity,
               JSON_UNQUOTE(JSON_EXTRACT(t.tag_json, '$.special_flag')) AS special_flag
        FROM review_ai_tag t
        JOIN review_data    r ON r.id = t.raw_id
        WHERE r.store_id = %s
          AND r.review_date BETWEEN %s AND %s
        ORDER BY r.review_date
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(sql, (store_id, start_date, end_date))
        rows = cur.fetchall()
    conn.close()
    records = []
    for r in rows:
        topics = json.loads(r['topics']) if r['topics'] else []
        records.append({
            "id":           r['id'],
            "sentiment":    r['sentiment'],
            "topics":       topics,
            "severity":     r['severity'],
            "special_flag": r['special_flag']
        })
    return records

def call_summary_api(records: list, store_id: str, start: str, end: str) -> (dict, str):
    system_prompt = (
        f"你是资深餐饮运营分析师。"
        f"请基于门店 {store_id} 在 {start} 到 {end} 期间的评价标签，"
        "生成如下内容的 JSON：\n"
        "1) praise_top: Top 3 被称赞的方面，需包含 count 和 pct（占比）；\n"
        "2) problem_top: Top 5 主要问题，需包含 count 和 pct（占比）；\n"
        "3) advice: 针对每个问题给一句改进建议。\n"
        "仅返回 JSON，字段名按上文保留，不要多余注释。"
    )
    data_str = json.dumps(records, ensure_ascii=False, indent=2)
    user_prompt = f"标签列表：\n{data_str}"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        "temperature": 0,
        "max_tokens": 8192
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post(API_URL, json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    ai_version = data.get("model", "")
    content    = data["choices"][0]["message"]["content"]
    summary = json.loads(content)
    return summary, ai_version

def save_summary(store_id: str, start: str, end: str, summary: dict, version: str):
    sql = """
        INSERT INTO review_ai_summary (
            store_id, period_start, period_end, summary_json, ai_version, generated_at
        ) VALUES (%s,%s,%s,%s,%s,NOW())
        ON DUPLICATE KEY UPDATE
          summary_json = VALUES(summary_json),
          ai_version   = VALUES(ai_version),
          generated_at = VALUES(generated_at)
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(sql, (
            store_id,
            start,
            end,
            json.dumps(summary, ensure_ascii=False),
            version
        ))
    conn.commit()
    conn.close()

def generate_summary(store_id: str, start: str, end: str):
    print(f"📑 拉取标签 → 门店 {store_id} | {start} ~ {end}")
    records = fetch_tag_records(store_id, start, end)
    if not records:
        print("⚠️ 区间内无标签数据，跳过")
        return
    print(f"📝 调用 AI 生成总结（共 {len(records)} 条标签）…")
    summary, version = call_summary_api(records, store_id, start, end)
    print("✅ AI 输出的 summary:\n", json.dumps(summary, ensure_ascii=False, indent=2))
    save_summary(store_id, start, end, summary, version)
    print("✅ 已写入 review_ai_summary")

if __name__ == "__main__":
    # 直接使用内置测试参数
    generate_summary(TEST_STORE_ID, TEST_START, TEST_END)
