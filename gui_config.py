# GUI配置文件
import json
import os
from pathlib import Path

# 默认商户配置
DEFAULT_BRANDS = {
    "流杯酒肆": {
        "基本定位": "位于上海静安寺，定位为社交型中餐酒馆，客单价约300元，融合定制调酒和中式小吃。",
        "目标人群": "25-35岁都市白领女性，重视社交体验、审美氛围与互动感。",
        "关键场景": "朋友聚会、女生小聚、夜间约会、节日送杯活动。",
        "核心亮点": "\"留杯玩法\"制造复购仪式感，调酒互动增强社交记忆点。",
        "当前阶段目标": "提升老客复购率与到店频次，辅助引导线上传播提升自然流量。",
        "潜在问题": "门店位置在二楼，进店率低；调酒环节依赖服务质量。",
        "品牌调性": "中式雅致+潮流打卡+地道台州菜，希望客人能轻松愉快地玩起来。",
        "是否投放 CPC": "是",
        "是否售卖线上代金券/团购": "是",
        "是否主打线下转化": "否",
        "策略备注": "品牌重视大众点评，会引导客人尽量购买使用线上交易产品及优惠活动"
    },
    "椿野里": {
        "基本定位": "位于上海徐家汇，定位为中餐餐厅，客单价约120元，菜品融合传统云贵本地特色和现代创意",
        "目标人群": "25-35岁都市白领女性，重视社交体验、审美氛围与互动感。",
        "关键场景": "朋友聚会、女生小聚、同事聚餐。",
        "核心亮点": "暂无",
        "当前阶段目标": "提升消费吸引力",
        "潜在问题": "周边竞对进店目的明确，本店缺少核心竞争力，导致消费吸引力不足，无明确进店理由，并且门店过度依赖站内流量，推广通花费过大，完全无站外流量补充；用餐时长较长，且很少排队，翻台率低",
        "品牌调性": "没什么特色，性价比挺高的",
        "是否投放 CPC": "是",
        "是否售卖线上代金券/团购": "是",
        "是否主打线下转化": "否",
        "策略备注": "品牌重视大众点评，会引导客人尽量购买使用线上交易产品及优惠活动"
    },
    "进士食堂": {
        "基本定位": "位于上海闵行区，定位为韩式烤肉自助，客单价约100元，菜品主要为烤肉和正宗韩料",
        "目标人群": "20-30岁中低消费的年轻群体，重视性价比、品牌和趣味体验。",
        "关键场景": "学生聚餐、朋友小聚、同事聚餐。",
        "核心亮点": "性价比高",
        "当前阶段目标": "提升新客吸引力",
        "潜在问题": "周边竞对走低价竞争，吸走较多客流",
        "品牌调性": "全球600+的百元自助烤肉连锁",
        "是否投放 CPC": "是",
        "是否售卖线上代金券/团购": "是",
        "是否主打线下转化": "否",
        "策略备注": "品牌重视大众点评，会引导客人尽量购买使用线上交易产品及优惠活动"
    }
}

# 界面配置
GUI_CONFIG = {
    "window_title": "餐饮数据运营助手",
    "window_size": "1200x800",
    "theme": "clam",
    "colors": {
        "primary": "#2c3e50",
        "success": "#27ae60",
        "warning": "#f39c12",
        "danger": "#e74c3c",
        "info": "#3498db",
        "light": "#f0f0f0"
    },
    "fonts": {
        "title": ("Microsoft YaHei", 20, "bold"),
        "heading": ("Microsoft YaHei", 14, "bold"),
        "body": ("Microsoft YaHei", 10),
        "button": ("Microsoft YaHei", 12, "bold")
    }
}

# 下载配置
DOWNLOAD_CONFIG = {
    "default_wait_time": 3,
    "min_wait_time": 1,
    "max_wait_time": 30,
    "download_paths": {
        "cpc_data": "./downloads/cpc_hourly_data",
        "operation_data": "./downloads/operation_data",
        "review_data": "./downloads/review_data"
    }
}

# 数据清洗配置
CLEANING_CONFIG = {
    "raw_data_path": r"D:\橡皮信息科技\橡皮客户运营\大众点评运营数据\raw_data",
    "processed_data_path": r"D:\橡皮信息科技\橡皮客户运营\大众点评运营数据\processed_data",
    "supported_formats": [".xlsx", ".xls", ".csv"],
    "backup_original": True
}

