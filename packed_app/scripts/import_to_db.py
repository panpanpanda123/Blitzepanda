
"""
批量导入下载完成后的 Excel 到数据库（精简版）。

功能保持与旧脚本一致，但依赖新的 app.* 模块：
- app.pipelines.import_operation_folder
- app.pipelines.import_cpc_folder
"""

import os
from app.pipelines import import_operation_folder, import_cpc_folder

def process_operation_folder(OPERATION_FOLDER):
    import_operation_folder(OPERATION_FOLDER)


def process_cpc_folder(CPC_HOURLY_FOLDER):
    import_cpc_folder(CPC_HOURLY_FOLDER)

if __name__ == '__main__':
    # 跟随 download_data.py，数据目录为 pythonProject/data/operation_data 和 pythonProject/data/cpc_hourly_data
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    OPERATION_FOLDER = os.path.join(base_dir, 'operation_data')
    CPC_HOURLY_FOLDER = os.path.join(base_dir, 'cpc_hourly_data')
    process_operation_folder(OPERATION_FOLDER)
    process_cpc_folder(CPC_HOURLY_FOLDER)
