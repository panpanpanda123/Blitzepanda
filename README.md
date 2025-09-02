项目说明（精简版下载流程）

一、环境准备
- 安装依赖：`pip install -r requirements.txt`
- 安装浏览器驱动：`python -m playwright install chrome`

二、配置
- 编辑 `scripts/settings.yaml`：
  - `chrome_user_data`: 本机 Chrome 用户数据目录
  - `clone_dir`: 克隆目录，程序会把需要的 Profile 复制到这里以免扫码
- 在 `scripts/profiles.py` 维护 Profile → 品牌/是否下载 CPC、运营 的映射

三、运行
```bash
python scripts/download_data.py
```
按提示选择日期与品牌后自动下载：
- 运营数据落盘：`data/operation_data`
- CPC 数据落盘：`data/cpc_hourly_data`

四、代码结构（新）
- `scripts/download_common.py`：启动/关闭浏览器、克隆 Profile、日期工具
- `scripts/download_operation.py`：运营数据下载（bizguide 报表页定位）
- `scripts/download_cpc.py`：CPC 下载（推广通嵌套 iframe 定位）
- `scripts/profiles.py`：Profile 与品牌映射
- `scripts/download_data.py`：新入口，仅引用上述新模块

五、legacy 说明
- 旧实现位于 `AI_auto_review_3_2025may/`，建议视为只读备份；新入口不再引用。


