
"""
数据下载主入口脚本
功能：自动化批量下载大众点评运营数据和CPC数据，保存到本地指定目录。
所有路径、品牌映射等配置均引用 config。
"""
import os
import sys
from pathlib import Path
from config.config import DATA_DOWNLOAD_DIR, BRAND_MAPPING
from utils.logger import get_logger
from datetime import date, timedelta
# 自动把 auto_download 目录加入 sys.path，保证所有依赖都能导入
auto_download_dir = Path(__file__).parent.parent / "AI_auto_review_3_2025may" / "scripts" / "auto_download"
if str(auto_download_dir) not in sys.path:
    sys.path.insert(0, str(auto_download_dir))
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import shutil
import yaml, getpass

# ========== 免扫码自动登录核心逻辑 ===========
def load_cfg():
    # 自动定位 settings.yaml 的绝对路径
    base_dir = Path(__file__).parent.parent / "AI_auto_review_3_2025may" / "scripts" / "auto_download"
    cfg_path = base_dir / "settings.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    user = getpass.getuser()
    for k, v in cfg.items():
        if isinstance(v, str):
            cfg[k] = v.replace("{{username}}", user)
    return cfg

def clone_user_data(SRC, CLONE, profiles):
    CLONE.mkdir(parents=True, exist_ok=True)
    if not (CLONE / "Local State").exists():
        shutil.copy(SRC / "Local State", CLONE / "Local State")
        print("✅ 已复制 Local State")
    for prof in profiles:
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

def download_dianping_data(download_dir, brand_mapping):
    """
    免扫码自动登录+多 profile 自动下载点评数据
    """
    # 1. 读取原有配置
    CFG = load_cfg()
    SRC = Path(CFG["chrome_user_data"]).expanduser().resolve()
    CLONE = Path(CFG["clone_dir"]).expanduser().resolve()
    from profile_brand_map import PROFILE_BRAND_MAP
    from bizguide_utils import (
        select_date_range, select_basic_filters, expand_more_metrics, select_all_metrics,
        download_with_generation, cleanup_page, try_close_popup, click_reset_if_exists
    )
    from cpc_utils import download_cpc, wait_if_paused
    EXPORT_URL = "https://ecom.meituan.com/bizguide/portal?cate=100057652"
    # 强制覆盖为项目 data 目录下的标准路径，保证与主流程一致
    root_dir = Path(__file__).parent.parent / "data"
    CPC_DIR = root_dir / "cpc_hourly_data"
    OPERATION_DIR = root_dir / "operation_data"
    CPC_DIR.mkdir(parents=True, exist_ok=True)
    OPERATION_DIR.mkdir(parents=True, exist_ok=True)
    PROFILES = list(PROFILE_BRAND_MAP.keys())

    # 2. 克隆用户数据，确保所有 profile 可用
    clone_user_data(SRC, CLONE, PROFILES)

    # 3. 选择日期
    today = date.today()
    if today.weekday() == 0:
        start = today - timedelta(days=3)
        end = today - timedelta(days=1)
    else:
        start = today - timedelta(days=1)
        end = start
    default = f"{start.isoformat()},{end.isoformat()}"
    text = input(f"下载日期范围（YYYY-MM-DD,YYYY-MM-DD），回车使用默认[{default}]: ").strip()
    start_date, end_date = tuple(map(str.strip, text.split(","))) if text else (start.isoformat(), end.isoformat())

    # 4. 选择品牌
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
        selected_profiles = PROFILES

    # 5. 自动化下载
    with sync_playwright() as p:
        for prof in selected_profiles:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(CLONE),
                channel="chrome", headless=False,
                args=[f"--profile-directory={prof}", "--disable-infobars"],
                accept_downloads=True, downloads_path=str(download_dir)
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            cfg = PROFILE_BRAND_MAP.get(prof, {})
            print(f"\n===== Running {prof} [{start_date} → {end_date}] =====")
            # —— 1. CPC 数据（仅当 cpc=True 时执行）——
            if cfg.get('cpc', False):
                HOME_URL = (
                    "https://ecom.meituan.com/meishi/?cate=5348"
                    "#https://midas.dianping.com/shopdiy/account/pcCpcEntry"
                    "?continueUrl=/app/peon-merchant-product-menu/html/index.html"
                )
                page.goto(HOME_URL, wait_until="networkidle")
                wait_if_paused()
                # 只在页面真的有iframe.loginFormContent时才处理弹窗，否则直接进入主流程
                popup = False
                try:
                    if page.query_selector("iframe.loginFormContent"):
                        popup = True
                except Exception:
                    popup = False
                if popup:
                    wait_if_paused()
                    login_frame = page.frame_locator("iframe.loginFormContent")
                    login_frame.locator('div.biz-item:has-text("我是餐饮商家")').click()
                    login_frame.locator('button.button.active:has-text("确定")').click()
                    page.wait_for_load_state("networkidle", timeout=5000)
                    print("✅ 已关闭弹窗，继续下载 CPC")
                wait_if_paused()
                download_cpc(page, CPC_DIR, start_date, end_date, prof)
            else:
                print(f"ℹ️ {cfg.get('brand', prof)} 未投放推广通，跳过推广通页面与 CPC 下载")
            # —— 2. 运营数据（仅当 op=True 时执行）——
            wait_if_paused()
            if cfg.get('op', True):
                # 1. 跳转到报表页
                page.goto(EXPORT_URL, wait_until="networkidle")
                # 2. 点击“报表”tab，确保进入正确页面（如有必要可根据实际tab文本调整）
                try:
                    page.get_by_text('报表', exact=True).click()
                    time.sleep(1.2)
                except Exception:
                    pass  # 如果没有报表tab则跳过
                # 3. 切换到报表iframe
                frame = page.frame_locator("iframe").first
                # 4. 处理弹窗
                try_close_popup(frame)
                # 5. 检查并点击“点击重置”按钮
                click_reset_if_exists(frame)
                # 6. 选择日期
                select_date_range(frame, start_date, end_date)
                # 7. 选择基础过滤项
                select_basic_filters(frame)
                # 8. 展开更多指标
                expand_more_metrics(frame)
                # 9. 全选所有指标
                select_all_metrics(frame)
                # 10. 下载生成报表
                download_with_generation(
                    frame, page, OPERATION_DIR,
                    start_date, end_date,
                    cfg.get('brand', prof)
                )
                # 11. 关闭当前页面
                cleanup_page(page)
            else:
                print(f"ℹ️ {cfg.get('brand', prof)} 未设置运营数据下载，跳过")

def main():
    logger = get_logger('download_data')
    logger.info(f"数据将下载到: {DATA_DOWNLOAD_DIR}")
    # 调用主下载逻辑
    download_dianping_data(DATA_DOWNLOAD_DIR, BRAND_MAPPING)
    logger.info("下载流程已完成")

if __name__ == '__main__':
    main()
