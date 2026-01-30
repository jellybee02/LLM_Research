"""
Database Initialization Script
데이터베이스 테이블 생성 및 초기 데이터 설정
"""

import sys
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import get_settings
from app.models.db_models import Base, QAMaster
from app.utils import get_logger

logger = get_logger(__name__)


async def create_tables():
    """
    데이터베이스 테이블 생성
    """
    settings = get_settings()
    
    logger.info("Creating database tables...")
    
    # 비동기 엔진 생성
    engine = create_async_engine(
        settings.database.url,
        echo=True,
    )
    
    try:
        async with engine.begin() as conn:
            # 모든 테이블 생성
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
    
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise
    
    finally:
        await engine.dispose()


async def insert_sample_data():
    """
    샘플 데이터 삽입
    """
    settings = get_settings()
    
    logger.info("Inserting sample data...")
    
    engine = create_async_engine(settings.database.url)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with AsyncSessionLocal() as session:
            # 샘플 QA 데이터
            sample_questions = [
                {
                    "domain": "응급의학",
                    "q_type": "multiple_choice",
                    "question": "급성 심근경색의 가장 흔한 초기 증상은?\n1. 두통\n2. 흉통\n3. 복통\n4. 어지러움",
                    "answer": "2",
                    "choices": ["두통", "흉통", "복통", "어지러움"],
                    "explanation": "급성 심근경색의 가장 흔한 초기 증상은 흉통이다. 전형적으로 압박감, 쥐어짜는 듯한 통증으로 나타난다.",
                },
                {
                    "domain": "내과",
                    "q_type": "short_answer",
                    "question": "당뇨병의 3대 증상은?",
                    "answer": "다뇨, 다음, 다식",
                    "explanation": "당뇨병의 3대 증상은 다뇨(많이 소변봄), 다음(많이 마심), 다식(많이 먹음)이다.",
                },
                {
                    "domain": "소아청소년과",
                    "q_type": "multiple_choice",
                    "question": "생후 2개월 영아가 접종해야 하는 백신은?\n1. MMR\n2. DTaP\n3. 일본뇌염\n4. 수두",
                    "answer": "2",
                    "choices": ["MMR", "DTaP", "일본뇌염", "수두"],
                    "explanation": "생후 2개월에는 DTaP(디프테리아, 파상풍, 백일해) 백신을 접종한다.",
                },
                {
                    "domain": "산부인과",
                    "q_type": "short_answer",
                    "question": "임신 중 복용을 피해야 하는 약물의 예를 2가지 쓰시오.",
                    "answer": "와파린, 이소트레티노인",
                    "explanation": "임신 중 와파린(항응고제), 이소트레티노인(여드름 치료제) 등은 태아에게 위험할 수 있어 복용을 피해야 한다.",
                },
            ]
            
            for qa_data in sample_questions:
                qa = QAMaster(**qa_data)
                session.add(qa)
            
            await session.commit()
            
            logger.info(f"Inserted {len(sample_questions)} sample questions")
    
    except Exception as e:
        logger.error(f"Error inserting sample data: {e}")
        raise
    
    finally:
        await engine.dispose()


async def main():
    """
    메인 함수
    """
    print("=" * 60)
    print("Database Initialization")
    print("=" * 60)
    
    try:
        # 테이블 생성
        await create_tables()
        print("\n✓ Tables created")
        
        # 샘플 데이터 삽입
        await insert_sample_data()
        print("✓ Sample data inserted")
        
        print("\n" + "=" * 60)
        print("Database initialization completed successfully!")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
