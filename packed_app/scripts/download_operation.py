"""
download_operation.py

用途：封装“运营数据”的 Playwright 自动化下载流程（Bizguide 报表页）。
定位方式：单层 iframe，主要通过可访问性选择器（get_by_role / get_by_text）与 MTD 组件类名。
"""

import time
from pathlib import Path
from playwright.sync_api import Page, TimeoutError


EXPORT_URL = "https://ecom.meituan.com/bizguide/portal?cate=100057652#https://ecom.meituan.com/bizguide/export"


def _try_close_popup(frame) -> None:
    try:
        btn = frame.locator("button.mtd-modal-close")
        if btn.count() > 0:
            btn.first.click()
    except Exception:
        pass


def _click_reset_if_exists(frame) -> None:
    try:
        reset_btns = frame.get_by_text("点击重置", exact=True)
        if reset_btns.count() > 0:
            reset_btns.first.click()
            time.sleep(0.3)
    except Exception:
        pass


def _select_date_range(frame, start_date: str, end_date: str) -> None:
    s_y, s_m, s_d = start_date.split("-")
    e_y, e_m, e_d = end_date.split("-")
    s_label_m = f"{int(s_m):02d}月"
    e_label_m = f"{int(e_m):02d}月"
    s_label_d, e_label_d = str(int(s_d)), str(int(e_d))

    frame.get_by_role("textbox", name="开始日期 至 结束日期").click()
    time.sleep(0.1)

    def find_panel(year: str, month_label: str):
        panels = frame.locator(".mtd-date-calendar-content.active")
        for i in range(panels.count()):
            panel = panels.nth(i)
            yr = panel.locator(".mtd-date-calendar-year-btn").inner_text().strip()
            mo = panel.locator(".mtd-date-calendar-month-btn").inner_text().strip()
            if yr == f"{year}年" and mo == month_label:
                return panel
        raise RuntimeError(f"未找到 {year}年 {month_label} 的日历面板")

    start_panel = find_panel(s_y, s_label_m)
    start_panel \
        .locator("div.mtd-date-panel-data-wrapper:not(.not-current-month)") \
        .get_by_role("button", name=s_label_d, exact=True) \
        .click()

    if (s_y, s_m) != (e_y, e_m):
        frame.locator(".mtd-date-calendar-month-switcher.right-switcher").first.click()
        time.sleep(0.1)
        end_panel = find_panel(e_y, e_label_m)
        end_panel \
            .locator("div.mtd-date-panel-data-wrapper:not(.not-current-month)") \
            .get_by_role("button", name=e_label_d, exact=True) \
            .click()
    else:
        start_panel \
            .locator("div.mtd-date-panel-data-wrapper:not(.not-current-month)") \
            .get_by_role("button", name=e_label_d, exact=True) \
            .click()


def _select_basic_filters(frame) -> None:
    try:
        frame.get_by_role("radio", name="流量、交易指标需要包含分来源数据").check()
    except TimeoutError:
        pass
    try:
        frame.get_by_role("checkbox", name=" 时间环比").uncheck()
    except TimeoutError:
        pass


def _expand_more_metrics(frame, groups: int = 4) -> None:
    expand_buttons = frame.locator(".report-form-module_actionText_v26Iw")
    total = expand_buttons.count()
    for i in range(min(groups, total)):
        expand_buttons.nth(i).click()


def _select_all_metrics(frame) -> None:
    # 模块级全选
    modules = frame.locator(".report-form-module_mainIndicator_Drhw9").all()
    for i in range(len(modules)):
        modules[i].locator(".report-form-module_actionText_v26Iw").click()
    # 文本级补全
    selects = frame.get_by_text("全选", exact=True)
    for i in range(selects.count()):
        selects.nth(i).click()


def _download_with_generation(frame, page: Page, download_dir: Path, start_date: str, end_date: str, profile: str) -> None:
    frame.get_by_role("button", name="立即下载", exact=True).click()
    time.sleep(1.5)
    frame.get_by_role("button", name="前往下载", exact=True).click()

    # 轮询“--”消失
    for _ in range(10):
        if frame.get_by_text("--", exact=True).count() == 0:
            break
        page.reload(wait_until="networkidle")
        frame = page.frame_locator("iframe").first
        time.sleep(1.5)
    else:
        raise RuntimeError("等待超时：文件可能尚未生成")

    first_row = frame.locator("tr.mtd-table-row").first
    download_btn = first_row.locator("span.report-list-module_btn_lyByD").filter(has_text="下载").first
    with page.expect_download(timeout=15_000) as dl_info:
        download_btn.click()
    download = dl_info.value
    filename = f"{profile}_{start_date.replace('-', '')}_{end_date.replace('-', '')}.xlsx"
    download.save_as(str(download_dir / filename))


def download_operation(page: Page, download_dir: Path, start_date: str, end_date: str, profile: str) -> None:
    """执行运营数据下载主流程。"""
    page.goto(EXPORT_URL, wait_until="networkidle")
    try:
        page.get_by_text('报表', exact=True).click()
        time.sleep(1)
    except Exception:
        pass
    frame = page.frame_locator("iframe").first
    _try_close_popup(frame)
    _click_reset_if_exists(frame)
    _select_date_range(frame, start_date, end_date)
    _select_basic_filters(frame)
    _expand_more_metrics(frame)
    _select_all_metrics(frame)
    _download_with_generation(frame, page, download_dir, start_date, end_date, profile)


