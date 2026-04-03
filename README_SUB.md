# 🛡️ K-Defense 전략물자 공급망 리스크 탐지 시스템

국방 핵심 전략물자(니켈, 리튬, 디스프로슘 등)의 **가격·수입량·위험 키워드·뉴스·국가별 의존도**를 실시간으로 모니터링하는 Streamlit 대시보드입니다.

---

## 📁 프로젝트 구조

```
project/
├── main.py                    # 메인 진입점 (광물 선택 홈 화면)
├── pages/
│   ├── nickel_page.py         # 니켈 대시보드
│   ├── lithium_page.py        # 리튬 대시보드
│   └── dysprosium_page.py     # 디스프로슘 + 희토류 대시보드
├── css_def/
│   ├── dashboard_css.py       # 전체 CSS 스타일 주입
│   └── dashboard_def.py       # 공통 상수 / 함수 / DB 로드 함수
├── DB/
│   └── DB.py                  # get_connection() - MySQL 연결
└── .streamlit/
    └── secrets.toml           # DB 접속 정보 (git 제외)
```

---

## 🖥️ 화면 구성

각 광물 페이지는 **3개 컬럼(col1 / col2 / col3)** 으로 구성됩니다.

| 컬럼 | 내용 |
|------|------|
| **col1** | 광물명 표시 / 가격·수입량 탭 전환 / 최근 7개월 추이 라인차트 / 국내 현황 테이블 |
| **col2** | 글로벌 지도 (choropleth) / 국가별 수입 의존도 도넛차트 |
| **col3** | 최근 주요뉴스 5건 (스크롤) / 위험 키워드 도넛차트 |

상단 타이틀 버튼(`🛡️ 국방 핵심광물 공급망 리스크 탐지 시스템`) 클릭 시 `main.py`로 이동합니다.

---

## 📄 파일 설명

### `css_def/dashboard_css.py`

전체 페이지 CSS를 `inject_css(st)` 함수로 주입합니다. `st`를 파라미터로 받아 circular import를 방지합니다.

- 다크 테마 (`#0A0C10` 배경)
- 패널, 버튼, 탭, 테이블, 뉴스 아이템 스타일 포함
- Pretendard 폰트 적용

```python
from css_def.dashboard_css import inject_css
inject_css(st)
```

---

### `css_def/dashboard_def.py`

`streamlit` import 없는 순수 Python 모듈입니다. circular import를 완전히 차단합니다.

**① 공통 상수**

| 상수 | 값 | 설명 |
|------|----|------|
| `CHART_H` | 292 | Plotly 라인차트 높이 (px) |
| `TABLE_H` | 324 | 테이블 스크롤 영역 높이 (px) |
| `KEYWORD_CHART_H` | 329 | 위험 키워드 도넛차트 높이 (px) |
| `NEWS_SCROLL_H` | 350 | 뉴스 스크롤 영역 높이 (px) |
| `COUNTRY_CHART_H` | 333 | 국가별 의존도 도넛차트 높이 (px) |
| `MAP_H` | 330 | 글로벌 지도 높이 (px) |
| `TRANSPARENT` | `"rgba(0,0,0,0)"` | Plotly 투명 배경값 |
| `COUNTRY_MAP` | dict | 국가명 한→영 매핑 (30개국) |

**② 공통 함수**

| 함수 | 설명 |
|------|------|
| `format_date_col(df, col)` | 날짜 컬럼을 `YYYY-MM-DD` 문자열로 포맷 |
| `nice_dtick(min, max, ticks)` | Plotly y축 눈금 간격 자동 계산 |
| `make_category_date_labels(df, col, mode)` | 차트용 날짜 레이블 생성 (`price`: MM-DD / `import`: YYYY-MM) |
| `style_category_xaxis(fig)` | Plotly x축 카테고리 스타일 적용 |
| `add_horizontal_yaxis_title(fig, text, x)` | y축 제목을 가로 방향으로 표시 |
| `render_delta_html(value, label)` | 등락률 HTML 생성 (▲ 빨강 / ▼ 파랑) |
| `render_scrollable_table_html(df, ...)` | 스크롤 가능한 HTML 테이블 생성 |
| `normalize_risk_keyword(risk)` | 위험 키워드 정규화 (한글 매핑) |
| `classify_news_badge(text)` | 뉴스 위험도 배지 분류 (위험 / 주의 / 경계) |
| `build_news_desc(row)` | 뉴스 설명 텍스트 자동 생성 |
| `clean_text(value, max_len)` | 텍스트 정리 및 말줄임 처리 |

