from typing import Dict, List, Optional
import openai
from pathlib import Path
import json

class GPTSummarizer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        openai.api_key = api_key
        
    def summarize(self, text: str, max_length: int = 500) -> str:
        """텍스트를 요약합니다."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
                    {"role": "user", "content": f"Please summarize the following text in {max_length} characters or less:\n\n{text}"}
                ],
                max_tokens=max_length,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"요약 생성 중 오류 발생: {str(e)}")
    
    def generate_key_points(self, text: str, num_points: int = 5) -> List[str]:
        """텍스트의 주요 포인트를 추출합니다."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts key points from documents."},
                    {"role": "user", "content": f"Please extract {num_points} key points from the following text:\n\n{text}"}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            points = response.choices[0].message.content.strip().split('\n')
            return [point.strip('- ') for point in points if point.strip()]
            
        except Exception as e:
            raise Exception(f"주요 포인트 추출 중 오류 발생: {str(e)}")
    
    def save_summary(self, summary: str, output_path: str):
        """요약을 파일로 저장합니다."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)
    
    def save_key_points(self, key_points: List[str], output_path: str):
        """주요 포인트를 JSON 파일로 저장합니다."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"key_points": key_points}, f, ensure_ascii=False, indent=2) 