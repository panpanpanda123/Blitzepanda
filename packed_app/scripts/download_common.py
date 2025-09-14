"""
download_common.py

用途：提供通用的 Playwright 启动、用户数据目录克隆、日期计算与输入等辅助函数。
说明：新下载流程只依赖本文件与同目录下的 download_operation.py / download_cpc.py。
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, List

from playwright.sync_api import sync_playwright


@dataclass
class DateRange:
    start: date
    end: date

    @classmethod
    def yesterday_or_weekend(cls) -> "DateRange":
        """若今天是周一，则取上周五~周日，否则取昨天~昨天。"""
        today = date.today()
        if today.weekday() == 0:
            start = today - timedelta(days=3)
            end = today - timedelta(days=1)
        else:
            start = today - timedelta(days=1)
            end = start
        return cls(start=start, end=end)

    def to_str_pair(self) -> tuple[str, str]:
        return self.start.isoformat(), self.end.isoformat()


def clone_user_data(src: Path, dst: Path, profiles: Iterable[str]) -> None:
    """克隆 Chrome 用户数据目录中的指定 profiles 到可读写的工作目录。

    - 仅在目标目录缺失对应数据时复制，避免重复 I/O。
    """
    dst.mkdir(parents=True, exist_ok=True)
    # Local State
    try:
        if not (dst / "Local State").exists() and (src / "Local State").exists():
            shutil.copy(src / "Local State", dst / "Local State")
    except Exception:
        pass

    for prof in profiles:
        prof_dst = dst / prof
        if prof_dst.exists():
            continue
        prof_src = src / prof
        if prof_src.exists():
            shutil.copytree(prof_src, prof_dst)


def open_chromium_context(user_data_dir: Path, profile: str, downloads_path: Path):
    """打开持久化 Chromium Context（免扫码），返回 (playwright, browser_context, page)。"""
    # Playwright 要求持久化上下文不能使用“默认用户数据目录”，否则会报 DevTools remote debugging 错误
    def _default_user_data_dir() -> Path:
        local_app_data = os.getenv("LOCALAPPDATA", "")
        if local_app_data:
            return Path(local_app_data) / "Google" / "Chrome" / "User Data"
        # 兜底：常见默认路径
        return Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"

    try:
        if user_data_dir.resolve().as_posix().lower() == _default_user_data_dir().resolve().as_posix().lower():
            raise RuntimeError(
                "检测到使用默认用户数据目录启动浏览器。Playwright 的持久化上下文要求使用非默认目录。"
                "请在 scripts/settings.yaml 中将 clone_dir 配置为非默认目录（例如 D:/chrome_playwright_clone），"
                "并确保其中包含所需的 Profile（如 'Profile 49'）。"
            )
    except Exception:
        # 若路径解析失败，不影响后续启动
        pass

    p = sync_playwright().start()
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        channel="chrome",
        headless=False,
        args=[f"--profile-directory={profile}", "--disable-infobars"],
        accept_downloads=True,
        downloads_path=str(downloads_path),
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    return p, ctx, page


def close_all(p, ctx) -> None:
    """关闭 Playwright 实例与浏览器上下文。"""
    try:
        ctx.close()
    finally:
        p.stop()


