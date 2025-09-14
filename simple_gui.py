#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
餐饮数据管理助手 - 多功能选项卡界面
包含：数据下载、数据导入、日报生成等功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

class DataManagementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("餐饮数据管理助手")
        self.root.geometry("1000x750")
        
        # 从profiles.py读取商户列表
        self.profiles = self.load_profiles()
        self.brand_vars = {}
        
        # 断点续传相关变量
        self.download_state = {
            'is_running': False,
            'resume_from': None,
            'completed_count': 0,
            'total_count': 0,
            'failed_at': None
        }
        
        # 其他状态变量
        self.import_state = {'is_running': False}
        self.report_state = {'is_running': False}
        
        # 导入选项变量
        self.import_cpc_var = tk.BooleanVar(value=True)
        self.import_op_var = tk.BooleanVar(value=True)
        
        self.setup_ui()
        
    def load_profiles(self):
        """从scripts/profiles.py加载商户列表"""
        try:
            from scripts.profiles import PROFILE_BRAND_MAP
            # 返回品牌名列表
            return [conf.get('brand', profile) for profile, conf in PROFILE_BRAND_MAP.items()]
        except ImportError:
            # 如果无法导入，使用默认列表
            return ["流杯酒肆", "椿野里", "进士食堂"]
    
    def setup_ui(self):
        """设置选项卡界面"""
        # 主标题
        title_label = tk.Label(self.root, text="餐饮数据管理助手", 
                              font=('Microsoft YaHei', 18, 'bold'))
        title_label.pack(pady=10)
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 创建各个选项卡
        self.setup_download_tab()
        self.setup_report_tab()
        
        # 状态栏和日志（所有选项卡共享）
        self.setup_shared_components()
    
    def setup_download_tab(self):
        """设置数据下载选项卡"""
        download_frame = ttk.Frame(self.notebook)
        self.notebook.add(download_frame, text="数据下载")
        
        # 商户选择区域
        brand_frame = ttk.LabelFrame(download_frame, text="商户选择", padding=10)
        brand_frame.pack(fill='x', padx=10, pady=5)
        
        # 全选/取消全选按钮
        btn_frame = tk.Frame(brand_frame)
        btn_frame.pack(fill='x', pady=5)
        
        tk.Button(btn_frame, text="全选", command=self.select_all,
                  bg='#3498db', fg='white', relief='flat').pack(side='left', padx=5)
        tk.Button(btn_frame, text="取消全选", command=self.deselect_all,
                  bg='#e74c3c', fg='white', relief='flat').pack(side='left', padx=5)
        
        # 商户复选框
        checkbox_frame = tk.Frame(brand_frame)
        checkbox_frame.pack(fill='x', pady=5)
        
        for i, brand in enumerate(self.profiles):
            var = tk.BooleanVar(value=True)
            self.brand_vars[brand] = var
            
            row = i // 3
            col = i % 3
            
            tk.Checkbutton(checkbox_frame, text=brand, variable=var,
                          font=('Microsoft YaHei', 10)).grid(row=row, column=col, 
                                                           sticky='w', padx=10, pady=2)
        
        # 下载设置区域
        settings_frame = ttk.LabelFrame(download_frame, text="下载设置", padding=10)
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        # 日期设置
        date_subframe = tk.Frame(settings_frame)
        date_subframe.pack(fill='x', pady=5)
        
        default_date = datetime.now() - timedelta(days=1)
        
        tk.Label(date_subframe, text="开始日期:").grid(row=0, column=0, sticky='w', padx=5)
        self.start_date_var = tk.StringVar(value=default_date.strftime('%Y-%m-%d'))
        tk.Entry(date_subframe, textvariable=self.start_date_var, width=15).grid(row=0, column=1, padx=5)
        
        tk.Label(date_subframe, text="结束日期:").grid(row=0, column=2, sticky='w', padx=5)
        self.end_date_var = tk.StringVar(value=default_date.strftime('%Y-%m-%d'))
        tk.Entry(date_subframe, textvariable=self.end_date_var, width=15).grid(row=0, column=3, padx=5)
        
        # 等待时间和路径设置
        path_subframe = tk.Frame(settings_frame)
        path_subframe.pack(fill='x', pady=5)
        
        tk.Label(path_subframe, text="等待时间(秒):").grid(row=0, column=0, sticky='w', padx=5)
        self.wait_time_var = tk.StringVar(value="3")
        tk.Entry(path_subframe, textvariable=self.wait_time_var, width=10).grid(row=0, column=1, padx=5)
        
        tk.Label(path_subframe, text="数据目录:").grid(row=0, column=2, sticky='w', padx=5)
        self.download_path_var = tk.StringVar(value=r"D:\pythonproject\pythonProject\data")
        tk.Entry(path_subframe, textvariable=self.download_path_var, width=40).grid(row=0, column=3, padx=5)
        
        # 下载控制按钮
        control_frame = ttk.LabelFrame(download_frame, text="下载控制", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # 下载按钮
        self.download_btn = tk.Button(control_frame, text="开始下载", command=self.start_download,
                                     bg='#27ae60', fg='white', font=('Microsoft YaHei', 12, 'bold'),
                                     relief='flat', padx=20, pady=8)
        self.download_btn.pack(side='left', padx=5)
        
        # 断点续传按钮
        self.resume_btn = tk.Button(control_frame, text="断点续传", command=self.resume_download,
                                   bg='#f39c12', fg='white', font=('Microsoft YaHei', 12, 'bold'),
                                   relief='flat', padx=20, pady=8, state='disabled')
        self.resume_btn.pack(side='left', padx=5)
        
        # 停止按钮
        self.stop_btn = tk.Button(control_frame, text="停止下载", command=self.stop_download,
                                 bg='#e74c3c', fg='white', font=('Microsoft YaHei', 12, 'bold'),
                                 relief='flat', padx=20, pady=8, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        # 数据清洗导入按钮
        self.import_btn = tk.Button(control_frame, text="数据清洗导入", command=self.start_import,
                                   bg='#9b59b6', fg='white', font=('Microsoft YaHei', 12, 'bold'),
                                   relief='flat', padx=20, pady=8)
        self.import_btn.pack(side='left', padx=5)
        
        # 自动导入选项
        auto_frame = tk.Frame(control_frame)
        auto_frame.pack(side='left', padx=20)
        
        self.auto_import_var = tk.BooleanVar(value=True)
        tk.Checkbutton(auto_frame, text="下载完成后自动导入", variable=self.auto_import_var,
                      font=('Microsoft YaHei', 10), fg='#666').pack(side='left')
        
        # 进度显示
        progress_frame = ttk.LabelFrame(download_frame, text="下载进度", padding=10)
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        self.progress_label = tk.Label(progress_frame, text="准备就绪", font=('Microsoft YaHei', 10))
        self.progress_label.pack(side='left')
        
        # 进度条
        self.progress = ttk.Progressbar(download_frame, mode='determinate')
        self.progress.pack(fill='x', padx=10, pady=5)
        
        # 导入状态标签
        self.import_status_label = tk.Label(progress_frame, text="导入状态: 就绪", 
                                           font=('Microsoft YaHei', 10), fg='#666')
        self.import_status_label.pack(side='right', padx=10)
    

    
    def setup_report_tab(self):
        """设置日报生成选项卡"""
        report_frame = ttk.Frame(self.notebook)
        self.notebook.add(report_frame, text="日报生成")
        
        # 日报设置区域
        settings_frame = ttk.LabelFrame(report_frame, text="日报设置", padding=20)
        settings_frame.pack(fill='x', padx=10, pady=20)
        
        # 日期设置
        date_frame = tk.Frame(settings_frame)
        date_frame.pack(fill='x', pady=10)
        
        tk.Label(date_frame, text="报告日期:", font=('Microsoft YaHei', 12)).grid(row=0, column=0, sticky='w', padx=5)
        
        # 默认使用昨天的日期
        default_report_date = datetime.now() - timedelta(days=1)
        self.report_date_var = tk.StringVar(value=default_report_date.strftime('%Y-%m-%d'))
        tk.Entry(date_frame, textvariable=self.report_date_var, width=20, 
                font=('Microsoft YaHei', 11)).grid(row=0, column=1, padx=10)
        
        tk.Label(date_frame, text="(YYYY-MM-DD格式)", font=('Microsoft YaHei', 9), 
                fg='#666').grid(row=0, column=2, sticky='w', padx=5)
        
        # 输出路径设置
        output_frame = tk.Frame(settings_frame)
        output_frame.pack(fill='x', pady=10)
        
        tk.Label(output_frame, text="输出目录:", font=('Microsoft YaHei', 12)).grid(row=0, column=0, sticky='w', padx=5)
        self.report_output_var = tk.StringVar(value=r"D:\pythonproject\pythonProject\output")
        tk.Entry(output_frame, textvariable=self.report_output_var, width=50, 
                font=('Microsoft YaHei', 10)).grid(row=0, column=1, padx=10)
        
        # 日报选项
        options_frame = ttk.LabelFrame(report_frame, text="生成选项", padding=15)
        options_frame.pack(fill='x', padx=10, pady=10)
        
        self.generate_txt_var = tk.BooleanVar(value=True)
        self.generate_excel_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(options_frame, text="生成文本日报 (.txt)", variable=self.generate_txt_var,
                      font=('Microsoft YaHei', 11)).pack(anchor='w', pady=5)
        tk.Checkbutton(options_frame, text="生成Excel数据文件 (.xlsx)", variable=self.generate_excel_var,
                      font=('Microsoft YaHei', 11)).pack(anchor='w', pady=5)
        
        # 日报控制按钮
        control_frame = ttk.LabelFrame(report_frame, text="生成控制", padding=20)
        control_frame.pack(fill='x', padx=10, pady=20)
        
        self.report_btn = tk.Button(control_frame, text="生成日报", command=self.start_report,
                                   bg='#2ecc71', fg='white', font=('Microsoft YaHei', 14, 'bold'),
                                   relief='flat', padx=30, pady=12)
        self.report_btn.pack(pady=10)
        
        # 日报状态
        self.report_status_label = tk.Label(control_frame, text="就绪状态", 
                                           font=('Microsoft YaHei', 11), fg='#666')
        self.report_status_label.pack(pady=5)
    
    def setup_shared_components(self):
        """设置共享组件（日志和状态栏）"""
        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="运行日志", padding=10)
        log_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_text.pack(fill='both', expand=True)
        
        # 状态栏
        self.status_label = tk.Label(self.root, text="状态: 就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def select_all(self):
        """全选"""
        for var in self.brand_vars.values():
            var.set(True)
        self.log_message("✅ 已全选所有商户")
    
    def deselect_all(self):
        """取消全选"""
        for var in self.brand_vars.values():
            var.set(False)
        self.log_message("✅ 已取消全选")
    
    def get_selected_brands(self):
        """获取选中的商户"""
        return [brand for brand, var in self.brand_vars.items() if var.get()]
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, current, total, message=""):
        """更新进度条和标签"""
        if total > 0:
            percentage = (current / total) * 100
            self.progress['value'] = percentage
            self.progress_label.config(text=f"{message} {current}/{total} ({percentage:.1f}%)")
        else:
            self.progress['value'] = 0
            self.progress_label.config(text=message)
        self.root.update_idletasks()
    
    def update_status(self, status):
        """更新状态栏"""
        self.status_label.config(text=f"状态: {status}")
        self.root.update_idletasks()
    
    def enable_controls(self, enable=True):
        """启用/禁用控制按钮"""
        state = 'normal' if enable else 'disabled'
        self.download_btn.config(state=state)
        self.resume_btn.config(state=state)
        self.stop_btn.config(state='disabled' if enable else 'normal')
    
    def start_download(self):
        """开始下载"""
        if self.download_state['is_running']:
            return
            
        selected_brands = self.get_selected_brands()
        if not selected_brands:
            messagebox.showwarning("警告", "请至少选择一个商户")
            return
        
        # 验证日期
        try:
            start_date = datetime.strptime(self.start_date_var.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.end_date_var.get(), '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式不正确，请使用YYYY-MM-DD格式")
            return
        
        # 验证等待时间
        try:
            wait_time = int(self.wait_time_var.get())
        except ValueError:
            messagebox.showerror("错误", "等待时间必须是数字")
            return
        
        # 验证路径
        download_path = self.download_path_var.get().strip()
        if not download_path:
            messagebox.showerror("错误", "请设置下载路径")
            return
        
        # 重置状态
        self.download_state['resume_from'] = None
        self.download_state['completed_count'] = 0
        self.download_state['total_count'] = len(selected_brands)
        self.download_state['is_running'] = True
        
        # 更新UI状态
        self.enable_controls(False)
        self.update_progress(0, len(selected_brands), "开始下载...")
        self.update_status("下载中...")
        
        # 在新线程中执行下载
        thread = threading.Thread(target=self.download_worker, 
                                args=(selected_brands, start_date, end_date, wait_time, download_path))
        thread.daemon = True
        thread.start()
    
    def resume_download(self):
        """断点续传"""
        if self.download_state['is_running'] or not self.download_state['resume_from']:
            return
            
        selected_brands = self.get_selected_brands()
        if not selected_brands:
            messagebox.showwarning("警告", "请至少选择一个商户")
            return
        
        # 验证其他参数
        try:
            start_date = datetime.strptime(self.start_date_var.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.end_date_var.get(), '%Y-%m-%d')
            wait_time = int(self.wait_time_var.get())
            download_path = self.download_path_var.get().strip()
        except (ValueError, AttributeError):
            messagebox.showerror("错误", "请检查参数设置")
            return
        
        if not download_path:
            messagebox.showerror("错误", "请设置下载路径")
            return
        
        # 设置断点续传状态
        self.download_state['is_running'] = True
        self.download_state['total_count'] = len(selected_brands)
        
        # 更新UI状态
        self.enable_controls(False)
        self.update_progress(self.download_state['completed_count'], len(selected_brands), "断点续传...")
        self.update_status("断点续传中...")
        
        # 在新线程中执行断点续传
        thread = threading.Thread(target=self.download_worker, 
                                args=(selected_brands, start_date, end_date, wait_time, download_path, True))
        thread.daemon = True
        thread.start()
    
    def stop_download(self):
        """停止下载"""
        self.download_state['is_running'] = False
        self.update_status("已停止")
        self.log_message("⚠️ 用户停止下载")
        self.enable_controls(True)
    
    def start_import(self):
        """开始数据清洗导入"""
        if self.download_state['is_running'] or self.import_state['is_running']:
            messagebox.showwarning("警告", "请等待其他任务完成后再进行数据导入")
            return
            
        # 验证导入路径（使用下载路径）
        import_path = self.download_path_var.get().strip()
        if not import_path:
            messagebox.showerror("错误", "请先设置下载路径")
            return
        
        # 检查是否有下载的数据
        cpc_dir = Path(import_path) / "cpc_hourly_data"
        op_dir = Path(import_path) / "operation_data"
        
        import_cpc = self.import_cpc_var.get()
        import_op = self.import_op_var.get()
        
        if not import_cpc and not import_op:
            messagebox.showwarning("警告", "请至少选择一种数据类型进行导入")
            return
        
        if import_cpc and not cpc_dir.exists():
            messagebox.showwarning("警告", "未找到CPC数据目录，请先下载数据")
            return
            
        if import_op and not op_dir.exists():
            messagebox.showwarning("警告", "未找到运营数据目录，请先下载数据")
            return
        
        # 确认操作
        import_types = []
        if import_cpc: import_types.append("CPC数据")
        if import_op: import_types.append("运营数据")
        
        result = messagebox.askyesno("确认", f"确定要开始导入以下数据吗？\n{', '.join(import_types)}\n\n这将处理已下载的数据并导入到数据库。")
        if not result:
            return
        
        # 更新UI状态
        self.import_state['is_running'] = True
        self.update_status("数据清洗导入中...")
        self.import_btn.config(state='disabled')
        self.import_status_label.config(text="导入中...", fg='#e67e22')
        
        # 在新线程中执行导入
        thread = threading.Thread(target=self.import_worker, args=(import_path, import_cpc, import_op))
        thread.daemon = True
        thread.start()
    
    def import_worker(self, import_path, import_cpc, import_op):
        """数据清洗导入工作线程"""
        try:
            self.log_message("🔄 开始数据清洗和导入...")
            self.log_message(f"数据路径: {import_path}")
            
            # 调用现有的数据清洗导入代码
            try:
                from app.pipelines import import_cpc_folder, import_operation_folder
                self.log_message("✅ 成功导入数据清洗模块")
                
                # 导入CPC数据
                if import_cpc:
                    cpc_dir = Path(import_path) / "cpc_hourly_data"
                    if cpc_dir.exists():
                        self.log_message("🔄 开始导入CPC数据...")
                        import_cpc_folder(cpc_dir)
                        self.log_message("✅ CPC数据导入完成")
                    else:
                        self.log_message("⚠️ 未找到CPC数据目录")
                
                # 导入运营数据
                if import_op:
                    op_dir = Path(import_path) / "operation_data"
                    if op_dir.exists():
                        self.log_message("🔄 开始导入运营数据...")
                        import_operation_folder(op_dir)
                        self.log_message("✅ 运营数据导入完成")
                    else:
                        self.log_message("⚠️ 未找到运营数据目录")
                
                self.log_message("🎉 所有数据清洗导入完成！")
                
            except ImportError as e:
                self.log_message(f"❌ 无法导入数据清洗模块: {e}")
                self.log_message("💡 请确保app/pipelines.py文件存在")
                
            except Exception as e:
                self.log_message(f"❌ 数据清洗导入过程中出现错误: {str(e)}")
                import traceback
                self.log_message(f"详细错误信息: {traceback.format_exc()}")
            
        except Exception as e:
            self.log_message(f"❌ 数据清洗导入过程中出现错误: {str(e)}")
        finally:
            # 恢复UI状态
            self.root.after(0, self.import_completed)
    
    def import_completed(self):
        """数据清洗导入完成"""
        self.import_state['is_running'] = False
        self.update_status("数据清洗导入完成")
        self.import_btn.config(state='normal')
        self.import_status_label.config(text="导入完成", fg='#27ae60')
        self.log_message("🎉 数据清洗导入任务完成！")
    
    def start_report(self):
        """开始生成日报"""
        if self.download_state['is_running'] or self.import_state['is_running'] or self.report_state['is_running']:
            messagebox.showwarning("警告", "请等待其他任务完成后再生成日报")
            return
            
        # 验证日期
        try:
            report_date = datetime.strptime(self.report_date_var.get(), '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式不正确，请使用YYYY-MM-DD格式")
            return
        
        # 验证输出路径
        output_path = self.report_output_var.get().strip()
        if not output_path:
            messagebox.showerror("错误", "请设置输出目录")
            return
        
        # 检查生成选项
        if not self.generate_txt_var.get() and not self.generate_excel_var.get():
            messagebox.showwarning("警告", "请至少选择一种报告格式")
            return
        
        # 确认操作
        report_types = []
        if self.generate_txt_var.get(): report_types.append("文本日报")
        if self.generate_excel_var.get(): report_types.append("Excel数据文件")
        
        result = messagebox.askyesno("确认", f"确定要生成 {report_date.strftime('%Y-%m-%d')} 的日报吗？\n\n将生成：{', '.join(report_types)}")
        if not result:
            return
        
        # 更新UI状态
        self.report_state['is_running'] = True
        self.update_status("生成日报中...")
        self.report_btn.config(state='disabled')
        self.report_status_label.config(text="生成中...", fg='#e67e22')
        
        # 在新线程中执行日报生成
        thread = threading.Thread(target=self.report_worker, 
                                args=(report_date, output_path, self.generate_txt_var.get(), self.generate_excel_var.get()))
        thread.daemon = True
        thread.start()
    
    def report_worker(self, report_date, output_path, generate_txt, generate_excel):
        """日报生成工作线程"""
        try:
            self.log_message("📊 开始生成日报...")
            self.log_message(f"报告日期: {report_date.strftime('%Y-%m-%d')}")
            self.log_message(f"输出目录: {output_path}")
            
            # 确保输出目录存在
            os.makedirs(output_path, exist_ok=True)
            
            # 调用现有的日报生成代码
            try:
                from scripts.generate_daily_report import generate_daily_report
                self.log_message("✅ 成功导入日报生成模块")
                
                # 生成日报
                self.log_message("🔄 开始执行日报生成...")
                generate_daily_report(report_date, output_path)
                self.log_message("✅ 日报生成完成")
                
                # 显示生成的文件
                try:
                    output_dir = Path(output_path)
                    date_str = report_date.strftime('%Y-%m-%d')
                    
                    # 查找生成的文件
                    txt_files = list(output_dir.glob(f"*{date_str}.txt"))
                    excel_files = list(output_dir.glob(f"*{date_str}_月度数据.xlsx"))
                    
                    if txt_files or excel_files:
                        self.log_message("📋 生成的文件：")
                        for f in txt_files:
                            self.log_message(f"  📄 {f.name}")
                        for f in excel_files:
                            self.log_message(f"  📊 {f.name}")
                    
                except Exception as e:
                    self.log_message(f"⚠️ 无法列出生成的文件: {e}")
                
                self.log_message("🎉 日报生成完成！")
                
            except ImportError as e:
                self.log_message(f"❌ 无法导入日报生成模块: {e}")
                self.log_message("💡 请确保scripts/generate_daily_report.py文件存在")
                
            except Exception as e:
                self.log_message(f"❌ 日报生成过程中出现错误: {str(e)}")
                import traceback
                self.log_message(f"详细错误信息: {traceback.format_exc()}")
            
        except Exception as e:
            self.log_message(f"❌ 日报生成过程中出现错误: {str(e)}")
        finally:
            # 恢复UI状态
            self.root.after(0, self.report_completed)
    
    def report_completed(self):
        """日报生成完成"""
        self.report_state['is_running'] = False
        self.update_status("日报生成完成")
        self.report_btn.config(state='normal')
        self.report_status_label.config(text="生成完成", fg='#27ae60')
        self.log_message("🎉 日报生成任务完成！")
    
    def download_worker(self, brands, start_date, end_date, wait_time, download_path, is_resume=False):
        """下载工作线程"""
        try:
            if is_resume:
                self.log_message(f"🔄 断点续传：从 {self.download_state['resume_from']} 开始")
            else:
                self.log_message(f"🚀 开始下载数据")
            
            self.log_message(f"商户: {', '.join(brands)}")
            self.log_message(f"日期: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
            self.log_message(f"等待时间: {wait_time}秒")
            self.log_message(f"下载路径: {download_path}")
            
            # 确保目录存在
            os.makedirs(download_path, exist_ok=True)
            
            # 调用新的GUI下载函数
            try:
                from scripts.download_data import download_dianping_data_gui
                self.log_message("✅ 成功导入下载模块")
                
                # 设置日志重定向到GUI
                import logging
                from utils.logger import get_logger
                
                # 创建自定义的日志处理器，将日志输出到GUI
                class GUILogHandler(logging.Handler):
                    def __init__(self, gui):
                        super().__init__()
                        self.gui = gui
                    
                    def emit(self, record):
                        msg = self.format(record)
                        # 使用after方法确保在主线程中更新GUI
                        self.gui.root.after(0, lambda: self.gui.log_message(msg))
                
                # 获取logger并添加GUI处理器
                logger = get_logger("download_data")
                gui_handler = GUILogHandler(self)
                gui_handler.setFormatter(logging.Formatter('%(message)s'))
                logger.addHandler(gui_handler)
                
                # 创建进度回调函数
                def progress_callback(current, total, message):
                    self.root.after(0, lambda: self.update_progress(current, total, message))
                
                # 调用下载函数
                download_path_obj = Path(download_path)
                self.log_message("🔄 开始执行下载...")
                
                result = download_dianping_data_gui(
                    download_root=download_path_obj,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    selected_brands=brands,
                    wait_time=wait_time,
                    resume_from=self.download_state['resume_from'] if is_resume else None,
                    progress_callback=progress_callback
                )
                
                # 处理下载结果
                if result['status'] == 'success':
                    self.log_message("🎉 所有数据下载完成！")
                    self.download_completed()
                else:
                    # 下载失败，设置断点续传
                    self.download_state['resume_from'] = result['resume_from']
                    self.download_state['completed_count'] = result['completed_count']
                    self.download_state['failed_at'] = result['failed_at']
                    
                    self.log_message(f"❌ 下载失败于: {result['failed_at']}")
                    self.log_message(f"✅ 已完成: {result['completed_count']}/{result['total_count']}")
                    self.log_message("💡 可以点击'断点续传'按钮继续下载")
                    
                    # 更新UI状态
                    self.root.after(0, self.download_failed, result)
                
            except ImportError as e:
                self.log_message(f"❌ 无法导入下载模块: {e}")
                self.log_message("💡 请确保scripts/download_data.py文件存在")
                
                # 模拟下载过程
                for brand in brands:
                    if not self.download_state['is_running']:
                        break
                    self.log_message(f"🔄 模拟下载 {brand} 的数据...")
                    time.sleep(wait_time)
                    self.log_message(f"✅ {brand} 模拟下载完成")
                
            except Exception as e:
                self.log_message(f"❌ 下载过程中出现错误: {str(e)}")
                import traceback
                self.log_message(f"详细错误信息: {traceback.format_exc()}")
            
        except Exception as e:
            self.log_message(f"❌ 下载过程中出现错误: {str(e)}")
        finally:
            # 恢复UI状态
            if self.download_state['is_running']:
                self.root.after(0, self.download_completed)
    
    def download_completed(self):
        """下载完成"""
        self.download_state['is_running'] = False
        self.progress.stop()
        self.update_progress(self.download_state['total_count'], self.download_state['total_count'], "下载完成")
        self.update_status("下载完成")
        self.enable_controls(True)
        self.log_message("🎉 下载任务完成！")
    
    def download_failed(self, result):
        """下载失败处理"""
        self.download_state['is_running'] = False
        self.progress.stop()
        self.update_progress(result['completed_count'], result['total_count'], f"下载失败于 {result['failed_at']}")
        self.update_status("下载失败，可断点续传")
        self.enable_controls(True)
        
        # 启用断点续传按钮
        self.resume_btn.config(state='normal')

def main():
    root = tk.Tk()
    app = DataManagementGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
