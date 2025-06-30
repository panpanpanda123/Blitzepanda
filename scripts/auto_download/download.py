import shutil
import time
from pathlib import Path
from datetime import date, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from cpc_utils import download_cpc, pause_listener, wait_if_paused
from profile_brand_map import PROFILE_BRAND_MAP
from bizguide_utils import (
    select_date_range, select_basic_filters,
    expand_more_metrics, select_all_metrics,
    download_with_generation, cleanup_page, try_close_popup, click_reset_if_exists
)
import threading


# 全局控制变量
PAUSED = False

threading.Thread(target=pause_listener, daemon=True).start()

# —— 配置 ——
SRC         = Path(r"C:\Users\豆豆\AppData\Local\Google\Chrome\User Data")
CLONE       = Path(r"D:\chrome_playwright_clone")
# 执行列表由映射动态生成
PROFILES    = list(PROFILE_BRAND_MAP.keys())
EXPORT_URL  = (
    "https://ecom.meituan.com/bizguide/portal?cate=100057652"
    "#https://ecom.meituan.com/bizguide/export"
)
DOWNLOAD_DIR = Path(r"D:\dianping_downloads")
CPC_DIR             = DOWNLOAD_DIR / "cpc_hourly_data"
OPERATION_DIR       = DOWNLOAD_DIR / "operation_data"
DOWNLOAD_DIR.mkdir(exist_ok=True)
# 创建目录（如果不存在）
for d in (CPC_DIR, OPERATION_DIR):
    d.mkdir(parents=True, exist_ok=True)

def clone_user_data():
    CLONE.mkdir(parents=True, exist_ok=True)

    # 如果 Local State 不存在，说明是首次，复制它（它会影响 profile 索引）
    if not (CLONE / "Local State").exists():
        shutil.copy(SRC / "Local State", CLONE / "Local State")
        print("✅ 已复制 Local State")

    # 只克隆有配置的 profile
    for prof in PROFILE_BRAND_MAP:
        target = CLONE / prof
        if not target.exists():
            src_path = SRC / prof
            if src_path.exists():
                shutil.copytree(src_path, target)
                print(f"📂 克隆成功：{prof}")
            else:
                print(f"⚠️ 警告：原始路径不存在 {src_path}，可能 profile 名写错")
        else:
            print(f"✅ 已存在 {prof}，跳过复制")

def get_download_period():
    today = date.today()

    if today.weekday() == 0:  # 周一
        # 上周五 ~ 周日
        start = today - timedelta(days=3)  # 上周五
        end = today - timedelta(days=1)  # 周日
    else:
        # 默认昨天
        start = today - timedelta(days=1)
        end = start

    default = f"{start.isoformat()},{end.isoformat()}"
    text = input(f"下载日期范围（YYYY-MM-DD,YYYY-MM-DD），回车使用默认[{default}]: ").strip()
    return tuple(map(str.strip, text.split(","))) if text else (start.isoformat(), end.isoformat())


def run_profile(ctx, profile: str, start_date: str, end_date: str):
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    print(f"\n===== Running {profile} [{start_date} → {end_date}] =====")
    # —— 1. CPC 数据（仅当 cpc=True 时执行）——
    cfg = PROFILE_BRAND_MAP.get(profile, {})
    print(f"DEBUG: 当前 {profile} 的配置 => {cfg}")
    if cfg.get('cpc', False):
        # 打开推广通入口
        HOME_URL = (
            "https://ecom.meituan.com/meishi/?cate=5348"
            "#https://midas.dianping.com/shopdiy/account/pcCpcEntry"
            "?continueUrl=/app/peon-merchant-product-menu/html/index.html"
        )
        page.goto(HOME_URL, wait_until="networkidle")
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        # —— 0. 快速检测“登录弹窗” ——
        wait_if_paused()
        popup = False
        try:
            # 只等 500 ms：要么立刻发现 iframe.loginFormContent，要么直接走主流程
            page.wait_for_selector("iframe.loginFormContent", timeout=500)
            popup = True
        except PlaywrightTimeoutError:
            popup = False

        if popup:
            # —— 1. 处理登录/业务选择弹窗 ——
            wait_if_paused()
            login_frame = page.frame_locator("iframe.loginFormContent")
            login_frame.locator('div.biz-item:has-text("我是餐饮商家")').click()
            login_frame.locator('button.button.active:has-text("确定")').click()
            page.wait_for_load_state("networkidle", timeout=5000)
            print("✅ 已关闭弹窗，继续下载 CPC")
        # —— 2. 再走 download_cpc ——
        wait_if_paused()
        download_cpc(page, CPC_DIR, start_date, end_date, profile)
    else:
        print(f"ℹ️ {cfg.get('brand', profile)} 未投放推广通，跳过推广通页面与 CPC 下载")
    # —— 2. 运营数据（仅当 op=True 时执行）——
    wait_if_paused()
    if cfg.get('op', True):
        page.goto(EXPORT_URL, wait_until="networkidle")
        frame = page.frame_locator("iframe").first
        try_close_popup(frame)
        click_reset_if_exists(frame)
        select_date_range(frame, start_date, end_date)
        select_basic_filters(frame)
        expand_more_metrics(frame)
        select_all_metrics(frame)
        download_with_generation(
            frame, page, OPERATION_DIR,
            start_date, end_date,
            cfg.get('brand', profile)
        )
        cleanup_page(page)
    else:
        print(f"ℹ️ {cfg.get('brand', profile)} 未设置运营数据下载，跳过")

def main():
    # 第一次运行时，从真身目录拷贝一份到 CLONE，后续只读/写 CLONE
    clone_user_data()
    start_date, end_date = get_download_period()

    # 允许用户输入品牌名进行筛选，多个用逗号分隔
    brand_input = input("👉 如需只下载部分品牌，请输入品牌名（多个用英文逗号隔开），回车则下载全部：").strip()
    if brand_input:
        selected_brands = set(b.strip() for b in brand_input.split(","))
        selected_profiles = [
            prof for prof, cfg in PROFILE_BRAND_MAP.items()
            if cfg.get("brand") in selected_brands
        ]
        if not selected_profiles:
            print("❌ 未匹配到任何品牌，请检查输入")
            return
    else:
        selected_profiles = PROFILES  # 全部

    with sync_playwright() as p:
        for prof in selected_profiles:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(CLONE),
                channel="chrome", headless=False,
                args=[f"--profile-directory={prof}", "--disable-infobars"],
                accept_downloads=True, downloads_path=str(DOWNLOAD_DIR)
            )
            run_profile(ctx, prof, start_date, end_date)

if __name__ == "__main__":
    main()