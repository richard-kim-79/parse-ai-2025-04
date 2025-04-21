from typing import Dict, List
import re
from pathlib import Path

class MarkdownGenerator:
    def __init__(self, parsed_data: Dict):
        self.parsed_data = parsed_data
        self.markdown_content = []
        
    def generate(self) -> str:
        """파싱된 데이터를 마크다운 형식으로 변환합니다."""
        self._add_metadata()
        self._add_content()
        self._add_tables()
        self._add_equations()
        
        return "\n".join(self.markdown_content)
    
    def _add_metadata(self):
        """메타데이터를 마크다운 형식으로 추가합니다."""
        metadata = self.parsed_data.get('metadata', {})
        self.markdown_content.append(f"# {metadata.get('title', 'Untitled')}\n")
        self.markdown_content.append(f"*Author: {metadata.get('author', 'Unknown')}*\n")
        self.markdown_content.append(f"*Pages: {metadata.get('pages', 0)}*\n")
        
    def _add_content(self):
        """본문 내용을 마크다운 형식으로 추가합니다."""
        content = self.parsed_data.get('content', [])
        for page in content:
            self.markdown_content.append(f"\n## Page {page['page']}\n")
            self.markdown_content.append(page['text'])
            
    def _add_tables(self):
        """표를 마크다운 형식으로 추가합니다."""
        tables = self.parsed_data.get('tables', [])
        if tables:
            self.markdown_content.append("\n## Tables\n")
            for i, table in enumerate(tables, 1):
                self.markdown_content.append(f"\n### Table {i}\n")
                # TODO: 표를 마크다운 테이블 형식으로 변환
                
    def _add_equations(self):
        """수식을 마크다운 형식으로 추가합니다."""
        equations = self.parsed_data.get('equations', [])
        if equations:
            self.markdown_content.append("\n## Equations\n")
            for i, equation in enumerate(equations, 1):
                self.markdown_content.append(f"\n### Equation {i}\n")
                self.markdown_content.append(f"```latex\n{equation}\n```")
                
    def save_to_file(self, output_path: str):
        """생성된 마크다운을 파일로 저장합니다."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.generate()) 