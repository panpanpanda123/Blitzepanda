"""
app.excel

用途：完全沿用老代码的读取方式：自动识别包含“日期”的表头行，再以该行为表头读取。
"""

from __future__ import annotations

import pandas as pd


def _find_header_row(file_path: str) -> int:
    df_raw = pd.read_excel(file_path, header=None, dtype=str)
    max_rows = df_raw.shape[0]
    for i in range(min(10, max_rows)):
        row = df_raw.iloc[i].astype(str)
        if row.str.contains('日期', na=False).any():
            return i
    raise ValueError(f"未找到包含'日期'的表头行: {file_path}")


def clean_and_load_excel(file_path: str) -> pd.DataFrame:
    """按老代码行为读取 Excel：
    - 在前 10 行内查找包含“日期”的行作为表头
    - 以该行为 header 读取，dtype=str
    - 去除列名中的换行与不间断空格，并 strip
    """
    header_row_index = _find_header_row(file_path)
    df = pd.read_excel(file_path, header=header_row_index, dtype=str)
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace('\n', '', regex=False)
        .str.replace('\xa0', ' ', regex=False)
    )
    return df


