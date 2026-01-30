"""
Qdrant Service
벡터 검색 및 문서 검색
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient, models

from app.config import Settings
from app.models import DepartmentCode
from app.utils import get_logger

logger = get_logger(__name__)


class QdrantService:
    """
    Qdrant 벡터 검색 서비스
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = QdrantClient(
            url=settings.qdrant.url,
            api_key=settings.qdrant.api_key,
            timeout=settings.qdrant.timeout,
        )
        self.collections = settings.qdrant.collections
        self.top_k = settings.qdrant.search.top_k
        self.score_threshold = settings.qdrant.search.score_threshold
    
    def get_collection_name(self, department: DepartmentCode) -> str:
        """
        진료과에 해당하는 컬렉션명 반환
        
        Args:
            department: 진료과 코드
            
        Returns:
            컬렉션명
        """
        dept_map = {
            DepartmentCode.EM: self.collections.em,
            DepartmentCode.IM: self.collections.im,
            DepartmentCode.PED: self.collections.ped,
            DepartmentCode.OBGYN: self.collections.obgyn,
            DepartmentCode.COMMON: self.collections.common,
        }
        return dept_map.get(department, self.collections.common)
    
    async def search(
        self,
        query_vector: List[float],
        department: DepartmentCode,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        벡터 유사도 검색
        
        Args:
            query_vector: 쿼리 임베딩 벡터
            department: 검색할 진료과
            top_k: 상위 K개 결과 (None이면 기본값)
            filters: 추가 필터 조건
            
        Returns:
            검색 결과 리스트
        """
        collection_name = self.get_collection_name(department)
        k = top_k or self.top_k
        
        try:
            # 필터 구성
            search_filter = None
            if filters:
                must_conditions = []
                for key, value in filters.items():
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                if must_conditions:
                    search_filter = models.Filter(must=must_conditions)
            
            # 검색 수행
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=k,
                score_threshold=self.score_threshold,
                query_filter=search_filter,
            )
            
            # 결과 변환
            results = []
            for hit in search_result:
                results.append({
                    "doc_id": hit.id,
                    "score": hit.score,
                    "content": hit.payload.get("content", ""),
                    "title": hit.payload.get("title", ""),
                    "source": hit.payload.get("source", ""),
                    "metadata": hit.payload.get("metadata", {}),
                })
            
            logger.info(
                "search_success",
                collection=collection_name,
                department=department.value,
                results_count=len(results),
                top_k=k,
            )
            
            return results
        
        except Exception as e:
            logger.error(
                "search_error",
                collection=collection_name,
                department=department.value,
                error=str(e),
            )
            # 검색 실패 시 빈 결과 반환
            return []
    
    async def search_with_fallback(
        self,
        query_vector: List[float],
        department: DepartmentCode,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fallback 전략이 있는 검색
        특정 진료과에서 결과가 없으면 COMMON 컬렉션에서 재검색
        
        Args:
            query_vector: 쿼리 임베딩 벡터
            department: 검색할 진료과
            top_k: 상위 K개 결과
            
        Returns:
            검색 결과 리스트
        """
        # 1차 검색: 지정된 진료과
        results = await self.search(
            query_vector=query_vector,
            department=department,
            top_k=top_k,
        )
        
        # 결과가 충분하지 않으면 COMMON에서 추가 검색
        if len(results) < (top_k or self.top_k) and department != DepartmentCode.COMMON:
            logger.info(
                "search_fallback",
                department=department.value,
                initial_results=len(results),
            )
            
            common_results = await self.search(
                query_vector=query_vector,
                department=DepartmentCode.COMMON,
                top_k=(top_k or self.top_k) - len(results),
            )
            
            results.extend(common_results)
        
        return results
    
    def check_collection_exists(self, department: DepartmentCode) -> bool:
        """
        컬렉션 존재 여부 확인
        
        Args:
            department: 진료과 코드
            
        Returns:
            컬렉션 존재 여부
        """
        collection_name = self.get_collection_name(department)
        
        try:
            collections = self.client.get_collections().collections
            return any(col.name == collection_name for col in collections)
        except Exception as e:
            logger.error(
                "check_collection_error",
                collection=collection_name,
                error=str(e),
            )
            return False
    
    async def get_collection_stats(self, department: DepartmentCode) -> Dict[str, Any]:
        """
        컬렉션 통계 조회
        
        Args:
            department: 진료과 코드
            
        Returns:
            컬렉션 통계
        """
        collection_name = self.get_collection_name(department)
        
        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            logger.error(
                "get_stats_error",
                collection=collection_name,
                error=str(e),
            )
            return {
                "name": collection_name,
                "error": str(e),
            }
