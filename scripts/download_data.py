
"""
数据下载主入口（精简版）

目标：不再引用 legacy 代码，采用本目录下的新模块执行“运营数据/CPC 数据”下载。
流程：
1) 读取本地 settings.yaml（位置可在此文件调整）以获得 Chrome 用户数据路径与工作克隆路径；
2) 克隆所需 profiles 的浏览器数据；
3) 逐个 profile 按配置执行 CPC 与/或运营数据下载；
4) 下载目录统一落在项目 data 目录下。
"""

from pathlib import Path
import sys
from datetime import date, timedelta
import getpass
import yaml

from config.config import DATA_DOWNLOAD_DIR
from utils.logger import get_logger

try:
    # 确保可以以 "python scripts/download_data.py" 方式运行
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
except Exception:
    pass

from scripts.download_common import clone_user_data, open_chromium_context, close_all, DateRange
from scripts.download_operation import download_operation
from scripts.download_cpc import download_cpc
from scripts.profiles import PROFILE_BRAND_MAP


def load_settings(settings_path: Path) -> dict:
    """读取 settings.yaml，并将 {{username}} 占位符替换为当前用户名。"""
    with open(settings_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    user = getpass.getuser()
    for k, v in cfg.items():
        if isinstance(v, str):
            cfg[k] = v.replace("{{username}}", user)
    return cfg


def download_dianping_data(download_root: Path) -> None:
    # 1) 读取设置
    base_dir = Path(__file__).parent  # scripts 目录
    settings_path = base_dir / "settings.yaml"
    cfg = load_settings(settings_path)
    src = Path(cfg["chrome_user_data"]).expanduser().resolve()
    clone = Path(cfg["clone_dir"]).expanduser().resolve()

    # 2) 确保下载目录（兼容旧脚本：若传入的是 data/downloads，则回退到 data 根目录）
    effective_root = download_root.parent if download_root.name.lower() == "downloads" else download_root
    cpc_dir = (effective_root / "cpc_hourly_data"); cpc_dir.mkdir(parents=True, exist_ok=True)
    op_dir = (effective_root / "operation_data"); op_dir.mkdir(parents=True, exist_ok=True)

    # 3) 克隆用户数据
    profiles = list(PROFILE_BRAND_MAP.keys())
    clone_user_data(src, clone, profiles)

    # 4) 选择日期（默认昨天；周一默认跨周五~周日）
    dr = DateRange.yesterday_or_weekend()
    default = f"{dr.start.isoformat()},{dr.end.isoformat()}"
    text = input(f"下载日期范围（YYYY-MM-DD,YYYY-MM-DD），回车默认[{default}]: ").strip()
    if text:
        s, e = map(str.strip, text.split(","))
    else:
        s, e = dr.to_str_pair()

    # 5) 可选品牌筛选
    brand_input = input("👉 如需只下载部分品牌，请输入品牌名（多个用英文逗号隔开），回车下载全部：").strip()
    if brand_input:
        selected = set(b.strip() for b in brand_input.split(","))
        selected_profiles = [p for p, conf in PROFILE_BRAND_MAP.items() if conf.get("brand") in selected]
        if not selected_profiles:
            print("❌ 未匹配到任何品牌，请检查输入"); return
    else:
        selected_profiles = profiles

    # 6) 逐 profile 下载
    for prof in selected_profiles:
        logger = get_logger("download_data")
        logger.info(f"===== Running {prof} [{s} → {e}] =====")
        p, ctx, page = open_chromium_context(clone, prof, download_root)
        try:
            conf = PROFILE_BRAND_MAP.get(prof, {})
            brand = conf.get("brand", prof)
            if conf.get("cpc", False):
                download_cpc(page, cpc_dir, s, e, prof, brand)
            if conf.get("op", True):
                download_operation(page, op_dir, s, e, brand)
        finally:
            close_all(p, ctx)


def download_dianping_data_gui(download_root: Path, start_date: str, end_date: str, selected_brands: list, wait_time: int = 3, resume_from: str = None, progress_callback=None) -> dict:
    """GUI版本的下载函数，支持断点续传和进度回调"""
    # 1) 读取设置
    base_dir = Path(__file__).parent  # scripts 目录
    settings_path = base_dir / "settings.yaml"
    cfg = load_settings(settings_path)
    src = Path(cfg["chrome_user_data"]).expanduser().resolve()
    clone = Path(cfg["clone_dir"]).expanduser().resolve()

    # 2) 确保下载目录（兼容旧脚本：若传入的是 data/downloads，则回退到 data 根目录）
    effective_root = download_root.parent if download_root.name.lower() == "downloads" else download_root
    cpc_dir = (effective_root / "cpc_hourly_data"); cpc_dir.mkdir(parents=True, exist_ok=True)
    op_dir = (effective_root / "operation_data"); op_dir.mkdir(parents=True, exist_ok=True)

    # 3) 克隆用户数据
    profiles = list(PROFILE_BRAND_MAP.keys())
    clone_user_data(src, clone, profiles)

    # 4) 根据选中的品牌筛选profiles
    if selected_brands:
        # 将品牌名转换为profile列表
        selected_profiles = []
        for profile, conf in PROFILE_BRAND_MAP.items():
            if conf.get("brand") in selected_brands:
                selected_profiles.append(profile)
        
        if not selected_profiles:
            raise ValueError(f"未找到对应的profile: {selected_brands}")
    else:
        selected_profiles = profiles

    # 5) 断点续传逻辑
    if resume_from:
        # 找到断点位置
        try:
            resume_index = selected_profiles.index(resume_from)
            logger = get_logger("download_data")
            logger.info(f"🔄 断点续传：从 {resume_from} 开始继续下载")
            selected_profiles = selected_profiles[resume_index:]
        except ValueError:
            logger = get_logger("download_data")
            logger.warning(f"⚠️ 断点 {resume_from} 不在当前列表中，从头开始下载")
    
    # 6) 记录下载结果
    download_results = {
        'success': [],
        'failed': [],
        'current_progress': 0,
        'total_count': len(selected_profiles),
        'last_successful': None,
        'last_failed': None
    }
    
    # 7) 逐 profile 下载
    for i, prof in enumerate(selected_profiles):
        logger = get_logger("download_data")
        current_progress = i + 1
        download_results['current_progress'] = current_progress
        
        logger.info(f"===== Running {prof} [{start_date} → {end_date}] ({current_progress}/{len(selected_profiles)}) =====")
        
        try:
            p, ctx, page = open_chromium_context(clone, prof, download_root)
            try:
                conf = PROFILE_BRAND_MAP.get(prof, {})
                brand = conf.get("brand", prof)
                
                # 根据配置决定下载什么数据
                if conf.get("cpc", False):
                    logger.info(f"开始下载 {brand} 的CPC数据...")
                    download_cpc(page, cpc_dir, start_date, end_date, prof, brand)
                    logger.info(f"{brand} CPC数据下载完成")
                    
                    # 等待用户设置的等待时间
                    if wait_time > 0:
                        logger.info(f"等待 {wait_time} 秒...")
                        import time
                        time.sleep(wait_time)
                
                if conf.get("op", True):
                    logger.info(f"开始下载 {brand} 的运营数据...")
                    download_operation(page, op_dir, start_date, end_date, brand)
                    logger.info(f"{brand} 运营数据下载完成")
                    
                    # 等待用户设置的等待时间
                    if wait_time > 0:
                        logger.info(f"等待 {wait_time} 秒...")
                        import time
                        time.sleep(wait_time)
                
                # 下载成功
                download_results['success'].append(prof)
                download_results['last_successful'] = prof
                logger.info(f"✅ {brand} 下载完成 ({current_progress}/{len(selected_profiles)})")
                
                # 调用进度回调函数
                if progress_callback:
                    progress_callback(current_progress, len(selected_profiles), f"已完成 {brand}")
                
            finally:
                close_all(p, ctx)
                
        except Exception as e:
            # 下载失败
            download_results['failed'].append(prof)
            download_results['last_failed'] = prof
            logger.error(f"❌ {prof} 下载失败: {str(e)}")
            
            # 返回当前状态，供GUI处理
            return {
                'status': 'failed',
                'error': str(e),
                'failed_at': prof,
                'progress': download_results,
                'resume_from': prof,  # 下次可以从这里继续
                'completed_count': len(download_results['success']),
                'total_count': len(selected_profiles)
            }
    
    # 全部下载完成
    logger.info("🎉 所有数据下载完成！")
    return {
        'status': 'success',
        'progress': download_results,
        'completed_count': len(selected_profiles),
        'total_count': len(selected_profiles)
    }


def main():
    logger = get_logger('download_data')
    logger.info(f"数据将下载到: {DATA_DOWNLOAD_DIR}")
    download_dianping_data(Path(DATA_DOWNLOAD_DIR))
    logger.info("下载流程已完成")


if __name__ == '__main__':
    main()
