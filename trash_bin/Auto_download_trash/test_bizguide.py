# test_bizguide_full.py

import shutil
import re
from pathlib import Path
from datetime import date
from playwright.sync_api import sync_playwright, TimeoutError

# —— 1. 配置 ——
# 您本机的原始 Chrome User Data 根目录（包含 Local State）
SRC = Path(r"C:\Users\豆豆\AppData\Local\Google\Chrome\User Data")
# 克隆到“非默认”目录，绕过 DevTools 远程调试限制
CLONE = Path(r"D:\chrome_playwright_clone")
# 要测试的 Profile 列表
PROFILES = ["Profile 41", "Profile 53"]
# 运营数据下载入口（含 Fragment，自动跳到 export 页面）
EXPORT_URL = (
    "https://ecom.meituan.com/bizguide/portal?cate=100057652"
    "#https://ecom.meituan.com/bizguide/export"
)
# 下载文件保存目录
DOWNLOAD_DIR = Path(r"D:\dianping_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# —— 2. 首次运行请保留，后续可注释 ——
def clone_user_data():
    if not CLONE.exists():
        print(f"⏳ 正在克隆 User Data 到 {CLONE} …")
        CLONE.mkdir(parents=True)
        # DPAPI 解密 key 在 Local State
        shutil.copy(SRC / "Local State", CLONE / "Local State")
        for prof in PROFILES:
            shutil.copytree(SRC / prof, CLONE / prof)
        print("✅ 克隆完成，后续可直接运行脚本。")

# —— 3. 运行录制步骤并下载 ——
def run_bizguide_for_profile(profile: str):
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(CLONE),
            channel="chrome",           # 真·Chrome
            headless=False,
            args=[f"--profile-directory={profile}", "--disable-infobars"],
            accept_downloads=True,
            downloads_path=str(DOWNLOAD_DIR),
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        print(f"[{profile}] 打开运营数据导出页 → {EXPORT_URL}")
        page.goto(EXPORT_URL, wait_until="networkidle")
        frame = page.frame_locator("iframe").first

        # 1) 打开日期输入
        frame.get_by_role("textbox", name="开始日期 至 结束日期").click()
        # 2) 录制时选了“9号”“9号”两次，这里保持不动
        frame.get_by_role("button", name="9", exact=True).first.click()
        frame.get_by_role("button", name="9", exact=True).first.click()

        # 2) 分来源 & 时间环比 —— （同录制）
        frame.get_by_role("radio", name=re.compile("流量、交易指标需要包含分来源数据")).check()
        frame.get_by_role("checkbox", name=" 时间环比").uncheck()

        # 3) 展开“更多指标” —— 示例依旧收集并依次点击
        expand_buttons = frame.locator(".report-form-module_actionText_v26Iw")
        for i in range(expand_buttons.count()):
            expand_buttons.nth(i).click()

        # 4) **遍历每一项指标，逐个点击复选框**
        #    这里我们直接定位所有复选框容器，然后在容器内点击文字或 checkbox
        checkbox_items = frame.locator(".report-form-module_checkbox_Zrrn3")
        for i in range(checkbox_items.count()):
            # 在第 i 个复选框项内，点击 actionText（文字“全选”旁边的那个 span）
            item = checkbox_items.nth(i)
            # 如果希望直接点击文字
            item.locator(".report-form-module_actionText_v26Iw").click()
            # 或者如果想点击实际的 input
            # item.locator("input[type='checkbox']").check()

        # 5) 报表维度展开及下载
        page.locator("div").filter(has_text="总览诊断流量交易商品评价").nth(1).click()
        frame.get_by_text("报表维度时间周期：每日每周每月每年时间范围").click()

        with page.expect_download() as dl_info:
            frame.get_by_role("button", name="立即下载").click()
        download = dl_info.value
        download.save_as(str(DOWNLOAD_DIR / f"{profile}_{today_str}_bizguide.xlsx"))

# —— 4. 主流程 ——
if __name__ == "__main__":
    clone_user_data()  # 首次运行保留，之后可注释掉
    for prof in PROFILES:
        print("\n" + "="*30)
        run_bizguide_for_profile(prof)
