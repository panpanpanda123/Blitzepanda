# auto_download.py
import asyncio, os, shutil
from pathlib import Path
from datetime import date, timedelta
from playwright.async_api import async_playwright, TimeoutError

# —— 1. 配置 ——
# 原始 Chrome User Data 根目录（务必包含 Local State）
SRC = Path(r"C:\Users\豆豆\AppData\Local\Google\Chrome\User Data")
# 克隆到一个“非默认”目录，Playwright 才能启动远程调试
CLONE = Path(r"D:\chrome_playwright_clone")
# 要测试的两个 Profile
PROFILES = ["Profile 41", "Profile 53"]
# 直接打开“点评推广分析”入口的 URL（codegen 录制时的 continueUrl）
TARGET_URL = (
    "https://midas.dianping.com/shopdiy/account/pcCpcEntry"
    "?continueUrl=/app/peon-hornet-promo/html/promo-list.html"
)
# 下载文件保存目录
DOWNLOAD_DIR = Path(r"D:\dianping_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# —— 2. 第一次运行时，拷贝 Local State + 两个 Profile ——
if not CLONE.exists():
    CLONE.mkdir(parents=True)
    print(f"Cloning User Data → {CLONE} …")
    # 解密 Cookie 的密钥存在 Local State
    shutil.copy(SRC / "Local State", CLONE / "Local State")
    for prof in PROFILES:
        shutil.copytree(SRC / prof, CLONE / prof)
    print("✅ 克隆完成，请下次直接运行脚本即可。")

# —— 3. 计算要下载的日期 ——
def get_dates_to_download(today: date):
    # 周一 下载周五/周六/周日，其它工作日 下载昨天
    wd = today.weekday()  # 0=周一
    if wd == 0:
        return [today - timedelta(days=d) for d in (3, 2, 1)]
    else:
        return [today - timedelta(days=1)]

# —— 4. 导航到“推广分析” ——
async def navigate_to_cpc(page):
    # 打开推广报表首页
    await page.goto(TARGET_URL, wait_until="networkidle")
    # 点击左侧“推广中心”
    await page.get_by_text("推广中心").click()
    # 切到内嵌 iframe，点击“推广通”
    await page.locator("#iframeContainer").content_frame.get_by_text("推广通").click()
    # 再点击“数据报告” → “推广分析”
    await page.locator("#iframeContainer") \
        .content_frame \
        .locator("iframe[title*='promo-list']") \
        .content_frame \
        .get_by_text("数据报告").click()
    await page.locator("#iframeContainer") \
        .content_frame \
        .locator("iframe[title*='promo-list']") \
        .content_frame \
        .get_by_text("推广分析").click()
    # 等待页面渲染完毕
    await page.wait_for_timeout(2000)

# —— 5. 针对单个日期“选时间 → 按时间拆分 → 下载” ——
async def download_for_date(page, dt: date, profile: str):
    dt_str = dt.strftime("%Y-%m-%d")
    frame = page.locator("#iframeContainer") \
                .content_frame \
                .locator("iframe[title*='promo-list']") \
                .content_frame

    # —— 5.1 选日期 ——
    # 录制时点击的是“昨日”，这里先这么写，后续可改为动态填入 dt_str
    await frame.get_by_text("昨日").click()
    # —— 5.2 按时间拆分 ——
    await frame.get_by_text("按时间拆分").click()
    # —— 5.3 下载明细 ——
    await frame.get_by_role("button", name="下载明细").click()

    # —— 5.4 等待下载并保存 ——
    try:
        download = await page.wait_for_event("download", timeout=60_000)
        filename = f"{profile}_{dt_str}.xlsx"
        await download.save_as(str(DOWNLOAD_DIR / filename))
        print(f"{profile} {dt_str} 下载完成 → {filename}")
    except TimeoutError:
        print(f"{profile} {dt_str} 下载超时，请检查 Selector 或网络")

# —— 6. 主流程 ——
async def main():
    async with async_playwright() as p:
        for prof in PROFILES:
            print(f"\n==== Processing {prof} ====")
            # 启动持久化上下文
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(CLONE),
                channel="chrome",      # 真·Chrome
                headless=False,
                args=[f"--profile-directory={prof}", "--disable-infobars"]
            )
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()

            # 跳到推广分析模块
            await navigate_to_cpc(page)

            # 计算并依次下载所需日期
            dates = get_dates_to_download(date.today())
            for dt in dates:
                await download_for_date(page, dt, prof)

            await ctx.close()

if __name__ == "__main__":
    asyncio.run(main())
