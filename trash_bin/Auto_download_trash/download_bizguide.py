import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(**playwright.devices["Desktop Chrome"])
    page = context.new_page()
    page.goto("https://ecom.meituan.com/bizaccount/login.html?epassportParams=bg_source%3D1%26service%3Dcom.sankuai.meishi.fe.bizsettle%26feconfig%3Dbssoify%26continue%3Dhttps%253A%252F%252Fepassport.meituan.com%252Fgw%252Fbsso%252FsetToken%253Fredirect_uri%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fbizaccount%25252Fredirect.html%25253Ftarget%25253Dhttps%2525253A%2525252F%2525252Fecom.meituan.com%2525252Fbizguide%2525252Fportal%2525253Fcate%2525253D100057652%25252523https%2525253A%2525252F%2525252Fecom.meituan.com%2525252Fbizguide%2525252Fexport&isProduction=true")
    page.locator("iframe").content_frame.get_by_role("link", name="扫码登录").click()
    page.locator("iframe").content_frame.get_by_text("下载列表").click()
    page.locator("iframe").content_frame.get_by_text("报表内容").click()
    page.locator("iframe").content_frame.get_by_text("下载列表").click()
    page.locator("iframe").content_frame.locator(".report-form-module_actionText_v26Iw").first.click()
    page.locator("iframe").content_frame.locator("div:nth-child(12) > .mtd-form-item-body > .report-form-module_indicatorContainer_oU77P > .report-form-module_mainIndicator_Drhw9 > .report-form-module_checkbox_Zrrn3 > .report-form-module_actionText_v26Iw").click()
    page.locator("iframe").content_frame.locator("div:nth-child(13) > .mtd-form-item-body > .report-form-module_indicatorContainer_oU77P > .report-form-module_mainIndicator_Drhw9 > .report-form-module_checkbox_Zrrn3 > .report-form-module_actionText_v26Iw").click()
    page.locator("iframe").content_frame.locator("div:nth-child(15) > .mtd-form-item-body > .report-form-module_indicatorContainer_oU77P > .report-form-module_mainIndicator_Drhw9 > .report-form-module_checkbox_Zrrn3 > .report-form-module_actionText_v26Iw").click()
    page.locator("iframe").content_frame.get_by_text("全选", exact=True).first.click()
    page.locator("iframe").content_frame.get_by_text("全选", exact=True).first.click()
    page.locator("iframe").content_frame.get_by_text("全选", exact=True).first.click()
    page.locator("iframe").content_frame.get_by_text("全选", exact=True).first.click()
    page.locator("iframe").content_frame.get_by_text("全选", exact=True).click()
    page.locator("iframe").content_frame.get_by_text("流量、交易指标需要包含分来源数据-来源包括：搜索、美食频道、团购频道、首页信息流、特价团、美团联盟、直播").click()
    page.locator("iframe").content_frame.get_by_role("textbox", name="开始日期 至 结束日期").click()
    page.locator("iframe").content_frame.get_by_role("button", name="").click()
    page.locator("iframe").content_frame.get_by_role("button", name="").first.click()
    page.locator("iframe").content_frame.get_by_role("button", name="1", exact=True).first.click()
    page.locator("iframe").content_frame.get_by_role("button", name="").first.dblclick()
    page.locator("iframe").content_frame.get_by_role("button", name="9", exact=True).first.click()
    page.locator("iframe").content_frame.get_by_role("button", name="立即下载").click()
    page.locator("iframe").content_frame.get_by_role("button", name="前往下载").click()
    page.locator("iframe").content_frame.get_by_text("--").click()
    page.locator("iframe").content_frame.get_by_text("--").click()
    page.locator("iframe").content_frame.get_by_text("--").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
