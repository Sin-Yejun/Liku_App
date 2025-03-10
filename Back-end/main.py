from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path  # 파일 경로 확인을 위한 Path 사용
from typing import List, Dict
import json
import random
from dotenv import load_dotenv
import os
import paho.mqtt.client as mqtt
import re

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

broker_ip = "20.41.118.19"
port = 1883
topic = "liku/809b335b-4c49-4a92-8db2-5d79e4b7a890/json/list"  # Publish할 topic


def publish_mqtt_message(response: str):
    client = mqtt.Client()  # MQTT 클라이언트 생성
    
    # 콜백 설정
    client.on_connect = lambda client, userdata, flags, rc: print("MQTT 연결 성공" if rc == 0 else f"MQTT 연결 실패, 코드: {rc}")
    client.on_publish = lambda client, userdata, mid: print("메시지 발행 성공")

    # MQTT 서버 연결
    client.connect(broker_ip, port, 60)

    # JSON payload 생성
    payload = {
        "data": [
            {
                "action": {
                    "action_name": "fighting",
                    "action_type": "overlap",
                    "pitch": 0,
                    "yaw": 0
                },
                "display": {
                    "display_name": "blink",
                    "delay": 0,
                    "playtime": 1,
                    "playspeed": 3
                },
                "speech": {
                    "speech_name": "TTS_output",
                    "TTS": response,  # 리쿠의 답변을 TTS에 넣음
                    "delay": 0,
                    "repeat": 0
                },
                "listen": False
            }
        ]
    }
    
    # MQTT로 payload 발행
    payload_str = json.dumps(payload, ensure_ascii=False)
    client.publish(topic, payload_str)
    print('메시지 발행 완료 >> ', payload_str)

    # 연결 종료
    client.disconnect()


# OpenAI 클라이언트 및 FastAPI 설정
app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 메시지 스키마 정의
class Message(BaseModel):
    content: str

# gpt-4o-mini
# gpt-4o
# LangChain 설정
llm = ChatOpenAI(api_key=openai_api_key, model= 'gpt-4o', temperature=0.3)
llm_mini = ChatOpenAI(api_key=openai_api_key, model='gpt-4o-mini', temperature=0.7)

# 파일 경로 확인
json_file_path = Path('kiosk.json')
manual_file_path = Path('manual.txt')
scenario_file_path = Path('scenario.txt')
history_file_path = Path('history.txt')

# 시나리오 생성 함수 정의
def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def generate_scenario():
    # 각 JSON 파일에서 데이터 로드
    time_data = load_data('time.json')['time']
    people_data = load_data('people.json')['people']
    destination_data = load_data('destination.json')['destination']
    
    # 랜덤으로 시간, 인원, 목적지 선택
    chosen_time = random.choice(time_data)
    chosen_people = random.choice(people_data)
    chosen_destination = random.choice(destination_data)['name']
    
    # 시나리오 텍스트 생성
    scenario_text = f"목적지 = \"{chosen_destination}\"\n버스시간 = \"{chosen_time}\"\n인원 = \"{chosen_people}\"\n"
    
    # 시나리오를 scenario.txt에 저장
    with open('scenario.txt', 'w', encoding='utf-8') as file:
        file.write(scenario_text)
    
    return scenario_text

# Lifespan 핸들러 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup 시 실행
    scenario = generate_scenario()
    print("\n 서버가 실행되었습니다. \n")
    global scenario_content
    with open('scenario.txt', 'r', encoding='utf-8') as file:
        scenario_content = file.read()
    
    yield  # 앱 실행 중
    
    # Shutdown 시 실행 (필요 시 추가)
    print("\n 서버가 종료되었습니다. \n")

app.router.lifespan_context = lifespan

# JSON 파일 로드
if json_file_path.exists():
    with open(json_file_path, 'r', encoding='utf-8') as file:
        json_content = json.load(file)
else:
    raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {json_file_path}")

# 시나리오 텍스트 파일 로드
if scenario_file_path.exists():
    with open(scenario_file_path, 'r', encoding='utf-8') as file:
        scenario_content = file.read()
else:
    raise FileNotFoundError(f"텍스트 파일을 찾을 수 없습니다: {scenario_file_path}")

# 메뉴얼 텍스트 파일 로드
if manual_file_path.exists():
    with open(manual_file_path, 'r', encoding='utf-8') as file:
        manual_content = file.read()
else:
    raise FileNotFoundError(f"텍스트 파일을 찾을 수 없습니다: {manual_file_path}")

# 히스토리 텍스트 파일 로드
if history_file_path.exists():
    with open(history_file_path, 'r', encoding='utf-8') as file:
        history_content = file.read()
