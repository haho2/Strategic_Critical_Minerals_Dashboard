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

# =========================
# 0. 사용자 설정
# =========================
KOMIS_URL = "https://www.komis.or.kr/Komis/RsrcPrice/ajax/getMnrlPrcByMnrkndUnqCd"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.komis.or.kr/",
}

MINERAL_CONFIG = {
    "리튬": {"code": "MNRL0001", "srchPrcCrtr": "773", "spcfct": "99.5"},
    "니켈": {"code": "MNRL0002", "srchPrcCrtr": "502"},
    "코발트": {"code": "MNRL0003", "srchPrcCrtr": "791", "spcfct": "99.8"},
    "망간": {"code": "MNRL0004", "srchPrcCrtr": "815", "spcfct": "75"},
    "흑연": {"code": "MNRL0005", "srchPrcCrtr": "801"},
    "네오디뮴": {"code": "MNRL1001", "srchPrcCrtr": "757", "spcfct": "99.5"},
    "디스프로슘": {"code": "MNRL1004", "srchPrcCrtr": "803", "spcfct": "99.5"},
    "터븀": {"code": "MNRL1005", "srchPrcCrtr": "806", "spcfct": "99.99"},
    "세륨": {"code": "MNRL1002", "srchPrcCrtr": "802", "spcfct": "99"},
    "란탄": {"code": "MNRL1003", "srchPrcCrtr": "813", "spcfct": "99.9"}
}

# =========================
# 1. DB 엔진 생성
# =========================
def get_engine(db_config: dict):
    print(f"[LOG] DB 엔진 생성 시도 중... (Host: {db_config.get('host')})")
    try:
        # DB.py의 키값(user, db)에 맞춰서 username, database 지정
        url = URL.create(
            "mysql+pymysql",
            username=db_config["user"],      # 'username' 대신 'user'
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["db"],        # 'database' 대신 'db'
            query={"charset": db_config["charset"]},
        )
        engine = create_engine(url, future=True)
        print("[LOG] DB 엔진 생성 완료")
        return engine
    except KeyError as e:
        print(f"[ERROR] DB 설정 키값이 맞지 않습니다: {e}")
        raise e

# =========================
# 2. DB 최신 날짜 확인
# =========================
def get_latest_dates(engine):
    print("[LOG] DB에서 광물별 최신 날짜 조회 중...")
    try:
        with engine.connect() as conn:
            mineral_rows = conn.execute(text("SELECT mineral_id, mineral_name FROM minerals")).mappings().all()
            latest_rows = conn.execute(text("""
                SELECT mineral_id, MAX(date) AS latest_date
                FROM mineral_prices
                GROUP BY mineral_id
            """)).mappings().all()

        mineral_id_map = {row["mineral_name"]: row["mineral_id"] for row in mineral_rows}
        latest_date_map = {name: None for name in mineral_id_map.keys()}

        id_to_name = {v: k for k, v in mineral_id_map.items()}
        for row in latest_rows:
            mineral_name = id_to_name.get(row["mineral_id"])
            if mineral_name:
                latest_date_map[mineral_name] = row["latest_date"]
        
        print(f"[LOG] 최신 날짜 조회 완료: {latest_date_map}")
        return mineral_id_map, latest_date_map
    except Exception as e:
        print(f"[ERROR] 최신 날짜 조회 중 오류: {e}")
        raise e

# =========================
# 3. 데이터 수집 (KOMIS API)
# =========================
def collect_all_minerals(latest_date_map: dict):
    today = date.today()
    collected_rows = []
    print(f"[LOG] 데이터 수집 시작 (기준일: {today})")

    def _extract_rows(obj):
        result = []
        if isinstance(obj, dict):
            if "crtrYmd" in obj and "cmercPrc" in obj:
                result.append(obj)
            for value in obj.values():
                result.extend(_extract_rows(value))
        elif isinstance(obj, list):
            for item in obj:
                result.extend(_extract_rows(item))
        return result

    session = requests.Session()
    session.headers.update(HEADERS)

    for mineral_name, cfg in MINERAL_CONFIG.items():
        latest_date = latest_date_map.get(mineral_name)
        if latest_date is None:
            start_date = date(2018, 1, 1)
        else:
            # DB 데이터가 date 객체인지 string인지 확인 후 계산
            if isinstance(latest_date, str):
                latest_date = datetime.strptime(latest_date, "%Y-%m-%d").date()
            start_date = latest_date + timedelta(days=1)

        if start_date > today:
            print(f"[SKIP] {mineral_name}: 이미 최신 데이터 보유 중 ({latest_date})")
            continue

        payload = {
            "mnrkndUnqRadioCd": cfg["code"],
            "srchMnrkndUnqCd": cfg["code"],
            "srchPrcCrtr": cfg["srchPrcCrtr"],
            "srchAvgOpt": "DAY",
            "srchField": "month",
            "srchStartDate": start_date.strftime("%Y%m"),
            "srchEndDate": today.strftime("%Y%m"),
            "lmeInvt": "Y",
        }
        if "spcfct" in cfg: payload["spcfct"] = cfg["spcfct"]

        try:
            resp = session.post(KOMIS_URL, data=payload, timeout=30)
            resp.raise_for_status()
            full_res = resp.json()
            
            # [수정] 재귀 함수 대신 명확한 경로(defaultMnrl)에서 추출
            # 응답 구조에 따라 full_res['data']['defaultMnrl'] 또는 full_res['defaultMnrl'] 확인
            rows = full_res.get("data", {}).get("defaultMnrl", [])
            
            if not rows: # 만약 data 아래에 없다면 루트에서 확인
                rows = full_res.get("defaultMnrl", [])

            print(f"[COLLECT] {mineral_name}: {len(rows)}건 수집됨")
            
            for row in rows:
                row["mineral_name"] = mineral_name
                collected_rows.append(row)
                
        except Exception as e:
            print(f"[ERROR] {mineral_name} 수집 실패: {e}")

    return pd.DataFrame(collected_rows)

