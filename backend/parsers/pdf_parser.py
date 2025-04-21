from typing import Dict, List, Optional
import PyPDF2
import json
from pathlib import Path
import pandas as pd
import re
import numpy as np
from grobid_client.grobid_client import GrobidClient

class PDFParser:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.metadata = {}
        self.content = []
        self.tables = []
        self.equations = []
        self.grobid_client = GrobidClient(config_path="./grobid_config.json")
        
    def parse(self) -> Dict:
        """PDF 파일을 파싱하여 구조화된 데이터를 반환합니다."""
        try:
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # 메타데이터 추출
                self.metadata = {
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'pages': len(pdf_reader.pages)
                }
                
                # 텍스트 내용 추출
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    self.content.append({
                        'page': page_num + 1,
                        'text': text
                    })
                    
                # 표 추출
                self._extract_tables()
                
                # 수식 추출
                self._extract_equations()
                
                return {
                    'metadata': self.metadata,
                    'content': self.content,
                    'tables': self.tables,
                    'equations': self.equations
                }
                
        except Exception as e:
            raise Exception(f"PDF 파싱 중 오류 발생: {str(e)}")
    
    def _extract_tables(self):
        """PDF에서 표를 추출합니다."""
        try:
            # PDF를 이미지로 변환하여 표 인식
            # TODO: 실제 표 인식 로직 구현
            # 예: pdf2image를 사용하여 PDF를 이미지로 변환 후 OpenCV로 표 인식
            
            # 임시 예시 데이터
            self.tables = [
                {
                    'page': 1,
                    'data': [
                        ['Header 1', 'Header 2', 'Header 3'],
                        ['Data 1', 'Data 2', 'Data 3'],
                        ['Data 4', 'Data 5', 'Data 6']
                    ],
                    'caption': 'Example Table'
                }
            ]
            
        except Exception as e:
            print(f"표 추출 중 오류 발생: {str(e)}")
    
    def _extract_equations(self):
        """PDF에서 수식을 추출합니다."""
        try:
            # Grobid을 사용하여 수식 추출
            result = self.grobid_client.process_pdf(
                str(self.file_path),
                "formula"
            )
            
            # 추출된 수식을 LaTeX 형식으로 변환
            for formula in result:
                self.equations.append({
                    'page': formula.get('page', 1),
                    'latex': formula.get('latex', ''),
                    'context': formula.get('context', '')
                })
                
        except Exception as e:
            print(f"수식 추출 중 오류 발생: {str(e)}")
    
    def to_markdown(self) -> str:
        """파싱된 내용을 Markdown 형식으로 변환합니다."""
        markdown = []
        
        # 메타데이터
        markdown.append(f"# {self.metadata.get('title', 'Untitled')}\n")
        markdown.append(f"*Author: {self.metadata.get('author', 'Unknown')}*\n")
        
        # 내용
        for page in self.content:
            markdown.append(f"\n## Page {page['page']}\n")
            markdown.append(page['text'])
            
        # 표
        if self.tables:
            markdown.append("\n## Tables\n")
            for table in self.tables:
                markdown.append(f"\n### {table.get('caption', 'Table')}\n")
                markdown.append(self._table_to_markdown(table['data']))
                
        # 수식
        if self.equations:
            markdown.append("\n## Equations\n")
            for equation in self.equations:
                markdown.append(f"\n### Equation on Page {equation['page']}\n")
                markdown.append(f"```latex\n{equation['latex']}\n```")
                if equation.get('context'):
                    markdown.append(f"\nContext: {equation['context']}\n")
            
        return "\n".join(markdown)
    
    def _table_to_markdown(self, table_data: List[List[str]]) -> str:
        """표 데이터를 마크다운 테이블 형식으로 변환합니다."""
        if not table_data:
            return ""
            
        markdown = []
        headers = table_data[0]
        markdown.append("| " + " | ".join(headers) + " |")
        markdown.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        for row in table_data[1:]:
            markdown.append("| " + " | ".join(row) + " |")
            
        return "\n".join(markdown)
    
    def to_jsonld(self) -> Dict:
        """파싱된 내용을 JSON-LD 형식으로 변환합니다."""
        return {
            "@context": "https://schema.org",
            "@type": "Document",
            "name": self.metadata.get('title', ''),
            "author": self.metadata.get('author', ''),
            "pageCount": self.metadata.get('pages', 0),
            "content": self.content,
            "tables": self.tables,
            "equations": self.equations
        } 