"""
app 包：承载精简后的通用能力，供脚本与后续扩展直接复用。

模块划分：
- app.db      ：数据库连接与通用导入
- app.excel   ：Excel 读取与标题清理
- app.cleaning：数据清洗与字段标准化
- app.mappings：列名映射与常量
- app.pipelines：按目录的导入流水线（运营/CPC）
"""


