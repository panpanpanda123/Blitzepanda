import re
import asyncio
from pathlib import Path
from playwright.async_api import Page, TimeoutError
from profile_brand_map import PROFILE_BRAND_MAP


async def download_cpc(page: Page, download_dir: Path, start_date: str, end_date: str, profile: str) -> None:
    print("🚀 进入推广通页面...")
    ad_iframe = page.frame_locator("#iframeContainer")

    for btn_text in ["推广通"]:
        btn = ad_iframe.get_by_text(btn_text, exact=True)
        await btn.scroll_into_view_if_needed(timeout=5000)
        await btn.wait_for(state="visible", timeout=5000)
        try:
            await btn.click(force=True)
            print(f"✅ 点击 {btn_text} 成功")
        except Exception:
            try:
                await btn.evaluate("el => el.click()")
                print(f"✅ JS 点击 {btn_text} 成功")
            except Exception as e2:
                screenshot = f"{btn_text}_点击失败.png"
                await page.screenshot(path=screenshot)
                raise RuntimeError(f"❌ 无法点击'{btn_text}'，已保存截图：{screenshot}，错误信息：{e2}")
        await asyncio.sleep(1)

    cpc_frame = ad_iframe.frame_locator("iframe[title^='https://midas.dianping.com/shopdiy/account/pcCpcEntry']")

    await cpc_frame.get_by_text("数据报告", exact=True).click()
    await asyncio.sleep(1)
    await cpc_frame.get_by_text("推广分析", exact=True).click()
    await asyncio.sleep(0.5)

    print("🔄 切换到点评频道…")
    await cpc_frame.locator("div").filter(has_text=re.compile(r"^美团\+点评$")).click()
    await asyncio.sleep(0.2)
    await cpc_frame.get_by_role("listitem").filter(has_text=re.compile(r"^点评$")).click()
    await asyncio.sleep(0.2)

    print(f"📅 选择自定义日期：{start_date} ~ {end_date}")
    date_container = cpc_frame.locator("div").filter(has_text=re.compile(r"自定义"))
    date_input = date_container.get_by_placeholder("开始日期").first
    await date_input.click()
    await asyncio.sleep(0.5)

    sd = start_date.split("-")[2].lstrip("0")
    ed = end_date.split("-")[2].lstrip("0")

    panels = cpc_frame.locator("div.merchant-date-picker-panel-calendar-month")
    start_label = f"{int(start_date.split('-')[1])}月"
    end_label = f"{int(end_date.split('-')[1])}月"
    start_panel = panels.filter(has_text=start_label).first
    end_panel = panels.filter(has_text=end_label).first

    await start_panel.locator("div.merchant-date-picker-panel-calendar-month__date--current-month"
        ":not(.merchant-date-picker-panel-calendar-month__date--disabled)") \
        .locator("div.merchant-date-picker-panel-calendar-month__date-date", has_text=sd).first.click()
    await asyncio.sleep(0.2)

    await end_panel.locator("div.merchant-date-picker-panel-calendar-month__date--current-month"
        ":not(.merchant-date-picker-panel-calendar-month__date--disabled)") \
        .locator("div.merchant-date-picker-panel-calendar-month__date-date", has_text=ed).first.click()
    await asyncio.sleep(0.2)

    await cpc_frame.get_by_role("button", name="确定", exact=True).click()
    await asyncio.sleep(1)

    try:
        seg_btn = cpc_frame.get_by_text("分天").first
        if await seg_btn.is_visible():
            await seg_btn.click()
            await asyncio.sleep(0.5)
            await cpc_frame.get_by_text("分小时", exact=True).click()
            print("✅ 已切换为分小时模式")
    except:
        pass

    print("🔀 应用「按时间拆分」…")
    await cpc_frame.get_by_text("按时间拆分", exact=True).first.click()
    await asyncio.sleep(0.5)

    print("📥 正在生成点评CPC报表...")
    try:
        await cpc_frame.get_by_role("button", name=re.compile("下载明细")).first.click()
    except:
        await cpc_frame.get_by_text("下载明细").first.click()
    await asyncio.sleep(1)
    try:
        await cpc_frame.get_by_text("我知道了", exact=True).click(timeout=2000)
    except:
        pass

    print("🔄 切换到美团…")
    await page.keyboard.press("PageUp")
    await asyncio.sleep(0.2)
    await page.keyboard.press("PageUp")
    await asyncio.sleep(0.5)

    await cpc_frame.locator("div").filter(has_text=re.compile(r"^点评$")).click()
    await asyncio.sleep(0.3)
    await cpc_frame.get_by_role("listitem").filter(has_text=re.compile(r"^美团$")).click()
    await asyncio.sleep(0.2)

    print("📥 正在生成美团CPC报表...")
    try:
        await cpc_frame.get_by_role("button", name=re.compile("下载明细")).first.click()
    except:
        await cpc_frame.get_by_text("下载明细").first.click()
    await asyncio.sleep(1)
    try:
        await cpc_frame.get_by_text("我知道了", exact=True).click(timeout=2000)
    except:
        pass

    await cpc_frame.get_by_role("button", name=re.compile("下载记录")).nth(0).click()
    await asyncio.sleep(1)

    rows = await cpc_frame.get_by_role("row").all()
    date_flag = start_date.replace("-", "")
    target_rows = [row async for row in rows if date_flag in await row.text_content() and "下载" in await row.text_content()][:2]
    if len(target_rows) < 2:
        raise RuntimeError("❌ 找到的下载记录不足两条，请稍后重试")

    date_s = start_date.replace("-", "")
    date_e = end_date.replace("-", "")
    brand = PROFILE_BRAND_MAP.get(profile, {}).get('brand', profile)
    platforms = ["美团", "点评"]

    for i, row in enumerate(target_rows):
        plat = platforms[i]
        async with page.expect_download() as dl_info:
            await row.get_by_text("下载").click()
        download = await dl_info.value
        filename = f"推广报表_{date_s}_{date_e}_{brand}_{plat}.xlsx"
        save_path = Path(download_dir) / filename
        await download.save_as(str(save_path))
        print(f"✅ 已下载 {plat} CPC 数据：{save_path}")
        await asyncio.sleep(1)
