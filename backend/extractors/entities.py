from typing import Dict, List, Tuple
import re
from datetime import datetime
from pathlib import Path
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import jpype
import jpype.imports
from konlpy.tag import Kkma

class EntityExtractor:
    def __init__(self, text: str):
        self.text = text
        self.entities = {
            'people': [],
            'organizations': [],
            'dates': [],
            'locations': [],
            'keywords': []
        }
        self.kkma = Kkma()
        
    def extract(self) -> Dict:
        """텍스트에서 엔티티를 추출합니다."""
        self._extract_people()
        self._extract_organizations()
        self._extract_dates()
        self._extract_locations()
        self._extract_keywords()
        
        return self.entities
    
    def _extract_people(self):
        """인물 이름을 추출합니다."""
        # 한글 이름 패턴 (성 + 이름)
        korean_name_pattern = r'[가-힣]{2,4}'
        # 영어 이름 패턴 (대문자로 시작하는 연속된 단어)
        english_name_pattern = r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*'
        
        # 한글 이름 추출
        korean_names = re.findall(korean_name_pattern, self.text)
        # 영어 이름 추출
        english_names = re.findall(english_name_pattern, self.text)
        
        # 추출된 이름 필터링
        self.entities['people'] = list(set(korean_names + english_names))
    
    def _extract_organizations(self):
        """조직명을 추출합니다."""
        # 조직 관련 키워드
        org_keywords = ['회사', '기관', '단체', '협회', '재단', '센터', '연구소', '대학', '학교', '병원']
        
        # 문장 분리
        sentences = self.text.split('.')
        
        for sentence in sentences:
            for keyword in org_keywords:
                if keyword in sentence:
                    # 키워드 주변의 텍스트 추출
                    pattern = f'[^。]*{keyword}[^。]*'
                    matches = re.findall(pattern, sentence)
                    self.entities['organizations'].extend(matches)
        
        # 중복 제거
        self.entities['organizations'] = list(set(self.entities['organizations']))
    
    def _extract_dates(self):
        """날짜를 추출합니다."""
        # 날짜 패턴
        date_patterns = [
            r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',  # 2023년 12월 31일
            r'\d{4}-\d{2}-\d{2}',  # 2023-12-31
            r'\d{4}/\d{2}/\d{2}',  # 2023/12/31
            r'\d{4}년\s*\d{1,2}월',  # 2023년 12월
            r'\d{4}년'  # 2023년
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, self.text)
            self.entities['dates'].extend(dates)
        
        # 중복 제거
        self.entities['dates'] = list(set(self.entities['dates']))
    
    def _extract_locations(self):
        """위치 정보를 추출합니다."""
        # 위치 관련 키워드
        location_keywords = ['시', '도', '구', '군', '읍', '면', '리', '동', '국', '지역']
        
        # 문장 분리
        sentences = self.text.split('.')
        
        for sentence in sentences:
            for keyword in location_keywords:
                if keyword in sentence:
                    # 키워드 주변의 텍스트 추출
                    pattern = f'[^。]*{keyword}[^。]*'
                    matches = re.findall(pattern, sentence)
                    self.entities['locations'].extend(matches)
        
        # 중복 제거
        self.entities['locations'] = list(set(self.entities['locations']))
    
    def _extract_keywords(self):
        """키워드를 추출합니다."""
        # 문장 분리
        sentences = [s.strip() for s in self.text.split('.') if s.strip()]
        
        # 형태소 분석
        words = []
        for sentence in sentences:
            pos = self.kkma.pos(sentence)
            # 명사, 동사, 형용사만 추출
            words.extend([word for word, tag in pos if tag.startswith(('N', 'V', 'A'))])
        
        # TF-IDF 계산
        vectorizer = TfidfVectorizer(max_features=10)
        try:
            tfidf_matrix = vectorizer.fit_transform([' '.join(words)])
            feature_names = vectorizer.get_feature_names_out()
            
            # 상위 10개 키워드 추출
            self.entities['keywords'] = feature_names.tolist()
        except:
            # 단어가 너무 적은 경우 빈도수 기반으로 추출
            word_counts = Counter(words)
            self.entities['keywords'] = [word for word, _ in word_counts.most_common(10)]
    
    def to_jsonld(self) -> Dict:
        """추출된 엔티티를 JSON-LD 형식으로 변환합니다."""
        return {
            "@context": "https://schema.org",
            "@type": "EntityExtraction",
            "people": [{"@type": "Person", "name": name} for name in self.entities['people']],
            "organizations": [{"@type": "Organization", "name": name} for name in self.entities['organizations']],
            "dates": [{"@type": "Date", "value": date} for date in self.entities['dates']],
            "locations": [{"@type": "Place", "name": name} for name in self.entities['locations']],
            "keywords": self.entities['keywords']
        } 