from dateutil.relativedelta import relativedelta

import time
import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# 상위 폴더 경로 추가 (DB 모듈 로드용)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from DB.DB import db_config as db_config
from pages.mineral_price_sync import get_engine

engine = get_engine(db_config)

# 1. DB에서 최신 날짜 가져오기
def get_latest_date():
    query = "SELECT MAX(date) FROM mineral_import"
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query)).fetchone()
            return result[0] if result[0] else None
    except Exception as e:
        print(f"⚠️ DB 조회 중 오류 (테이블이 없거나 첫 수집일 수 있음): {e}")
        
        return None



TARGET_URL = "https://www.komis.or.kr/Komis/MnrlMap/MapKorea/ajax/getListKoreaData"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.komis.or.kr/Komis/MnrlMap/Korea",
    "Origin": "https://www.komis.or.kr"
}

'''
MNRL0002		니켈
MNRL0001		리튬
MNRL0003		코발트
MNRL0004		망간
MNRL0005		흑연
MNRL0006        희토류
'''

MINERAL_ID_MAP = {
    "MNRL0001": 1, "MNRL0002": 2, "MNRL0003": 3, 
    "MNRL0004": 4, "MNRL0005": 5, "MNRL0006": 11
}


# db에서 나라 id, 코드 가져오는 함수
def get_country_mapping(engine):
    query = "SELECT country_id, country_code FROM countries"
    try:
        df_countries = pd.read_sql(query, engine)
        return dict(zip(df_countries['country_code'], df_countries['country_id']))
    except Exception: return {}



