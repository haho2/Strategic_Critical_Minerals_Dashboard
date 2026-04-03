import os
import sys
# 경로 설정
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from concurrent.futures import ThreadPoolExecutor, as_completed
from konlpy.tag import Okt
from sqlalchemy import text
import time
import random

from DB.DB import db_config as DB_CONF
from pages.mineral_price_sync import get_engine

okt = Okt()

MINERALS_LIST = ['리튬', '니켈', '코발트', '망간', '흑연', '네오디뮴', '디스프로슘', '터븀', '세륨', '란탄']
RISK_CONFIG_KR = {
    "수입·무역 제한": ["수입 차질", "수입 지연", "수입 중단", "통관 지연", "수출 제한", "수출 규제", "수출 통제", "수출 금지", "수출 중단", "제재", "경제 제재", "무역 제재", "금수", "금수 조치", "수출입 금지", "무역 금지", "관세", "관세 인상", "관세 부과", "자원 민족주의", "국유화","수출입 통제","수입 통제","수출 통제"],
    "생산·공급 차질": ["공급 부족", "공급난", "공급 차질", "수급 차질", "조달 차질", "생산 차질", "생산 중단", "생산 감소", "감산", "광산 중단", "광산 폐쇄", "채굴 중단", "정제 차질", "제련 차질", "가공 차질", "재고 부족", "비축 부족"],
    "물류 차질": ["운송 지연", "선적 지연", "물류 차질", "물류 지연", "항만 혼잡", "부두 적체", "항만 적체", "컨테이너 적체", "병목", "병목현상", "운임 상승", "운임 급등", "물류비 상승"],
    "정치·지정학 리스크": ["지정학적 리스크", "지정학적 긴장", "정치 불안", "무력 충돌", "군사 충돌", "분쟁", "내전", "파업", "노조 파업", "봉쇄", "전쟁"],
    "시장 경보": ["공급망 리스크", "공급 리스크", "가격 급등", "가격 폭등", "변동성", "가격 변동성"]
}
FINANCIAL_NOISE = ['증시', '코스피', '주가', '상장', '테마주', '매수', '매도']



# =========================
# 1. DB에서 마지막 뉴스 날짜 가져오기
# =========================
def get_latest_news_date(engine):
    print("[LOG] DB에서 마지막 뉴스 날짜 조회 중...")
    query = text("SELECT MAX(date) FROM news")
    with engine.connect() as conn:
        result = conn.execute(query).scalar()
    
    if result:
        # datetime 객체라면 date로 변환, 문자열이라면 파싱
        if isinstance(result, datetime):
            return result.date()
        return pd.to_datetime(result).date()
    
    # DB가 비어있다면 어제 날짜
    return date.today() - timedelta(days=1)


def get_article_details(url):
    try:
        headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://search.daum.net/",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 언론사명
        press_tag = soup.select_one('#kakaoHead *[data-tiara="언론사명"]')
        press_name = press_tag.get_text(strip=True) if press_tag else None
        
        # 본문
        content_tag = soup.select_one('.article_view') or soup.select_one('#dic_area')
        content = content_tag.text.strip() if content_tag else ""
        
        return {"content": content, "press_name": press_name}
    except:
        return {"content": "", "press_name": "정보없음"}

def process_article_task(art, mineral):
    try:
        title_tag = art.select_one('.item-title a') or art.select_one('.tit_main') or art.select_one('a.c-title-link')
        if not title_tag: return None

        title = title_tag.text.strip()
        link = title_tag['href']

        if any(word in title for word in FINANCIAL_NOISE):
            return None

        details = get_article_details(link)
        if not details["content"]: return None

        full_text = title + " " + details["content"]

        # 광물 체크
        if mineral not in full_text:
            return None

        # 리스크 체크
        tokens = [word for word, pos in okt.pos(full_text[:1200], stem=True) if pos in ['Noun', 'Verb']]
        refined_body = " ".join(tokens)

        found_groups = []
        for group, keywords in RISK_CONFIG_KR.items():
            for kw in keywords:
                if kw in refined_body:
                    found_groups.append(group)
                    break

        if found_groups:
            return {
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'title': title,
                'content': details["content"][:200],
                'source_type' : 'DAUM',
                'source_name': details["press_name"],
                'url': link,
                'mineral_keyword': json.dumps([mineral], ensure_ascii=False),
                'risk_keyword': json.dumps(list(set(found_groups)), ensure_ascii=False)
            }
    except:
        return None
# =========================
# 2. 뉴스 수집 및 저장 실행
# =========================
def run_news_sync():
    engine = get_engine(DB_CONF)
    
    # 시작일 설정 (마지막 날짜 + 1일)
    last_date = get_latest_news_date(engine)
    start_date = last_date + timedelta(days=1)
    today = date.today()

    if start_date > today:
        print(f"[SKIP] 뉴스 데이터가 이미 최신입니다. (마지막 날짜: {last_date})")
        return 0

    # Daum 검색용 날짜 포맷 (YYYYMMDD)
    sd = start_date.strftime("%Y%m%d")
    ed = today.strftime("%Y%m%d")
    
    print(f"[START] 뉴스 동기화 시작: {sd} ~ {ed}")
    
    all_results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Referer": "https://search.daum.net/",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    for mineral in MINERALS_LIST:
        print(f"🔎 [{mineral}] 수집 중...")
        search_items = []
        
        
        for page in range(1, 6): # 페이지 수 조절
            url = f"https://search.daum.net/search?w=news&q={mineral}&sd={sd}000000&ed={ed}235959&period=u&sort=recency&p={page}"
            
            try:
                time.sleep(random.uniform(1.5, 3.0))
                res = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')
                items = soup.select('.item-bundle-news') or \
                        soup.select('ul.c-list-basic > li') or \
                        soup.select('.coll_cont li')
                # print(soup)
                print(f"   - [{mineral}] {page}페이지 검색 결과 수: {len(items)}건")
                if not items: break
                search_items.extend(items)
            except:
                break

        # 병렬 상세 수집 실행
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_article_task, art, mineral) for art in search_items]
            for future in as_completed(futures):
                res = future.result()
                if res: all_results.append(res)

    # DB 저장 로직 (중복 제거 포함)
    if all_results:
        df = pd.DataFrame(all_results).drop_duplicates(subset=['url'])
        
        # ON DUPLICATE KEY UPDATE를 써서 이미 있는 URL은 무시하거나 업데이트
        sql = text("""
            INSERT INTO news (source_type, date, title, content, source_name, url, mineral_keyword, risk_keyword)
            VALUES (:source_type, :date, :title, :content, :source_name, :url, :mineral_keyword, :risk_keyword)
            ON DUPLICATE KEY UPDATE date=VALUES(date)
        """)
        
        with engine.begin() as conn:
            conn.execute(sql, df.to_dict(orient='records'))
        
        print(f"[FINISH] 뉴스 {len(df)}건 저장 완료")
        return len(df)
    
    print("[FINISH] 새로 수집된 조건에 맞는 뉴스가 없습니다.")
    return 0