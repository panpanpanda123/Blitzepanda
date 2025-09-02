import re
import time
from pathlib import Path
from playwright.sync_api import Page, TimeoutError, Locator
from profile_brand_map import PROFILE_BRAND_MAP
import keyboard

PAUSED = False

def pause_listener():
    global PAUSED
    while True:
        keyboard.wait("F9")  # 按一次 F9 就切换一次状态
        PAUSED = not PAUSED
        print("⏸️ 暂停中..." if PAUSED else "▶️ 继续执行")

def wait_if_paused():
    while PAUSED:
        time.sleep(0.1)

def download_cpc(page: Page, download_dir: Path, start_date: str, end_date: str, profile: str) -> None:
    """
    优化后的 CPC 数据下载函数，借鉴 download_cpc_data.py 中的定位与交互方式
    """
    print("🚀 进入推广通页面...")
    ad_iframe = page.frame_locator("#iframeContainer")

    # —— 1. 点击“推广通”按钮 ——
    ad_iframe = page.frame_locator("#iframeContainer")
    for btn_text in ["推广通"]:
        # 注意：一定要在 iframe 里找
        btn = ad_iframe.get_by_text(btn_text, exact=True)
        # 先滚动到可见，再等待可见
        btn.scroll_into_view_if_needed(timeout=7500)
        btn.wait_for(state="visible", timeout=7500)
        wait_if_paused()
        try:
            btn.click(force=True)
            print(f"✅ 点击 {btn_text} 成功")
        except Exception as e1:
            try:
                btn.evaluate("el => el.click()")
                print(f"✅ JS 点击 {btn_text} 成功")
            except Exception as e2:
                screenshot = f"{btn_text}_点击失败.png"
                page.screenshot(path=screenshot)
                raise RuntimeError(f"❌ 无法点击'{btn_text}'，已保存截图：{screenshot}，错误信息：{e2}")
        time.sleep(1)


        # 2. 定位到内层 CPC iframe
    cpc_frame = ad_iframe.frame_locator("iframe[title^='https://midas.dianping.com/shopdiy/account/pcCpcEntry']")

    # 3. 点击“数据报告”→“推广分析”
    wait_if_paused()
    cpc_frame.get_by_text("数据报告", exact=True).click()
    time.sleep(1.5)
    cpc_frame.get_by_text("推广分析", exact=True).click()
    time.sleep(0.5)

    # 4. 切换频道：先点“美团+点评”，再选“点评”
    print("🔄 切换到点评频道…")
    wait_if_paused()
    # 录制中是在最内层 iframe 里用 div.filter
    cpc_frame.locator("div").filter(
        has_text=re.compile(r"^美团\+点评$")).click()  # :contentReference[oaicite:0]{index=0}
    time.sleep(0.2)
    cpc_frame.get_by_role("listitem").filter(
        has_text=re.compile(r"^点评$")).click()  # :contentReference[oaicite:1]{index=1}
    time.sleep(0.2)

    # —— 5. 选择自定义日期并点击具体日期
    print(f"📅 选择自定义日期：{start_date} ~ {end_date}")
    wait_if_paused()
    date_container = cpc_frame.locator("div").filter(has_text=re.compile(r"自定义"))
    date_input = date_container.get_by_placeholder("开始日期").first
    date_input.click()
    time.sleep(0.5)

    # 拆出“日”数字（去掉前导0）
    sd = start_date.split("-")[2].lstrip("0")
    ed = end_date.split("-")[2].lstrip("0")

    # 拿到所有月面板
    panels = cpc_frame.locator("div.merchant-date-picker-panel-calendar-month")
    start_label = f"{int(start_date.split('-')[1])}月"
    end_label   = f"{int(end_date.split('-')[1])}月"
    start_panel = panels.filter(has_text=start_label).first
    end_panel   = panels.filter(has_text=end_label).first

    # 点击起始日
    start_panel \
      .locator(
        "div.merchant-date-picker-panel-calendar-month__date--current-month"
        ":not(.merchant-date-picker-panel-calendar-month__date--disabled)"
      ) \
      .locator("div.merchant-date-picker-panel-calendar-month__date-date", has_text=sd) \
      .first.click()
    time.sleep(0.2)

    # 点击结束日
    end_panel \
      .locator(
        "div.merchant-date-picker-panel-calendar-month__date--current-month"
        ":not(.merchant-date-picker-panel-calendar-month__date--disabled)"
      ) \
      .locator("div.merchant-date-picker-panel-calendar-month__date-date", has_text=ed) \
      .first.click()
    time.sleep(0.2)

    # 确认／应用
    cpc_frame.get_by_role("button", name="确定", exact=True).click()
    time.sleep(1)


    # 6. 如果当前是“分天”模式，则切换到“分小时”
    try:
        seg_btn = cpc_frame.get_by_text("分天").first
        if seg_btn.is_visible():
            seg_btn.click()
            time.sleep(0.5)
            cpc_frame.get_by_text("分小时", exact=True).click()
            print("✅ 已切换为分小时模式")
    except:
        pass

    # —— 6.5 点击“按时间拆分” ——
    print("🔀 应用「按时间拆分」…")
    wait_if_paused()
    cpc_frame.get_by_text("按时间拆分", exact=True).first.click()
    time.sleep(0.5)

    # 7. 点击“下载明细”
    print("📥 正在生成点评CPC报表...")
    wait_if_paused()
    try:
        cpc_frame.get_by_role("button", name=re.compile("下载明细")).first.click()
    except:
        cpc_frame.get_by_text("下载明细").first.click()
    time.sleep(1)
    try:
        cpc_frame.get_by_text("我知道了", exact=True).click(timeout=2000)
    except:
        pass

    # 8. 切换美团平台
    print("🔄 切换到美团…")
    wait_if_paused()
    # 录制中是在最内层 iframe 里用 div.filter
    page.keyboard.press("PageUp")  # 连续往上滚一滚
    time.sleep(0.2)
    page.keyboard.press("PageUp")
    time.sleep(0.5)

    cpc_frame.locator("div").filter(
        has_text=re.compile(r"^点评$")).click()  # :contentReference[oaicite:0]{index=0}
    time.sleep(0.3)
    cpc_frame.get_by_role("listitem").filter(
        has_text=re.compile(r"^美团$")).click()  # :contentReference[oaicite:1]{index=1}
    time.sleep(0.2)

    # 9. 再次点击“下载明细”
    print("📥 正在生成美团CPC报表...")
    wait_if_paused()
    try:
        cpc_frame.get_by_role("button", name=re.compile("下载明细")).first.click()
    except:
        cpc_frame.get_by_text("下载明细").first.click()
    time.sleep(1)
    try:
        cpc_frame.get_by_text("我知道了", exact=True).click(timeout=2000)
    except:
        pass

    # —— 点击“下载记录”，取最近两条 ——
    wait_if_paused()
    cpc_frame.get_by_role("button", name=re.compile("下载记录")).nth(0).click()
    time.sleep(1)

    rows = cpc_frame.get_by_role("row").all()
    date_flag = start_date.replace("-", "")
    # 筛出前两条目标行
    target_rows = [
        row for row in rows
        if date_flag in row.text_content() and "下载" in row.text_content()
    ][:2]
    if len(target_rows) < 2:
        raise RuntimeError("❌ 找到的下载记录不足两条，请稍后重试")

    # 准备命名
    date_s = start_date.replace("-", "")
    date_e = end_date.replace("-", "")
    brand  = PROFILE_BRAND_MAP.get(profile, {}).get('brand', profile)
    # 顺序：第0条是美团，第1条是点评
    platforms = ["美团", "点评"]

    for i, row in enumerate(target_rows):
        plat = platforms[i]
        with page.expect_download() as dl_info:
            row.get_by_text("下载").click()
        download = dl_info.value
        filename = f"推广报表_{date_s}_{date_e}_{brand}_{plat}.xlsx"
        save_path = Path(download_dir) / filename
        download.save_as(str(save_path))
        print(f"✅ 已下载 {plat} CPC 数据：{save_path}")
        time.sleep(1)

