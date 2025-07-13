import numpy as np, pandas as pd, warnings, os, openai, json
from tqdm.auto import tqdm
from openai import OpenAI
warnings.filterwarnings('ignore')
import requests
from typing import List, Tuple, Union
from langchain_ollama.embeddings import OllamaEmbeddings
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from haversine import haversine, Unit


current_dir = os.path.dirname(__file__)  # function.py가 있는 디렉토리
api_key_path = os.path.join(current_dir, '../../../api_key.txt')

with open(api_key_path, 'r') as f:
    api_key = f.read()

openai.api_key = api_key

# 입력데이터 값 임베딩 변경
class OllamaSentenceTransformer():
    def __init__(
            self,
            *args,
            **kargs,
            ) -> None:
                # self.base_url = kargs.get()
                self.model = kargs.get("model","bge-m3")
                self.embedding_model = OllamaEmbeddings(
                            model = self.model,
                            # base_url = self.base_rul,
                        )
                        
    
    def encode(
            self,
            documents:Union[str, List[str], np.ndarray],
            *args,
            **kargs,
        )-> np.ndarray:
        if isinstance(documents, str):
            document_embeddings = self.embedding_model.embed_query(documents)
            return np.array(document_embeddings)
        
        if isinstance(documents, np.ndarray):
            documents = documents.tolist()
        
        document_embeddings = [self.embedding_model.embed_query(s) for s in documents]
        return np.array(document_embeddings)
    




# NOTE 위치정보 입력 : -> 위도 경도 반환
def get_lat_lon(location_name):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': location_name,
        'format': 'json'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; ChatGPT-Example/1.0; +http://yourdomain.com)'
    }

    response = requests.get(url, params=params, headers=headers)

    # 응답 확인
    if response.status_code != 200:
        print(f"요청 실패: {response.status_code}")
        print("응답 내용:", response.text)
        return None

    try:
        data = response.json()
        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            return float(lat), float(lon)
        else:
            print("위치 정보를 찾을 수 없습니다.")
            return None
    except ValueError as e:
        print("JSON 파싱 오류:", e)
        print("응답 내용:", response.text)
        return None
    

def compare_cosim(all_asset_encoded_val:np.array, asset_info:np.array) -> float:
    cos_sim = cosine_similarity(all_asset_encoded_val, [asset_info])
    return cos_sim

def invoke_openai(
           prompt,
           api_key=api_key,
           model="gpt-4o",
           temperature=0.7):
    client = OpenAI(api_key=api_key)

    # 메시지 구성
    messages = [
        # {"role": "system", "content": prompt},
        {"role": "user", "content": prompt}
    ]
    # 스트리밍 요청
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        # stream=True  # ⭐ 핵심 옵션!
    )

    # generator 반환 (chunk 단위 텍스트 출력)
    return stream






