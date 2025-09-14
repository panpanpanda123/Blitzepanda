"""
数据清洗相关工具函数
"""
import pandas as pd

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """对DataFrame进行基础清洗，如去重、去空行等"""
    df = df.drop_duplicates()
    df = df.dropna(how='all')
    return df
