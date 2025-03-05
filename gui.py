import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import os
from pathlib import Path
import shutil
import subprocess
import mimetypes

class GespexamGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("试卷管理系统")
        self.root.geometry("1200x800")
        
        # 创建试卷存储目录
        self.exams_dir = Path("exams")
        self.exams_dir.mkdir(exist_ok=True)
        
        # 初始化数据库连接
        self.conn = sqlite3.connect('gespexam.db')
        self.create_tables()
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
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def create_main_interface(self):
        """创建主界面"""
        # 左侧试卷列表
        left_frame = ttk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)
        
        # 试卷列表标题
        ttk.Label(left_frame, text="试卷列表").pack(pady=5)
        
        # 试卷列表
        columns = ('id', 'name', 'type', 'time')
        self.exam_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=20)
        self.exam_tree.heading('id', text='ID')
        self.exam_tree.heading('name', text='试卷名称')
        self.exam_tree.heading('type', text='文件类型')
        self.exam_tree.heading('time', text='上传时间')
        
        # 设置列宽
        self.exam_tree.column('id', width=50)
        self.exam_tree.column('name', width=200)
        self.exam_tree.column('type', width=80)
        self.exam_tree.column('time', width=150)
        
        self.exam_tree.pack(fill=tk.BOTH, expand=True)
        
        # 按钮区域
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="上传试卷", command=self.upload_exam).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="下载试卷", command=self.download_exam).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="预览试卷", command=self.preview_exam).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="删除试卷", command=self.delete_exam).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="重命名", command=self.rename_exam).pack(side=tk.LEFT, padx=2)
        
        # 加载试卷列表
        self.load_exams()
    
    def upload_exam(self):
        """上传试卷"""
        file_types = [
            ('所有支持的文件', '*.pdf;*.doc;*.docx'),
            ('PDF文件', '*.pdf'),
            ('Word文件', '*.doc;*.docx'),
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
            new_path = self.exams_dir / original_filename
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
    
    def download_exam(self):
        """下载试卷"""
        selection = self.exam_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个试卷！")
            return
        
        try:
            # 获取试卷信息
            exam_id = self.exam_tree.item(selection[0])['values'][0]
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT original_filename, file_path 
                FROM exams 
                WHERE id = ?
            """, (exam_id,))
            
            original_filename, file_path = cursor.fetchone()
            
            # 选择保存位置
            save_path = filedialog.asksaveasfilename(
                title="保存试卷",
                initialfile=original_filename,
                defaultextension=Path(original_filename).suffix
            )
            
            if save_path:
                shutil.copy2(file_path, save_path)
                messagebox.showinfo("成功", "试卷下载成功！")
                
        except Exception as e:
            messagebox.showerror("错误", f"下载失败: {str(e)}")
    
    def preview_exam(self):
        """预览试卷"""
        selection = self.exam_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个试卷！")
            return
        
        try:
            # 获取试卷路径
            exam_id = self.exam_tree.item(selection[0])['values'][0]
            cursor = self.conn.cursor()
            cursor.execute("SELECT file_path FROM exams WHERE id = ?", (exam_id,))
            file_path = cursor.fetchone()[0]
            
            # 使用系统默认程序打开文件
            os.startfile(file_path)
            
        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {str(e)}")
    
    def delete_exam(self):
        """删除试卷"""
        selection = self.exam_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个试卷！")
            return
            
        if not messagebox.askyesno("确认", "确定要删除选中的试卷吗？"):
            return
            
        try:
            exam_id = self.exam_tree.item(selection[0])['values'][0]
            
            # 获取文件路径
            cursor = self.conn.cursor()
            cursor.execute("SELECT file_path FROM exams WHERE id = ?", (exam_id,))
            file_path = cursor.fetchone()[0]
            
            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 从数据库中删除记录
            cursor.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
            self.conn.commit()
            
            # 刷新列表
            self.load_exams()
            messagebox.showinfo("成功", "试卷已删除！")
            
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {str(e)}")
    
    def rename_exam(self):
        """重命名试卷"""
        selection = self.exam_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个试卷！")
            return
            
        exam_id = self.exam_tree.item(selection[0])['values'][0]
        
        # 获取当前名称
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM exams WHERE id = ?", (exam_id,))
        current_name = cursor.fetchone()[0]
        
        # 创建重命名对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("重命名试卷")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="新名称:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.insert(0, current_name)
        name_entry.pack(pady=5)
        
        def do_rename():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("警告", "名称不能为空！")
                return
                
            try:
                cursor.execute("UPDATE exams SET name = ? WHERE id = ?", (new_name, exam_id))
                self.conn.commit()
                self.load_exams()
                dialog.destroy()
                messagebox.showinfo("成功", "重命名成功！")
            except Exception as e:
                messagebox.showerror("错误", f"重命名失败: {str(e)}")
        
        ttk.Button(dialog, text="确定", command=do_rename).pack(side=tk.LEFT, padx=50)
        ttk.Button(dialog, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
    
    def load_exams(self):
        """加载试卷列表"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, file_type, upload_time
            FROM exams 
            ORDER BY upload_time DESC
        """)
        
        # 清空现有列表
        for item in self.exam_tree.get_children():
            self.exam_tree.delete(item)
        
        # 添加试卷到列表
        for exam in cursor.fetchall():
            self.exam_tree.insert('', 'end', values=exam)
    
    def __del__(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = GespexamGUI(root)
    root.mainloop()
