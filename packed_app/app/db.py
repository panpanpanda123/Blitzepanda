from __future__ import annotations

"""
app.db

- 提供统一的数据库连接创建与 DataFrame 写入 MySQL 的方法。
- 与老代码保持等价的接口名称：import_to_mysql、get_dtype_for_operation/get_dtype_for_cpc_hourly 的占位（可在需要时扩展）。
"""

from typing import Dict, Optional

import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy import types as sqltypes
from sqlalchemy.engine import Engine

from config.config import db_config


def get_engine() -> Engine:
    conn_str = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database']}?charset={db_config['charset']}"
    )
    return create_engine(conn_str)


def import_to_mysql(df: pd.DataFrame, table: str, conn_str: Optional[str] = None, dtype: Optional[Dict] = None, if_exists: str = "append") -> None:
    """将 DataFrame 写入 MySQL 指定表。

    - conn_str 为空时使用全局 db_config.
    - dtype 可传入以控制列类型。
    - 默认 if_exists=append。
    """
    engine = create_engine(conn_str) if conn_str else get_engine()
    df.to_sql(table, engine, if_exists=if_exists, index=False, dtype=dtype)


def reflect_existing_columns(table: str) -> list[str]:
    """反射表结构，返回已存在的列名列表。"""
    engine = get_engine()
    inspector = inspect(engine)
    return [c["name"] for c in inspector.get_columns(table)]


# 以下 dtype 推断函数保留占位实现，确保与老接口兼容；
# 可按需完善具体字段类型

def get_dtype_for_operation(df: pd.DataFrame) -> Dict:
    """基于列名的简单类型推断，覆盖常见字段。

    - 日期列 → Date
    - start_time → DateTime
    - 数值列 → Float（整型列可按需再细化）
    - 文本列 → String
    - store_id → String(50)
    - extra_metrics → JSON
    - rankings_detail → Text
    """
    dtype: Dict = {}
    for col in df.columns:
        name = str(col)
        low = name.lower()
        if name in ("日期", "date"):
            dtype[col] = sqltypes.Date()
        elif low == "start_time":
            dtype[col] = sqltypes.DateTime()
        elif low in ("extra_metrics",):
            dtype[col] = sqltypes.JSON()
        elif low in ("rankings_detail",):
            dtype[col] = sqltypes.Text()
        elif low in ("store_id", "门店id"):
            dtype[col] = sqltypes.String(50)
        else:
            series = df[col]
            if pd.api.types.is_integer_dtype(series):
                dtype[col] = sqltypes.Integer()
            elif pd.api.types.is_float_dtype(series) or pd.api.types.is_numeric_dtype(series):
                dtype[col] = sqltypes.Float()
            else:
                # 其他按文本处理
                dtype[col] = sqltypes.String(length=255)
    return dtype


def get_dtype_for_cpc_hourly(df: pd.DataFrame) -> Dict:
    """与 operation 一致的推断规则，额外兼容 CPC 列（如 platform/plan_key）。"""
    dtype = get_dtype_for_operation(df)
    # 覆盖常见 CPC 标识列
    for key in ("platform", "plan_key", "plan_name"):
        if key in df.columns:
            dtype[key] = sqltypes.String(length=100)
    return dtype


