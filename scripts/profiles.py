"""
profiles.py

用途：集中维护浏览器 Profile 与品牌、是否需要下载 CPC/运营数据 的映射关系。
说明：此文件为新代码的唯一映射来源，避免继续引用 legacy 目录下的老文件。
"""

from typing import Dict, Any


# 可根据实际维护：键为 Chrome 的 Profile 名（如 "Profile 27"），值为配置字典
# - brand: 品牌名（仅用于命名下载文件）
# - cpc: 是否下载 CPC 数据
# - op: 是否下载运营数据
PROFILE_BRAND_MAP: Dict[str, Dict[str, Any]] = {
    'Profile 59': {'brand': '青鹤谷',          'cpc': False, 'op': True},
    'Profile 41': {'brand': '流杯酒肆',        'cpc': True, 'op': True},
    'Profile 27': {'brand': '三德',           'cpc': True, 'op': True},
    'Profile 36': {'brand': '大连进士食堂',   'cpc': False, 'op': True},
    'Profile 43': {'brand': '进士食堂',       'cpc': True, 'op': True},
    'Profile 45': {'brand': '杜九月',         'cpc': True, 'op': True},
    'Profile 49': {'brand': '木槿花',         'cpc': True, 'op': True},
    'Profile 50': {'brand': '韩味岛',         'cpc': True, 'op': True},
    'Profile 60': {'brand': '朱桢',           'cpc': True, 'op': True},
    'Profile 57': {'brand': '香啦啦',           'cpc': True, 'op': True},
}


