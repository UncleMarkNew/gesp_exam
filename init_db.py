import sqlite3
import os
from pathlib import Path

def init_db():
    """初始化数据库"""
    # 确保数据库关闭
    try:
        if os.path.exists('gespexam.db'):
            os.remove('gespexam.db')
    except PermissionError:
        print("警告：数据库文件正在使用中，请关闭所有相关程序后重试。")
        return
    
    # 创建新的数据库连接
    conn = sqlite3.connect('gespexam.db')
    cursor = conn.cursor()
    
    # 创建试卷表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,                    -- 试卷名称
        original_filename TEXT NOT NULL,       -- 原始文件名
        file_path TEXT NOT NULL,              -- 文件路径
        file_type TEXT NOT NULL,              -- 文件类型
        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        duration INTEGER DEFAULT 120           -- 考试时长(分钟)
    )
    ''')
    
    # 创建答案表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,             -- 关联的试卷ID
        question_number INTEGER NOT NULL,     -- 题目序号
        correct_answer TEXT NOT NULL,         -- 正确答案
        score INTEGER DEFAULT 5,              -- 分值
        FOREIGN KEY (exam_id) REFERENCES exams (id)
    )
    ''')
    
    # 创建考试记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exam_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,             -- 关联的试卷ID
        student_name TEXT NOT NULL,           -- 考生姓名
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,                   -- 结束时间
        answers TEXT,                         -- JSON格式存储答案 {question_number: answer}
        score INTEGER,                        -- 得分
        FOREIGN KEY (exam_id) REFERENCES exams (id)
    )
    ''')
    
    # 创建存储目录
    base_dir = Path('exam_data')
    if not base_dir.exists():
        base_dir.mkdir()
        
    exams_dir = base_dir / 'exams'
    if not exams_dir.exists():
        exams_dir.mkdir()
    
    conn.commit()
    conn.close()
    print("数据库初始化完成！")

if __name__ == "__main__":
    init_db()
