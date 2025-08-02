import asyncio, os, shutil
from pathlib import Path
from playwright.async_api import async_playwright

#—— 1. 原始路径（包含 Local State 和多个 Profile）
SRC = Path(r"C:\Users\豆豆\AppData\Local\Google\Chrome\User Data")
#—— 2. 克隆目标（非默认目录）
CLONE = Path(r"D:\chrome_playwright_clone")

# 第一次运行时做一次拷贝，之后可注释掉这段
if not CLONE.exists():
    CLONE.mkdir(parents=True)
    # 记得把 Local State 也拷进来，Cookie 解密 key 就在这里
    shutil.copy(SRC / "Local State", CLONE / "Local State")
    for prof in ("Profile 41", "Profile 53"):
        shutil.copytree(SRC / prof, CLONE / prof)

PROFILES   = ["Profile 41", "Profile 53"]
TARGET_URL = "https://midas.dianping.com/shopdiy/account/pcCpcEntry"

async def verify_login(profile_name: str):
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(CLONE),          # <- 指向“克隆”目录
            channel="chrome",                  # 真·Chrome
            headless=False,
            args=[f"--profile-directory={profile_name}",
                  "--disable-infobars"]
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto(TARGET_URL, wait_until="networkidle")
        # 截图 & 判断
        fn = f"{profile_name}_login_check.png"
        await page.screenshot(path=fn)
        html = await page.content()
        ok = not any(k in html for k in ("登录", "验证码", "请输入账号"))
        print(f"[{profile_name}] {'✅ 登录态复用成功' if ok else '⚠️ 仍在登录页'}，截图：{fn}")
        await ctx.close()

async def main():
    for prof in PROFILES:
        print(f"== 验证 {prof} ==")
        await verify_login(prof)

if __name__ == "__main__":
    asyncio.run(main())
