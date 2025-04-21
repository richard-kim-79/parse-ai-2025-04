from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
import shutil
from pathlib import Path
from pdfminer.high_level import extract_text
import json
from datetime import datetime, date
from konlpy.tag import Okt
from collections import Counter
import re
import markdown
import latex2mathml
import pandas as pd
import csv
from transformers import pipeline
import spacy
import zipfile
import io
from pydantic import BaseModel
import logging
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
import uuid
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="AI-Parseable 문서 플랫폼")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3009")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 정적 파일 디렉토리 설정
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# 업로드 디렉토리 설정
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 파싱 결과 저장 디렉토리
PARSED_DIR = Path("parsed")
PARSED_DIR.mkdir(exist_ok=True)

# 변환 결과 저장 디렉토리
CONVERTED_DIR = Path("converted")
CONVERTED_DIR.mkdir(exist_ok=True)

# JSON 저장 디렉토리
JSON_STORE = Path("json_store")
JSON_STORE.mkdir(exist_ok=True)

# Hugging Face 요약 모델 로드
# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
summarizer = None  # 임시로 None으로 설정

# spaCy 한국어 모델 로드
# nlp = spacy.load("ko_core_news_sm")
nlp = None  # 임시로 None으로 설정

# SPARQL 관련 설정
RDF_STORE = "rdf_store"
os.makedirs(RDF_STORE, exist_ok=True)

# SPARQL 쿼리 로그 디렉토리 설정
SPARQL_LOG_DIR = Path("sparql_logs")
SPARQL_LOG_DIR.mkdir(exist_ok=True)

security = HTTPBasic()

def get_admin_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, os.getenv("ADMIN_USERNAME", "admin"))
    correct_password = secrets.compare_digest(credentials.password, os.getenv("ADMIN_PASSWORD", "admin123"))
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="관리자 인증이 필요합니다.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def log_sparql_query(query: str, results: dict, execution_time: float):
    """SPARQL 쿼리와 실행 결과를 로그에 저장합니다."""
    try:
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "query": query,
            "results_count": len(results["results"]["bindings"]),
            "execution_time_ms": execution_time * 1000,
            "results": results
        }
        
        # 로그 파일 이름 생성 (연/월/일 기준)
        log_date = datetime.now().strftime("%Y-%m-%d")
        log_file = SPARQL_LOG_DIR / f"sparql_log_{log_date}.json"
        
        # 기존 로그 읽기
        existing_logs = []
        if log_file.exists():
            with log_file.open("r", encoding="utf-8") as f:
                existing_logs = json.load(f)
        
        # 새 로그 추가
        existing_logs.append(log_entry)
        
        # 로그 저장
        with log_file.open("w", encoding="utf-8") as f:
            json.dump(existing_logs, f, ensure_ascii=False, indent=2)
            
        logging.info(f"SPARQL 쿼리 로그가 저장되었습니다: {log_file}")
    except Exception as e:
        logging.error(f"SPARQL 쿼리 로그 저장 중 오류 발생: {str(e)}")

