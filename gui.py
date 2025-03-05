import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import sqlite3
import os
from pathlib import Path
import shutil
import json
from datetime import datetime
from exam_window import ExamWindow

class GespexamGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("试卷管理系统")
        
        # 设置窗口大小
        self.root.geometry("800x600")
        
        # 初始化数据库连接
        self.conn = sqlite3.connect('gespexam.db')
        self.create_tables()
        
        # 创建主界面
        self.create_main_interface()
    
    def create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration INTEGER DEFAULT 120
            )
        ''')
        self.conn.commit()
    
    def create_main_interface(self):
        """创建主界面"""
        # 创建工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="上传试卷", command=self.upload_exam).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="预览试卷", command=self.preview_exam).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="开始考试", command=self.start_exam).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="修改名称", command=self.rename_exam).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="删除试卷", command=self.delete_exam).pack(side=tk.LEFT, padx=5)
        
        # 创建试卷列表
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建表格
        columns = ('id', 'name', 'upload_time', 'duration')
        self.exam_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.exam_tree.heading('id', text='ID')
        self.exam_tree.heading('name', text='试卷名称')
        self.exam_tree.heading('upload_time', text='上传时间')
        self.exam_tree.heading('duration', text='考试时长(分钟)')
        
        # 设置列宽
        self.exam_tree.column('id', width=50)
        self.exam_tree.column('name', width=300)
        self.exam_tree.column('upload_time', width=150)
        self.exam_tree.column('duration', width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.exam_tree.yview)
        self.exam_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.exam_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载试卷列表
        self.load_exams()
    
    def load_exams(self):
        """加载试卷列表"""
        # 清空当前列表
        for item in self.exam_tree.get_children():
            self.exam_tree.delete(item)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, upload_time, duration
            FROM exams 
            ORDER BY upload_time DESC
        """)
        
        for row in cursor.fetchall():
            self.exam_tree.insert('', 'end', values=row)
    
    def upload_exam(self):
        """上传试卷"""
        file_types = [
            ('PDF文件', '*.pdf'),
            ('所有文件', '*.*')
        ]
        
        file_path = filedialog.askopenfilename(
            title="选择试卷文件",
            filetypes=file_types
        )
        
        if not file_path:
            return
            
        try:
            # 获取文件信息
            file_path = Path(file_path)
            original_filename = file_path.name
            file_type = file_path.suffix.lower()
            
            # 复制文件到存储目录
            exam_dir = Path('exam_data/exams')
            exam_dir.mkdir(parents=True, exist_ok=True)
            new_path = exam_dir / original_filename
            shutil.copy2(file_path, new_path)
            
            # 保存到数据库
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO exams (name, original_filename, file_path, file_type)
                VALUES (?, ?, ?, ?)
            ''', (
                original_filename,
                original_filename,
                str(new_path),
                file_type
            ))
            
            self.conn.commit()
            self.load_exams()
            messagebox.showinfo("成功", "试卷上传成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"上传失败: {str(e)}")
    
    def preview_exam(self):
        """预览试卷"""
        selection = self.exam_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个试卷！")
            return
            
        exam_id = self.exam_tree.item(selection[0])['values'][0]
        
        # 获取试卷文件路径
        cursor = self.conn.cursor()
        cursor.execute("SELECT file_path FROM exams WHERE id = ?", (exam_id,))
        file_path = cursor.fetchone()[0]
        
        # 使用系统默认程序打开PDF
        try:
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {str(e)}")
    
    def start_exam(self):
        """开始考试"""
        selection = self.exam_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个试卷！")
            return
            
        exam_id = self.exam_tree.item(selection[0])['values'][0]
        
        # 创建考试窗口
        exam_window = ExamWindow(self.root, exam_id)
    
    def rename_exam(self):
        """修改试卷名称"""
        selection = self.exam_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个试卷！")
            return
            
        exam_id = self.exam_tree.item(selection[0])['values'][0]
        current_name = self.exam_tree.item(selection[0])['values'][1]
        
        # 创建输入对话框
        new_name = simpledialog.askstring(
            "修改名称",
            "请输入新的试卷名称：",
            initialvalue=current_name
        )
        
        if new_name:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE exams 
                SET name = ?
                WHERE id = ?
            """, (new_name, exam_id))
            
            self.conn.commit()
            self.load_exams()
    
    def delete_exam(self):
        """删除试卷"""
        selection = self.exam_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个试卷！")
            return
            
        if not messagebox.askyesno("确认", "确定要删除选中的试卷吗？"):
            return
            
        exam_id = self.exam_tree.item(selection[0])['values'][0]
        
        try:
            cursor = self.conn.cursor()
            
            # 获取文件路径
            cursor.execute("SELECT file_path FROM exams WHERE id = ?", (exam_id,))
            file_path = cursor.fetchone()[0]
            
            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 删除数据库记录
            cursor.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
            cursor.execute("DELETE FROM answers WHERE exam_id = ?", (exam_id,))
            cursor.execute("DELETE FROM exam_records WHERE exam_id = ?", (exam_id,))
            
            self.conn.commit()
            self.load_exams()
            messagebox.showinfo("成功", "试卷删除成功！")
            
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")
    
    def __del__(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = GespexamGUI(root)
    root.mainloop()
