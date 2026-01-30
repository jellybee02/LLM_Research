"""
Qdrant Document Indexing Script
의료 문서를 Qdrant에 인덱싱
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import uuid

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.config import get_settings
from app.services import LLMService
from app.models import DepartmentCode
from app.utils import get_logger

logger = get_logger(__name__)


# 샘플 의료 문서 데이터
SAMPLE_DOCUMENTS = {
    DepartmentCode.EM: [
        {
            "title": "급성 관상동맥 증후군 가이드라인",
            "content": "급성 관상동맥 증후군은 심근경색과 불안정 협심증을 포함하는 응급 질환이다. 주요 증상으로 흉통, 호흡곤란, 식은땀이 있으며, 즉시 응급실 방문이 필요하다.",
            "source": "대한심장학회",
            "metadata": {
                "published_at": "2023-01-15",
                "category": "cardiac",
            }
        },
        {
            "title": "뇌졸중 응급 대응",
            "content": "뇌졸중의 주요 증상은 FAST로 기억한다. Face(얼굴 마비), Arm(팔 약화), Speech(언어 장애), Time(시간이 중요). 증상 발현 시 즉시 119에 연락한다.",
            "source": "대한신경과학회",
            "metadata": {
                "published_at": "2023-03-20",
                "category": "neurology",
            }
        },
    ],
    DepartmentCode.IM: [
        {
            "title": "당뇨병 관리 지침",
            "content": "2형 당뇨병 환자는 식이요법, 운동, 약물치료를 병행해야 한다. 목표 혈당은 공복 시 80-130mg/dL, 식후 2시간 180mg/dL 이하이다. 정기적인 HbA1c 검사가 필요하다.",
            "source": "대한당뇨병학회",
            "metadata": {
                "published_at": "2023-02-10",
                "category": "endocrinology",
            }
        },
        {
            "title": "고혈압 진단과 치료",
            "content": "고혈압은 수축기 혈압 140mmHg 이상 또는 이완기 혈압 90mmHg 이상으로 정의된다. 생활습관 개선과 함께 필요시 약물치료를 시행한다.",
            "source": "대한고혈압학회",
            "metadata": {
                "published_at": "2023-01-25",
                "category": "cardiology",
            }
        },
    ],
    DepartmentCode.PED: [
        {
            "title": "영유아 예방접종 일정",
            "content": "생후 2개월부터 DTaP, 폴리오, B형간염, Hib, 폐렴구균 백신을 접종한다. 12개월에 MMR과 수두 백신을 접종하며, 각 백신은 정해진 간격으로 추가 접종이 필요하다.",
            "source": "질병관리청",
            "metadata": {
                "published_at": "2023-04-01",
                "category": "vaccination",
            }
        },
        {
            "title": "소아 발열 대응",
            "content": "소아의 발열은 38도 이상을 의미한다. 3개월 미만 영아의 발열은 즉시 의료기관을 방문해야 한다. 해열제는 체온이 38.5도 이상일 때 사용을 고려한다.",
            "source": "대한소아과학회",
            "metadata": {
                "published_at": "2023-02-15",
                "category": "fever",
            }
        },
    ],
    DepartmentCode.OBGYN: [
        {
            "title": "임신 중 약물 안전성",
            "content": "임신 중에는 FDA 카테고리 A, B 약물이 비교적 안전하다. 와파린, 이소트레티노인 등은 태아 기형을 유발할 수 있어 금기이다. 약물 복용 전 반드시 의사와 상담이 필요하다.",
            "source": "대한산부인과학회",
            "metadata": {
                "published_at": "2023-03-05",
                "category": "pregnancy",
            }
        },
        {
            "title": "산후 출혈 관리",
            "content": "산후 출혈은 분만 후 500mL(제왕절개는 1000mL) 이상의 출혈을 의미한다. 주요 원인은 자궁 수축부전, 태반 잔류, 산도 열상 등이다. 즉각적인 처치가 필요하다.",
            "source": "대한산부인과학회",
            "metadata": {
                "published_at": "2023-01-30",
                "category": "postpartum",
            }
        },
    ],
    DepartmentCode.COMMON: [
        {
            "title": "건강한 생활습관",
            "content": "건강을 유지하기 위해서는 균형잡힌 식사, 규칙적인 운동, 충분한 수면이 중요하다. 금연과 절주를 실천하고, 정기적인 건강검진을 받는 것이 좋다.",
            "source": "보건복지부",
            "metadata": {
                "published_at": "2023-01-01",
                "category": "lifestyle",
            }
        },
        {
            "title": "감기와 독감의 차이",
            "content": "감기는 주로 코와 목에 증상이 나타나며 점진적으로 발병한다. 독감은 고열, 근육통, 두통 등 전신 증상이 급격히 나타난다. 독감은 예방접종으로 예방 가능하다.",
            "source": "질병관리청",
            "metadata": {
                "published_at": "2023-02-01",
                "category": "infectious_disease",
            }
        },
    ],
}


async def create_collections(client: QdrantClient, settings):
    """
    Qdrant 컬렉션 생성
    """
    collections = settings.qdrant.collections
    embedding_dim = 1536  # text-embedding-3-small dimension
    
    for dept in DepartmentCode:
        collection_name = getattr(collections, dept.value.lower())
        
        # 컬렉션이 이미 존재하는지 확인
        existing_collections = client.get_collections().collections
        if any(col.name == collection_name for col in existing_collections):
            logger.info(f"Collection {collection_name} already exists, skipping creation")
            continue
        
        # 컬렉션 생성
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE,
            ),
        )
        
        logger.info(f"Created collection: {collection_name}")


async def index_documents(
    client: QdrantClient,
    llm_service: LLMService,
    settings,
):
    """
    문서 인덱싱
    """
    for department, documents in SAMPLE_DOCUMENTS.items():
        collection_name = getattr(settings.qdrant.collections, department.value.lower())
        
        logger.info(f"Indexing {len(documents)} documents for {department.value}...")
        
        points = []
        
        for doc in documents:
            # 문서 임베딩 생성
            embedding = await llm_service.generate_embedding(doc["content"])
            
            # Point 생성
            point_id = str(uuid.uuid4())
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "doc_id": point_id,
                    "title": doc["title"],
                    "content": doc["content"],
                    "source": doc["source"],
                    "department": department.value,
                    "metadata": doc["metadata"],
                }
            )
            
            points.append(point)
        
        # 배치로 인덱싱
        client.upsert(
            collection_name=collection_name,
            points=points,
        )
        
        logger.info(f"Indexed {len(points)} documents to {collection_name}")


async def main():
    """
    메인 함수
    """
    print("=" * 60)
    print("Qdrant Document Indexing")
    print("=" * 60)
    
    try:
        # 설정 로드
        settings = get_settings()
        
        # Qdrant 클라이언트 생성
        client = QdrantClient(
            url=settings.qdrant.url,
            api_key=settings.qdrant.api_key,
        )
        
        # LLM 서비스 생성
        llm_service = LLMService(settings)
        
        # 컬렉션 생성
        print("\n1. Creating collections...")
        await create_collections(client, settings)
        print("✓ Collections created")
        
        # 문서 인덱싱
        print("\n2. Indexing documents...")
        await index_documents(client, llm_service, settings)
        print("✓ Documents indexed")
        
        # 통계 출력
        print("\n3. Collection statistics:")
        for dept in DepartmentCode:
            collection_name = getattr(settings.qdrant.collections, dept.value.lower())
            info = client.get_collection(collection_name)
            print(f"  - {collection_name}: {info.points_count} documents")
        
        print("\n" + "=" * 60)
        print("Document indexing completed successfully!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
