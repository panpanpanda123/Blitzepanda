import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(**playwright.devices["Desktop Chrome"])
    page = context.new_page()
    page.goto("https://ecom.meituan.com/bizaccount/login.html?loginByPhoneNumber=true&isProduction=true&epassportParams=%3Fbg_source%3D1%26service%3Dcom.sankuai.meishi.fe.ecom%26part_type%3D0%26feconfig%3Dbssoify%26biz_line%3D1%26continue%3Dhttps%253A%252F%252Fecom.meituan.com%252Fbizaccount%252Fbiz-choice.html%253Fredirect_uri%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fmeishi%2526_t%253D1749706227996%2526target%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fmeishi%26leftBottomLink%3D%26signUpTarget%3Dself")
    page.locator("iframe").content_frame.get_by_text("账号登录验证码登录扫码登录账号密码忘记密码忘记账号登录还没有账号？免费注册其他登录方式微信登录").click()
    page.locator("iframe").content_frame.get_by_role("link", name="扫码登录").click()
    page.get_by_text("推广中心").click()
    page.get_by_role("button", name="").click()
    page.locator("#iframeContainer").content_frame.get_by_text("更多").click()
    page.locator("#iframeContainer").content_frame.get_by_text("多账号管理").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-cpm-ncpm\\/html\\/sub-account-manage\\.html\"]").content_frame.get_by_role("cell", name="mt15618816515").click()
    page.locator("#iframeContainer").content_frame.get_by_text("推广通").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_text("数据报告").click()
    page.locator("#iframeContainer").content_frame.get_by_text("多账号管理").click()
    page.locator("#iframeContainer").content_frame.get_by_text("订阅管理").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/notice-manage\\.html\"]").content_frame.get_by_text("其他订阅").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/notice-manage\\.html\"]").content_frame.get_by_text("操作授权").click()
    page.locator("#iframeContainer").content_frame.get_by_text("推广通").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
