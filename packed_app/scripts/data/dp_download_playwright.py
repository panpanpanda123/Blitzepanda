import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(**playwright.devices["Desktop Chrome"])
    page = context.new_page()
    page.goto("https://ecom.meituan.com/bizguide/portal?cate=100057633#https://ecom.meituan.com/bizguide/trade-analysis/overview")
    page.goto("https://ecom.meituan.com/bizaccount/login.html?epassportParams=bg_source%3D1%26service%3Dcom.sankuai.meishi.fe.bizsettle%26feconfig%3Dbssoify%26continue%3Dhttps%253A%252F%252Fepassport.meituan.com%252Fgw%252Fbsso%252FsetToken%253Fredirect_uri%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fbizaccount%25252Fredirect.html%25253Ftarget%25253Dhttps%2525253A%2525252F%2525252Fecom.meituan.com%2525252Fbizguide%2525252Fportal%2525253Fcate%2525253D100057633%25252523https%2525253A%2525252F%2525252Fecom.meituan.com%2525252Fbizguide%2525252Ftrade-analysis%2525252Foverview&isProduction=true")
    page.frame_locator("iframe").get_by_role("link", name="扫码登录").click()
    page.goto("https://ecom.meituan.com/bizguide/portal?cate=100057633#https://ecom.meituan.com/bizguide/trade-analysis/overview")
    page.locator("html").click()
    page.frame_locator("iframe").locator("div").filter(has_text=re.compile(r"^交易在线门店数1较对比时间持平$")).locator("span").nth(1).click()
    page.frame_locator("iframe").get_by_text("全部套餐代金券买单秒提营业门店数查看行业大盘2").click()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
