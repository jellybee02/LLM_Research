import streamlit as st
from openai import OpenAI
from haversine import haversine, Unit
# from .script.run import get_lat_lon
import requests, pickle
import numpy as np, pandas as pd, warnings, os, json, openai
from tqdm.auto import tqdm
from openai import OpenAI
warnings.filterwarnings('ignore')
import requests
from typing import List, Tuple, Union
from langchain_ollama.embeddings import OllamaEmbeddings
import pickle
from sklearn.metrics.pairwise import cosine_similarity

# openai.api_key = "your-api-key"
key = open('../../../api_key.txt','r')

api_key = key.read()

 
openai.api_key = api_key
print(api_key)

with open('./data/encoded_tool_name2.pkl', "rb") as f:
    all_tool_encoded_array = pickle.load(f)
use_col = ['공구 이름', '과금기준', '수량','대여장소명', '상세주소','전화번호', '평일오픈시간', '평일클로즈시간', '생성일시', '요금']
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
        




sentence_transformer = OllamaSentenceTransformer()



def invoke(
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

# 샘플 공구 대여소 데이터 (위도, 경도 포함)


df = pd.read_csv("./data/prep3.csv", encoding='cp949')

# 사용자 입력
st.title("🔧 공구 대여 도우미 챗봇")

tool = st.text_input("원하는 공구를 입력하세요 (예: 전동드릴)")
location = st.text_input("원하는 현재 위치를 입력하세요 (예: 강남역)")
content = st.text_input("수행하려는 작업 내용을 입력해주세요 (예 : 전동드릴을 사용해서 나무를 고정하고 싶어)")

# lat = st.number_input("현재 위치 위도 입력", format="%.6f")
# lon = st.number_input("현재 위치 경도 입력", format="%.6f")
encoded_tool_name = sentence_transformer.encode(tool)
# location_name = input_content['location']
# spot_location = get_lat_lon(location_name)
df['tool_sim_result'] = compare_cosim(all_tool_encoded_array, encoded_tool_name)
df = df[df['tool_sim_result']>0.9]



if st.button("대여소 찾기 및 추천 받기"):
    if tool and location:
        # 거리 계산
        lat, lon = get_lat_lon(location) # 위도, 경도
        df['distance_km'] = df[["위도","경도"]].apply(lambda x : round(haversine((lat, lon), (x['위도'], x['경도']), unit=Unit.KILOMETERS),3), axis=1)


        
        
        nearest = df.sort_values("distance_km").head(3)
        print(nearest)

        st.subheader("📍 가장 가까운 공구 대여소 Top 3")
        for _, row in nearest.iterrows():
            st.markdown(f"**{row['대여장소명']}**\n- 주소: {row['상세주소']}\n- 거리: {row['distance_km']:.2f} km")

        # GPT에게 함께 쓰기 좋은 공구 추천 요청
        with st.spinner("공구 조합 추천 중..."):
            if content is not None:
                prompt = f"""
                나는 '{tool}'을 빌리려고 해.
                그리고 {content}는 내가 하려는 작업 내용이야.
                해당 작업 내용을 진행하기 위해 같이 대여하면 좋은 작업 도구를 입력해주고 왜 필요한지 설명해줘.
                작업을 진행할 때 발생할 수 있는 위험 상황을 고려해서 주의사항도 함께 작성해줘.
                """
            else:
                prompt = f"""
                나는 '{tool}'을 빌리려고 해. 함께 쓰면 유용한 다른 공구 2~3개를 추천해줘.
                작업을 진행할 때 발생할 수 있는 위험 상황을 고려해서 주의사항도 함께 작성해줘.
               """
            
            response = invoke(prompt)
            answer = response.choices[0].message.content

        st.subheader("🛠 함께 사용하면 좋은 공구 추천")
        st.markdown(answer)
    else:
        st.warning("공구 이름과 위치 정보를 모두 입력해주세요.")






