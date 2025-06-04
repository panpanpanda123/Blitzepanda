# excel_header_finder.py
import pandas as pd

def find_header_row(file_path):
    df_raw = pd.read_excel(file_path, header=None, dtype=str)
    max_rows = df_raw.shape[0]  # 文件实际行数
    for i in range(min(10, max_rows)):  # 避免超出实际行数
        if df_raw.iloc[i].str.contains('日期').any():
            print(f"✅ 表头行定位成功，行号为：{i}")
            return i
    raise ValueError(f"❌ 文件{file_path}未找到包含'日期'的表头行！")


def clean_and_load_excel(file_path):
    header_row_index = find_header_row(file_path)
    df = pd.read_excel(file_path, header=header_row_index, dtype=str)
    df.columns = df.columns.str.strip().str.replace('\n', '').str.replace('\xa0', '')
    return df