# 数据库配置
DATABASE_CONFIG = {
    "connection_string": "mysql+pymysql://root:xpxx1688@localhost:3306/dianping",
    "tables": {
        "operation_data": "operation_data",
        "cpc_hourly_data": "cpc_hourly_data",
        "review_data": "review_data",
        "store_mapping": "store_mapping"
    }
}

# 报告生成配置
REPORT_CONFIG = {
    "output_directory": "./daily_report",
    "report_types": ["txt", "excel", "png"],
    "default_date_offset": 1,  # 默认昨天
    "threshold": 30,  # 暴涨/暴跌判定阈值 %
    "core_fields": ["消费金额", "打卡人数", "新增收藏人数", "新好评数", "新中差评数"]
}

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="gui_config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "brands": DEFAULT_BRANDS,
            "gui": GUI_CONFIG,
            "download": DOWNLOAD_CONFIG,
            "cleaning": CLEANING_CONFIG,
            "database": DATABASE_CONFIG,
            "report": REPORT_CONFIG
        }
    
    def save_config(self):
        """保存配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get_brands(self):
        """获取商户列表"""
        return self.config.get("brands", DEFAULT_BRANDS)
    
    def get_gui_config(self):
        """获取界面配置"""
        return self.config.get("gui", GUI_CONFIG)
    
    def get_download_config(self):
        """获取下载配置"""
        return self.config.get("download", DOWNLOAD_CONFIG)
    
    def get_cleaning_config(self):
        """获取清洗配置"""
        return self.config.get("cleaning", CLEANING_CONFIG)
    
    def get_database_config(self):
        """获取数据库配置"""
        return self.config.get("database", DATABASE_CONFIG)
    
    def get_report_config(self):
        """获取报告配置"""
        return self.config.get("report", REPORT_CONFIG)
    
    def update_brands(self, brands):
        """更新商户配置"""
        self.config["brands"] = brands
        return self.save_config()
    
    def update_gui_config(self, gui_config):
        """更新界面配置"""
        self.config["gui"] = gui_config
        return self.save_config()
    
    def add_brand(self, brand_name, brand_info):
        """添加新商户"""
        self.config["brands"][brand_name] = brand_info
        return self.save_config()
    
    def remove_brand(self, brand_name):
        """删除商户"""
        if brand_name in self.config["brands"]:
            del self.config["brands"][brand_name]
            return self.save_config()
        return False
    
    def get_brand_info(self, brand_name):
        """获取指定商户信息"""
        return self.config["brands"].get(brand_name, {})
    
    def validate_config(self):
        """验证配置完整性"""
        required_sections = ["brands", "gui", "download", "cleaning", "database", "report"]
        missing_sections = [section for section in required_sections if section not in self.config]
        
        if missing_sections:
            print(f"配置缺失以下部分: {missing_sections}")
            return False
        
        # 验证商户配置
        if not self.config["brands"]:
            print("商户配置为空")
            return False
        
        return True

# 全局配置管理器实例
config_manager = ConfigManager()

def get_config():
    """获取全局配置管理器"""
    return config_manager

def get_brands():
    """获取商户列表"""
    return config_manager.get_brands()

def get_gui_config():
    """获取界面配置"""
    return config_manager.get_gui_config()

def get_download_config():
    """获取下载配置"""
    return config_manager.get_download_config()

def get_cleaning_config():
    """获取清洗配置"""
    return config_manager.get_cleaning_config()

def get_database_config():
    """获取数据库配置"""
    return config_manager.get_database_config()

def get_report_config():
    """获取报告配置"""
    return config_manager.get_report_config()

if __name__ == "__main__":
    # 测试配置管理器
    config = get_config()
    print("商户列表:")
    for brand, info in config.get_brands().items():
        print(f"  - {brand}: {info.get('基本定位', 'N/A')}")
    
    print(f"\n配置验证结果: {config.validate_config()}")
    
    # 保存配置
    if config.save_config():
        print("配置已保存到 gui_config.json")
    else:
        print("配置保存失败")