**③ DB 로드 함수** (`get_connection`을 파라미터로 받음, `@st.cache_data` 없이 순수하게 동작)

| 함수 | 반환값 | 설명 |
|------|--------|------|
| `load_price_data(mineral_name, get_connection)` | `(mineral_row, chart_df, table_df)` | 광물 가격 데이터 로드 |
| `load_import_data(mineral_name, get_connection)` | `(mineral_row, chart_df, country_df, table_df)` | 수입량 및 국가별 의존도 로드 |
| `load_news_keyword_data(keywords, get_connection)` | `DataFrame` | 위험 키워드 집계 (상위 5개) |
| `load_news_data(keywords, get_connection)` | `DataFrame` | 최근 뉴스 5건 로드 |

---

### `pages/nickel_page.py` / `pages/lithium_page.py`

단일 광물 대시보드입니다. 광물 설정만 다르고 나머지 구조는 동일합니다.

```python
# nickel_page.py
MINERAL_NAME          = "니켈"
MINERAL_ENG_NAME      = "NICKEL"
NEWS_MINERAL_KEYWORDS = ("니켈",)

# lithium_page.py
MINERAL_NAME          = "리튬"
MINERAL_ENG_NAME      = "LITHIUM"
NEWS_MINERAL_KEYWORDS = ("리튬",)
```

### `pages/dysprosium_page.py`

가격(디스프로슘)과 수입량(희토류)을 **서로 다른 광물**로 분리하여 조회하는 복합 대시보드입니다.

```python
PRICE_MINERAL_NAME     = "디스프로슘"
IMPORT_MINERAL_NAME    = "희토류"
NEWS_MINERAL_KEYWORDS  = ("디스프로슘", "희토류")
```

---

## ⚙️ 실행 방법

### 1. 환경 설치

```bash
conda activate streamlit
pip install streamlit plotly pandas pymysql
```

### 2. DB 설정

`.streamlit/secrets.toml` 파일에 DB 접속 정보를 입력합니다.

```toml
[mysql]
host     = "localhost"
port     = 3306
database = "your_db"
user     = "your_user"
password = "your_password"
```

### 3. 실행

```bash
streamlit run main.py
```

---

## 🗄️ DB 테이블 구조

| 테이블 | 주요 컬럼 | 설명 |
|--------|-----------|------|
| `minerals` | `mineral_id`, `mineral_name`, `category` | 광물 기본 정보 |
| `mineral_prices` | `mineral_id`, `date`, `price` | 광물 일별 가격 |
| `mineral_import` | `mineral_id`, `country_id`, `date`, `import_weight`, `import_share` | 국가별 수입량 및 의존도 |
| `countries` | `country_id`, `country_name` | 국가 정보 |
| `news` | `id`, `date`, `title`, `source_name`, `content`, `url`, `mineral_keyword`, `risk_keyword` | 뉴스 (JSON 배열 컬럼 포함) |

> `news.mineral_keyword`, `news.risk_keyword` 는 JSON 배열로 저장됩니다. (`JSON_TABLE`로 파싱)

---

## 🔄 자동 새로고침

`streamlit-autorefresh` 패키지 대신 세션 상태 기반으로 **5분마다** 자동 새로고침합니다.

```python
import time
if "_last_refresh" not in st.session_state:
    st.session_state._last_refresh = time.time()
if time.time() - st.session_state._last_refresh > 300:
    st.session_state._last_refresh = time.time()
    st.rerun()
```

> `streamlit-autorefresh`는 Streamlit 1.x와 circular import 충돌이 있어 사용하지 않습니다.

---

## ➕ 새 광물 페이지 추가 방법

1. `pages/` 폴더에 새 파일 생성 (예: `cobalt_page.py`)
2. `nickel_page.py`를 복사한 뒤 상단 광물 설정만 수정

```python
MINERAL_NAME          = "코발트"
MINERAL_ENG_NAME      = "COBALT"
NEWS_MINERAL_KEYWORDS = ("코발트",)
```

CSS, 공통 함수, DB 로직은 `css_def/` 모듈을 그대로 사용하므로 별도 수정이 필요 없습니다.

---

## 🛠️ 기술 스택

| 항목 | 버전 |
|------|------|
| Python | 3.10+ |
| Streamlit | 1.55.0 |
| Plotly | 5.x |
| Pandas | 2.x |
| MySQL | 8.0+ |
| PyMySQL | 최신 |
