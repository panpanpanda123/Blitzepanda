# async_download.py
# 异步并发版点评数据下载脚本（改造自 download.py）

import asyncio
import shutil
from pathlib import Path
from datetime import date, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from profile_brand_map import PROFILE_BRAND_MAP
from cpc_utils_async import download_cpc
from bizguide_utils_async import (
    try_close_popup, click_reset_if_exists,
    select_date_range, select_basic_filters,
    expand_more_metrics, select_all_metrics,
    download_with_generation, cleanup_page
)
import shutil
from pathlib import Path

# 配置路径
SRC = Path(r"C:\Users\豆豆\AppData\Local\Google\Chrome\User Data")
CLONE = Path(r"D:\chrome_playwright_clone")
# 并发时的临时工作目录
WORK_BASE = CLONE.parent / f"{CLONE.name}_workspace"
WORK_BASE.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR = Path(r"D:\dianping_downloads")
CPC_DIR = DOWNLOAD_DIR / "cpc_hourly_data"
OP_DIR = DOWNLOAD_DIR / "operation_data"

for d in (DOWNLOAD_DIR, CPC_DIR, OP_DIR):
    d.mkdir(parents=True, exist_ok=True)

def clone_user_data():
    # 1) 把 Local State 复制到 CLONE 根目录
    CLONE.mkdir(parents=True, exist_ok=True)
    local_state_src = SRC / "Local State"
    if local_state_src.exists():
        shutil.copy(local_state_src, CLONE / "Local State")
        print("✅ 已复制 Local State")
    else:
        print("⚠️ 未找到 Local State")

    # 2) 再把每个 profile 子目录复制到 CLONE
    for prof in PROFILE_BRAND_MAP:
        dst = CLONE / prof
        if not dst.exists():
            src_prof = SRC / prof
            if src_prof.exists():
                shutil.copytree(src_prof, dst)
                print(f"📂 克隆成功：{prof}")
            else:
                print(f"⚠️ 源配置不存在：{src_prof}")

def get_download_period():
    today = date.today()
    if today.weekday() == 0:
        start = today - timedelta(days=3)
        end = today - timedelta(days=1)
    else:
        start = today - timedelta(days=1)
        end = start
    default = f"{start},{end}"
    text = input(f"下载日期范围（YYYY-MM-DD,YYYY-MM-DD），回车默认[{default}]: ").strip()
    return tuple(map(str.strip, text.split(","))) if text else (start.isoformat(), end.isoformat())

async def run_profile(p, profile, start_date, end_date, semaphore):
    async with semaphore:
        print(f"\n===== 开始处理 {profile} =====")
        # —— 为每个 profile 准备独立的工作目录 ——
        work_dir = WORK_BASE / profile
        if not work_dir.exists():
            work_dir.mkdir(parents=True, exist_ok=True)
            # a) 拷 Local State
            shutil.copy(CLONE / "Local State", work_dir / "Local State")
            # b) 拷该 profile 的子目录
            shutil.copytree(CLONE / profile, work_dir / profile)
        try:
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(work_dir),
                channel="chrome",
                headless=False,
                args=[f"--profile-directory={profile}"],
                accept_downloads=True,
                downloads_path=str(DOWNLOAD_DIR)
            )
        except Exception as e:
            print(f"❌ {profile} 初始化失败：{e}")
            return

        page = await ctx.new_page()
        cfg = PROFILE_BRAND_MAP.get(profile, {})
        brand = cfg.get("brand", profile)

        try:
            # —— CPC 下载 ——
            if cfg.get("cpc", False):
                await page.goto(
                    "https://ecom.meituan.com/meishi/?cate=5348"
                    "#https://midas.dianping.com/shopdiy/account/pcCpcEntry",
                    timeout=10000
                )
                await download_cpc(page, CPC_DIR, start_date, end_date, profile)

            # —— 运营数据下载 ——
            if cfg.get("op", True):
                await page.goto(
                    "https://ecom.meituan.com/bizguide/portal?cate=100057652"
                    "#https://ecom.meituan.com/bizguide/export",
                    timeout=10000
                )
                # 等待 iframe 出现后再定位
                await page.wait_for_selector("iframe", timeout=10000)
                frame = page.frame_locator("iframe").first
                await try_close_popup(frame)
                await click_reset_if_exists(frame)
                await select_date_range(frame, start_date, end_date)
                await select_basic_filters(frame)
                await expand_more_metrics(frame)
                await select_all_metrics(frame)
                await download_with_generation(frame, page, OP_DIR, start_date, end_date, brand)
                await cleanup_page(page)

            print(f"✅ {brand} 下载完成")
        except Exception as e:
            # 出错时截图并暂停
            await page.screenshot(path=f"error_{profile}.png")
            print(f"❌ {brand} 出错：{e}")
            input(f"⚠️ 错误发生在 {brand}，请排查后按回车继续：")
        finally:
            await ctx.close()

async def main():
    clone_user_data()
    start_date, end_date = get_download_period()
    brand_input = input("👉 输入品牌名（多个逗号分隔），或回车全选：").strip()
    selected_profiles = [
        prof for prof, cfg in PROFILE_BRAND_MAP.items()
        if not brand_input or cfg["brand"] in brand_input.split(",")
    ]

    semaphore = asyncio.Semaphore(2)  # 控制并发数
    async with async_playwright() as p:
        tasks = [
            run_profile(p, prof, start_date, end_date, semaphore)
            for prof in selected_profiles
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())
