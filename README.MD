## 시연
```url
[https://strategiccriticalmineralsdashboard.streamlit.app/](https://strategiccriticalmineralsdashboard.streamlit.app/)
```



## 필요한 라이브러리 설치
```bash
pip install streamlit pandas sqlalchemy pymysql plotly requests beautifulsoup4 python-dateutil konlpy streamlit_autorefresh
```

추가로 환경에 따라 아래 패키지가 필요할 수 있습니다.
```bash
pip install lxml
```

## 패키지 기록
```bash
pip freeze > requirements.txt
```

예시 `requirements.txt`
```txt
beautifulsoup4==4.14.3
folium==0.20.0
konlpy==0.6.0
numpy==2.4.3
openpyxl
pandas==2.3.3
plotly==6.6.0
PyMySQL==1.1.2
requests==2.32.5
smmap==5.0.3
SQLAlchemy==2.0.48
streamlit==1.55.0
streamlit-folium==0.27.0
toml==0.10.2
urllib3==2.6.3
streamlit-autorefresh
dotenv

```

## MySQL DB 준비
1) DB 생성
```sql
CREATE DATABASE datax
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

2) 기본 데이터 예시
```sql
INSERT INTO minerals (mineral_name, category) VALUES 
('리튬', '이차전지 광물'),
('니켈', '이차전지 광물'),
('코발트', '이차전지 광물'),
('망간', '이차전지 광물'),
('흑연', '이차전지 광물'),
('네오디뮴', '희토류'),
('디스프로슘', '희토류'),
('터븀', '희토류'),
('세륨', '희토류'),
('란탄', '희토류'),
('희토류', '희토류');
```

## 프로젝트 폴더 구조
```text
mineral_dashboard/
│
├─ main.py
├─ README.md
├─ DB.py
├─ requirements.txt
├─ packeges.txt
├─ .gitignore
├─ .env.example
│
├─ .streamlit
│  ├─ config.toml
│
├─ utils/
│  ├─ draw_news.py
│  └─ mineral_fnt.py
│
├─ pages/
│  ├─ info_sync.py
│  ├─ mineral_import_sync.py
│  ├─ mineral_price_sync.py
│  └─ news_sync.py
│  └─ all_minerals...
│
├─ css_def/
│  ├─ dashboard_css
│  ├─ dashboard_def
│  ├─ main.css
│  ├─ mineral_card.css
│  ├─ hot_topics.css
│  ├─ recent_news.css
│  └─ plot_wrapper.css

```

## 환경설정
```bash
conda create -n streamlit python=3.13 -y
conda activate streamlit
```

## DB 연결 설정
`DB.py`에서 MySQL 접속 정보를 관리합니다.

```python
db_config = {
    "host": host,
    "port": 3306,
    "user": user,
    "password": password,
    "db": db,
    "charset": "utf8mb4"
}
```

## 실행 방법
```bash
streamlit run main.py
```

## 메인 화면 구성
메인 화면은 다음 영역으로 구성됩니다.

1. 핵심광물 시세 카드
2. 위험 키워드 발생 추이(최근 30일)
3. 광물 핫토픽 TOP3
4. 최근 주요뉴스
5. 핵심광물 이슈 발생 빈도(최근 7일)

## 파일별 역할

### main.py
- Streamlit 메인 대시보드 실행 파일
- 핵심광물 카드, 위험 키워드 추이, 핫토픽, 최근 뉴스, 이슈 빈도 영역 구성
- CSS 파일 로드 및 정보 동기화 버튼 처리

### utils/mineral_fnt.py
- DB 데이터 조회 함수 모음
- 핵심광물 카드 렌더링
- 핫토픽 패널 렌더링
- 최근 뉴스 패널 렌더링
- Plotly wrapper 렌더링
- 뉴스/키워드 전처리 함수

### utils/draw_news.py
- 핵심광물 이슈 발생 빈도 막대 차트 생성

### pages/info_sync.py
- 전체 동기화 실행
- 가격 / 수입 / 뉴스 동기화 모듈 호출

### pages/mineral_price_sync.py
- KOMIS 가격 데이터 수집
- 광물 가격 데이터 전처리 및 DB 저장

### pages/mineral_import_sync.py
- KOMIS 수입 데이터 수집
- 국가별 수입량/수입액/점유율 데이터 저장

### pages/news_sync.py
- Daum 뉴스 검색 기반 기사 수집
- 기사 본문 분석
- 광물 키워드 / 리스크 키워드 분류
- news 테이블 저장

### css_def/*.css
- 대시보드 UI 스타일 정의
- 메인 전역 스타일 / 카드 / 핫토픽 / 뉴스 / Plotly wrapper 분리 관리

## 데이터 동기화
대시보드 상단의 `정보 동기화` 버튼을 누르면 아래 작업이 순차 실행됩니다.

1. 광물 가격 동기화
2. 광물 수입 동기화
3. 뉴스 동기화

또는 필요 시 각 파일을 개별 실행해서 수동 점검할 수 있습니다.

## 주요 사용 데이터
현재 코드 기준 주요 광물은 아래와 같습니다.

- 리튬
- 니켈
- 코발트
- 망간
- 흑연
- 네오디뮴
- 디스프로슘
- 터븀
- 세륨
- 란탄
