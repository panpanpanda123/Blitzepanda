# review_cleaner.py  —— 2025-05-29 aligned version
# ---------------------------------------------
# 1. 只做基础清洗 + 门店匹配
# 2. 补齐 main.py 需要的 8 列，占位列用 None
# ---------------------------------------------
import os, re, unicodedata, json
import pandas as pd
from rapidfuzz import process, fuzz
from sqlalchemy import types as sqltypes
from database_importer import import_to_mysql  # 如果只清洗就不需要，可保留

# ---------- MySQL 字段类型（供外部脚本可选复用） ----------
dtype_review = {
    "store_id":     sqltypes.String(50),
    "review_date":  sqltypes.Date,
    "rating_raw":   sqltypes.Numeric(3, 1),   # e.g. 4.0
    "rating_label": sqltypes.String(2),       # “好 / 中 / 差”
    "review_text":  sqltypes.Text,
    "senti_score":  sqltypes.Float,
    "senti_label":  sqltypes.String(2),
    "key_topics":   sqltypes.JSON,
}

# ---------- 正则 & 工具 ----------
RE_PAREN = re.compile(r"[（(].*?[)）]")
RE_DOT   = re.compile(r"[·•・\.]")
RE_SPACE = re.compile(r"\s+")

def normalize_name(name: str) -> str:
    if pd.isna(name):
        return ""
    name = unicodedata.normalize("NFKC", name)
    name = RE_PAREN.sub(" ", name)
    name = RE_DOT.sub(" ", name)
    name = name.replace("店", " ")
    return RE_SPACE.sub(" ", name).strip().lower()

FUZZ_TOKEN_TH, FUZZ_PART_TH = 90, 85
def fuzzy_match(name, candidats_df):
    if not name:
        return None
    n_name = normalize_name(name)
    top = process.extract(
        n_name,
        candidats_df["store_name_norm"],
        scorer=fuzz.token_sort_ratio,
        limit=3
    )
    for match_str, score, idx in top:
        part = fuzz.partial_ratio(n_name, match_str)
        if score >= FUZZ_TOKEN_TH or part >= FUZZ_PART_TH:
            return candidats_df.iloc[idx]["store_id"]
    return None

# ---------- 主函数 ----------
KEEP_COLS = [
    "store_id", "review_date", "rating_raw", "rating_label",
    "review_text", "senti_score", "senti_label", "key_topics"
]

def clean_review_file(xlsx_path: str, store_mapping: pd.DataFrame) -> pd.DataFrame:
    """读取原始评价 Excel -> 清洗 -> 匹配门店 -> 返回 8 列 DataFrame，完全兼容 main.py"""
    df = (
        pd.read_excel(xlsx_path, header=0, dtype=str)
          .rename(columns={
              "评分":      "rating",
              "评价":      "review_text",
              "门店":      "store_name",
              "评价时间":  "review_date",
          })
    )

    # —— 基础字段清洗 ——
    df["rating"]      = pd.to_numeric(df["rating"], errors="coerce")
    df["review_date"] = pd.to_datetime(df["review_date"]).dt.date
    df.dropna(subset=["review_text", "store_name"], inplace=True)

    # —— 门店匹配 ——
    stores_df = store_mapping.rename(columns={
        "推广门店": "store_name",
        "门店ID":   "store_id"
    })
    stores_df["store_name_norm"] = stores_df["store_name"].apply(normalize_name)

    df = df.merge(stores_df[["store_name", "store_id"]], how="left", on="store_name")

    # 需要模糊匹配的再补
    mask = df["store_id"].isna()
    if mask.any():
        df.loc[mask, "store_id"] = df.loc[mask, "store_name"].apply(
            lambda x: fuzzy_match(x, stores_df)
        )

    # 未匹配日志
    unmatched = df["store_id"].isna().sum()
    if unmatched:
        log_name = f"unmatched_review_{pd.Timestamp.now():%Y%m%d_%H%M%S}.csv"
        df[df["store_id"].isna()].to_csv(log_name, index=False, encoding="utf-8-sig")
        print(f"⚠️ {unmatched} 条门店未识别，已写入 {log_name}")

    # —— 补齐 main.py 需要的列 ——
    df["rating_raw"]   = df["rating"].round(1)  # e.g. 4.0
    df["rating_label"] = df["rating"].apply(
        lambda x: "好" if x >= 4 else ("中" if x == 3 else "差")
    )
    df["senti_score"]  = None
    df["senti_label"]  = None
    df["key_topics"]   = None

    return df[KEEP_COLS]

# ---------- CLI / 测试 ----------
if __name__ == "__main__":
    # 示例调用：实际 running 时由 main.py 调用，无需单独运行
    REVIEW_FILE         = r"./示例评价.xlsx"
    STORE_MAPPING_FILE  = r"./store_mapping.xlsx"
    DB_STR              = "mysql+pymysql://user:pwd@localhost/db?charset=utf8mb4"

    stores_df = pd.read_excel(STORE_MAPPING_FILE, dtype=str)
    cleaned   = clean_review_file(REVIEW_FILE, stores_df)

    # 若想单独测试写库 ↓
    # from database_importer import import_to_mysql
    # import_to_mysql(cleaned, "review_data", DB_STR, dtype=dtype_review, if_exists="append")
    print(cleaned.head())
