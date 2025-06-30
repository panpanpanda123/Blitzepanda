import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(**playwright.devices["Desktop Chrome"])
    page = context.new_page()
    page.goto("https://ecom.meituan.com/bizaccount/login.html?loginByPhoneNumber=true&isProduction=true&epassportParams=%3Fbg_source%3D1%26service%3Dcom.sankuai.meishi.fe.ecom%26part_type%3D0%26feconfig%3Dbssoify%26biz_line%3D1%26continue%3Dhttps%253A%252F%252Fecom.meituan.com%252Fbizaccount%252Fbiz-choice.html%253Fredirect_uri%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fmeishi%2526_t%253D1750992080844%2526target%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fmeishi%26leftBottomLink%3D%26signUpTarget%3Dself")
    page.locator("iframe").content_frame.get_by_role("link", name="扫码登录").click()
    page.locator("iframe").content_frame.get_by_text("美食餐厅、饮品店、保健食品、水果生鲜等").click()
    page.locator("iframe").content_frame.locator(".circle").first.click()
    page.locator("iframe").content_frame.get_by_role("button", name="确定").click()
    with page.expect_popup() as page1_info:
        page.get_by_text("经营参谋").click()
    page1 = page1_info.value
    page1.get_by_role("link", name="报表").click()
    page1.locator("iframe").content_frame.get_by_text("点击重置").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
