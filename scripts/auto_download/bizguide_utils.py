import re
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Locator, Page, TimeoutError

def force_select_all_checkboxes(frame: Locator) -> None:
    """
    使用 JS 脚本遍历页面上所有未勾选的复选框并点击，强制全选。
    """
    # 直接在 frame 上 evaluate
    frame.evaluate(
        """() => {
            document
              .querySelectorAll('input[type=\"checkbox\"]')
              .forEach(cb => { if (!cb.checked) cb.click(); });
        }"""
    )
    print("✅ JS 强制勾选所有复选框完成")


def try_close_popup(frame: Locator) -> None:
    """
    尝试关闭可能弹出的活动推荐类弹窗
    """
    try:
        btn = frame.locator("button.mtd-modal-close")
        if btn.count() > 0:
            btn.first.click()
            print("✅ 发现弹窗，已关闭")
        else:
            print("⚠️ 没有发现关闭按钮，跳过")
    except Exception as e:
        print(f"⚠️ 关闭弹窗失败，异常信息：{e}")

def click_reset_if_exists(frame: Locator) -> None:
    """
    若页面出现“点击重置”按钮，则点击一次以清空上次保存的维度设置。
    """
    try:
        reset_btns = frame.get_by_text("点击重置", exact=True)
        if reset_btns.count() > 0:
            reset_btns.first.click()
            print("🔄 已点击“点击重置”，重置维度成功")
            time.sleep(0.5)           # 给页面一点反应时间
    except Exception as e:
        # 非关键流程，异常时仅提示
        print(f"⚠️ 点击“点击重置”失败：{e}")

def select_date_range(frame: Locator, start_date: str, end_date: str) -> None:
    """
    在报表页里，打开日期选择器后，
    通过年月匹配左右两侧日历面板，再分别点击开始/结束日，最后点 确定。
    """
    # 拆年月日 & 月份格式化为两位数 (“06月”)
    s_y, s_m, s_d = start_date.split("-")
    e_y, e_m, e_d = end_date.split("-")
    s_label_m = f"{int(s_m):02d}月"
    e_label_m = f"{int(e_m):02d}月"
    s_label_d, e_label_d = str(int(s_d)), str(int(e_d))

    # 打开选择器
    frame.get_by_role("textbox", name="开始日期 至 结束日期").click()
    time.sleep(0.1)

    # Helper：在所有 calendar-content 里，找出匹配年月的那个面板
    def find_panel(year: str, month_label: str):
        panels = frame.locator(".mtd-date-calendar-content.active")
        for i in range(panels.count()):
            panel = panels.nth(i)
            yr = panel.locator(".mtd-date-calendar-year-btn").inner_text().strip()
            mo = panel.locator(".mtd-date-calendar-month-btn").inner_text().strip()
            if yr == f"{year}年" and mo == month_label:
                return panel
        raise RuntimeError(f"未找到 {year}年 {month_label} 的日历面板")

    # 1. 选开始日
    start_panel = find_panel(s_y, s_label_m)
    start_panel \
        .locator("div.mtd-date-panel-data-wrapper:not(.not-current-month)") \
        .get_by_role("button", name=s_label_d, exact=True) \
        .click()
    # 2. 选结束日
    # 如果跨月，先翻月再找；同月直接在同一个面板里找第二个

    if (s_y, s_m) != (e_y, e_m):
          # 跨月：翻到结束月，再在当前月面板里点
        frame.locator(".mtd-date-calendar-month-switcher.right-switcher").first.click()
        time.sleep(0.1)
        end_panel = find_panel(e_y, e_label_m)
        end_panel\
            .locator("div.mtd-date-panel-data-wrapper:not(.not-current-month)") \
            .get_by_role("button", name=e_label_d, exact=True) \
            .click()
    else:
      # 同月：同样只在当前月面板里选第二个（此时只有一个匹配）
        start_panel \
            .locator("div.mtd-date-panel-data-wrapper:not(.not-current-month)") \
            .get_by_role("button", name=e_label_d, exact=True) \
            .click()

    print(f"✅ 已选择日期：{start_date} 至 {end_date}")


def select_basic_filters(frame: Locator) -> None:
    """
    Applies basic radio and checkbox filters: include source and disable time comparison.
    """
    # 分来源
    try:
        frame.get_by_role(
            "radio", name=re.compile(r"流量、交易指标需要包含分来源数据")
        ).check()
    except TimeoutError:
        print("⚠️ 分来源选项未找到，跳过")
    # 取消时间环比
    try:
        frame.get_by_role("checkbox", name=" 时间环比").uncheck()
    except TimeoutError:
        print("⚠️ 时间环比复选框未找到，跳过")


def expand_more_metrics(frame: Locator, groups: int = 4) -> None:
    """
    Expands the given number of "更多指标" sections.
    """
    expand_buttons = frame.locator(".report-form-module_actionText_v26Iw")
    total = expand_buttons.count()
    for i in range(min(groups, total)):
        expand_buttons.nth(i).click()
    print(f"✅ 展开了 {min(groups, total)} 组更多指标")


