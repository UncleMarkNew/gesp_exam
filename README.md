# 考试系统 v2.0

一个简单而功能完整的考试系统，支持PDF试卷上传、预览、考试和自动评分。

## 主要功能

### 试卷管理
- 上传PDF格式试卷
- 预览试卷内容
- 修改试卷名称
- 删除试卷

### 考试功能
- 全屏考试界面
- 单题显示模式
- 可调节试题缩放
- 双向滚动支持
- 实时计时
- 自动题号填充
- 答案提交
- 自动评分

## 系统要求

- Python 3.6+
- 依赖包：
  - tkinter (Python标准库)
  - sqlite3 (Python标准库)
  - PyMuPDF
  - Pillow

## 安装

1. 克隆或下载项目代码
2. 安装依赖：
```bash
pip install PyMuPDF Pillow
```
3. 初始化数据库：
```bash
python init_db.py
```

## 使用说明

1. 启动程序：
```bash
python gui.py
```

2. 上传试卷：
   - 点击"上传试卷"按钮
   - 选择PDF格式的试卷文件
   - 输入试卷名称

3. 开始考试：
   - 在试卷列表中选择要考试的试卷
   - 点击"开始考试"按钮
   - 在考试界面中：
     - 使用"放大"/"缩小"按钮调整试题大小
     - 使用滚动条查看完整题目
     - 输入答案并点击"提交答案"
     - 使用"上一题"/"下一题"按钮切换题目
     - 点击"结束考试"完成考试

## 文件说明

- `gui.py`: 主界面程序
- `exam_window.py`: 考试窗口程序
- `init_db.py`: 数据库初始化程序
- `gespexam.db`: SQLite数据库文件

## 数据库结构

### exams表
- id: 试卷ID
- name: 试卷名称
- file_path: PDF文件路径
- duration: 考试时长（分钟）

### answers表
- id: 答案ID
- exam_id: 对应的试卷ID
- question_number: 题号
- correct_answer: 正确答案
- score: 分值

### exam_records表
- id: 记录ID
- exam_id: 试卷ID
- student_name: 考生姓名
- start_time: 开始时间
- end_time: 结束时间
- answers: 考生答案（JSON格式）
- score: 得分

## 版本历史

### v2.0 (2025-03-06)
- 新增单题显示模式
- 添加试题缩放功能
- 优化界面布局
- 改进滚动支持
- 自动题号填充

### v1.0
- 基础试卷管理
- PDF试卷支持
- 考试功能
- 自动评分
