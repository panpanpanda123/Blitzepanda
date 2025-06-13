import re
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Locator, Page, TimeoutError

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

def select_date_range(frame: Locator, start_date_str: str, end_date_str: str) -> None:
    """
    Selects the date range via textbox and day buttons.
    """
    # 解析日数，去掉前导0
    start_day = str(int(start_date_str.split("-")[-1]))
    end_day   = str(int(end_date_str.split("-")[-1]))

    # 点击日期输入框
    frame.get_by_role("textbox", name="开始日期 至 结束日期").click()
    # 选择开始日和结束日
    frame.get_by_role("button", name=start_day, exact=True).first.click()
    frame.get_by_role("button", name=end_day, exact=True).first.click()

    print(f"✅ 已选择日期范围 {start_date_str} 至 {end_date_str}")


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
    # 捕获 popup 和 download
    with page.expect_download() as dl_info:
        with page.expect_popup() as popup_info:
            # 匹配行
            rows = frame.get_by_role("row")
            for i in range(rows.count()):
                row = rows.nth(i)
                name = row.get_attribute("name") or ""
                if name.startswith(date_str):
                    row.locator("span").nth(3).click()
                    break
        popup = popup_info.value
    download = dl_info.value
    filename = f"{profile}_{date_str}.xlsx"
    target = download_dir / filename
    download.save_as(str(target))
    print(f"✅ 下载完成：{filename}")
    popup.close()


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

    # 3. 构造匹配行的正则
    pat = re.compile(start_date.replace("-", "") + ".*" + end_date.replace("-", ""))
    row = None

    # 4. 轮询尝试 5 次查找目标文件
    for attempt in range(5):
        try:
            rows = frame.get_by_role("row", name=pat)
            rows.get_by_text("下载", exact=True).first.wait_for(timeout=3000)
            row = rows.first
            print(f"✅ 第 {attempt+1} 次：记录已生成，准备下载...")
            break
        except TimeoutError:
            print(f"⏳ 第 {attempt+1} 次：未找到目标记录或下载按钮，3 秒后重试")
            time.sleep(3)
            page.reload()
            frame = page.frame_locator("iframe").first

    if not row:
        raise RuntimeError("❌ 运营数据生成失败，未找到匹配的记录")

    # 5. 点击下载并保存文件
    with page.expect_download() as dl_info:
        with page.expect_popup() as popup_info:
            row.get_by_text("下载", exact=True).first.click()
        download_page = popup_info.value

    download = dl_info.value
    filename = f"{profile}_{start_date.replace('-','')}_{end_date.replace('-','')}.xlsx"
    target = download_dir / filename
    download.save_as(str(target))
    print(f"✅ 运营数据下载完成：{target.name}")

    # 6. 清理页面
    download_page.close()
