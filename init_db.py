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
        name TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    
    # 创建必要的目录
    Path('exams').mkdir(exist_ok=True)
    
    print("数据库初始化完成！")

if __name__ == "__main__":
    init_db()