@app.get("/")
async def root():
    return {"message": "AI-Parseable 문서 플랫폼 API 서버"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """PDF 파일을 업로드합니다."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": file.filename}

@app.get("/files/")
async def list_files():
    """업로드된 파일 목록을 반환합니다."""
    files = []
    for file in UPLOAD_DIR.glob("*.pdf"):
        parsed_file = PARSED_DIR / f"{file.name}.json"
        files.append({
            "filename": file.name,
            "size": file.stat().st_size,
            "uploaded_at": file.stat().st_mtime,
            "is_parsed": parsed_file.exists()
        })
    return files

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """파일을 삭제합니다."""
    file_path = UPLOAD_DIR / filename
    parsed_path = PARSED_DIR / f"{filename}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    try:
        # 원본 파일 삭제
        file_path.unlink()
        
        # 파싱된 파일이 있으면 삭제
        if parsed_path.exists():
            parsed_path.unlink()
        
        return {"message": "파일이 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def parse_pdf(file_path: Path) -> dict:
    """PDF 파일을 파싱하여 텍스트와 메타데이터를 추출합니다."""
    try:
        # 텍스트 추출
        text = extract_text(str(file_path))
        
        return {
            "content": text,
            "metadata": {
                "title": "제목 없음",
                "author": "작성자 불명",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 파싱 중 오류 발생: {str(e)}")

@app.post("/parse/{filename}")
async def parse_file(filename: str):
    """PDF 파일을 파싱하고 결과를 저장합니다."""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    try:
        # PDF 파싱
        parsed_data = parse_pdf(file_path)
        
        # 결과 저장
        output_path = PARSED_DIR / f"{filename}.json"
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "message": "파싱이 완료되었습니다.",
            "data": parsed_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/convert/{filename}")
async def convert_file(
    filename: str,
    format: str = Query(..., description="변환할 형식 (markdown, latex, csv, jsonld)")
):
    """파일을 지정된 형식으로 변환합니다."""
    parsed_path = PARSED_DIR / f"{filename}.json"
    if not parsed_path.exists():
        raise HTTPException(status_code=404, detail="파싱된 파일을 찾을 수 없습니다.")
    
    try:
        with parsed_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 변환 결과 저장 디렉토리 생성
        format_dir = CONVERTED_DIR / format
        format_dir.mkdir(exist_ok=True)
        
        if format == "markdown":
            # Markdown 변환
            md_content = f"# {data['metadata']['title']}\n\n"
            md_content += f"**작성자**: {data['metadata']['author']}\n\n"
            md_content += f"**작성일**: {data['metadata']['date']}\n\n"
            md_content += data['content']
            
            output_path = format_dir / f"{filename}.md"
            with output_path.open("w", encoding="utf-8") as f:
                f.write(md_content)
                
        elif format == "latex":
            # LaTeX 변환
            latex_content = f"\\documentclass{{article}}\n\\title{{{data['metadata']['title']}}}\n\\author{{{data['metadata']['author']}}}\n\\date{{{data['metadata']['date']}}}\n\\begin{{document}}\n\\maketitle\n\n"
            latex_content += data['content'].replace('\n', '\n\n')
            latex_content += "\n\\end{document}"
            
            output_path = format_dir / f"{filename}.tex"
            with output_path.open("w", encoding="utf-8") as f:
                f.write(latex_content)
                
        elif format == "csv":
            # CSV 변환 (표 형식 데이터 추출)
            # 간단한 예시: 각 문단을 행으로 변환
            paragraphs = [p.strip() for p in data['content'].split('\n\n') if p.strip()]
            df = pd.DataFrame({
                'paragraph': paragraphs,
                'length': [len(p) for p in paragraphs]
            })
            
            output_path = format_dir / f"{filename}.csv"
            df.to_csv(output_path, index=False, encoding='utf-8')
            
        elif format == "jsonld":
            # JSON-LD 변환
            jsonld = {
                "@context": "https://schema.org",
                "@type": "Document",
                "name": data['metadata']['title'],
                "author": {
                    "@type": "Person",
                    "name": data['metadata']['author']
                },
                "dateCreated": data['metadata']['date'],
                "text": data['content']
            }
            
            output_path = format_dir / f"{filename}.jsonld"
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(jsonld, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "message": f"파일이 {format} 형식으로 변환되었습니다.",
            "path": str(output_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str, format: str):
    """변환된 파일을 다운로드합니다."""
    format_dir = CONVERTED_DIR / format
    file_path = format_dir / f"{filename}.{format}"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="변환된 파일을 찾을 수 없습니다.")
    
    return {
        "filename": f"{filename}.{format}",
        "content": file_path.read_text(encoding="utf-8")
    }

@app.get("/documents/{filename}")
async def get_document(filename: str):
    """파싱된 문서 데이터를 반환합니다."""
    file_path = PARSED_DIR / f"{filename}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파싱된 문서를 찾을 수 없습니다.")
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/")
async def search_documents(query: str):
    """문서를 검색합니다."""
    results = []
    for file in PARSED_DIR.glob("*.json"):
        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if query.lower() in data["content"].lower() or \
                   query.lower() in data["metadata"]["title"].lower() or \
                   query.lower() in data["metadata"]["author"].lower():
                    results.append({
                        "filename": file.stem,
                        "title": data["metadata"]["title"],
                        "author": data["metadata"]["author"],
                        "date": data["metadata"]["date"],
                        "snippet": data["content"][:200] + "..."
                    })
        except Exception:
            continue
    return results

@app.get("/advanced-search/")
async def advanced_search(
    query: str = "",
    author: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    tags: Optional[List[str]] = Query(None)
):
    """고급 검색 기능을 제공합니다."""
    results = []
    
    for file in PARSED_DIR.glob("*.json"):
        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                
                # 기본 검색어 매칭
                content_match = not query or query.lower() in data["content"].lower()
                
                # 작성자 필터링
                author_match = not author or (
                    data["metadata"]["author"] and 
                    author.lower() in data["metadata"]["author"].lower()
                )
                
                # 날짜 범위 필터링
                doc_date = datetime.strptime(data["metadata"]["date"], "%Y-%m-%d").date()
                date_match = (
                    (not start_date or doc_date >= start_date) and
                    (not end_date or doc_date <= end_date)
                )
                
                # 태그 필터링 (태그 기능은 나중에 구현)
                tags_match = not tags or any(
                    tag in data.get("tags", []) for tag in tags
                )
                
                if content_match and author_match and date_match and tags_match:
                    results.append({
                        "filename": file.stem,
                        "title": data["metadata"]["title"],
                        "author": data["metadata"]["author"],
                        "date": data["metadata"]["date"],
                        "snippet": data["content"][:200] + "...",
                        "tags": data.get("tags", [])
                    })
        except Exception:
            continue
            
    return results

@app.put("/files/{filename}/metadata")
async def update_file_metadata(
    filename: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    """파일의 메타데이터를 업데이트합니다."""
    file_path = PARSED_DIR / f"{filename}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        if title:
            data["metadata"]["title"] = title
        if author:
            data["metadata"]["author"] = author
        if tags is not None:
            data["tags"] = tags
            
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return {"message": "메타데이터가 업데이트되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/files/{filename}/rename")
async def rename_file(filename: str, new_filename: str):
    """파일 이름을 변경합니다."""
    if not new_filename.endswith('.pdf'):
        new_filename += '.pdf'
        
    old_file = UPLOAD_DIR / filename
    new_file = UPLOAD_DIR / new_filename
    old_json = PARSED_DIR / f"{filename}.json"
    new_json = PARSED_DIR / f"{new_filename}.json"
    
    if not old_file.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    if new_file.exists():
        raise HTTPException(status_code=400, detail="이미 존재하는 파일 이름입니다.")
    
    try:
        # 원본 파일 이름 변경
        old_file.rename(new_file)
        
        # 파싱된 JSON 파일이 있다면 이름 변경
        if old_json.exists():
            old_json.rename(new_json)
            
        return {"message": "파일 이름이 변경되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}/versions")
async def get_file_versions(filename: str):
    """파일의 버전 기록을 반환합니다."""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    # 버전 디렉토리 생성
    versions_dir = UPLOAD_DIR / "versions" / filename.replace('.pdf', '')
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    # 버전 목록 반환
    versions = []
    for version in versions_dir.glob("*.pdf"):
        versions.append({
            "version": version.stem.split('_v')[-1],
            "created_at": version.stat().st_mtime,
            "size": version.stat().st_size
        })
    
    return sorted(versions, key=lambda x: x["version"], reverse=True)

@app.post("/files/{filename}/version")
async def create_version(filename: str, version_note: str = ""):
    """파일의 새 버전을 생성합니다."""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    # 버전 디렉토리 생성
    versions_dir = UPLOAD_DIR / "versions" / filename.replace('.pdf', '')
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    # 새 버전 번호 생성
    existing_versions = [int(v.stem.split('_v')[-1]) for v in versions_dir.glob("*.pdf")]
    new_version = max(existing_versions, default=0) + 1
    
    # 새 버전 파일 생성
    version_file = versions_dir / f"{filename.replace('.pdf', '')}_v{new_version}.pdf"
    shutil.copy2(file_path, version_file)
    
    # 버전 메타데이터 저장
    metadata_file = version_file.with_suffix('.json')
    with metadata_file.open('w', encoding='utf-8') as f:
        json.dump({
            "version": new_version,
            "created_at": datetime.now().isoformat(),
            "note": version_note
        }, f, ensure_ascii=False, indent=2)
    
    return {
        "message": "새 버전이 생성되었습니다.",
        "version": new_version
    }

@app.get("/tags/")
async def get_all_tags():
    """모든 태그 목록을 반환합니다."""
    tags = set()
    for file in PARSED_DIR.glob("*.json"):
        try:
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if "tags" in data:
                    tags.update(data["tags"])
        except Exception:
            continue
    
    return sorted(list(tags))

def extract_keywords(text: str, top_n: int = 10) -> List[dict]:
    """텍스트에서 주요 키워드를 추출합니다."""
    okt = Okt()
    
    # 명사 추출
    nouns = okt.nouns(text)
    
    # 2글자 이상의 명사만 선택
    nouns = [noun for noun in nouns if len(noun) > 1]
    
    # 빈도수 계산
    counter = Counter(nouns)
    
    # 상위 N개 키워드 반환
    keywords = [
        {"word": word, "count": count}
        for word, count in counter.most_common(top_n)
    ]
    
    return keywords

def summarize_text(text: str, sentences: int = 3) -> str:
    """텍스트를 요약합니다."""
    # Okt 초기화
    okt = Okt()
    
    # 문장 분리
    sentence_list = re.split('[.!?]', text)
    sentence_list = [s.strip() for s in sentence_list if s.strip()]
    
    # 각 문장의 중요도 계산 (단순히 키워드 포함 개수로 계산)
    keywords = extract_keywords(text, top_n=20)
    keyword_set = {kw["word"] for kw in keywords}
    
    sentence_scores = []
    for sentence in sentence_list:
        score = sum(1 for word in okt.nouns(sentence) if word in keyword_set)
        sentence_scores.append((sentence, score))
    
    # 점수가 높은 순으로 정렬하여 상위 N개 문장 선택
    sorted_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
    summary_sentences = [s[0] for s in sorted_sentences[:sentences]]
    
    # 원래 순서대로 재정렬
    original_order = []
    for sentence in sentence_list:
        if sentence in summary_sentences:
            original_order.append(sentence)
    
    return '. '.join(original_order) + '.'

@app.get("/files/{filename}/analysis")
async def analyze_document(filename: str):
    """문서를 분석하여 요약과 키워드를 추출합니다."""
    file_path = PARSED_DIR / f"{filename}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파싱된 문서를 찾을 수 없습니다.")
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        text = data["content"]
        
        # 분석 수행
        keywords = extract_keywords(text)
        summary = summarize_text(text)
        
        return {
            "keywords": keywords,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}/summary")
async def get_summary(filename: str):
    """문서의 요약본을 생성합니다."""
    try:
        file_path = PARSED_DIR / f"{filename}.json"
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="파싱된 문서를 찾을 수 없습니다.")
        
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            
        # 텍스트 요약
        if summarizer is None:
            # 기본 요약 기능 사용
            summary = summarize_text(data["content"])
        else:
            summary = summarizer(data["content"], max_length=130, min_length=30, do_sample=False)
            summary = summary[0]["summary_text"]
        
        return {
            "summary": summary
        }
    except Exception as e:
        print(f"Summary error: {str(e)}")  # 에러 로깅
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}/entities")
async def extract_entities(filename: str):
    """문서에서 개체를 추출합니다."""
    try:
        print(f"Processing entities for file: {filename}")  # 파일명 로깅
        file_path = PARSED_DIR / f"{filename}.json"
        if not file_path.exists():
            print(f"File not found: {file_path}")  # 파일 존재 여부 로깅
            raise HTTPException(status_code=404, detail="파싱된 문서를 찾을 수 없습니다.")
        
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"Successfully loaded JSON data for: {filename}")  # JSON 로드 성공 로깅
            
        # 개체 추출
        if nlp is None:
            print("Using default entity extraction")  # 기본 추출 사용 로깅
            # 기본 개체 추출 기능 사용
            entities = {
                "organizations": [],
                "dates": [],
                "locations": [],
                "persons": [],
                "keywords": extract_keywords(data["content"])
            }
        else:
            print("Using spaCy for entity extraction")  # spaCy 사용 로깅
            # spaCy로 개체 추출
            doc = nlp(data["content"])
            
            entities = {
                "organizations": [],
                "dates": [],
                "locations": [],
                "persons": [],
                "keywords": extract_keywords(data["content"])
            }
            
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    entities["organizations"].append(ent.text)
                elif ent.label_ == "DATE":
                    entities["dates"].append(ent.text)
                elif ent.label_ == "GPE" or ent.label_ == "LOC":
                    entities["locations"].append(ent.text)
                elif ent.label_ == "PERSON":
                    entities["persons"].append(ent.text)
        
        print(f"Successfully extracted entities for: {filename}")  # 추출 성공 로깅
        return entities
    except Exception as e:
        print(f"Entities error for {filename}: {str(e)}")  # 에러 로깅
        print(f"Error type: {type(e)}")  # 에러 타입 로깅
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/files/{filename}/convert-all")
async def convert_all_formats(filename: str):
    """파일을 모든 형식으로 변환합니다."""
    try:
        print(f"Converting file: {filename}")  # 파일명 로깅
        formats = ["markdown", "latex", "csv", "jsonld"]
        converted_files = []
        
        for format in formats:
            try:
                print(f"Converting to {format}")  # 변환 형식 로깅
                # 각 형식으로 변환
                response = await convert_file(filename, format)
                converted_files.append({
                    "format": format,
                    "path": response["path"]
                })
            except Exception as e:
                print(f"Error converting to {format}: {str(e)}")  # 변환 에러 로깅
                continue
        
        # ZIP 파일 생성
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file_info in converted_files:
                file_path = Path(file_info["path"])
                if file_path.exists():
                    zip_file.write(file_path, f"{filename}.{file_info['format']}")
        
        print(f"Successfully converted {filename}")  # 변환 성공 로깅
        return {
            "filename": f"{filename}_converted.zip",
            "content": zip_buffer.getvalue()
        }
    except Exception as e:
        print(f"Convert-all error for {filename}: {str(e)}")  # 에러 로깅
        print(f"Error type: {type(e)}")  # 에러 타입 로깅
        raise HTTPException(status_code=500, detail=str(e))

# SPARQL 엔드포인트 수정
@app.post("/sparql")
async def sparql_query(query: str):
    try:
        start_time = datetime.now()
        
        # RDF 그래프 생성
        g = Graph()
        
        # JSON-LD 파일들을 RDF로 변환
        for filename in os.listdir(JSON_STORE):
            if filename.endswith('.json'):
                file_path = os.path.join(JSON_STORE, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    # JSON-LD를 RDF로 변환
                    g.parse(data=json.dumps(json_data), format='json-ld')
        
        # SPARQL 쿼리 실행
        results = g.query(query)
        
        # 결과를 JSON 형식으로 변환
        bindings = []
        for row in results:
            binding = {}
            for var in results.vars:
                value = row[var]
                if value:
                    binding[str(var)] = str(value)
            bindings.append(binding)
        
        response = {
            "head": {"vars": [str(var) for var in results.vars]},
            "results": {"bindings": bindings}
        }
        
        # 실행 시간 계산 및 로그 저장
        execution_time = (datetime.now() - start_time).total_seconds()
        log_sparql_query(query, response, execution_time)
        
        return response
    except Exception as e:
        error_msg = f"SPARQL 쿼리 실행 중 오류 발생: {str(e)}"
        logging.error(error_msg)
        # 에러도 로그에 저장
        log_sparql_query(query, {"error": error_msg}, 0)
        raise HTTPException(status_code=500, detail=error_msg)

# 쿼리 로그 조회 엔드포인트 추가
@app.get("/sparql/logs")
async def get_sparql_logs(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    username: str = Depends(get_admin_credentials)
):
    """SPARQL 쿼리 로그를 조회합니다."""
    try:
        all_logs = []
        
        # 모든 로그 파일 읽기
        for log_file in SPARQL_LOG_DIR.glob("sparql_log_*.json"):
            with log_file.open("r", encoding="utf-8") as f:
                logs = json.load(f)
                all_logs.extend(logs)
        
        # 날짜 필터링
        if start_date or end_date:
            filtered_logs = []
            for log in all_logs:
                log_date = datetime.fromisoformat(log["timestamp"]).date()
                if start_date and log_date < start_date:
                    continue
                if end_date and log_date > end_date:
                    continue
                filtered_logs.append(log)
            all_logs = filtered_logs
        
        # 최신 순으로 정렬
        all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "total": len(all_logs),
            "logs": all_logs[:limit]
        }
    except Exception as e:
        logging.error(f"쿼리 로그 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sparql/logs/stats")
async def get_sparql_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    username: str = Depends(get_admin_credentials)
):
    """SPARQL 쿼리 통계를 반환합니다."""
    try:
        all_logs = []
        
        # 모든 로그 파일 읽기
        for log_file in SPARQL_LOG_DIR.glob("sparql_log_*.json"):
            with log_file.open("r", encoding="utf-8") as f:
                logs = json.load(f)
                all_logs.extend(logs)
        
        # 날짜 필터링
        if start_date or end_date:
            filtered_logs = []
            for log in all_logs:
                log_date = datetime.fromisoformat(log["timestamp"]).date()
                if start_date and log_date < start_date:
                    continue
                if end_date and log_date > end_date:
                    continue
                filtered_logs.append(log)
            all_logs = filtered_logs
        
        # 통계 계산
        total_queries = len(all_logs)
        total_execution_time = sum(log["execution_time_ms"] for log in all_logs)
        avg_execution_time = total_execution_time / total_queries if total_queries > 0 else 0
        
        # PREFIX 사용 통계
        prefix_stats = {}
        pattern_stats = {}
        
        for log in all_logs:
            query = log["query"]
            
            # PREFIX 추출 및 통계
            prefix_matches = re.findall(r'PREFIX\s+(\w+):\s*<([^>]+)>', query)
            for prefix, uri in prefix_matches:
                if prefix not in prefix_stats:
                    prefix_stats[prefix] = {"count": 0, "uri": uri}
                prefix_stats[prefix]["count"] += 1
            
            # 쿼리 패턴 추출 (SELECT, ASK, CONSTRUCT 등)
            pattern_match = re.match(r'^\s*(SELECT|ASK|CONSTRUCT|DESCRIBE)', query)
            if pattern_match:
                pattern = pattern_match.group(1)
                pattern_stats[pattern] = pattern_stats.get(pattern, 0) + 1
        
        # 가장 많이 사용된 PREFIX 정렬
        top_prefixes = sorted(
            [(prefix, data["count"], data["uri"]) for prefix, data in prefix_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # 가장 많이 사용된 패턴 정렬
        top_patterns = sorted(
            pattern_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_queries": total_queries,
            "avg_execution_time_ms": round(avg_execution_time, 2),
            "top_prefixes": [
                {"prefix": prefix, "count": count, "uri": uri}
                for prefix, count, uri in top_prefixes
            ],
            "top_patterns": [
                {"pattern": pattern, "count": count}
                for pattern, count in top_patterns
            ],
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
    except Exception as e:
        logging.error(f"통계 조회 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sparql/logs/search")
async def search_sparql_logs(
    keyword: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    username: str = Depends(get_admin_credentials)
):
    """SPARQL 쿼리 로그를 검색합니다."""
    try:
        all_logs = []
        
        # 모든 로그 파일 읽기
        for log_file in SPARQL_LOG_DIR.glob("sparql_log_*.json"):
            with log_file.open("r", encoding="utf-8") as f:
                logs = json.load(f)
                all_logs.extend(logs)
        
        # 날짜 필터링
        if start_date or end_date:
            filtered_logs = []
            for log in all_logs:
                log_date = datetime.fromisoformat(log["timestamp"]).date()
                if start_date and log_date < start_date:
                    continue
                if end_date and log_date > end_date:
                    continue
                filtered_logs.append(log)
            all_logs = filtered_logs
        
        # 키워드 검색
        if keyword:
            keyword = keyword.lower()
            search_results = []
            for log in all_logs:
                # 쿼리 내용 검색
                if keyword in log["query"].lower():
                    search_results.append(log)
                    continue
                
                # 결과 내용 검색
                if "results" in log and "bindings" in log["results"]:
                    for binding in log["results"]["bindings"]:
                        for value in binding.values():
                            if keyword in str(value).lower():
                                search_results.append(log)
                                break
                        if log in search_results:
                            break
            
            all_logs = search_results
        
        # 최신 순으로 정렬
        all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "total": len(all_logs),
            "keyword": keyword,
            "logs": all_logs[:limit]
        }
    except Exception as e:
        logging.error(f"쿼리 로그 검색 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def protect_log_files(request: Request, call_next):
    # 로그 파일 직접 접근 차단
    if request.url.path.startswith("/sparql_logs/"):
        return JSONResponse(
            status_code=403,
            content={"detail": "로그 파일에 직접 접근할 수 없습니다."}
        )
    return await call_next(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 