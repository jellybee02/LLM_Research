import streamlit as st
import openai
import pandas as pd
from geopy.distance import geodesic

# openai.api_key = "your-api-key"

key = open('../../api_key.txt','r')
api_key = key.read()
openai.api_key = api_key

# 샘플 공구 대여소 데이터 (위도, 경도 포함)
tool_rentals = pd.DataFrame([
    {"name": "공구천국 강남점", "lat": 37.4981, "lon": 127.0276, "address": "서울 강남구 테헤란로 123"},
    {"name": "툴마켓 삼성점", "lat": 37.5105, "lon": 127.0636, "address": "서울 강남구 봉은사로 321"},
    {"name": "대여툴 역삼점", "lat": 37.4995, "lon": 127.0366, "address": "서울 강남구 역삼로 10"},
    {"name": "건설툴 서초점", "lat": 37.4830, "lon": 127.0322, "address": "서울 서초구 방배로 56"},
])

df = pd.read_csv("./data/prep3.csv", encoding='cp949')

# 사용자 입력
st.title("🔧 공구 대여 도우미 챗봇")

tool = st.text_input("원하는 공구를 입력하세요 (예: 전동드릴)")
location = st.text_input("원하는 현재 위치를 입력하세요 (예: 전동드릴)")

lat = st.number_input("현재 위치 위도 입력", format="%.6f")
lon = st.number_input("현재 위치 경도 입력", format="%.6f")

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