def select_all_by_module(frame: Locator, skip_last: int = 0) -> None:
    """
    一次性“全选”前 len(modules)-skip_last 个模块，跳过最后几个模块。
    """
    modules = frame.locator(".report-form-module_mainIndicator_Drhw9").all()
    total   = len(modules)
    print(f"🔍 共检测到 {total} 个指标模块，将跳过最后 {skip_last} 个")
    for i in range(total - skip_last):
        modules[i].locator(".report-form-module_actionText_v26Iw").click()
    print("✅ 模块级全选完成")

def select_all_by_text(frame: Locator) -> None:
    """
    点击页面中所有“全选”按钮，确保所有模块和分类都被勾选。
    """
    selects = frame.get_by_text("全选", exact=True)
    count = selects.count()
    print(f"🔍 找到 {count} 个“全选”按钮，逐一点击")
    for i in range(count):
        selects.nth(i).click()
    print("✅ 已完成所有“全选”点击")

def select_all_metrics(frame: Locator) -> None:
    """
    综合使用模块级与文本级全选策略，全量勾选所有指标。
    """
    # 先模块级全选
    select_all_by_module(frame, skip_last=0)
    # 再文本级全选补漏
    select_all_by_text(frame)
    # 已去除JS兜底，避免报错

def click_dimension_expand(frame: Locator) -> None:
    """
    Expands the report dimension/time cycle selector.
    """
    try:
        frame.get_by_text(
            "报表维度时间周期：每日每周每月每年时间范围"
        ).click()
        print("✅ 维度选择已展开")
    except TimeoutError:
        print("⚠️ 维度展开按钮未找到，跳过")


def click_go_to_download(frame: Locator) -> None:
    """
    Clicks the '前往下载' button to navigate to generated report list.
    """
    try:
        frame.get_by_role("button", name="前往下载", exact=True).click()
        print("✅ 点击前往下载")
    except TimeoutError:
        print("⚠️ 前往下载按钮未找到，跳过")


def download_generated_report(
    frame: Locator,
    page: Page,
    download_dir: Path,
    date_str: str,
    profile: str
) -> None:
    """
    Download the first generated report matching date_str and save.
    """
    first_row = frame.locator("tr.mtd-table-row").first
    with page.expect_download(timeout=15_000) as dl_info:
        try:
            with page.expect_popup(timeout=3_000) as pop_info:
                first_row.locator("span.report-list-module_btn_lyByD").click()
            pop = pop_info.value
        except TimeoutError:
            pop = None

    download = dl_info.value
    filename = f"{profile}_{date_str}.xlsx"
    download.save_as(str(download_dir / filename))
    print(f"✅ 下载完成：{filename}")
    if pop:
        pop.close()

def cleanup_page(page: Page) -> None:
    """
    Closes the current page after download to clean up context.
    """
    page.close()

def download_with_generation(
    frame: Locator,
    page: Page,
    download_dir: Path,
    start_date: str,
    end_date: str,
    profile: str
) -> None:
    """
    点击“立即下载”+“前往下载”，等待“--”消失后，再轮询匹配行并点击“下载”。
    """
    # 1. 触发生成
    frame.get_by_role("button", name="立即下载", exact=True).click()
    time.sleep(2)
    frame.get_by_role("button", name="前往下载", exact=True).click()
    print("📥 等待运营数据文件生成中...")

    # 2. 若仍存在“--”，则轮询等待其消失
      # 2. 若仍存在“--”，则轮询等待其消失（最多 10 次，每次 reload 后等待加载）

    for i in range(10):

        if frame.get_by_text("--", exact=True).count() == 0:

            break
            print(f"⏳ 第 {i + 1} 次：检测到“--”，等待2s并 reload…")
            page.reload(wait_until="networkidle")
            frame = page.frame_locator("iframe").first
            time.sleep(2)
    else:
        raise RuntimeError("❌ 等待超时，页面仍存在 “--”，文件可能尚未生成")

    # 3-5. 查找最新记录并下载
    first_row = frame.locator("tr.mtd-table-row").first  # ① 永远拿第一行
    download_btn = first_row.locator("span.report-list-module_btn_lyByD") \
        .filter(has_text="下载").first  # ② 下载按钮

    with page.expect_download(timeout=15_000) as dl_info:  # ③ 先监听 download
        # popup 秒关不稳定 → 尝试捕获，但失败也无妨
        try:
            with page.expect_popup(timeout=3_000) as pop_info:
                download_btn.click()
            popup_page = pop_info.value
        except TimeoutError:
            popup_page = None

    download = dl_info.value
    filename = f"{profile}_{start_date.replace('-', '')}_{end_date.replace('-', '')}.xlsx"
    download.save_as(str(download_dir / filename))
    print(f"✅ 运营数据下载完成：{filename}")

    # 6. 关闭秒关的弹出页签，防止残留
    if popup_page:
        popup_page.close()
