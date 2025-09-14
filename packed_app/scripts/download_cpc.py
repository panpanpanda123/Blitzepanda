"""
download_cpc.py

用途：封装“CPC（推广通）数据”的 Playwright 自动化下载流程。
定位方式：两层 iframe（外层 #iframeContainer，内层以 midas.dianping.com 为前缀的 iframe），
          频道切换、日期控件、下载记录表定位与逐条下载。
"""

import re
import time
from pathlib import Path
from typing import Tuple

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


HOME_URL = (
    "https://ecom.meituan.com/meishi/?cate=5348"
    "#https://midas.dianping.com/shopdiy/account/pcCpcEntry"
    "?continueUrl=/app/peon-merchant-product-menu/html/index.html"
)


def _handle_business_login_popup(page: Page) -> None:
    """处理顶层登录/业务选择弹窗（iframe.loginFormContent）。

    老代码逻辑：
    - 尝试 500~800ms 侦测弹窗 iframe
    - 若存在：选择“我是餐饮商家”，点击“确定”，并等待网络空闲
    """
    popup = False
    try:
        page.wait_for_selector("iframe.loginFormContent", timeout=800)
        popup = True
    except PlaywrightTimeoutError:
        popup = False

    if not popup:
        return

    login_frame = page.frame_locator("iframe.loginFormContent")
    try:
        login_frame.locator('div.biz-item:has-text("我是餐饮商家")').click()
    except Exception:
        try:
            login_frame.get_by_text("我是餐饮商家", exact=False).click()
        except Exception:
            pass
    try:
        login_frame.locator('button.button.active:has-text("确定")').click()
    except Exception:
        try:
            login_frame.get_by_role("button", name="确定").click()
        except Exception:
            pass
    page.wait_for_load_state("networkidle", timeout=5000)


def _enter_midas_cpc(page: Page):
    """进入推广通页面并切到 CPC 内层 iframe。返回内层 frame 定位器。"""
    page.goto(HOME_URL, wait_until="networkidle")
    _handle_business_login_popup(page)
    ad_iframe = page.frame_locator("#iframeContainer")
    btn = ad_iframe.get_by_text("推广通", exact=True)
    btn.scroll_into_view_if_needed(timeout=6000)
    btn.wait_for(state="visible", timeout=6000)
    try:
        btn.click(force=True)
    except Exception:
        btn.evaluate("el => el.click()")
    time.sleep(1)
    cpc_frame = ad_iframe.frame_locator("iframe[title^='https://midas.dianping.com/shopdiy/account/pcCpcEntry']")
    return cpc_frame


