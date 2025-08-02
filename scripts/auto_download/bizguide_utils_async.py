import re
import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import Locator, Page, TimeoutError


async def try_close_popup(frame: Locator) -> None:
    try:
        btn = frame.locator("button.mtd-modal-close")
        if await btn.count() > 0:
            await btn.first.click()
            print("✅ 发现弹窗，已关闭")
        else:
            print("⚠️ 没有发现关闭按钮，跳过")
    except Exception as e:
        print(f"⚠️ 关闭弹窗失败，异常信息：{e}")


async def click_reset_if_exists(frame: Locator) -> None:
    reset_btns = frame.get_by_text("点击重置", exact=True)
    cnt = await reset_btns.count()
    if cnt == 0:
        print("⚠️ 未发现“点击重置”按钮，跳过重置")
        return
    try:
        await reset_btns.first.click()
        print("🔄 已点击“点击重置”，重置维度成功")
        await asyncio.sleep(0.5)
    except Exception as e:
        print(f"⚠️ 点击“点击重置”异常：{e}")


async def select_date_range(frame: Locator, start_date: str, end_date: str) -> None:
    s_y, s_m, s_d = start_date.split("-")
    e_y, e_m, e_d = end_date.split("-")
    s_label_m = f"{int(s_m):02d}月"
    e_label_m = f"{int(e_m):02d}月"
    s_label_d, e_label_d = str(int(s_d)), str(int(e_d))

    await frame.get_by_role("textbox", name="开始日期 至 结束日期").click()
    await asyncio.sleep(0.1)

    async def find_panel(year: str, month_label: str):
        panels = frame.locator(".mtd-date-calendar-content.active")
        count = await panels.count()
        for i in range(count):
            panel = panels.nth(i)
            yr = (await panel.locator(".mtd-date-calendar-year-btn").inner_text()).strip()
            mo = (await panel.locator(".mtd-date-calendar-month-btn").inner_text()).strip()
            if yr == f"{year}年" and mo == month_label:
                return panel
        raise RuntimeError(f"未找到 {year}年 {month_label} 的日历面板")

    start_panel = await find_panel(s_y, s_label_m)
    await start_panel.locator("div.mtd-date-panel-data-wrapper:not(.not-current-month)") \
        .get_by_role("button", name=s_label_d, exact=True).click()

    if (s_y, s_m) != (e_y, e_m):
        await frame.locator(".mtd-date-calendar-month-switcher.right-switcher").first.click()
        await asyncio.sleep(0.1)
        end_panel = await find_panel(e_y, e_label_m)
        await end_panel.locator("div.mtd-date-panel-data-wrapper:not(.not-current-month)") \
            .get_by_role("button", name=e_label_d, exact=True).click()
    else:
        await start_panel.locator("div.mtd-date-panel-data-wrapper:not(.not-current-month)") \
            .get_by_role("button", name=e_label_d, exact=True).click()

    print(f"✅ 已选择日期：{start_date} 至 {end_date}")


async def select_basic_filters(frame: Locator) -> None:
    try:
        await frame.get_by_role("radio", name=re.compile(r"流量、交易指标需要包含分来源数据")).check()
    except TimeoutError:
        print("⚠️ 分来源选项未找到，跳过")
    try:
        await frame.get_by_role("checkbox", name="\ue024 时间环比").uncheck()
    except TimeoutError:
        print("⚠️ 时间环比复选框未找到，跳过")


async def expand_more_metrics(frame: Locator, groups: int = 4) -> None:
    expand_buttons = frame.locator(".report-form-module_actionText_v26Iw")
    total = await expand_buttons.count()
    for i in range(min(groups, total)):
        await expand_buttons.nth(i).click()
    print(f"✅ 展开了 {min(groups, total)} 组更多指标")


async def select_all_by_module(frame: Locator, skip_last: int = 0) -> None:
    modules = await frame.locator(".report-form-module_mainIndicator_Drhw9").all()
    total = len(modules)
    print(f"🔍 共检测到 {total} 个指标模块，将跳过最后 {skip_last} 个")
    for i in range(total - skip_last):
        await modules[i].locator(".report-form-module_actionText_v26Iw").click()
    print("✅ 模块级全选完成")


async def select_all_by_text(frame: Locator) -> None:
    selects = frame.get_by_text("全选", exact=True)
    count = await selects.count()
    print(f"🔍 找到 {count} 个“全选”按钮，逐一点击")
    for i in range(count):
        await selects.nth(i).click()
    print("✅ 已完成所有“全选”点击")


async def select_all_metrics(frame: Locator) -> None:
    await select_all_by_module(frame, skip_last=0)
    await select_all_by_text(frame)


async def cleanup_page(page: Page) -> None:
    await page.close()


async def download_with_generation(
    frame: Locator,
    page: Page,
    download_dir: Path,
    start_date: str,
    end_date: str,
    profile: str
) -> None:
    await frame.get_by_role("button", name="立即下载", exact=True).click()
    await asyncio.sleep(2)
    await frame.get_by_role("button", name="前往下载", exact=True).click()
    print("📥 等待运营数据文件生成中...")

    for i in range(10):
        if await frame.get_by_text("--", exact=True).count() == 0:
            break
        print(f"⏳ 第 {i + 1} 次：检测到“--”，等待2s并 reload…")
        await page.reload(wait_until="networkidle")
        frame = page.frame_locator("iframe").first
        await asyncio.sleep(2)
    else:
        raise RuntimeError("❌ 等待超时，页面仍存在 “--”，文件可能尚未生成")

    first_row = frame.locator("tr.mtd-table-row").first
    download_btn = first_row.locator("span.report-list-module_btn_lyByD").filter(has_text="下载").first

    async with page.expect_download(timeout=15000) as dl_info:
        try:
            async with page.expect_popup(timeout=3000) as pop_info:
                await download_btn.click()
            popup_page = await pop_info.value
        except TimeoutError:
            popup_page = None

    download = await dl_info.value
    filename = f"{profile}_{start_date.replace('-', '')}_{end_date.replace('-', '')}.xlsx"
    await download.save_as(str(download_dir / filename))
    print(f"✅ 运营数据下载完成：{filename}")

    if popup_page:
        await popup_page.close()
