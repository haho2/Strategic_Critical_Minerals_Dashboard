import html
import os
from datetime import date
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from pages.info_sync import run_all_sync
from utils.mineral_fnt import (
    build_subpage_url,
    render_clickable_mineral_card,
    render_plotly_with_top_modebar,
    render_recent_news_panel,
    get_top_risk_keywords_by_mineral,
    get_issue_frequency_df,
    load_each_mineral_individually,
    load_risk_keyword_trend_from_db,
    load_recent_news_from_db,
)

from utils.draw_news import draw_issue_freq_bar

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = CURRENT_DIR

st_autorefresh(interval=300000, key="datarefresh")
st.set_page_config(layout="wide", page_title="K-Defense 핵심광물 모니터링")

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark"

bg_raw = "#0A0C10" if st.session_state.theme_mode == "Dark" else "#FFFFFF"
text_raw = "#FFFFFF" if st.session_state.theme_mode == "Dark" else "#1F2937"

sync_script_path = os.path.join(ROOT_DIR, "pages", "info_sync.py")
hot_topics_css_path = os.path.join(ROOT_DIR, "css_def", "hot_topics.css")

def load_css_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"CSS 파일 로드 오류: {e}")
        return ""

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

mineral_data = load_each_mineral_individually()
recent_news_df = load_recent_news_from_db(limit=5)
df_trend = load_risk_keyword_trend_from_db(days=30, top_n=5)
df_issue_freq = get_issue_frequency_df()

left_news_panel_height = max(320, min(760, len(recent_news_df) * 105))
top_left_chart_height = 245
top_right_hot_topic_height = 260
right_issue_chart_height = left_news_panel_height + 10

mineral_registry = {
    "GROUP 01. 희토류": {
        "네오디뮴": mineral_data["네오디뮴"],
        "디스프로슘": mineral_data["디스프로슘"],
        "터븀": mineral_data["터븀"],
        "세륨": mineral_data["세륨"],
        "란탄": mineral_data["란탄"],
    },
    "GROUP 02. 희토류 외 핵심광물": {
        "리튬": mineral_data["리튬"],
        "니켈": mineral_data["니켈"],
        "코발트": mineral_data["코발트"],
        "망간": mineral_data["망간"],
        "흑연": mineral_data["흑연"],
    }
}

st.markdown(f"""
<style>
    [data-testid="stHeader"] {{
        background-color: rgba(0,0,0,0) !important;
    }}
    .stApp {{
        background-color: {bg_raw} !important;
    }}
    .block-container {{
        max-width: 100% !important;
        padding-top: 0.6rem !important;
        padding-bottom: 0.4rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
    div[data-testid="stButton"] > button {{
        min-height: 24px !important;
        height: 24px !important;
        padding: 0 10px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        border-radius: 7px !important;
        background: #1B2130 !important;
        color: #E5E7EB !important;
        border: 1px solid #34425C !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        white-space: nowrap !important;
    }}
    div[data-testid="stButton"] > button:hover {{
        border-color: #42506A !important;
        color: #FFFFFF !important;
    }}
</style>
""", unsafe_allow_html=True)

header_title_col, header_button_col = st.columns([9.2, 0.8])

with header_title_col:
    st.markdown("<div style='font-size:24px; font-weight:800; margin-bottom:2px;'>🛡️ 국방 핵심광물 공급망 리스크 탐지 시스템</div>", unsafe_allow_html=True)

with header_button_col:
    st.markdown("<div style='height:2px;'></div>", unsafe_allow_html=True)
    if st.button("정보 동기화", key="top_sync_button", use_container_width=True):
        try:
            if not os.path.exists(sync_script_path):
                st.error(f"파일 없음: {sync_script_path}")
            else:
                run_all_sync()
                # subprocess.Popen([sys.executable, sync_script_path], cwd=ROOT_DIR)
                st.success("동기화 실행됨")
        except Exception as e:
            st.error(f"실행 오류: {e}")

st.markdown("<hr style='margin:8px 0 10px 0; border:0; border-top:1px solid rgba(255,255,255,0.12);'>", unsafe_allow_html=True)

today_str = date.today().strftime("%Y-%m-%d")

