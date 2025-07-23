
from openai import OpenAI
from haversine import haversine, Unit
import streamlit as st, numpy as np, pandas as pd, warnings, os, openai, json, requests, pickle
from tqdm.auto import tqdm
from typing import List, Tuple, Union
from script.function import OllamaSentenceTransformer, get_lat_lon, invoke_openai, compare_cosim
warnings.filterwarnings('ignore')

# openai.api_key = "your-api-key"
key = open('../../api_key.txt','r')

api_key = key.read()

 
openai.api_key = api_key
print(api_key)

with open('./data/encoded_tool_name2.pkl', "rb") as f:
    all_tool_encoded_array = pickle.load(f)


sentence_transformer = OllamaSentenceTransformer()



# 샘플 공구 대여소 데이터 (위도, 경도 포함)


df = pd.read_csv("./data/prep3.csv", encoding='cp949')

# 사용자 입력
st.title("🔧 공구 대여 도우미 챗봇")
tool = st.text_input("원하는 공구를 입력하세요 (예: 전동드릴)")
location = st.text_input("원하는 현재 위치를 입력하세요 (예: 강남역)")
content = st.text_input("수행하려는 작업 내용을 입력해주세요 (예 : 전동드릴을 사용해서 나무를 고정하고 싶어)")
encoded_tool_name = sentence_transformer.encode(tool)
df['tool_sim_result'] = compare_cosim(all_tool_encoded_array, encoded_tool_name)
df = df[df['tool_sim_result']>0.9]



if st.button("대여소 찾기 및 추천 받기"):
    if tool and location:
        # 거리 계산
        lat, lon = get_lat_lon(location) # 위도, 경도
        df['distance_km'] = df[["위도","경도"]].apply(lambda x : round(haversine((lat, lon), (x['위도'], x['경도']), unit=Unit.KILOMETERS),3), axis=1)
        nearest = df.sort_values("distance_km").head(3)
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
            
            response = invoke_openai(prompt)
            answer = response.choices[0].message.content

        st.subheader("🛠 함께 사용하면 좋은 공구 추천")
        st.markdown(answer)
    else:
        st.warning("공구 이름과 위치 정보를 모두 입력해주세요.")






