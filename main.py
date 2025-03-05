import sqlite3
import json
from pathlib import Path
import shutil

class GespexamManager:
    def __init__(self):
        self.conn = sqlite3.connect('gespexam.db')
        self.cursor = self.conn.cursor()
        
        # 确保PDF存储目录存在
        self.pdf_dir = Path("pdfs")
        self.pdf_dir.mkdir(exist_ok=True)
        
        # 确保其他目录存在
        self.exams_dir = Path("exams")
        self.exams_dir.mkdir(exist_ok=True)
        
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def add_exam(self, name, file_path):
        """添加新试卷"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        # 复制PDF文件到存储目录
        pdf_path = self.pdf_dir / file_path.name
        shutil.copy2(file_path, pdf_path)
        
        self.cursor.execute("""
            INSERT INTO exams (name, file_path, pdf_path, status)
            VALUES (?, ?, ?, ?)
        """, (name, str(file_path), str(pdf_path), 'pending'))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_question(self, exam_id, question_type, question_text, options=None, correct_answer=None, question_number=None):
        """添加题目到试卷"""
        if question_number is None:
            # 获取当前试卷的题目数量
            self.cursor.execute("SELECT COUNT(*) FROM questions WHERE exam_id = ?", (exam_id,))
            question_number = self.cursor.fetchone()[0] + 1
        
        self.cursor.execute("""
            INSERT INTO questions (
                exam_id, question_type, question_text,
                options, correct_answer, question_number
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            exam_id,
            question_type,
            question_text,
            json.dumps(options) if options else None,
            correct_answer,
            question_number
        ))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_exam(self, exam_id):
        """获取试卷信息"""
        self.cursor.execute("""
            SELECT id, name, file_path, pdf_path, status,
                   total_questions, single_choice_count,
                   true_false_count, programming_count
            FROM exams
            WHERE id = ?
        """, (exam_id,))
        return self.cursor.fetchone()
    
    def get_questions(self, exam_id):
        """获取试卷的所有题目"""
        self.cursor.execute("""
            SELECT id, question_type, question_text,
                   options, correct_answer, question_number
            FROM questions
            WHERE exam_id = ?
            ORDER BY question_number
        """, (exam_id,))
        return self.cursor.fetchall()
    
    def complete_exam(self, exam_id):
        """完成试卷编辑"""
        # 获取题目统计
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN question_type = 'single_choice' THEN 1 ELSE 0 END) as single_choice,
                SUM(CASE WHEN question_type = 'true_false' THEN 1 ELSE 0 END) as true_false,
                SUM(CASE WHEN question_type = 'programming' THEN 1 ELSE 0 END) as programming
            FROM questions 
            WHERE exam_id = ?
        """, (exam_id,))
        
        counts = self.cursor.fetchone()
        
        # 更新试卷状态和题目数量
        self.cursor.execute('''
            UPDATE exams SET 
                status = 'completed',
                total_questions = ?,
                single_choice_count = ?,
                true_false_count = ?,
                programming_count = ?
            WHERE id = ?
        ''', (counts[0], counts[1], counts[2], counts[3], exam_id))
        
        self.conn.commit()
    
    def export_exam(self, exam_id, output_file):
        """导出试卷为JSON格式"""
        # 获取试卷信息
        exam = self.get_exam(exam_id)
        if not exam:
            raise ValueError("试卷不存在")
        
        # 获取所有题目
        questions = self.get_questions(exam_id)
        
        # 构建导出数据
        exam_data = {
            'name': exam[1],
            'questions': []
        }
        
        for q in questions:
            question = {
                'type': q[1],
                'text': q[2],
                'correct_answer': q[4]
            }
            if q[3]:  # 如果有选项
                question['options'] = json.loads(q[3])
            exam_data['questions'].append(question)
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(exam_data, f, ensure_ascii=False, indent=2)
    
    def __del__(self):
        """关闭数据库连接"""
        self.conn.close()

# 测试代码
if __name__ == "__main__":
    # 初始化管理器
    manager = GespexamManager()
    
    # 创建示例PDF文件
    example_pdf = Path("exams/2025_spring_python.pdf")
    if not example_pdf.exists():
        # 创建一个空的PDF文件作为示例
        example_pdf.write_bytes(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
    
    # 添加试卷
    exam_id = manager.add_exam("2025年春季Python考试", str(example_pdf))
    
    # 添加题目
    # 单选题示例
    manager.add_question(
        exam_id,
        "single_choice",
        "以下哪个不是Python的基本数据类型？",
        ["int", "float", "string", "array"],
        "array"
    )
    
    # 判断题示例
    manager.add_question(
        exam_id,
        "true_false",
        "Python是一门编译型语言。",
        correct_answer="false"
    )
    
    # 编程题示例
    manager.add_question(
        exam_id,
        "programming",
        "请编写一个函数，计算斐波那契数列的第n项。",
        correct_answer="def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
    )
    
    # 完成试卷
    manager.complete_exam(exam_id)
    
    # 导出试卷
    manager.export_exam(exam_id, "output/2025_spring_python.json")
