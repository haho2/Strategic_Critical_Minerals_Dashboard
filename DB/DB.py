import os
import pymysql
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSL_CERT_PATH = os.path.join(BASE_DIR, "global-bundle.pem")
dotenv_path = os.path.join(BASE_DIR, ".env")

try:
    host = st.secrets["HOST"]
    user = st.secrets["USER"]
    password = st.secrets["PASSWORD"]
    db = st.secrets["DB"]
    
    print(f"성공적으로 가져온 HOST: {host[:10]}...") # 로그 확인용
except KeyError as e:
    st.error(f"Secrets 키를 찾을 수 없습니다: {e}")
    load_dotenv(dotenv_path)
    host = os.getenv("HOST")
    user = os.getenv("USER")
    password = os.getenv("PASSWORD")
    db = os.getenv("DB")




print(f"현재 BASE_DIR: {BASE_DIR}")
print(f"찾고 있는 .env 경로: {dotenv_path}")

# 1. 접속 정보 설정 (본인의 환경에 맞게 수정하세요)
db_config = {
    'host': host,          # 엔드포인트
    'port': 3306,          # MySQL 기본 포트는 3306
    'user': user,          # 접속 계정 아이디
    'password': password,  # 접속 비밀번호
    'db': db,              # 사용할 데이터베이스 이름
    'charset': 'utf8mb4',         # 한글 깨짐 방지 설정
    'cursorclass': pymysql.cursors.DictCursor, # 결과를 딕셔너리 형태로 받기 위한 설정
}

if os.path.exists(SSL_CERT_PATH):
    db_config['ssl'] = {'ca': SSL_CERT_PATH}

def get_connection():
    return pymysql.connect(**db_config)