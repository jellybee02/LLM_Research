# Medical QA/RAG API

의료 데이터 기반 QA 및 RAG(Retrieval-Augmented Generation) 시스템

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [시스템 아키텍처](#시스템-아키텍처)
- [설치 및 실행](#설치-및-실행)
- [API 사용법](#api-사용법)
- [설정](#설정)
- [개발](#개발)

## 🎯 개요

의료 데이터를 기반으로 두 가지 핵심 기능을 제공하는 API 시스템입니다:

1. **QA 답변 생성 및 채점** - 주어진 의료 문제에 대해 답변을 생성하고 채점
2. **RAG 기반 전문 답변** - 진료과 분류 후 관련 문서를 검색하여 근거 기반 답변 제공

## ✨ 주요 기능

### 기능 1: QA 답변 생성 및 채점
- 의료 문제에 대한 자동 답변 생성
- 객관식/주관식 문제 지원
- 정답과의 비교 및 채점
- 답변 로그 및 감사 추적

### 기능 2: RAG 기반 전문 답변
- 질문을 5개 진료과로 자동 분류
  - 응급의학과 (EM)
  - 내과 (IM)
  - 소아청소년과 (PED)
  - 산부인과 (OBGYN)
  - 공용 (COMMON)
- Qdrant 기반 벡터 검색
- 진료과별 맞춤 프롬프트 적용
- 문서 근거 기반 답변 생성
- 안전성 체크 및 경고 메시지

## 🏗 시스템 아키텍처

```
┌─────────────┐
│   FastAPI   │ ← API 서버
└─────┬───────┘
      │
      ├─────────────────────────────────────┐
      │                                     │
┌─────▼──────┐                    ┌────────▼────────┐
│ PostgreSQL │                    │     Qdrant      │
│            │                    │                 │
│ - QA 문제  │                    │ - 의료 문서     │
│ - 답변 로그│                    │ - 임베딩 벡터   │
│ - 감사 로그│                    │ - 메타데이터    │
└────────────┘                    └─────────────────┘
      │
      │
┌─────▼──────┐
│  OpenAI    │
│  ChatGPT   │
│            │
│ - 답변 생성│
│ - 분류     │
│ - 임베딩   │
└────────────┘
```

### 구성 요소

- **FastAPI**: API 서버 (라우팅, 요청 검증, 응답 표준화)
- **PostgreSQL**: 문제/정답 데이터, 로그, 감사 추적
- **Qdrant**: 의료 문서 벡터 저장소
- **OpenAI ChatGPT**: LLM 기반 답변 생성 및 분류

## 🚀 설치 및 실행

### 1. 사전 요구사항

- Python 3.10+
- PostgreSQL 12+
- Qdrant (Docker 또는 Cloud)
- OpenAI API Key

### 2. 설치

```bash
# 저장소 클론
git clone <repository-url>
cd medical-qa-rag-api

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 설정

`config.yaml` 파일을 편집하여 필요한 설정을 입력합니다:

```yaml
database:
  host: "localhost"
  port: 5432
  name: "medical_qa_db"
  user: "postgres"
  password: "your_password"

qdrant:
  url: "http://localhost:6333"

openai:
  api_key: "sk-your-api-key"
```

**보안 권장사항**: 프로덕션 환경에서는 환경변수 사용:

```bash
export DATABASE_PASSWORD="your_password"
export OPENAI_API_KEY="sk-your-api-key"
export QDRANT_API_KEY="your_qdrant_key"
```

### 4. 데이터베이스 초기화

```bash
python scripts/init_db.py
```

### 5. 문서 인덱싱

```bash
python scripts/index_documents.py
```

### 6. 서버 실행

```bash
# 개발 모드
python -m app.main

# 또는 uvicorn 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 시작되면 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📖 API 사용법

### 헬스체크

```bash
curl http://localhost:8000/health
```

### 기능 1: QA 답변 생성

**문제 ID로 조회:**
```bash
curl -X POST http://localhost:8000/api/v1/qa/answer \
  -H "Content-Type: application/json" \
  -d '{
    "qa_id": 1
  }'
```

**직접 문제 입력:**
```bash
curl -X POST http://localhost:8000/api/v1/qa/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "급성 심근경색의 주요 증상은?"
  }'
```

**응답 예시:**
```json
{
  "trace_id": "req_abc123",
  "qa_id": 1,
  "question": "급성 심근경색의 주요 증상은?",
  "predicted_answer": "흉통, 호흡곤란",
  "correct_answer": "흉통, 호흡곤란, 발한",
  "is_correct": false,
  "score": 0.67,
  "explanation": "주요 증상은 맞췄으나 발한을 누락",
  "meta": {
    "model": "gpt-4-turbo-preview",
    "latency_ms": 1234
  }
}
```

### 기능 2: RAG 기반 답변

```bash
curl -X POST http://localhost:8000/api/v1/rag/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "급성 흉통이 있을 때 어떻게 해야 하나요?",
    "patient_info": {
      "age": 45,
      "gender": "male"
    }
  }'
```

**응답 예시:**
```json
{
  "trace_id": "req_xyz789",
  "question": "급성 흉통이 있을 때 어떻게 해야 하나요?",
  "department": "EM",
  "answer": "급성 흉통은 심근경색의 주요 증상일 수 있어 즉시 응급실 방문이 필요합니다...",
  "references": [
    {
      "doc_id": "doc_001",
      "title": "급성 관상동맥 증후군 가이드라인",
      "content": "...",
      "score": 0.92,
      "source": "대한심장학회"
    }
  ],
  "confidence": 0.89,
  "warnings": [
    "⚠️ 응급 상황이 의심됩니다. 즉시 119에 연락하거나 응급실을 방문하세요."
  ],
  "meta": {
    "model": "gpt-4-turbo-preview",
    "latency_ms": 2345
  }
}
```

### 진료과 분류 (테스트용)

```bash
curl -X POST "http://localhost:8000/api/v1/rag/classify?question=임신%20중%20복용%20가능한%20약은?"
```

## ⚙️ 설정

### config.yaml 주요 섹션

#### 서버 설정
```yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors_origins:
    - "http://localhost:3000"
```

#### 데이터베이스 설정
```yaml
database:
  host: "localhost"
  port: 5432
  name: "medical_qa_db"
  pool_size: 10
```

#### OpenAI 설정
```yaml
openai:
  api_key: "sk-xxx"
  model: "gpt-4-turbo-preview"
  temperature: 0.3
  max_tokens: 2000
```

#### 프롬프트 설정
진료과별 시스템 프롬프트는 `config.yaml`의 `prompts.rag` 섹션에서 관리됩니다.

## 🛠 개발

### 프로젝트 구조

```
medical-qa-rag-api/
├── app/
│   ├── main.py              # FastAPI 앱
│   ├── config.py            # 설정 관리
│   ├── models/              # 데이터 모델
│   │   ├── schemas.py       # Pydantic 스키마
│   │   └── db_models.py     # SQLAlchemy 모델
│   ├── services/            # 비즈니스 로직
│   │   ├── qa_service.py
│   │   ├── rag_service.py
│   │   ├── router_service.py
│   │   ├── llm_service.py
│   │   ├── qdrant_service.py
│   │   └── scoring_service.py
│   ├── repositories/        # DB 접근
│   │   ├── qa_repository.py
│   │   └── audit_repository.py
│   ├── api/                 # API 엔드포인트
│   │   ├── routes/
│   │   │   ├── qa.py
│   │   │   ├── rag.py
│   │   │   └── health.py
│   │   └── dependencies.py
│   └── utils/               # 유틸리티
│       ├── logging.py
│       ├── security.py
│       └── prompts.py
├── scripts/
│   ├── init_db.py           # DB 초기화
│   └── index_documents.py   # 문서 인덱싱
├── tests/                   # 테스트
├── config.yaml              # 설정 파일
└── requirements.txt         # 의존성
```

### 테스트 실행

```bash
# 전체 테스트
pytest

# 특정 테스트 파일
pytest tests/test_qa_service.py -v

# 커버리지 포함
pytest --cov=app tests/
```

### 코드 스타일

```bash
# Black 포맷팅
black app/ tests/

# Flake8 린팅
flake8 app/ tests/
```

## 📊 모니터링 및 로깅

### 구조화된 로깅
모든 요청은 `trace_id`로 추적되며, JSON 형식으로 로깅됩니다.

### 감사 로그
의료 데이터 특성상 모든 요청/응답이 감사 로그에 기록됩니다:
- 사용자 요청 내용
- 생성된 답변
- 사용된 모델 및 설정
- 응답 시간

### PII 마스킹
개인 식별 정보(주민등록번호, 전화번호 등)는 자동으로 마스킹됩니다.

## 🔒 보안

1. **API Key 관리**: 환경변수 사용 권장
2. **파일 권한**: config.yaml 접근 제한 (600)
3. **HTTPS**: 프로덕션에서 HTTPS 사용 필수
4. **Rate Limiting**: 설정 파일에서 활성화 가능
5. **PII 보호**: 자동 마스킹 및 익명화

## ⚠️ 주의사항

- 본 시스템은 **참고용**이며, 실제 진단 및 처방은 의료기관을 방문하여 받으시기 바랍니다.
- 응급 상황 시 즉시 119에 연락하거나 응급실을 방문하세요.
- 의료 데이터는 민감 정보이므로 보안에 각별히 주의하세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

## 🤝 기여

버그 리포트, 기능 제안, 풀 리퀘스트를 환영합니다!

## 📧 문의

문의사항이 있으시면 이슈를 등록해주세요.
