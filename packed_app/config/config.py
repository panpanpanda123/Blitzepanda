# config.py
"""
全局配置文件，集中管理数据库、路径、品牌等配置信息。
"""

import os

# 数据库配置（自动对齐老代码实际连接参数）
db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'xpxx1688',
    'database': 'dianping',
    'charset': 'utf8mb4',
}

# 数据下载路径
DATA_DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'downloads')
# 数据处理后存放路径
DATA_PROCESSED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'processed')

# 品牌映射配置（如有更复杂需求可用 json/yaml 文件）
BRAND_MAPPING = {
    # '品牌名': '标准品牌名',
}

# 其他全局参数
REPORT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')

# Word 模板路径，指向项目根目录下 templates 文件夹中的模板
WORD_TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'templates',
    'monthly_report_template.docx'
)

# 可根据实际情况补充其他配置