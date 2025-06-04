# path_manager.py
import os
from tkinter import Tk, filedialog

def select_folder():
    Tk().withdraw()  # 隐藏主窗口
    folder_path = filedialog.askdirectory(title="选择数据文件夹")
    if folder_path:
        print(f"✅ 已选择文件夹: {folder_path}")
        return folder_path
    else:
        print("❌ 未选择文件夹！")
        return None

def get_output_path(folder_path, filename="merged_data.csv"):
    return os.path.join(folder_path, filename)
