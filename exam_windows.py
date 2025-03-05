import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json

class ExamWindow:
    def __init__(self, parent, exam_id):
        self.window = tk.Toplevel(parent)
        self.window.title("考试界面")
        self.window.geometry("800x600")
        self.window.transient(parent)  # 设置为父窗口的临时窗口
        
        self.exam_id = exam_id
        self.current_question = 0
        self.answers = {}
        self.questions = []
        
        # 从数据库加载试卷信息
        self.conn = sqlite3.connect('gespexam.db')
        self.load_exam_info()
        
        # 创建界面
        self.create_widgets()
        
    def load_exam_info(self):
        """加载试卷信息和题目"""
        cursor = self.conn.cursor()
        
        # 获取试卷信息
        cursor.execute("SELECT name FROM exams WHERE id = ?", (self.exam_id,))
        self.exam_name = cursor.fetchone()[0]
        
        # 获取所有题目
        cursor.execute("""
            SELECT id, question_type, question_text, options, correct_answer, question_number, score
            FROM questions
            WHERE exam_id = ?
            ORDER BY question_number
        """, (self.exam_id,))
        self.questions = cursor.fetchall()
        
    def create_widgets(self):
        """创建界面组件"""
        # 试卷标题
        ttk.Label(self.window, text=self.exam_name, font=('Arial', 16, 'bold')).pack(pady=10)
        
        # 题目区域
        self.question_frame = ttk.Frame(self.window)
        self.question_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 答题区域
        self.answer_frame = ttk.Frame(self.window)
        self.answer_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 导航按钮
        nav_frame = ttk.Frame(self.window)
        nav_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(nav_frame, text="上一题", command=self.prev_question).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="下一题", command=self.next_question).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="提交试卷", command=self.submit_exam).pack(side=tk.RIGHT, padx=5)
        
        # 显示第一题
        self.show_current_question()
        
    def show_current_question(self):
        """显示当前题目"""
        # 清空当前显示
        for widget in self.question_frame.winfo_children():
            widget.destroy()
        for widget in self.answer_frame.winfo_children():
            widget.destroy()
            
        if not self.questions:
            ttk.Label(self.question_frame, text="没有题目").pack()
            return
            
        question = self.questions[self.current_question]
        q_id, q_type, q_text, options, correct, q_num, score = question
        
        # 显示题号和分值
        ttk.Label(self.question_frame, text=f"第{q_num}题 ({score}分)").pack(anchor=tk.W)
        ttk.Label(self.question_frame, text=q_text, wraplength=700).pack(anchor=tk.W, pady=10)
        
        # 根据题目类型显示不同的答题区域
        if q_type == 'single_choice':
            self.show_choice_question(q_id, options)
        elif q_type == 'true_false':
            self.show_true_false_question(q_id)
        elif q_type == 'programming':
            self.show_programming_question(q_id)
            
    def show_choice_question(self, q_id, options):
        """显示选择题"""
        options = json.loads(options)
        var = tk.StringVar(value=self.answers.get(q_id, ''))
        
        for i, option in enumerate(options):
            ttk.Radiobutton(
                self.answer_frame,
                text=option,
                value=option,
                variable=var,
                command=lambda: self.save_answer(q_id, var.get())
            ).pack(anchor=tk.W, pady=2)
            
    def show_true_false_question(self, q_id):
        """显示判断题"""
        var = tk.StringVar(value=self.answers.get(q_id, ''))
        
        ttk.Radiobutton(
            self.answer_frame,
            text="正确",
            value="true",
            variable=var,
            command=lambda: self.save_answer(q_id, var.get())
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            self.answer_frame,
            text="错误",
            value="false",
            variable=var,
            command=lambda: self.save_answer(q_id, var.get())
        ).pack(anchor=tk.W, pady=2)
        
    def show_programming_question(self, q_id):
        """显示编程题"""
        text = tk.Text(self.answer_frame, height=10, width=60)
        text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        if q_id in self.answers:
            text.insert('1.0', self.answers[q_id])
            
        def save_text(_):
            self.save_answer(q_id, text.get('1.0', tk.END).strip())
            
        text.bind('<KeyRelease>', save_text)
        
    def save_answer(self, q_id, answer):
        """保存答案"""
        self.answers[q_id] = answer
        
    def next_question(self):
        """下一题"""
        if self.current_question < len(self.questions) - 1:
            self.current_question += 1
            self.show_current_question()
            
    def prev_question(self):
        """上一题"""
        if self.current_question > 0:
            self.current_question -= 1
            self.show_current_question()
            
    def submit_exam(self):
        """提交试卷"""
        if not messagebox.askyesno("确认", "确定要提交试卷吗？"):
            return
            
        # 计算得分
        total_score = 0
        for question in self.questions:
            q_id, q_type, _, _, correct, _, score = question
            if q_id in self.answers:
                answer = self.answers[q_id]
                if q_type in ('single_choice', 'true_false'):
                    if str(answer).lower() == str(correct).lower():
                        total_score += score
                # 编程题需要人工评分，这里暂不计分
        
        # 保存考试结果
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO exam_results (exam_id, student_name, end_time, total_score, answers)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
        """, (
            self.exam_id,
            "匿名学生",  # 这里可以添加输入学生姓名的功能
            total_score,
            json.dumps(self.answers)
        ))
        self.conn.commit()
        
        # 显示得分
        messagebox.showinfo("考试完成", f"您的得分是：{total_score}分")
        self.window.destroy()
        
    def __del__(self):
        """关闭数据库连接"""
        self.conn.close()

class AddQuestionsWindow:
    def __init__(self, parent, exam_id, main_gui):
        self.window = tk.Toplevel(parent)
        self.window.title("添加题目")
        self.window.geometry("600x400")
        self.window.transient(parent)  # 设置为父窗口的临时窗口
        
        self.exam_id = exam_id
        self.main_gui = main_gui
        self.conn = sqlite3.connect('gespexam.db')
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        # 题目类型选择
        type_frame = ttk.Frame(self.window)
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(type_frame, text="题目类型：").pack(side=tk.LEFT)
        self.question_type = tk.StringVar(value="single_choice")
        ttk.Radiobutton(type_frame, text="单选题", value="single_choice", variable=self.question_type).pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="判断题", value="true_false", variable=self.question_type).pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="编程题", value="programming", variable=self.question_type).pack(side=tk.LEFT)
        
        # 题目内容
        content_frame = ttk.Frame(self.window)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(content_frame, text="题目内容：").pack(anchor=tk.W)
        self.question_text = tk.Text(content_frame, height=5)
        self.question_text.pack(fill=tk.X)
        
        # 选项区域（单选题使用）
        self.options_frame = ttk.LabelFrame(self.window, text="选项")
        self.options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.options = []
        for i in range(4):
            option = ttk.Entry(self.options_frame)
            option.pack(fill=tk.X, padx=5, pady=2)
            self.options.append(option)
        
        # 答案
        answer_frame = ttk.Frame(self.window)
        answer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(answer_frame, text="正确答案：").pack(side=tk.LEFT)
        self.answer_entry = ttk.Entry(answer_frame)
        self.answer_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 分数
        score_frame = ttk.Frame(self.window)
        score_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(score_frame, text="分值：").pack(side=tk.LEFT)
        self.score_var = tk.StringVar(value="10")
        ttk.Entry(score_frame, textvariable=self.score_var, width=10).pack(side=tk.LEFT)
        
        # 保存按钮
        ttk.Button(self.window, text="保存题目", command=self.save_question).pack(pady=10)
        
        # 绑定题目类型变化事件
        self.question_type.trace('w', self.on_type_change)
        
    def on_type_change(self, *args):
        """当题目类型改变时更新界面"""
        q_type = self.question_type.get()
        
        # 显示/隐藏选项区域
        if q_type == 'single_choice':
            self.options_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.options_frame.pack_forget()
            
        # 更新答案提示
        if q_type == 'true_false':
            self.answer_entry.delete(0, tk.END)
            self.answer_entry.insert(0, 'true')
        elif q_type == 'programming':
            self.answer_entry.delete(0, tk.END)
            self.answer_entry.insert(0, '示例答案')
        
    def save_question(self):
        """保存题目"""
        try:
            # 获取题目信息
            q_type = self.question_type.get()
            q_text = self.question_text.get('1.0', tk.END).strip()
            answer = self.answer_entry.get().strip()
            score = int(self.score_var.get())
            
            if not q_text:
                raise ValueError("题目内容不能为空")
                
            if not answer:
                raise ValueError("答案不能为空")
                
            # 获取选项（如果是单选题）
            options = None
            if q_type == 'single_choice':
                options = [opt.get().strip() for opt in self.options]
                if not all(options):
                    raise ValueError("单选题的选项不能为空")
                if answer not in options:
                    raise ValueError("正确答案必须是选项之一")
            
            # 获取当前题号
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM questions WHERE exam_id = ?", (self.exam_id,))
            question_number = cursor.fetchone()[0] + 1
            
            # 保存题目
            cursor.execute("""
                INSERT INTO questions (
                    exam_id, question_type, question_text,
                    options, correct_answer, question_number, score
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                self.exam_id,
                q_type,
                q_text,
                json.dumps(options) if options else None,
                answer,
                question_number,
                score
            ))
            
            self.conn.commit()
            
            # 更新主界面
            self.main_gui.load_exams()
            
            messagebox.showinfo("成功", "题目添加成功！")
            
            # 清空输入
            self.question_text.delete('1.0', tk.END)
            self.answer_entry.delete(0, tk.END)
            for opt in self.options:
                opt.delete(0, tk.END)
                
        except ValueError as e:
            messagebox.showerror("错误", str(e))
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
            
    def __del__(self):
        """关闭数据库连接"""
        self.conn.close()
