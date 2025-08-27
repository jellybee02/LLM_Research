# main.py
from fastapi import FastAPI
from pydantic import BaseModel
import chromadb

# FastAPI 인스턴스 생성
app = FastAPI()

# 요청 모델 정의
class QuestionRequest(BaseModel):
    question: str

# ChromaDB 클라이언트 연결
client = chromadb.PersistentClient(path="./chroma_db")  # DB 경로는 실제 환경에 맞게 변경
collection = client.get_or_create_collection("medical_qa")

@app.post("/ask")
def ask_question(request: QuestionRequest):
    # 유사한 질문 검색
    results = collection.query(
        query_texts=[request.question],
        n_results=1
    )

    if results and results["documents"]:
        answer = results["documents"][0][0]  # 가장 유사한 answer
        return {"question": request.question, "answer": answer}
    else:
        return {"question": request.question, "answer": "답변을 찾을 수 없습니다."}