# ==========================================
#  데이터 수집 실행
# ==========================================
def run_import_crawler():
    country_id_map = get_country_mapping(engine)
    last_db_date = get_latest_date()
    last_db_date = last_db_date + relativedelta(months=1)

    last_db_date = last_db_date.replace(day=1)
    start_date = last_db_date
    # end_date 생성 시 .date()를 붙여 타입 에러 방지
    end_date = (datetime.now() - relativedelta(months=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0).date()

    if start_date > end_date:
        print(f"✅ 이미 최신 상태입니다. (DB 최신: {start_date})")
        return

    months = []
    current = start_date
    while current <= end_date:
        months.append(current)
        current += relativedelta(months=1)

    print(f"🚀 {start_date.strftime('%Y-%m')}부터 {end_date.strftime('%Y-%m')}까지 수집 시작...")

    all_processed_data = []

    # 광물id, 코드 매핑
    for mnrl_code, m_id in MINERAL_ID_MAP.items():
        print(f"\n📦 광물 코드 [{mnrl_code}] 작업 중...")
        for month_dt in months:
            s_date = month_dt.strftime("%Y%m01")
            e_date = month_dt.strftime("%Y%m31")
            prev_dt = month_dt - relativedelta(months=1)
            
            payload = {
                "srchNtnCd": "",
                "srchDateE": e_date,
                "orderSort": "DESC",
                "srchMttrFlowDtlCd": "",
                "srchIncmExp": "I",
                "srchHsCd": "",
                "orderBy": "realPrdctnQuty1",
                "srchMnrkndUnqCd": mnrl_code,
                "listCount": "100",
                "srchDatePE": prev_dt.strftime("%Y%m31"),
                "srchMttrFlowCd": "",
                "srchDateS": s_date,
                "page": "1",
                "srchTypeAW": "A",
                "srchCrtrYmd": "M",
                "srchDatePS": prev_dt.strftime("%Y%m01")
            }
            
            try:
                response = requests.post(TARGET_URL, data=payload, headers=HEADERS)
                if response.status_code != 200:
                    continue

                data = response.json()
                
                if "list" in data and data["list"]:
                    df_temp = pd.DataFrame(data["list"])
                    
                    # JSON 데이터에 맞춰 필드명 매핑
                    # 수입액: incmAmt, 수입중량: incmWeig, 전체수입액: sumIncmAmt
                    val_col = 'incmAmt' if 'incmAmt' in df_temp.columns else 'realPrdctnAmt1'
                    qty_col = 'incmWeig' if 'incmWeig' in df_temp.columns else 'realPrdctnQuty1'
                    
                    df_db = pd.DataFrame()
                    df_db['mineral_id'] = [m_id] * len(df_temp)
                    df_db['ntnCd'] = df_temp['ntnCd']
                    df_db['country_id'] = df_temp['ntnCd'].map(country_id_map)
                    df_db['date'] = month_dt.strftime("%Y-%m-01")
                    
                    # 숫자 변환
                    df_db['import_value'] = pd.to_numeric(df_temp[val_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    df_db['import_weight'] = pd.to_numeric(df_temp[qty_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                    
                    # 점유율 계산 (shre가 없으면 직접 계산: 수입액 / 총수입액 * 100)
                    if 'shre' in df_temp.columns:
                        df_db['import_share'] = pd.to_numeric(df_temp['shre'], errors='coerce').fillna(0)
                    elif 'sumIncmAmt' in df_temp.columns:
                        total_amt = pd.to_numeric(df_temp['sumIncmAmt'].iloc[0], errors='coerce')
                        df_db['import_share'] = (df_db['import_value'] / total_amt * 100) if total_amt > 0 else 0
                    else:
                        df_db['import_share'] = 0
                    
                    all_processed_data.append(df_db)
                    print(f"  > {month_dt.strftime('%Y-%m')} 완료 ({len(df_temp)}건)")
                else:
                    print(f"  > {month_dt.strftime('%Y-%m')} 데이터 없음")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  > 에러 ({month_dt.strftime('%Y-%m')}): {e}")
                
    save_to_db(all_processed_data, engine)


# 수집된 데이터 리스트를 DB에 저장하는 함수
def save_to_db(all_processed_data, engine):
    if not all_processed_data:
        print("\n❌ 저장할 데이터가 없습니다. (수집된 내역 없음)")
        return

    # 1. 데이터 통합
    final_df = pd.concat(all_processed_data, ignore_index=True)

    # 2. 필터링: 수입액(천USD)과 수입중량(톤)이 모두 1보다 큰 데이터만 남김
    # (0데이터 및 의미 없는 소액 데이터 제거)
    final_df = final_df[
        (final_df['import_value'] > 1) & 
        (final_df['import_weight'] > 1)
    ]

    # 3. 결측치 제거: 국가 매핑이 안 된 데이터(NaN)는 PK 제약조건 때문에 저장 불가
    final_df = final_df.dropna(subset=['country_id'])

    if final_df.empty:
        print("\n⚠️ 필터링 후 남은 데이터가 없습니다. (모든 데이터가 1 이하이거나 매핑 실패)")
        return

    # 4. 타입 변환 및 순서 정렬 (이미지 DB 구조 기준)
    try:
        final_df['country_id'] = final_df['country_id'].astype(int)
        final_df['mineral_id'] = final_df['mineral_id'].astype(int)
        
        # 이미지의 컬럼 순서: country_id, date, import_value, import_weight, import_share, mineral_id
        target_columns = [
            'country_id', 
            'date', 
            'import_value', 
            'import_weight', 
            'import_share', 
            'mineral_id'
        ]
        final_df = final_df[target_columns]
        
    except Exception as e:
        print(f"❌ 데이터 정리 중 오류 발생: {e}")
        return

    # 5. DB 저장 실행
    print("\n" + "="*60)
    print(f"📊 최종 {len(final_df)}행 데이터를 DB에 저장합니다...")
    print("="*60)
    
    try:
        final_df.to_sql('mineral_import', engine, if_exists='append', index=False)
        print("🚀 [성공] DB 저장이 완료되었습니다!")
    except Exception as e:
        print(f"❌ [실패] DB 저장 중 오류 발생: {e}")

