import ast
import html
import os
import urllib.parse

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_DIR = os.path.join(ROOT_DIR, "css_def")

SUBPAGE_ROUTE_MAP = {
    "리튬": "리튬",
    "니켈": "니켈",
    "코발트": "코발트",
    "망간": "망간",
    "흑연": "흑연",
    "네오디뮴": "네오디뮴",
    "디스프로슘": "디스프로슘",
    "터븀": "터븀",
    "세륨": "세륨",
    "란탄": "란탄",
}
DEFAULT_SUBPAGE_ROUTE = "sub"

TARGET_MINERAL_ORDER = [
    ("네오디뮴", ["neodymium", "네오디뮴"]),
    ("디스프로슘", ["dysprosium", "디스프로슘"]),
    ("터븀", ["terbium", "터븀"]),
    ("세륨", ["cerium", "세륨"]),
    ("란탄", ["lanthanum", "란탄"]),
    ("리튬", ["lithium", "리튬"]),
    ("니켈", ["nickel", "니켈"]),
    ("코발트", ["cobalt", "코발트"]),
    ("망간", ["manganese", "망간"]),
    ("흑연", ["graphite", "흑연"]),
]

MINERAL_META = {
    "네오디뮴": {"en": "NEODYMIUM"},
    "디스프로슘": {"en": "DYSPROSIUM"},
    "터븀": {"en": "TERBIUM"},
    "세륨": {"en": "CERIUM"},
    "란탄": {"en": "LANTHANUM"},
    "리튬": {"en": "LITHIUM"},
    "니켈": {"en": "NICKEL"},
    "코발트": {"en": "COBALT"},
    "망간": {"en": "MANGANESE"},
    "흑연": {"en": "GRAPHITE"},
}

TARGET_MINERALS = [name for name, _ in TARGET_MINERAL_ORDER]
MINERAL_ALIAS_MAP = {name: aliases for name, aliases in TARGET_MINERAL_ORDER}
ORDER_MAP = {name: idx for idx, (name, _) in enumerate(TARGET_MINERAL_ORDER)}


def get_connection():
    from DB.DB import get_connection as _get_connection
    return _get_connection()