def _switch_channel_to_dianping(cpc_frame):
    """切换到点评频道"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 等待页面加载
            time.sleep(2)  # 增加等待时间
            
            # 点击"数据报告"
            data_report_btn = cpc_frame.get_by_text("数据报告", exact=True)
            data_report_btn.wait_for(state="visible", timeout=5000)  # 增加超时时间
            data_report_btn.click()
            time.sleep(1.5)  # 增加等待时间
            
            # 尝试定位"推广分析"按钮
            promotion_btn = None
            try:
                # 优先使用精确文本匹配
                promotion_btn = cpc_frame.get_by_text("推广分析", exact=True)
                promotion_btn.wait_for(state="visible", timeout=3000)
            except Exception:
                try:
                    # 备选方案：模糊文本匹配
                    promotion_btn = cpc_frame.get_by_text("推广分析", exact=False)
                    promotion_btn.wait_for(state="visible", timeout=3000)
                except Exception:
                    # 最后备选：通过div定位
                    promotion_btn = cpc_frame.locator("div").filter(has_text="推广分析").first
                    promotion_btn.wait_for(state="visible", timeout=3000)
            
            if promotion_btn and promotion_btn.is_visible():
                # 点击按钮
                try:
                    promotion_btn.click()
                except Exception:
                    promotion_btn.click(force=True)
                
                time.sleep(1)  # 增加等待时间
                print("✅ 已点击推广分析按钮，继续下一步")
                break
            else:
                print(f"⚠️ 第{retry_count + 1}次尝试：未找到推广分析按钮")
                retry_count += 1
                time.sleep(2)  # 增加等待时间
                continue
                
        except Exception as e:
            print(f"⚠️ 第{retry_count + 1}次尝试：切换频道时出错 - {str(e)}")
            retry_count += 1
            time.sleep(2)  # 增加等待时间
            continue
    
    if retry_count >= max_retries:
        print("⚠️ 无法找到推广分析按钮，尝试继续执行后续步骤...")
    
    # 继续后续操作
    time.sleep(1)  # 增加等待时间
    cpc_frame.locator("div").filter(has_text=re.compile(r"^美团\+点评$")).click()
    time.sleep(0.5)  # 增加等待时间
    cpc_frame.get_by_role("listitem").filter(has_text=re.compile(r"^点评$")).click()
    time.sleep(0.5)  # 增加等待时间


def _pick_date_range(cpc_frame, start_date: str, end_date: str) -> None:
    # 选择自定义日期
    container = cpc_frame.locator("div").filter(has_text=re.compile(r"自定义"))
    container.get_by_placeholder("开始日期").first.click()
    time.sleep(0.5)

    sd = start_date.split("-")[2].lstrip("0")
    ed = end_date.split("-")[2].lstrip("0")
    start_label = f"{int(start_date.split('-')[1])}月"
    end_label = f"{int(end_date.split('-')[1])}月"

    panels = cpc_frame.locator("div.merchant-date-picker-panel-calendar-month")
    start_panel = panels.filter(has_text=start_label).first
    end_panel = panels.filter(has_text=end_label).first

    start_panel \
        .locator(
            "div.merchant-date-picker-panel-calendar-month__date--current-month:not(.merchant-date-picker-panel-calendar-month__date--disabled)"
        ) \
        .locator("div.merchant-date-picker-panel-calendar-month__date-date", has_text=sd) \
        .first.click()
    time.sleep(0.2)

    end_panel \
        .locator(
            "div.merchant-date-picker-panel-calendar-month__date--current-month:not(.merchant-date-picker-panel-calendar-month__date--disabled)"
        ) \
        .locator("div.merchant-date-picker-panel-calendar-month__date-date", has_text=ed) \
        .first.click()
    time.sleep(0.2)

    cpc_frame.get_by_role("button", name="确定", exact=True).click()
    time.sleep(0.8)


def _ensure_hourly_split(cpc_frame):
    """确保选择分小时模式，如果找不到则跳过"""
    max_retries = 2
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 等待页面稳定
            time.sleep(1)
            
            # 尝试找到"分天"按钮
            seg_btn = cpc_frame.get_by_text("分天").first
            if seg_btn.is_visible():
                seg_btn.click()
                time.sleep(0.8)  # 增加等待时间
                
                # 点击"分小时"
                hourly_btn = cpc_frame.get_by_text("分小时", exact=True)
                hourly_btn.wait_for(state="visible", timeout=3000)
                hourly_btn.click()
                time.sleep(0.8)  # 增加等待时间
                print("✅ 已切换到分小时模式")
                return
            else:
                print("✅ 已经是分小时模式或无需切换")
                return
                
        except Exception as e:
            print(f"⚠️ 第{retry_count + 1}次尝试：切换到分小时模式失败 - {str(e)}")
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2)  # 等待后重试
                continue
            else:
                print("⚠️ 切换到分小时模式失败，继续执行后续步骤")
                break
    
    print("⚠️ 切换到分小时模式失败，继续执行后续步骤")


def _apply_time_split(cpc_frame):
    """应用时间拆分，如果找不到按钮则完全重新执行推广分析流程"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 尝试找到"按时间拆分"按钮
            time_split_btn = cpc_frame.get_by_text("按时间拆分", exact=True).first
            time_split_btn.wait_for(state="visible", timeout=5000)
            time_split_btn.click()
            time.sleep(0.4)
            print("✅ 成功点击按时间拆分按钮")
            return
        except Exception as e:
            print(f"⚠️ 第{retry_count + 1}次尝试：未找到'按时间拆分'按钮 - {str(e)}")
            retry_count += 1
            
            if retry_count < max_retries:
                print("🔄 页面可能已重置，完全重新执行推广分析流程...")
                # 完全重新执行推广分析流程
                try:
                    # 等待页面稳定
                    time.sleep(2)
                    
                    # 1. 重新点击"数据报告"
                    print("   🔄 重新点击数据报告...")
                    data_report_btn = cpc_frame.get_by_text("数据报告", exact=True)
                    data_report_btn.wait_for(state="visible", timeout=5000)
                    data_report_btn.click()
                    time.sleep(1.5)
                    
                    # 2. 重新点击"推广分析"
                    print("   🔄 重新点击推广分析...")
                    promotion_btn = None
                    try:
                        promotion_btn = cpc_frame.get_by_text("推广分析", exact=True)
                        promotion_btn.wait_for(state="visible", timeout=3000)
                    except Exception:
                        try:
                            promotion_btn = cpc_frame.get_by_text("推广分析", exact=False)
                            promotion_btn.wait_for(state="visible", timeout=3000)
                        except Exception:
                            promotion_btn = cpc_frame.locator("div").filter(has_text="推广分析").first
                            promotion_btn.wait_for(state="visible", timeout=3000)
                    
                    if promotion_btn and promotion_btn.is_visible():
                        promotion_btn.click()
                        time.sleep(1.5)
                        print("   ✅ 重新进入推广分析页面")
                        
                        # 3. 重新选择"点评"频道
                        print("   🔄 重新选择点评频道...")
                        cpc_frame.locator("div").filter(has_text=re.compile(r"^美团\+点评$")).click()
                        time.sleep(0.5)
                        cpc_frame.get_by_role("listitem").filter(has_text=re.compile(r"^点评$")).click()
                        time.sleep(0.5)
                        print("   ✅ 重新选择点评频道完成")
                        
                        # 4. 等待页面完全加载
                        time.sleep(2)
                        print("   ✅ 页面重新加载完成，准备重试")
                    else:
                        print("   ⚠️ 无法重新找到推广分析按钮")
                        continue
                        
                except Exception as retry_e:
                    print(f"   ⚠️ 重新执行推广分析流程失败: {str(retry_e)}")
                    time.sleep(2)
                    continue
                
                time.sleep(1)  # 额外等待页面稳定
                continue
    
    # 如果所有重试都失败，抛出异常
    raise RuntimeError("无法找到'按时间拆分'按钮，请检查页面状态")