else:
    raise FileNotFoundError(f"텍스트 파일을 찾을 수 없습니다: {history_file_path}")

# 프롬프트 템플릿 설정 (문서의 내용을 반영)
prompt_template = """
당신은 60대 이상 어른에게 키오스크 사용에 도움을 주는 AI입니다.
사용자는 현재 누르고 있는 버튼에 대한 정보를 입력합니다. 입력에 대한 답변은 아래의 관련 문서를 참고해 답변해주세요.

Kiosk Context:
{context}

User Manual:
{manual}

The scenario that the user must follow::
{scenario}

User input & AI response Log
{history}

Button information pressed by the user:
{question}

답변 (한국어로, 1줄만):
"""
prompt = PromptTemplate(template=prompt_template, input_variables=["context", "manual", "scenario", "history", "question"])

qa_chain = prompt | llm

def ask_question(query):
    # JSON 내용을 문자열로 변환
    context = json.dumps(json_content, ensure_ascii=False)

    # 프롬프트에 질문과 문서 내용 연결
    answer = qa_chain.invoke({"context": context,  "manual": manual_content, "scenario": scenario_content, "history": history_content, "question": query})
    
    return answer.content


with open('history.txt', 'w', encoding='utf-8') as file:
    pass

def clean_history():
    with open('history.txt', 'w', encoding='utf-8') as file:
         file.truncate(0)

def compliment_generate(response):
    # 칭찬 생성 프롬프트 설정
    compliment_prompt = PromptTemplate(template="{response}\n위의 응답내용의 앞이나 뒤에 응답 내용과 어울리는 칭찬이나 격려를 한마디만 더해주세요. 단, 응답 내용을 전부 그대로 적어줘야 합니다. Example. 괜찮아요. 다시한번 생각해볼까요? 잘하고 있습니다! etc",
    input_variables=["response"]
    ).format(response=response)

    # Generate the response with possible compliment using gpt-4o-mini
    final_response = llm_mini.invoke(compliment_prompt)

    # Return the content generated by gpt-4o-mini
    return final_response.content

# FastAPI 라우트 정의
@app.post("/chat")
async def chat(message: Message):
    global scenario_content

    # 사용자가 앱을 실행했다면
    if message.content == "사용자가 앱을 실행했습니다.":
        scenario = generate_scenario()
        with open('scenario.txt', 'r', encoding='utf-8') as file:
            scenario_content = file.read()

        # Extract values for 목적지, 버스시간, 인원
        destination = re.search(r'목적지 = "(.*?)"', scenario_content).group(1)
        bus_time = re.search(r'버스시간 = "(.*?)"', scenario_content).group(1)
        people = re.search(r'인원 = "(.*?)"', scenario_content).group(1)

        # Format the response
        response = f"안녕하세요. 리쿠와 함께하는 키오스크 교육에 오신 것을 환영합니다. 오늘 해볼 미션은 [{destination}] 지역으로 가는 [{bus_time}] 버스를 선택하고 [{people}]을 예매하는 것입니다. 화면 오른쪽 보라색 버튼을 눌러 목적지 선택 화면으로 이동해볼까요?"

        clean_history()  # Clear history

        print('사용자 입력 >> ' + message.content)
        print('AI 답변 >> ' + response)

        with open('history.txt', 'a', encoding='utf-8') as file:
            file.write(f'User Input >> {message.content}\n')
            file.write(f'AI Response >>  {response}\n\n')
        #publish_mqtt_message(response)

        return response
    
    # 사용자가 재시작 버튼을 눌렀다면
    if message.content == "RESTART":
        scenario = generate_scenario()
        print(f"생성된 시나리오:\n{scenario}")
        #global scenario_content
        with open('scenario.txt', 'r', encoding='utf-8') as file:
            scenario_content = file.read()
        response = ask_question(message.content)
        print(response)
        #publish_mqtt_message(response)
        clean_history()
        return response
    
    response = ask_question(message.content)

    # 50% 확률로 칭찬 추가
    if random.random() < 0.5 and message.content[0] == '*':
        response = compliment_generate(response)

    print('사용자 입력 >> ' + message.content)
    print('AI 답변 >> ' + response)

    with open('history.txt', 'a', encoding='utf-8') as file:
        file.write(f'User Input >> {message.content}\n')
        file.write(f'AI Response >>  {response}\n\n')
    #publish_mqtt_message(response)
    # 답변을 출력
    return response

@app.get("/scenario")
async def get_scenario():
    with open('scenario.txt', 'r', encoding='utf-8') as file:
        scenario = file.read()
    return {"scenario": scenario}
# uvicorn main:app --reload
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