def load_css_file(filename: str, replacements: dict | None = None) -> str:
    path = os.path.join(CSS_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            css = f.read()
        for key, value in (replacements or {}).items():
            css = css.replace(key, str(value))
        return css
    except Exception as e:
        st.error(f"CSS 파일 로드 오류: {e}")
        return ""


def parse_mixed_datetime(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce")
    s_str = series.astype(str).str.strip()

    mask_14 = dt.isna() & s_str.str.fullmatch(r"\d{14}", na=False)
    if mask_14.any():
        dt.loc[mask_14] = pd.to_datetime(s_str.loc[mask_14], format="%Y%m%d%H%M%S", errors="coerce")

    mask_8 = dt.isna() & s_str.str.fullmatch(r"\d{8}", na=False)
    if mask_8.any():
        dt.loc[mask_8] = pd.to_datetime(s_str.loc[mask_8], format="%Y%m%d", errors="coerce")

    mask_unix_sec = dt.isna() & s_str.str.fullmatch(r"\d{10}", na=False)
    if mask_unix_sec.any():
        dt.loc[mask_unix_sec] = pd.to_datetime(
            pd.to_numeric(s_str.loc[mask_unix_sec], errors="coerce"),
            unit="s",
            errors="coerce",
        )

    mask_unix_ms = dt.isna() & s_str.str.fullmatch(r"\d{13}", na=False)
    if mask_unix_ms.any():
        dt.loc[mask_unix_ms] = pd.to_datetime(
            pd.to_numeric(s_str.loc[mask_unix_ms], errors="coerce"),
            unit="ms",
            errors="coerce",
        )

    return dt


def normalize_keyword_text(value) -> list[str]:
    if pd.isna(value):
        return []

    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            items = parsed
        elif parsed is None:
            items = []
        else:
            items = [parsed]
    except Exception:
        cleaned = text.replace("[", "").replace("]", "").replace('"', "").replace("'", "")
        items = cleaned.split(",")

    result = []
    seen = set()
    for item in items:
        v = str(item).strip()
        if not v or v.lower() == "nan":
            continue
        key = v.lower()
        if key not in seen:
            seen.add(key)
            result.append(v)
    return result


def build_subpage_url(mineral_name: str) -> str:
    route_name = SUBPAGE_ROUTE_MAP.get(mineral_name, DEFAULT_SUBPAGE_ROUTE)
    return f"/{route_name}?mineral={urllib.parse.quote(mineral_name)}"


def build_mineral_card(mineral_name, price, change_rate):
    meta = MINERAL_META[mineral_name]
    m_price = pd.to_numeric(price, errors="coerce")
    m_change = pd.to_numeric(change_rate, errors="coerce")

    return {
        "en": meta["en"],
        "price_text": "-" if pd.isna(m_price) else f"${m_price:,.2f}",
        "unit_text": "/ t",
        "delta": "-" if pd.isna(m_change) else f"{abs(m_change):.2f}%",
        "dir": "flat" if pd.isna(m_change) else "up" if m_change > 0 else "down" if m_change < 0 else "flat",
    }


def get_empty_cards():
    return {mineral: build_mineral_card(mineral, None, None) for mineral in TARGET_MINERALS}


@st.cache_data(ttl=300, show_spinner=False)
def load_each_mineral_individually():
    result = get_empty_cards()

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            for mineral_name in TARGET_MINERALS:
                query = f"""
                SELECT
                    mp.price,
                    mp.daily_change_rate,
                    mp.date
                FROM datax.mineral_prices AS mp
                INNER JOIN minerals AS m
                    ON mp.mineral_id = m.mineral_id
                WHERE m.mineral_name LIKE '%{mineral_name}%'
                ORDER BY mp.date DESC
                LIMIT 2
                """
                cursor.execute(query)
                rows = cursor.fetchall()

                if not rows:
                    continue

                latest_row = rows[0]
                latest_price = latest_row.get("price")
                latest_rate = latest_row.get("daily_change_rate")

                computed_rate = None
                latest_price_num = pd.to_numeric(latest_price, errors="coerce")

                if len(rows) >= 2:
                    prev_price_num = pd.to_numeric(rows[1].get("price"), errors="coerce")
                    if pd.notna(latest_price_num) and pd.notna(prev_price_num) and float(prev_price_num) != 0:
                        computed_rate = ((float(latest_price_num) - float(prev_price_num)) / float(prev_price_num)) * 100

                change_rate = computed_rate if computed_rate is not None else latest_rate

                result[mineral_name] = build_mineral_card(
                    mineral_name=mineral_name,
                    price=latest_price,
                    change_rate=change_rate,
                )

        conn.close()

    except Exception as e:
        st.error(f"광물 카드 데이터 조회 오류: {e}")

    return result


@st.cache_data(ttl=300, show_spinner=False)
def load_recent_news_from_db(limit=5):
    empty_df = pd.DataFrame(columns=["title", "content", "mineral_keyword", "risk_keyword", "date", "date_str"])

    query = f"""
    SELECT
        title,
        content,
        mineral_keyword,
        risk_keyword,
        date
    FROM datax.news
    WHERE title IS NOT NULL
      AND TRIM(title) <> ''
    ORDER BY date DESC
    LIMIT {int(limit)}
    """

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return empty_df

        news_df = pd.DataFrame(rows)
        if 0 in news_df.columns:
            news_df.columns = ["title", "content", "mineral_keyword", "risk_keyword", "date"][: len(news_df.columns)]

        news_df = news_df.reindex(columns=["title", "content", "mineral_keyword", "risk_keyword", "date"], fill_value="").copy()
        news_df["title"] = news_df["title"].fillna("-").astype(str).str.strip()
        news_df["content"] = (
            news_df["content"]
            .fillna("")
            .astype(str)
            .str.strip()
            .apply(lambda x: x[: x.find("다.") + 2] if "다." in x else x)
        )
        news_df["mineral_keyword"] = news_df["mineral_keyword"].fillna("").astype(str).str.strip()
        news_df["risk_keyword"] = news_df["risk_keyword"].fillna("").astype(str).str.strip()
        news_df["date"] = parse_mixed_datetime(news_df["date"])
        news_df["date_str"] = news_df["date"].dt.strftime("%Y-%m-%d").fillna("-")
        return news_df.sort_values("date", ascending=False, na_position="last").reset_index(drop=True)
    except Exception as e:
        st.error(f"최근 뉴스 DB 조회 오류: {e}")
        return empty_df


@st.cache_data(ttl=300, show_spinner=False)
def load_risk_keyword_trend_from_db(days=30, top_n=5):
    empty_df = pd.DataFrame(columns=["날짜"])

    query = """
    SELECT
        date,
        risk_keyword
    FROM datax.news
    WHERE risk_keyword IS NOT NULL
      AND TRIM(risk_keyword) <> ''
      AND date IS NOT NULL
    ORDER BY date ASC
    """

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return empty_df

        trend_raw_df = pd.DataFrame(rows)
        if 0 in trend_raw_df.columns:
            trend_raw_df.columns = ["date", "risk_keyword"][: len(trend_raw_df.columns)]

        trend_raw_df = trend_raw_df.reindex(columns=["date", "risk_keyword"], fill_value="").copy()
        trend_raw_df["date"] = parse_mixed_datetime(trend_raw_df["date"])
        trend_raw_df = trend_raw_df.dropna(subset=["date"]).copy()
        if trend_raw_df.empty:
            return empty_df

        trend_raw_df["날짜"] = pd.to_datetime(trend_raw_df["date"].dt.date)
        max_date = trend_raw_df["날짜"].max()
        min_date = max_date - pd.Timedelta(days=days - 1)
        trend_raw_df = trend_raw_df[trend_raw_df["날짜"] >= min_date].copy()
        if trend_raw_df.empty:
            return empty_df

        exploded_rows = []
        for _, row in trend_raw_df.iterrows():
            for kw in normalize_keyword_text(row["risk_keyword"]):
                kw_clean = str(kw).strip()
                if kw_clean:
                    exploded_rows.append({"날짜": row["날짜"], "risk_kw": kw_clean})

        if not exploded_rows:
            return empty_df

        exploded_df = pd.DataFrame(exploded_rows)
        top_keywords = exploded_df["risk_kw"].value_counts().head(top_n).index.tolist()
        exploded_df = exploded_df[exploded_df["risk_kw"].isin(top_keywords)].copy()
        if exploded_df.empty:
            return empty_df

        grouped_df = exploded_df.groupby(["날짜", "risk_kw"]).size().reset_index(name="count")
        df_trend = grouped_df.pivot_table(
            index="날짜",
            columns="risk_kw",
            values="count",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()

        full_dates = pd.date_range(start=min_date, end=max_date, freq="D")
        df_trend = df_trend.set_index("날짜").reindex(full_dates, fill_value=0).reset_index()
        df_trend = df_trend.rename(columns={"index": "날짜"})
        return df_trend.sort_values("날짜").reset_index(drop=True)
    except Exception as e:
        st.error(f"위험 키워드 발생 추이 조회 오류: {e}")
        return empty_df


@st.cache_data(ttl=300, show_spinner=False)
def load_news_window(days=7):
    query = f"""
    SELECT
        date,
        mineral_keyword,
        risk_keyword
    FROM datax.news
    WHERE date IS NOT NULL
      AND date >= NOW() - INTERVAL {int(days)} DAY
      AND (
            (mineral_keyword IS NOT NULL AND TRIM(mineral_keyword) <> '')
         OR (risk_keyword IS NOT NULL AND TRIM(risk_keyword) <> '')
      )
    """

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        conn.close()

        if not rows:
            return pd.DataFrame(columns=["date", "mineral_keyword", "risk_keyword"])

        df = pd.DataFrame(rows)
        if 0 in df.columns:
            df.columns = ["date", "mineral_keyword", "risk_keyword"][: len(df.columns)]

        return df.reindex(columns=["date", "mineral_keyword", "risk_keyword"], fill_value="").copy()
    except Exception as e:
        st.error(f"최근 {days}일 뉴스 데이터 조회 오류: {e}")
        return pd.DataFrame(columns=["date", "mineral_keyword", "risk_keyword"])


@st.cache_data(ttl=300, show_spinner=False)
def _build_issue_summary(days=7):
    df = load_news_window(days=days)
    issue_counts = {name: 0 for name in TARGET_MINERALS}
    risk_counter_map = {name: {} for name in TARGET_MINERALS}

    if df.empty:
        return issue_counts, risk_counter_map

    for _, row in df.iterrows():
        mineral_text = str(row["mineral_keyword"]).lower()
        matched = []
        for mineral_name, aliases in TARGET_MINERAL_ORDER:
            if any(alias.lower() in mineral_text for alias in aliases):
                matched.append(mineral_name)

        if not matched:
            continue

        risk_keywords = normalize_keyword_text(row["risk_keyword"])
        for mineral_name in matched:
            issue_counts[mineral_name] += 1
            for kw in risk_keywords:
                kw = str(kw).strip()
                if kw:
                    current = risk_counter_map[mineral_name].get(kw, 0)
                    risk_counter_map[mineral_name][kw] = current + 1

    return issue_counts, risk_counter_map


@st.cache_data(ttl=300, show_spinner=False)
def get_issue_frequency_df(days=7):
    issue_counts, _ = _build_issue_summary(days=days)

    df_issue = pd.DataFrame(
        [{"mineral_display": name, "cnt": issue_counts.get(name, 0)} for name in TARGET_MINERALS]
    )
    df_issue["sort_order"] = df_issue["mineral_display"].map(ORDER_MAP)
    return df_issue.sort_values(["cnt", "sort_order"], ascending=[False, True]).reset_index(drop=True)[
        ["mineral_display", "cnt"]
    ]


@st.cache_data(ttl=300, show_spinner=False)
def get_top_risk_keywords_by_mineral(mineral_name, days=7, top_n=3):
    _, risk_counter_map = _build_issue_summary(days=days)
    counter = risk_counter_map.get(mineral_name, {})
    if not counter:
        return "-"
    top_keywords = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return ", ".join([kw for kw, _ in top_keywords]) if top_keywords else "-"


def build_risk_keywords_text(risk_keyword):
    keywords = normalize_keyword_text(risk_keyword)[:3]
    return ", ".join(keywords) if keywords else "키워드 없음"


def build_mineral_keywords_text(mineral_keyword):
    keywords = normalize_keyword_text(mineral_keyword)
    return ", ".join(keywords) if keywords else "광물 없음"


def render_clickable_mineral_card(name, data):
    if data["dir"] == "up":
        d_icon = "▲"
        d_color = "#FF5A5F"
    elif data["dir"] == "down":
        d_icon = "▼"
        d_color = "#2F80FF"
    else:
        d_icon = "•"
        d_color = "#A0A7B4"

    css = load_css_file("mineral_card.css", {"__DELTA_COLOR__": d_color})
    safe_target_url = html.escape(build_subpage_url(name), quote=True)
    safe_name = html.escape(str(name))
    safe_price = html.escape(str(data["price_text"]))
    safe_unit = html.escape(str(data["unit_text"]))
    safe_en = html.escape(str(data["en"]))
    safe_delta = html.escape(str(data["delta"]))

    card_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <style>{css}</style>
        <script>
            function openMineralPage(url) {{
                try {{
                    window.open(url, "_blank", "noopener,noreferrer");
                }} catch (e) {{
                    window.location.href = url;
                }}
            }}
        </script>
    </head>
    <body>
        <a
            href="{safe_target_url}"
            target="_blank"
            rel="noopener noreferrer"
            class="card-link"
            onclick="openMineralPage('{safe_target_url}'); return false;"
        >
            <div class="card">
                <div class="top-row">
                    <div class="name">{safe_name}</div>
                    <div class="price-wrap">
                        <span class="price">{safe_price}</span>
                    </div>
                </div>
                <div class="bottom-row">
                    <div class="en">{safe_en}</div>
                    <div class="right">
                        <span class="delta">{d_icon} {safe_delta}</span>
                    </div>
                </div>
            </div>
        </a>
    </body>
    </html>
    """
    components.html(card_html, height=96, scrolling=False)


def render_plotly_with_top_modebar(fig, height=500):
    css = load_css_file("plot_wrapper.css", {"__HEIGHT__": f"{height}px"})
    config = {
        "displayModeBar": True,
        "displaylogo": False,
        "responsive": True,
        "scrollZoom": True,
        "doubleClick": "reset",
        "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"],
    }
    plot_html = fig.to_html(include_plotlyjs="cdn", full_html=False, config=config)

    wrapped_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <style>{css}</style>
    </head>
    <body>
        <div class="plot-wrap">{plot_html}</div>
    </body>
    </html>
    """
    components.html(wrapped_html, height=height, scrolling=False)


def render_hot_topics_panel(hot_topics, height=245):
    css = load_css_file("hot_topics.css")
    cards_html = f"<style>{css}</style>"

    for item in hot_topics:
        target_url = html.escape(build_subpage_url(item["name"]))
        safe_name = html.escape(item["name"])
        safe_en = html.escape(item["en"])
        safe_keywords = html.escape(item["keywords"])
        safe_score = html.escape(str(item["score"]))
        safe_rank = html.escape(str(item["rank"]))

        cards_html += f"""
        <a href="{target_url}" target="_blank" class="hot-topic-link">
            <div class="hot-topic-card">
                <div class="hot-rank-wrap">
                    <div class="hot-rank">{safe_rank}</div>
                </div>
                <div class="hot-name-wrap">
                    <div class="hot-name-line">
                        <span class="hot-name">{safe_name}</span>
                        <span class="hot-en">{safe_en}</span>
                    </div>
                </div>
                <div class="hot-meta-wrap">
                    <div class="hot-row">
                        <span class="hot-label">발생 건수</span>
                        <span class="hot-score">{safe_score}건</span>
                    </div>
                    <div class="hot-row">
                        <span class="hot-label">주요 키워드</span>
                        <span class="hot-keywords">{safe_keywords}</span>
                    </div>
                </div>
            </div>
        </a>
        """

    if not hot_topics:
        cards_html += """
        <div class="hot-empty-state">
            최근 7일 기준 핵심광물 데이터가 없습니다.
        </div>
        """

    full_html = f"""
    <div class="hot-topics-wrap">
        {cards_html}
    </div>
    """
    components.html(full_html, height=height, scrolling=False)


def render_recent_news_panel(news_df, panel_height=None):
    if news_df.empty:
        st.info("최근 뉴스 데이터가 없습니다.")
        return

    rows_html = ""
    for _, news in news_df.iterrows():
        safe_title = html.escape(str(news["title"]))
        safe_content = html.escape(str(news["content"]))
        safe_date = html.escape(str(news["date_str"]))
        risk_keywords = html.escape(build_risk_keywords_text(news["risk_keyword"]))
        mineral_keywords = html.escape(build_mineral_keywords_text(news["mineral_keyword"]))

        rows_html += f"""
        <div class="news-row">
            <div class="news-main">
                <div class="news-title">{safe_title}</div>
                <div class="news-content">{safe_content}</div>
            </div>
            <div class="news-keywords">
                <div>
                    <span class="kw-label">광물 키워드</span>
                    <span class="kw-text">{mineral_keywords}</span>
                </div>
                <div class="news-keyword-gap">
                    <span class="kw-label">주요 키워드</span>
                    <span class="kw-text">{risk_keywords}</span>
                </div>
            </div>
            <div class="news-date">{safe_date}</div>
        </div>
        """

    if panel_height is None:
        panel_height = max(220, min(520, len(news_df) * 92 + 8))

    css = load_css_file("recent_news.css")
    panel_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <style>{css}</style>
    </head>
    <body>
        <div class="news-wrap">
            {rows_html}
        </div>
    </body>
    </html>
    """
    components.html(panel_html, height=panel_height, scrolling=False)