for group_name, minerals in mineral_registry.items():
    title_col, info_col = st.columns([8.5, 1.5])

    with title_col:
        st.markdown(
            f"<div style='font-size:13px; font-weight:800; margin-bottom:2px;'>{group_name}</div>",
            unsafe_allow_html=True
        )

    with info_col:
        st.markdown(
            f"""
            <div style='text-align:right; margin-bottom:2px;'>
                <div style='font-size:12px; font-weight:400; color:#9CA3AF; line-height:1.2; margin-bottom:2px;'>기준날짜: {today_str}</div>
                <div style='font-size:12px; font-weight:400; color:#9CA3AF; line-height:1.2;'>기준: DoD | 가격기준: /t</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    cols = st.columns(len(minerals))
    for i, (name, data) in enumerate(minerals.items()):
        with cols[i]:
            render_clickable_mineral_card(name, data)

c_left, c_right = st.columns([2.2, 1.25])

with c_left:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:18px; font-weight:800; margin-bottom:2px;'>📈 위험 키워드 발생 추이 <span style='color:gray; font-size:13px;'>(최근 30일)</span></div>",
            unsafe_allow_html=True
        )

        if df_trend.empty or len(df_trend.columns) <= 1:
            st.info("최근 30일 위험 키워드 데이터가 없습니다.")
        else:
            fig = go.Figure()
            colors = ["#18CDB9", "#E34A4A", "#C89A35", "#8E4EDB", "#2F80ED"]
            draw_cols = [col for col in df_trend.columns if col != "날짜"]

            for i, col in enumerate(draw_cols):
                fig.add_trace(go.Scatter(
                    x=df_trend["날짜"],
                    y=df_trend[col],
                    name=col,
                    mode="lines",
                    stackgroup="one",
                    line=dict(width=2, color=colors[i % len(colors)]),
                    fill="tonexty"
                ))

            min_x = pd.to_datetime(df_trend["날짜"].min())
            max_x = pd.to_datetime(df_trend["날짜"].max())

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color=text_raw,
                height=top_left_chart_height,
                margin=dict(l=42, r=8, t=42, b=28),
                legend=dict(
                    orientation="h",
                    y=1.08,
                    x=1,
                    xanchor="right",
                    font=dict(size=11),
                    itemwidth=70
                ),
                xaxis=dict(
                    title=dict(
                        text="날짜",
                        font=dict(size=11),
                        standoff=10
                    ),
                    tickfont=dict(size=10),
                    showgrid=False,
                    tickformat="%m/%d",
                    range=[min_x, max_x],
                    minallowed=min_x,
                    maxallowed=max_x
                ),
                yaxis=dict(
                    title=dict(
                        text="기사 수",
                        font=dict(size=11),
                        standoff=6
                    ),
                    tickfont=dict(size=10),
                    gridcolor="rgba(255,255,255,0.08)",
                    rangemode="tozero"
                ),
                uirevision="risk_trend_chart"
            )

            render_plotly_with_top_modebar(fig, height=top_left_chart_height)

with c_right:
    st.markdown(
        "<div style='font-size:18px; font-weight:800; margin-bottom:4px;'>광물 핫토픽 TOP3</div>",
        unsafe_allow_html=True
    )

    hot_topics = []

    if not df_issue_freq.empty:
        top_issue_df = df_issue_freq.head(3)

        for rank, row in enumerate(top_issue_df.itertuples(index=False), start=1):
            mineral_name = str(row.mineral_display).strip()
            issue_count = int(row.cnt)

            top_risks_text = get_top_risk_keywords_by_mineral(
                mineral_name=mineral_name,
                days=7,
                top_n=3
            )

            hot_topics.append({
                "rank": rank,
                "name": mineral_name,
                "en": MINERAL_META.get(mineral_name, {}).get("en", mineral_name.upper()),
                "score": issue_count,
                "keywords": top_risks_text
            })

    cards_html = f"<style>{load_css_file(hot_topics_css_path)}</style>"

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
        <div style="
            color:#A3AAB8;
            font-size:13px;
            padding:14px 6px;
        ">
            최근 7일 기준 핵심광물 데이터가 없습니다.
        </div>
        """

    full_html = f"""
    <div style="
        background-color: transparent;
        font-family: Pretendard, Arial, sans-serif;
        color: white;
        box-sizing: border-box;
        overflow: visible;
        padding-top: 2px;
        padding-bottom: 0;
    ">
        {cards_html}
    </div>
    """

    components.html(full_html, height=top_right_hot_topic_height, scrolling=False)

st.markdown("<div style='margin-top:-6px;'></div>", unsafe_allow_html=True)
c_low_left, c_low_right = st.columns([2.2, 1.25], gap="small")

with c_low_left:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:20px; font-weight:800; margin-bottom:2px;'>📰 최근 주요뉴스</div>",
            unsafe_allow_html=True
        )
        render_recent_news_panel(recent_news_df, panel_height=left_news_panel_height)

with c_low_right:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:18px; font-weight:800;'>📊 핵심광물 이슈 발생 빈도 <span style='font-size:13px; color:gray;'>(최근 7일)</span></div>",
            unsafe_allow_html=True
        )
        draw_issue_freq_bar(df_issue_freq, right_issue_chart_height)

