import re
import PyPDF2
from typing import List, Dict, Tuple

class ExamParser:
    def __init__(self):
        # 题目类型的正则表达式模式
        self.patterns = {
            'single_choice': r'(?:选择题|单选题)[^\n]*(?:\n|.)*?(?:\d+[\.、]|\([A-D]\))\s*(.*?)(?=(?:\d+[\.、]|\([A-D]\))|$)',
            'true_false': r'(?:判断题)[^\n]*(?:\n|.)*?(?:\d+[\.、])\s*(.*?)(?=\d+[\.、]|$)',
            'programming': r'(?:编程题|程序题)[^\n]*(?:\n|.)*?(?:\d+[\.、])\s*(.*?)(?=\d+[\.、]|$)'
        }
        
        # 选项模式
        self.option_pattern = r'[A-D][\.、](.*?)(?=[A-D][\.、]|$)'
        
    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        """解析PDF文件，返回题目列表"""
        questions = []
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                
                print("\n=== PDF解析开始 ===")
                print(f"PDF页数: {len(reader.pages)}")
                
                # 提取所有页面的文本
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    text += page_text
                    print(f"\n--- 第{i+1}页内容预览 ---")
                    print(page_text[:200] + "...")  # 只显示前200个字符
                
                print("\n=== 开始识别题目 ===")
                # 解析不同类型的题目
                single_choice = self._parse_single_choice(text)
                print(f"\n找到选择题: {len(single_choice)}道")
                for q in single_choice:
                    print(f"- 题目: {q['text'][:50]}...")
                    print(f"  选项: {q.get('options', [])}")
                
                true_false = self._parse_true_false(text)
                print(f"\n找到判断题: {len(true_false)}道")
                for q in true_false:
                    print(f"- 题目: {q['text'][:50]}...")
                
                programming = self._parse_programming(text)
                print(f"\n找到编程题: {len(programming)}道")
                for q in programming:
                    print(f"- 题目: {q['text'][:50]}...")
                
                questions.extend(single_choice)
                questions.extend(true_false)
                questions.extend(programming)
                
                print(f"\n=== 解析完成，共找到{len(questions)}道题目 ===\n")
                
        except Exception as e:
            print(f"\n解析PDF时出错: {str(e)}")
            
        return questions
    
    def _parse_single_choice(self, text: str) -> List[Dict]:
        """解析单选题"""
        questions = []
        matches = re.finditer(self.patterns['single_choice'], text, re.DOTALL)
        
        for match in matches:
            question_text = match.group(1).strip()
            # 查找选项
            options = re.findall(self.option_pattern, question_text)
            if options:
                # 分离题目和选项
                main_text = question_text.split('A.')[0].strip()
                questions.append({
                    'type': 'single_choice',
                    'text': main_text,
                    'options': options,
                    'score': 10  # 默认分值
                })
        
        return questions
    
    def _parse_true_false(self, text: str) -> List[Dict]:
        """解析判断题"""
        questions = []
        matches = re.finditer(self.patterns['true_false'], text, re.DOTALL)
        
        for match in matches:
            questions.append({
                'type': 'true_false',
                'text': match.group(1).strip(),
                'score': 5  # 默认分值
            })
        
        return questions
    
    def _parse_programming(self, text: str) -> List[Dict]:
        """解析编程题"""
        questions = []
        matches = re.finditer(self.patterns['programming'], text, re.DOTALL)
        
        for match in matches:
            questions.append({
                'type': 'programming',
                'text': match.group(1).strip(),
                'score': 20  # 默认分值
            })
        
        return questions
