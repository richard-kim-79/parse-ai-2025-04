# SPARQL 통계 대시보드

SPARQL 쿼리 실행 로그를 분석하고 통계를 제공하는 대시보드 애플리케이션입니다.

## 기능

- SPARQL 쿼리 로그 수집 및 저장
- 쿼리 패턴 분석
- Prefix 사용 통계
- 실행 시간 분석
- 로그 검색 기능

## 기술 스택

### 백엔드
- FastAPI
- Python 3.9
- RDFLib
- pandas

### 프론트엔드
- Next.js
- React
- Recharts
- Tailwind CSS

## 설치 및 실행

### 백엔드

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8008
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

## 환경 변수

### 백엔드 (.env)
- ADMIN_USERNAME: 관리자 사용자명
- ADMIN_PASSWORD: 관리자 비밀번호
- FRONTEND_URL: 프론트엔드 URL
- PORT: 서버 포트

### 프론트엔드 (.env)
- NEXT_PUBLIC_BACKEND_URL: 백엔드 서버 URL

## 배포

이 프로젝트는 Render.com을 통해 배포됩니다. 자세한 배포 설정은 `render.yaml` 파일을 참조하세요. 