import fitz  # PyMuPDF
import json
from pathlib import Path
import re
import shutil
from typing import List, Dict, Tuple
import uuid

class PDFExtractor:
    def __init__(self):
        self.base_dir = Path('exam_data')
        self.images_dir = self.base_dir / 'images'
        self.temp_dir = self.base_dir / 'temp'
        
        # 确保目录存在
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 题目标记模式
        self.patterns = {
            'question_start': r'^\s*\d+[\.)、]\s+|^\s*[一二三四五六七八九十]+、\s*|[（(]\s*\d+\s*[)）]',
            'section_start': r'[一二三四五六七八九十]+、|^\d+、|[（(]\s*\d+\s*[)）]'
        }
    
    def extract_questions(self, pdf_path: str) -> List[Dict]:
        """从PDF中提取题目"""
        questions = []
        doc = fitz.open(pdf_path)
        
        try:
            current_section = None
            current_question = None
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" not in block:
                        continue
                        
                    text = self._get_block_text(block)
                    if not text.strip():
                        continue
                    
                    # 检查是否是新的题型部分
                    if self._is_section_start(text):
                        current_section = self._get_section_type(text)
                        continue
                    
                    # 检查是否是新题目
                    if self._is_question_start(text):
                        # 保存前一个题目
                        if current_question:
                            questions.append(current_question)
                        
                        # 创建新题目
                        current_question = {
                            'type': current_section or 'unknown',
                            'text': text,
                            'page_number': page_num + 1,
                            'bbox': list(block['bbox']),
                            'images': [],
                            'options': []
                        }
                        
                        # 检查题目区域是否包含图片
                        rect = fitz.Rect(block['bbox'])
                        self._extract_images(page, rect, current_question)
                    
                    # 如果是当前题目的一部分
                    elif current_question:
                        current_question['text'] += '\n' + text
                        
                        # 检查是否包含选项
                        if re.match(r'^[A-D][.、]', text):
                            current_question['options'].append(text)
            
            # 添加最后一个题目
            if current_question:
                questions.append(current_question)
            
        finally:
            doc.close()
        
        return self._process_questions(questions)
    
    def _get_block_text(self, block: Dict) -> str:
        """获取文本块的内容"""
        text = ""
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text += span.get("text", "")
        return text
    
    def _is_section_start(self, text: str) -> bool:
        """检查是否是新的题型部分"""
        return bool(re.match(self.patterns['section_start'], text.strip()))
    
    def _is_question_start(self, text: str) -> bool:
        """检查是否是新题目的开始"""
        return bool(re.match(self.patterns['question_start'], text.strip()))
    
    def _get_section_type(self, text: str) -> str:
        """根据标题确定题目类型"""
        text = text.strip().lower()
        if '选择' in text:
            return 'single_choice'
        elif '判断' in text:
            return 'true_false'
        elif '编程' in text or '程序' in text:
            return 'programming'
        return 'unknown'
    
    def _extract_images(self, page: fitz.Page, rect: fitz.Rect, question: Dict):
        """提取指定区域的图片"""
        images = page.get_images(full=True)
        
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = page.parent.extract_image(xref)
            
            if base_image:
                image_rect = page.get_image_bbox(img)
                # 如果图片与题目区域有重叠
                if rect.intersects(image_rect):
                    # 保存图片
                    image_path = self.images_dir / f"{uuid.uuid4()}.{base_image['ext']}"
                    with open(image_path, 'wb') as f:
                        f.write(base_image['image'])
                    question['images'].append(str(image_path))
    
    def _process_questions(self, questions: List[Dict]) -> List[Dict]:
        """处理提取的题目，整理格式"""
        processed = []
        for i, q in enumerate(questions, 1):
            question_data = {
                'question_number': i,
                'question_type': q['type'],
                'question_text': q['text'],
                'question_image_path': json.dumps(q['images']) if q['images'] else None,
                'options': json.dumps(q['options']) if q['options'] else None,
                'options_image_path': None,  # 暂时不处理选项图片
                'score': self._get_default_score(q['type']),
                'page_number': q['page_number'],
                'bbox': json.dumps(q['bbox'])
            }
            processed.append(question_data)
        return processed
    
    def _get_default_score(self, question_type: str) -> int:
        """获取题目类型的默认分值"""
        scores = {
            'single_choice': 10,
            'true_false': 5,
            'programming': 20,
            'unknown': 10
        }
        return scores.get(question_type, 10)

    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir()
