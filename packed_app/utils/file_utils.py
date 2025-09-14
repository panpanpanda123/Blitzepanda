"""
文件操作相关工具函数
"""
import os
import shutil

def ensure_dir(path):
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path)

def move_file(src, dst):
    """移动文件到目标目录"""
    ensure_dir(os.path.dirname(dst))
    shutil.move(src, dst)
