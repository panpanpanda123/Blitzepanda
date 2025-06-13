import tkinter as tk
from tkinter import simpledialog, messagebox
import os

# 确保脚本目录下有 profile_brand_map.py 文件路径
MAP_FILE = os.path.join(os.path.dirname(__file__), 'profile_brand_map.py')

def load_existing_map():
    '''从已有文件中加载映射，若不存在则返回空 dict'''
    if not os.path.isfile(MAP_FILE):
        return {}
    try:
        namespace = {}
        with open(MAP_FILE, 'r', encoding='utf-8') as f:
            code = f.read()
            exec(code, namespace)
        return namespace.get('PROFILE_BRAND_MAP', {})
    except Exception:
        return {}


def save_map(mapping):
    '''将 mapping 写入 profile_brand_map.py'''
    lines = [
        '# 自动生成，请勿手动修改\n',
        'PROFILE_BRAND_MAP = {\n',
    ]
    for key, val in sorted(mapping.items()):
        lines.append(f"    '{key}': '{val}',\n")
    lines.append('}\n')
    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def main():
    root = tk.Tk()
    root.withdraw()
    mapping = load_existing_map()

    while True:
        num = simpledialog.askstring('输入 Profile 编号', '请输入数字，例如 41，留空或取消则结束：')
        if not num:
            break
        key = f'Profile {num.strip()}'
        brand = simpledialog.askstring('输入品牌名', f'{key} 对应的品牌名：')
        if not brand:
            break
        mapping[key] = brand.strip()
        # 实时保存每一次输入
        save_map(mapping)
        messagebox.showinfo('已更新', f'已在 {MAP_FILE} 中添加或更新: {key} -> {brand.strip()}')

    root.destroy()


if __name__ == '__main__':
    main()
