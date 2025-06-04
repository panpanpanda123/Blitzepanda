import pandas as pd
import tkinter as tk
from tkinter import simpledialog, Toplevel, Listbox, MULTIPLE, END, Button, Label
from tkcalendar import Calendar
from config_and_brand import get_mysql_engine


def select_from_list(title, prompt, options, root):
    selected = []
    top = Toplevel(root)
    top.title(title)
    Label(top, text=prompt).pack()
    lb = Listbox(top, selectmode="browse")
    for option in options:
        lb.insert(END, option)
    lb.pack()

    def on_select():
        sel = lb.curselection()
        if sel:
            selected.append(lb.get(sel[0]))
        top.destroy()

    Button(top, text="确定", command=on_select).pack()
    top.wait_window()
    return selected[0] if selected else None


def select_single_date(title, prompt, root):
    selected = []
    top = Toplevel(root)
    top.title(title)
    Label(top, text=prompt).pack()
    cal = Calendar(top, selectmode='day')
    cal.pack()

    def on_select():
        selected.append(cal.get_date())
        top.destroy()

    Button(top, text="确定", command=on_select).pack()
    top.wait_window()
    return selected[0] if selected else None


def get_user_selected_brand_and_dates(root, engine=None):
    if engine is None:
        engine = get_mysql_engine()

    store_mapping = pd.read_sql("store_mapping", engine)
    brand_list = store_mapping["推广门店"].dropna().unique().tolist()

    brand = select_from_list("选择门店品牌", "请选择品牌", brand_list, root)
    if not brand:
        raise Exception("未选择品牌")

    start_date = select_single_date("选择开始日期", "请选择数据起始日", root)
    end_date = select_single_date("选择结束日期", "请选择数据结束日", root)

    return brand, start_date, end_date