# =========================
# 4. DB 형식에 맞게 전처리
# =========================
def preprocess_to_db_format(raw_df: pd.DataFrame, mineral_id_map: dict, latest_date_map: dict):
    if not raw_df.empty:
        print(f"🔍 [DEBUG] 첫 번째 데이터 샘플: {raw_df.iloc[0].to_dict()}")
    if raw_df.empty:
        print("[LOG] 전처리할 데이터가 없습니다.")
        return pd.DataFrame()

    df = raw_df.copy()

    # [수정] 숫자에 포함된 콤마(,) 제거 및 데이터 정제 함수
    def clean_numeric(value):
        if pd.isna(value) or value == "" or value == "-":
            return 0
        # 문자열인 경우 콤마 제거 후 숫자로 변환
        if isinstance(value, str):
            value = value.replace(",", "").strip()
        try:
            return float(value)
        except ValueError:
            return 0

    # 1. 날짜 처리
    df["date"] = pd.to_datetime(df["crtrYmd"], format="%Y%m%d", errors="coerce").dt.date

    # 2. 숫자형 데이터 처리 (안전하게 변환)
    # KOMIS API의 키값이 대소문자를 가리거나 다를 수 있으므로 확인 필요
    price_col = "cmercPrc"
    change_col = "flctnPrc"     # 변화량
    rate_col = "flctnPrcnt"    # 변화율

    df["price"] = df[price_col].apply(clean_numeric)
    
    # 컬럼이 존재할 때만 처리, 없으면 0으로 채움
    if change_col in df.columns:
        df["daily_change"] = df[change_col].apply(clean_numeric)
    else:
        print(f"[WARN] {change_col} 컬럼이 API 응답에 없습니다.")
        df["daily_change"] = 0

    if rate_col in df.columns:
        df["daily_change_rate"] = df[rate_col].apply(clean_numeric)
    else:
        print(f"[WARN] {rate_col} 컬럼이 API 응답에 없습니다.")
        df["daily_change_rate"] = 0

    # 3. ID 매핑 및 결측치 제거
    df["mineral_id"] = df["mineral_name"].map(mineral_id_map)
    df = df.dropna(subset=["mineral_id", "date"])

    # 4. 중복 제거 (최신 데이터 우선)
    df = df.drop_duplicates(subset=["mineral_id", "date"], keep="last")

    # 5. 기존 DB 날짜와 비교하여 신규 데이터만 필터링
    keep_rows = []
    for _, row in df.iterrows():
        m_name = row["mineral_name"]
        l_date = latest_date_map.get(m_name)
        
        if l_date is None:
            keep_rows.append(True)
        else:
            # l_date가 string일 경우를 대비해 date 객체로 변환 후 비교
            current_l_date = pd.to_datetime(l_date).date() if not isinstance(l_date, (date, datetime)) else l_date
            keep_rows.append(row["date"] > current_l_date)

    df = df[keep_rows].copy()
    
    # 6. 최종 컬럼 정리
    df = df[["mineral_id", "date", "price", "daily_change", "daily_change_rate"]]
    print(f"[LOG] 전처리 완료: {len(df)}건의 유효 데이터 추출됨")
    
    return df

# =========================
# 5. DB 저장
# =========================
def save_to_db(engine, df: pd.DataFrame):
    if df.empty:
        print("[LOG] 저장할 데이터가 없습니다 (Empty DataFrame)")
        return 0

    print(f"[LOG] DB 저장 시작 (총 {len(df)}건)")
    sql = text("""
        INSERT INTO mineral_prices (
            mineral_id, date, price, daily_change, daily_change_rate
        ) VALUES (
            :mineral_id, :date, :price, :daily_change, :daily_change_rate
        )
        ON DUPLICATE KEY UPDATE
            price = VALUES(price),
            daily_change = VALUES(daily_change),
            daily_change_rate = VALUES(daily_change_rate)
    """)

    records = df.to_dict(orient="records")
    try:
        with engine.begin() as conn:
            conn.execute(sql, records)
        print(f"[LOG] DB 저장 성공: {len(records)}건 완료")
        return len(records)
    except Exception as e:
        print(f"[ERROR] DB 저장 중 오류 발생: {e}")
        raise e

# =========================
# 실행 함수
# =========================
def run_mineral_sync():
    print("\n" + "="*50)
    print(f"[START] 광물 동기화 프로세스 시작 ({datetime.now()})")
    print("="*50)
    
    try:
        engine = get_engine(db_config)
        mineral_id_map, latest_date_map = get_latest_dates(engine)
        
        raw_df = collect_all_minerals(latest_date_map)
        
        if not raw_df.empty:
            processed_df = preprocess_to_db_format(raw_df, mineral_id_map, latest_date_map)
            saved_count = save_to_db(engine, processed_df)
            print(f"[FINISH] 동기화 프로세스 정상 종료 (갱신: {saved_count}건)")
            return saved_count
        else:
            print("[FINISH] 모든 데이터가 이미 최신입니다. 추가 저장 없음.")
            return 0
    except Exception as e:
        print(f"[FATAL ERROR] 동기화 중단됨: {e}")
        return f"에러 발생: {e}"
