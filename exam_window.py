import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import io
import os

class ExamWindow:
    def __init__(self, parent, exam_id):
        self.window = tk.Toplevel(parent)
        self.window.title("考试界面")
        self.window.attributes('-fullscreen', True)
        
        self.exam_id = exam_id
        self.conn = sqlite3.connect('gespexam.db')
        self.load_exam_info()
        
        self.current_page = 0
        self.student_answers = {}
        self.start_time = datetime.now()
        self.zoom_level = 1.5  # 默认缩放级别
        
        self.create_interface()
        self.load_pdf()
        self.show_current_page()
        self.update_timer()

    def create_interface(self):
        """创建考试界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部信息栏
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"试卷：{self.exam_name}").pack(side=tk.LEFT)
        self.timer_label = ttk.Label(info_frame, text="剩余时间：")
        self.timer_label.pack(side=tk.RIGHT)
        
        # 缩放控制
        zoom_frame = ttk.Frame(main_frame)
        zoom_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(zoom_frame, text="放大", command=self.zoom_in).pack(side=tk.LEFT, padx=5)
        ttk.Button(zoom_frame, text="缩小", command=self.zoom_out).pack(side=tk.LEFT, padx=5)
        
        # 试卷显示区域（带滚动条）
        self.pdf_frame = ttk.Frame(main_frame)
        self.pdf_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建画布和滚动条
        self.pdf_canvas = tk.Canvas(self.pdf_frame, bg='white')
        h_scrollbar = ttk.Scrollbar(self.pdf_frame, orient=tk.HORIZONTAL, command=self.pdf_canvas.xview)
        v_scrollbar = ttk.Scrollbar(self.pdf_frame, orient=tk.VERTICAL, command=self.pdf_canvas.yview)
        
        # 配置画布滚动
        self.pdf_canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # 使用网格布局放置组件
        self.pdf_canvas.grid(row=0, column=0, sticky="nsew")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 配置网格权重
        self.pdf_frame.grid_rowconfigure(0, weight=1)
        self.pdf_frame.grid_columnconfigure(0, weight=1)
        
        # 答题区域
        answer_frame = ttk.Frame(main_frame)
        answer_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(answer_frame, text="题号：").pack(side=tk.LEFT)
        self.question_var = tk.StringVar()
        self.question_entry = ttk.Entry(answer_frame, width=5, textvariable=self.question_var)
        self.question_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(answer_frame, text="答案：").pack(side=tk.LEFT)
        self.answer_var = tk.StringVar()
        self.answer_entry = ttk.Entry(answer_frame, width=10, textvariable=self.answer_var)
        self.answer_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(answer_frame, text="提交答案", command=self.submit_answer).pack(side=tk.LEFT, padx=5)
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="上一题", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="下一题", command=self.next_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="结束考试", command=self.finish_exam).pack(side=tk.RIGHT, padx=5)

    def zoom_in(self):
        """放大"""
        self.zoom_level *= 1.2
        self.show_current_page()
    
    def zoom_out(self):
        """缩小"""
        self.zoom_level /= 1.2
        self.show_current_page()

    def show_current_page(self):
        """显示当前页"""
        if not hasattr(self, 'doc'):
            return
            
        # 清空画布
        self.pdf_canvas.delete("all")
        
        # 获取页面
        page = self.doc[self.current_page]
        
        # 获取页面尺寸
        canvas_width = self.pdf_canvas.winfo_width()
        canvas_height = self.pdf_canvas.winfo_height()
        
        # 将PDF页面渲染为图片
        zoom_matrix = fitz.Matrix(2 * self.zoom_level, 2 * self.zoom_level)
        pix = page.get_pixmap(matrix=zoom_matrix)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 保存图片引用
        self.photo = ImageTk.PhotoImage(img)
        
        # 在画布上显示图片
        self.pdf_canvas.create_image(0, 0, anchor="nw", image=self.photo)
        
        # 更新画布的滚动区域
        self.pdf_canvas.configure(scrollregion=self.pdf_canvas.bbox("all"))
        
        # 更新标题
        self.window.title(f"考试界面 - 第{self.current_page + 1}/{self.total_pages}题")
        
        # 自动设置当前题号
        self.question_var.set(str(self.current_page + 1))

    def load_exam_info(self):
        """加载考试信息"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, file_path, duration
            FROM exams 
            WHERE id = ?
        """, (self.exam_id,))
        
        self.exam_name, self.file_path, self.duration = cursor.fetchone()
        self.remaining_minutes = self.duration
    
    def load_pdf(self):
        """加载PDF文件"""
        try:
            self.doc = fitz.open(self.file_path)
            self.total_pages = len(self.doc)
        except Exception as e:
            messagebox.showerror("错误", f"无法加载PDF文件：{str(e)}")
            self.window.destroy()
    
    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.show_current_page()
    
    def next_page(self):
        """下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.show_current_page()
    
    def submit_answer(self):
        """提交答案"""
        question_num = self.question_var.get().strip()
        answer = self.answer_var.get().strip()
        
        if not question_num or not answer:
            messagebox.showwarning("警告", "请输入题号和答案！")
            return
        
        try:
            question_num = int(question_num)
            self.student_answers[question_num] = answer
            messagebox.showinfo("成功", "答案已记录！")
            
            # 清空输入框
            self.question_var.set("")
            self.answer_var.set("")
            
        except ValueError:
            messagebox.showwarning("警告", "题号必须是数字！")
    
    def update_timer(self):
        """更新计时器"""
        if self.remaining_minutes <= 0:
            self.finish_exam()
            return
            
        self.timer_label.config(text=f"剩余时间：{self.remaining_minutes}分钟")
        self.remaining_minutes -= 1
        self.window.after(60000, self.update_timer)  # 每分钟更新一次
    
    def finish_exam(self):
        """结束考试"""
        if not messagebox.askyesno("确认", "确定要结束考试吗？"):
            return
            
        try:
            # 获取标准答案
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT question_number, correct_answer, score
                FROM answers
                WHERE exam_id = ?
            """, (self.exam_id,))
            
            correct_answers = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
            
            # 计算得分
            total_score = 0
            for question_num, answer in self.student_answers.items():
                if question_num in correct_answers:
                    correct_answer, score = correct_answers[question_num]
                    if answer.upper() == correct_answer.upper():
                        total_score += score
            
            # 保存考试记录
            cursor.execute("""
                INSERT INTO exam_records (
                    exam_id, student_name, start_time,
                    end_time, answers, score
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.exam_id,
                "匿名考生",  # 可以添加输入考生姓名的功能
                self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                json.dumps(self.student_answers),
                total_score
            ))
            
            self.conn.commit()
            
            # 显示得分
            messagebox.showinfo("考试结束", f"您的得分是：{total_score}分")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存考试记录失败：{str(e)}")
        finally:
            self.doc.close()
            self.conn.close()
            self.window.destroy()
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'doc'):
            self.doc.close()
        if hasattr(self, 'conn'):
            self.conn.close()
