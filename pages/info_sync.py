import os
import sys

# 1. 현재 파일의 부모의 부모(mineral 폴더) 경로를 계산
# abspath(__file__)은 현재 파일의 절대경로, dirname은 그 부모 폴더
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. 시스템 경로(sys.path) 맨 앞에 루트 폴더 추가
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st
from DB.DB import get_connection 
from pages.mineral_price_sync import run_mineral_sync
from pages.mineral_import_sync import run_import_crawler
from pages.news_sync import run_news_sync

def run_all_sync():
    results = {}
    
    # 1. 광물 가격 동기화
    print('광물 가격 동기화 중')
    try:
        results['mineral'] = run_mineral_sync()
    except Exception as e:
        results['mineral'] = f"에러: {e}"


    # 2. 광물 가격 동기화
    print('광물 수입 동기화 중')
    try:
        results['import'] = run_import_crawler()
    except Exception as e:
        results['import'] = f"에러: {e}"

    # 3. 뉴스 동기화
    print('뉴스 동기화 중')
    try:
        results['import'] = run_news_sync()
    except Exception as e:
        results['import'] = f"에러: {e}"

    st.cache_data.clear()

    st.rerun()
    
    return results