def _click_download_detail(cpc_frame):
    try:
        cpc_frame.get_by_role("button", name=re.compile("下载明细")).first.click()
    except Exception:
        cpc_frame.get_by_text("下载明细").first.click()
    time.sleep(1)
    try:
        cpc_frame.get_by_text("我知道了", exact=True).click(timeout=2000)
    except Exception:
        pass


def _download_from_records(page: Page, cpc_frame, download_dir: Path, start_date: str, end_date: str, brand: str) -> None:
    # 打开下载记录
    cpc_frame.get_by_role("button", name=re.compile("下载记录")).nth(0).click()
    time.sleep(1)

    rows = cpc_frame.get_by_role("row").all()
    date_flag = start_date.replace("-", "")
    targets = [r for r in rows if date_flag in r.text_content() and "下载" in r.text_content()][:2]
    if len(targets) < 2:
        raise RuntimeError("下载记录不足两条（点评/美团），请稍后重试")

    platforms = ["美团", "点评"]  # 顺序与页面记录顺序相匹配
    date_s = start_date.replace("-", "")
    date_e = end_date.replace("-", "")
    for i, row in enumerate(targets):
        plat = platforms[i]
        with page.expect_download() as dl_info:
            row.get_by_text("下载").click()
        download = dl_info.value
        filename = f"推广报表_{date_s}_{date_e}_{brand}_{plat}.xlsx"
        download.save_as(str(Path(download_dir) / filename))
        time.sleep(0.8)


def download_cpc(page: Page, download_dir: Path, start_date: str, end_date: str, profile: str, brand: str) -> None:
    """执行 CPC（推广通）数据下载主流程。"""
    cpc_frame = _enter_midas_cpc(page)
    _switch_channel_to_dianping(cpc_frame)
    _pick_date_range(cpc_frame, start_date, end_date)
    _ensure_hourly_split(cpc_frame)
    _apply_time_split(cpc_frame)
    _click_download_detail(cpc_frame)  # 点点评

    # 切换到美团再点一次“下载明细”
    page.keyboard.press("PageUp"); time.sleep(0.2)
    page.keyboard.press("PageUp"); time.sleep(0.3)
    cpc_frame.locator("div").filter(has_text=re.compile(r"^点评$")).click(); time.sleep(0.2)
    cpc_frame.get_by_role("listitem").filter(has_text=re.compile(r"^美团$")).click(); time.sleep(0.2)
    _click_download_detail(cpc_frame)

    # 打开下载记录并分别下载两条
    _download_from_records(page, cpc_frame, download_dir, start_date, end_date, brand)


