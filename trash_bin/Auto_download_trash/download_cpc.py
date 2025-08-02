import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(**playwright.devices["Desktop Chrome"])
    page = context.new_page()
    page.goto("https://ecom.meituan.com/bizaccount/login.html?loginByPhoneNumber=true&isProduction=true&epassportParams=%3Fbg_source%3D1%26service%3Dcom.sankuai.meishi.fe.ecom%26part_type%3D0%26feconfig%3Dbssoify%26biz_line%3D1%26continue%3Dhttps%253A%252F%252Fecom.meituan.com%252Fbizaccount%252Fbiz-choice.html%253Fredirect_uri%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fmeishi%2526_t%253D1749530731114%2526target%253Dhttps%25253A%25252F%25252Fecom.meituan.com%25252Fmeishi%26leftBottomLink%3D%26signUpTarget%3Dself")
    page.locator("iframe").content_frame.get_by_role("link", name="扫码登录").click()
    page.locator("iframe").content_frame.locator(".circle").first.click()
    page.locator("iframe").content_frame.get_by_role("main").locator("div").filter(has_text="我是餐饮商家 餐饮商家版 美食餐厅、饮品店、保健食品、水果生鲜等").first.click()
    page.locator("iframe").content_frame.get_by_role("button", name="确定").click()
    page.get_by_text("推广中心").click()
    page.locator("#iframeContainer").content_frame.get_by_text("首页推广通智选展位置顶卡关键词素材中心推广方案推广财务推广教程更多").click()
    page.locator("#iframeContainer").content_frame.get_by_text("推广通").click()
    page.locator("#iframeContainer").content_frame.get_by_text("推广通").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_text("数据报告").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_text("推广分析").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.locator("div").filter(has_text=re.compile(r"^美团\+点评$")).click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_role("listitem").filter(has_text=re.compile(r"^点评$")).click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.locator("div").filter(has_text=re.compile(r"^今日昨日近7日自定义~对比$")).get_by_placeholder("开始日期").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_text("9", exact=True).first.click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_text("9", exact=True).first.click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_role("button", name="确定").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.locator("div").filter(has_text=re.compile(r"^分小时$")).click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_role("listitem").filter(has_text="分小时").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_text("按时间拆分").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_role("button", name=" 下载明细").first.click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_role("button", name="我知道了").click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.locator("div").filter(has_text=re.compile(r"^点评$")).click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_role("listitem").filter(has_text=re.compile(r"^美团$")).click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_role("button", name=" 下载明细").first.click()
    page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_text("前往获取>>").click()
    with page.expect_download() as download_info:
        with page.expect_popup() as page1_info:
            page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_role("row", name="2025-06-10 12:48:48 推广报表").get_by_role("button").click()
        page1 = page1_info.value
    download = download_info.value
    page1.close()
    with page.expect_download() as download1_info:
        with page.expect_popup() as page2_info:
            page.locator("#iframeContainer").content_frame.locator("iframe[title=\"https\\:\\/\\/midas\\.dianping\\.com\\/shopdiy\\/account\\/pcCpcEntry\\?continueUrl\\=\\/app\\/peon-hornet-promo\\/html\\/promo-list\\.html\"]").content_frame.get_by_role("row", name="2025-06-10 12:48:38 推广报表").get_by_role("button").click()
        page2 = page2_info.value
    download1 = download1_info.value
    page2.close()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
