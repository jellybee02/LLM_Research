import script.streamlit as st
# import openai
import pandas as pd
from geopy.distance import geodesic
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

key = open('../../../api_key.txt','r')
api_key = key.read()
openai.api_key = api_key

base_ = open('../../../base_url.txt','r')
base_url = base_.read()
# openai.api_key = api_key

df = pd.read_csv("../data/prep3.csv", encoding='cp949')

# 사용자 입력
st.title("🔧 서울시 공구 대여 도우미 챗봇")

tool = st.text_input("원하는 공구를 입력하세요 (예: 전동드릴)")
location = st.text_input("현재 위치를 입력하세요 (예 : 강남역)")
# lat = st.number_input("현재 위치 위도 입력", format="%.6f")
# lon = st.number_input("현재 위치 경도 입력", format="%.6f")
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

loc1, loc2 = get_lat_lon(location)
#위도, 경도


if st.button("대여소 찾기 및 추천 받기"):
    if tool and lat and lon:
        # 거리 계산
        user_location = (lat, lon)
        tool_rentals["distance_km"] = tool_rentals.apply(
            lambda row: geodesic(user_location, (row["lat"], row["lon"])).km,
            axis=1
        )

        nearest = tool_rentals.sort_values("distance_km").head(3)

        st.subheader("📍 가장 가까운 공구 대여소 Top 3")
        for _, row in nearest.iterrows():
            st.markdown(f"**{row['name']}**\n- 주소: {row['address']}\n- 거리: {row['distance_km']:.2f} km")

        # GPT에게 함께 쓰기 좋은 공구 추천 요청
        with st.spinner("공구 조합 추천 중..."):
            prompt = f"""
            나는 '{tool}'을 빌리려고 해. 함께 쓰면 유용한 다른 공구 2~3개를 추천해줘.
            각 공구마다 간단한 설명도 덧붙여줘.
            """
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response["choices"][0]["message"]["content"]

        st.subheader("🛠 함께 사용하면 좋은 공구 추천")
        st.markdown(answer)
    else:
        st.warning("공구 이름과 위치 정보를 모두 입력해주세요.")
