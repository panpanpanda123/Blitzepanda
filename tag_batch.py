#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tag_batch.py

批量从 review_data 拉取近30天未处理的评价，调用 Kimi AI 生成标签，写入 review_ai_tag 表
"""

import os
import json
import time
import pymysql
from pymysql.cursors import DictCursor
import requests

# ---------- 配置区域（请核对） ----------
DB_PARAMS = {
    'host':       'localhost',
    'user':       'root',
    'password':   'xpxx1688',
    'db':         'dianping',
    'charset':    'utf8mb4',
    'cursorclass': DictCursor
}
from config_and_brand import API_URL, API_KEY, MODEL

BATCH_SIZE = 50   # 调小批次，减少单次响应长度


def get_connection():
    return pymysql.connect(**DB_PARAMS)


def fetch_unprocessed(limit: int = BATCH_SIZE * 10):
    sql = """
        SELECT id,
               store_id,
               review_date,
               rating_raw AS rating,
               review_text
        FROM review_data
        WHERE id NOT IN (SELECT raw_id FROM review_ai_tag)
          AND review_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        LIMIT %s
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(sql, (limit,))
        rows = cur.fetchall()
    conn.close()
    return rows


def call_kimi_api(records: list) -> list:
    """
    改成 Chat Completions 调用，返回一个 JSON 数组：
    [
      {"id":123, "tags":{...}},
      ...
    ]
    """
    # 1) 系统提示
    system_prompt = (
        "你是专业餐饮运营数据分析师。"
        "请为下列顾客评价生成标签，"
        "按 JSON 数组返回，每个元素格式为："
        '{"id":<raw_id>,"tags":{'
          '"sentiment":"正面/中性/负面",'
          '"topics":[...],'
          '"severity":"高/中/低",'
          '"special_flag":""'
        '}}。'
        "不要输出多余文字。"
    )
    # 2) 构造评价列表字符串
    lines = []
    for rec in records:
        rid = rec["id"]
        rating = float(rec["rating"]) if rec["rating"] is not None else None
        text = rec["review_text"].replace("\n", " ").strip()
        lines.append(f"{rid}|{rating}|{text}")
    user_content = "评价列表（每行 id|rating|text）：\n" + "\n".join(lines)

    # 3) payload
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_content}
        ],
        "temperature": 0,
        "max_tokens": 8192  # 确保有足够输出空间
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()

    chat = resp.json()
    content = chat["choices"][0]["message"]["content"]
    # 4) 解析 JSON，如果失败，存一份原文以便排查
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 保存完整响应到本地，调试用
        with open("error_response.json", "w", encoding="utf-8") as f:
            f.write(content)
            raise ValueError("JSON 解析失败，已保存响应到 error_response.json，请检查。")

def save_tags(results: list):
    sql = """
        INSERT INTO review_ai_tag (raw_id, tag_json, ai_version, processed_at)
        VALUES (%s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
          tag_json = VALUES(tag_json),
          ai_version = VALUES(ai_version),
          processed_at = VALUES(processed_at)
    """
    conn = get_connection()
    with conn.cursor() as cur:
        for item in results:
            raw_id   = item["id"]
            tag_json = json.dumps(item["tags"], ensure_ascii=False)
            version  = item.get("version", "")
            cur.execute(sql, (raw_id, tag_json, version))
    conn.commit()
    conn.close()


def main():
    print("🕵️‍♂️ 拉取未处理评价…")
    rows = fetch_unprocessed()
    if not rows:
        print("✅ 暂无新评价需要处理")
        return

    print(f"📦 共 {len(rows)} 条待处理，分批调用 API…")
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        try:
            results = call_kimi_api(batch)
            save_tags(results)
            print(f"✅ 已处理第 {i//BATCH_SIZE+1} 批，共写入 {len(results)} 条")
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ 批次 {i//BATCH_SIZE+1} 处理失败：{e}")
            break

if __name__ == "__main__":
    main()
