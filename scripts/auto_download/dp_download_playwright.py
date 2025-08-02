import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(**playwright.devices["Desktop Chrome"])
    page = context.new_page()
    page.goto("https://ecom.meituan.com/bizaccount/login.html?loginByPhoneNumber=true&isProduction=true&epassportParams=%3Fbg_source%3D1%26service%3Dcom.sankuai.meishi.fe.ecom%26part_type%3D0%26feconfig%3Dbssoify%26biz_line%3D1%26continue%3Dhttps%253A%252F%252Fecom.meituan.com%252Fbizaccount%252Fbiz-choice.html%253Fredirect_uri%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fmeishi%2526_t%253D1753846425726%2526target%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fmeishi%26leftBottomLink%3D%26signUpTarget%3Dself")
    page.locator("iframe").content_frame.get_by_role("link", name="扫码登录").click()
    page.locator("iframe").content_frame.locator(".dot").first.click()
    page.locator("iframe").content_frame.get_by_role("button", name="确定").click()
    page.get_by_role("button", name="开始体验").click()
    with page.expect_popup() as page1_info:
        page.get_by_text("经营参谋").click()
    page1 = page1_info.value
    page.close()
    page1.get_by_role("link", name="商品列表 分商品数据明细").click()
    page1.locator("iframe").content_frame.get_by_role("button", name="单日").click()
    page1.locator("iframe").content_frame.get_by_role("button", name="29").click()
    page1.locator("iframe").content_frame.get_by_role("button", name="单月").click()
    page1.locator("iframe").content_frame.get_by_role("button", name="6月").click()
    page1.locator("iframe").content_frame.get_by_role("button", name="自定义日期区间").click()
    page1.locator("iframe").content_frame.get_by_role("button", name="27").first.click()
    page1.locator("iframe").content_frame.get_by_role("button", name="29").first.click()
    page1.locator("iframe").content_frame.get_by_role("button", name=" 导出数据").click()
    page1.locator("iframe").content_frame.get_by_role("radio", name="导出每日明细数据").check()
    page1.locator("iframe").content_frame.get_by_role("button", name="确定").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
