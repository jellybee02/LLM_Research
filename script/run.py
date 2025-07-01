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


with open('../data/user_input_content.json', "rb") as f:
    input_content = json.load(f)
df = pd.read_csv("../data/prep3.csv", encoding='cp949')
key = open('../../../api_key.txt','r')
api_key = key.read()
openai.api_key = api_key
with open('../data/encoded_tool_name2.pkl', "rb") as f:
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


encoded_tool_name = sentence_transformer.encode(input_content['tool_name'])
location_name = input_content['location']
spot_location = get_lat_lon(location_name)
df['tool_sim_result'] = compare_cosim(all_tool_encoded_array, encoded_tool_name)
df_s = df[df['tool_sim_result']>0.9]
df_s['Distance(Km)'] = df_s[["위도","경도"]].apply(lambda x : round(haversine((spot_location[0], spot_location[1]), (x['위도'], x['경도']), unit=Unit.KILOMETERS),3), axis=1)
df_s.sort_values(by='Distance(Km)', ascending=True, inplace=True)



client = OpenAI(api_key=api_key)
def invoke(question, info = None, model="gpt-4o", temperature=0.7):
    response = client.chat.completions.create(
        model=model,
        messages = [
                    {"role": "system", 
                        "content": 
                            
                        
                            f"""너는 사람들의 질문에 친절히 답해주는 도우미야.
                        너는 서울시에서 운영하는 대여 공구 찾기 정보 시스템이야. 
                        관련 정보는 {info}와 같아. 
                        이정보를 통해서 사용자의 답변에 친절해 답해줘.
                        """ if info != None else
                            f"""너는 사람들의 질문에 친절히 답해주는 도우미야.
                        너는 서울시에서 운영하는 대여 공구 찾기 정보 시스템이야. 
                        사용자의 답변에 친절해 답해줘.
                        """
                        },
                    {"role": "user", 
                    "content": question}
                ],
        temperature=temperature,
        # stream=True
    )
    # print("💬 GPT 응답")
    # print("")
    # for chunk in response.choices[0].message.content:
    #     print(chunk, end='', flush=True)
    
    
    
    return response.choices[0].message.content

question = f"""나는 {input_content['tool_name']}을(를) 빌리고 싶어. 
            그리고 이 도구를 이용해서 하려는 작업은 '{input_content['job_content']}' 이야. 
            해당 작업을 하면서 같이 빌리면 좋은 공구도 함께 알려줘"""



answer = invoke(question)
print("가까운 대여소 : ", df_s[use_col].head(3).T.to_dict())
print("💬 GPT 응답:", answer)










