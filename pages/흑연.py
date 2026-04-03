import os
import sys
import time

# ── 경로 설정 (가장 먼저) ──────────────────────────────────
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR    = os.path.dirname(CURRENT_DIR)
CSS_DEF_DIR = os.path.join(ROOT_DIR, "css_def")
for p in [ROOT_DIR, CSS_DEF_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── streamlit 초기화 ───────────────────────────────────────
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide", page_title="K-Defense 전략물자 모니터링")

# 5분마다 자동 새로고침
if "_last_refresh" not in st.session_state:
    st.session_state._last_refresh = time.time()
if time.time() - st.session_state._last_refresh > 300:
    st.session_state._last_refresh = time.time()
    st.rerun()

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "가격"

# ── css_def import ────────────────
from css_def.dashboard_css import inject_css
from css_def.dashboard_def import (
    CHART_H, TABLE_H, KEYWORD_CHART_H,
    NEWS_SCROLL_H, COUNTRY_CHART_H, MAP_H, TRANSPARENT, COUNTRY_MAP,
    nice_dtick, format_date_col, make_category_date_labels,
    style_category_xaxis, add_horizontal_yaxis_title,
    render_delta_html, render_scrollable_table_html,
    load_price_data, load_import_data,
    load_news_keyword_data, load_news_data,
)
from DB.DB import get_connection
import html as html_module
import pandas as pd

# =========================
# 광물 설정
# =========================
MINERAL_NAME          = "흑연"
MINERAL_ENG_NAME      = "GRAPHITE"
NEWS_MINERAL_KEYWORDS = ("흑연",)

# CSS 주입
inject_css(st)

# =========================
# st.cache_data 래핑
# =========================
@st.cache_data(ttl=300)
def cached_load_price_data(mineral_name):
    return load_price_data(mineral_name, get_connection)

@st.cache_data(ttl=300)
def cached_load_import_data(mineral_name):
    return load_import_data(mineral_name, get_connection)

@st.cache_data(ttl=300)
def cached_load_news_keyword_data(mineral_keywords):
    return load_news_keyword_data(mineral_keywords, get_connection)

@st.cache_data(ttl=300)
def cached_load_news_data(mineral_keywords):
    return load_news_data(mineral_keywords, get_connection)

def set_view_mode(mode):
    st.session_state.view_mode = mode

def render_scrollable_table(df, right_align_cols=None, height_px=300):
    html_str = render_scrollable_table_html(df, right_align_cols, height_px)
    st.markdown(html_str, unsafe_allow_html=True)

# =========================
# 데이터 로드
# =========================
try:
    keyword_df = cached_load_news_keyword_data(NEWS_MINERAL_KEYWORDS)
except Exception:
    keyword_df = pd.DataFrame(columns=["키워드","비율"])

if keyword_df.empty:
    keyword_df = pd.DataFrame({"키워드":["수출통제","공급부족","정치리스크","시장경보","물류 차질"],
                                "비율":[30,24,18,15,13]})

try:
    news_df = cached_load_news_data(NEWS_MINERAL_KEYWORDS)
except Exception:
    news_df = pd.DataFrame(columns=["date","title","desc","risk_tag","tag_bg","url"])

try:
    price_info,  price_df,  price_table_df  = cached_load_price_data(MINERAL_NAME)
    import_info, import_df, country_df, import_table_df = cached_load_import_data(MINERAL_NAME)
except Exception as e:
    st.error(f"DB 조회 오류: {e}"); st.stop()

if price_info  is None: st.error(f"'{MINERAL_NAME}' 가격 데이터를 찾지 못했습니다.");  st.stop()
if import_info is None: st.error(f"'{MINERAL_NAME}' 수입량 데이터를 찾지 못했습니다."); st.stop()

latest_price      = price_df.iloc[-1]["가격"]   if not price_df.empty  else None
price_delta_rate  = price_df.iloc[-1]["등락률"]  if not price_df.empty  else None
latest_import     = import_df.iloc[-1]["수입량"] if not import_df.empty else None
import_delta_rate = import_df.iloc[-1]["등락률"] if not import_df.empty else None

if not country_df.empty:
    country_chart_df = country_df.copy()
    country_chart_df["영문국가"] = country_df["국가"].map(COUNTRY_MAP).fillna(country_chart_df["국가"])
else:
    country_chart_df = pd.DataFrame({"국가":["중국","호주","홍콩"],"의존도":[50,30,20],
                                      "영문국가":["China","Australia","Hong Kong"]})

country_color_map = {
    c: ["#FF4D4D","#FF8C42","#FFD666","#2ECC71","#7DB7E5"][i%5]
    for i,c in enumerate(country_chart_df["국가"].tolist())
}

price_chart_df  = make_category_date_labels(price_df,  "날짜", mode="price")  if not price_df.empty  else pd.DataFrame()
import_chart_df = make_category_date_labels(import_df, "날짜", mode="import") if not import_df.empty else pd.DataFrame()

# =========================
# 화면
# =========================
st.markdown("""
<style>
div.st-key-home_title_button button {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 0 0.8rem 0 !important;
    color: inherit !important;
    font-size: 2.1rem !important;
    font-weight: 700 !important;
    line-height: 1.2 !important;
    text-align: left !important;
    box-shadow: none !important;
}
div.st-key-home_title_button button:hover,
div.st-key-home_title_button button:active,
div.st-key-home_title_button button:focus {
    background: transparent !important;
    border: none !important;
    color: inherit !important;
    box-shadow: none !important;
}
div.st-key-home_title_button button p {
    font-size: 2.1rem !important;
    font-weight: 700 !important;
    line-height: 1.2 !important;
}
</style>
""", unsafe_allow_html=True)

if st.button("🛡️ 국방 핵심광물 공급망 리스크 탐지 시스템", key="home_title_button"):
    st.switch_page("main.py")
col1, col2, col3 = st.columns([1,1,1], gap="medium")

with col1:
    with st.container(border=True):
        view = st.session_state.view_mode
        hdr_l, hdr_r = st.columns([3,2])
        with hdr_l:
            st.markdown(f'<div class="col1-top-kor">{price_info["mineral_name"]}</div>',
                        unsafe_allow_html=True)
        with hdr_r:
            b1, b2 = st.columns(2)
            with b1:
                if view == "가격":
                    st.markdown("<div style='background:#2563EB;border:1px solid #2563EB;border-radius:10px;padding:9px 0;text-align:center;font-weight:800;font-size:15px;color:white;'>가격</div>", unsafe_allow_html=True)
                else:
                    st.button("가격", key="price_tab", use_container_width=True, on_click=set_view_mode, args=("가격",))
            with b2:
                if view == "수입량":
                    st.markdown("<div style='background:#2563EB;border:1px solid #2563EB;border-radius:10px;padding:9px 0;text-align:center;font-weight:800;font-size:15px;color:white;'>수입량</div>", unsafe_allow_html=True)
                else:
                    st.button("수입량", key="import_tab", use_container_width=True, on_click=set_view_mode, args=("수입량",))

        if view == "가격":
            sect_title = "📈"
            val_str    = f"{latest_price:,.2f}$" if latest_price is not None else "데이터 없음"
            delta_rate, delta_lbl = price_delta_rate, ""
        else:
            sect_title = "📦"
            val_str    = f"{latest_import:,.2f} /t" if latest_import is not None else "데이터 없음"
            delta_rate, delta_lbl = import_delta_rate, ""

        delta_html = render_delta_html(delta_rate, delta_lbl)
        st.markdown(
            f"<div style='display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:8px;'>"
            f"<div class='col1-section-title' style='margin:0;'>{sect_title}</div>"
            f"<div class='col1-value-big' style='margin:0;'>{val_str}</div>"
            f"{delta_html}"
            f"</div>",
            unsafe_allow_html=True
        )

        if view == "가격" and not price_chart_df.empty:
            y_min = float(price_chart_df["가격"].min()); y_max = float(price_chart_df["가격"].max())
            fig_c = px.line(price_chart_df, x="date_label", y="가격",
                            category_orders={"date_label": price_chart_df["date_label"].tolist()})
            fig_c.update_traces(line=dict(color="#1D9BF0", width=3))
            fig_c.update_layout(height=CHART_H, margin=dict(l=90,r=20,t=6,b=36),
                paper_bgcolor=TRANSPARENT, plot_bgcolor=TRANSPARENT, font_color="white",
                yaxis=dict(gridcolor="rgba(255,255,255,0.18)", tickfont=dict(color="white"),
                           tickmode="linear", dtick=nice_dtick(y_min,y_max,10)))
            fig_c = style_category_xaxis(fig_c)
            fig_c = add_horizontal_yaxis_title(fig_c, "가격($)", -0.17)
            fig_c.update_xaxes(title_text="날짜")
            st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False})
        elif view == "수입량" and not import_chart_df.empty:
            y_min = float(import_chart_df["수입량"].min()); y_max = float(import_chart_df["수입량"].max())
            fig_c = px.line(import_chart_df, x="date_label", y="수입량",
                            category_orders={"date_label": import_chart_df["date_label"].tolist()})
            fig_c.update_traces(line=dict(color="#22C55E", width=3))
            fig_c.update_layout(height=CHART_H, margin=dict(l=90,r=20,t=6,b=36),
                paper_bgcolor=TRANSPARENT, plot_bgcolor=TRANSPARENT, font_color="white",
                yaxis=dict(gridcolor="rgba(255,255,255,0.18)", tickfont=dict(color="white"),
                           tickmode="linear", dtick=nice_dtick(y_min,y_max,10)))
            fig_c = style_category_xaxis(fig_c)
            fig_c = add_horizontal_yaxis_title(fig_c, "수입량/t", -0.17)
            fig_c.update_xaxes(title_text="날짜")
            st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="col1-subtitle">⚠ 국내 현황</div>', unsafe_allow_html=True)
        if view == "가격":
            render_scrollable_table(price_table_df,  right_align_cols=["가격","날짜"],  height_px=TABLE_H)
        else:
            render_scrollable_table(import_table_df, right_align_cols=["중량","날짜"], height_px=TABLE_H)

with col2:
    with st.container(border=True):
        st.markdown('<div class="section-title"> 글로벌 지도</div>', unsafe_allow_html=True)
        world_map_df = country_chart_df[["국가","영문국가"]].drop_duplicates().copy()
        fig_map = px.choropleth(world_map_df, locations="영문국가", locationmode="country names",
            color="국가", hover_name="국가", color_discrete_map=country_color_map)
        fig_map.update_layout(height=MAP_H, margin=dict(l=0,r=0,t=0,b=0),
            paper_bgcolor=TRANSPARENT, plot_bgcolor=TRANSPARENT, showlegend=False,
            geo=dict(showframe=False, showcoastlines=False, showcountries=True,
                     countrycolor="#CFCFD4", countrywidth=0.7,
                     showland=True, landcolor="#F3F4F6",
                     showocean=True, oceancolor="#D1D5DB",
                     bgcolor=TRANSPARENT, projection_type="equirectangular",
                     projection_scale=1.18, center=dict(lat=15, lon=0),
                     lataxis=dict(range=[-100,100]), lonaxis=dict(range=[-180,180])))
        st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})
    with st.container(border=True):
        st.markdown('<div class="section-title" style="margin:0;padding:0;">국가별 의존도</div>', unsafe_allow_html=True)
        fig_cty = px.pie(country_chart_df, names="국가", values="의존도", hole=0.55,
            color="국가", color_discrete_map=country_color_map)
        fig_cty.update_traces(textinfo="percent", textfont=dict(size=15, color="black"))
        fig_cty.update_layout(height=COUNTRY_CHART_H, margin=dict(l=10,r=10,t=6,b=6),
            paper_bgcolor=TRANSPARENT, plot_bgcolor=TRANSPARENT,
            font_color="white", showlegend=True,
            legend=dict(font=dict(size=13), x=1.02, y=0.96, itemsizing="constant"))
        st.plotly_chart(fig_cty, use_container_width=True, config={"displayModeBar": False})

import streamlit.components.v1 as components
components.html("""
<script>
(function() {
    function fixCol3() {
        var cols = document.querySelectorAll('div[data-testid="stColumn"]');
        if (cols.length < 3) return false;
        var panel = cols[2].querySelector('div[data-testid="stVerticalBlockBorderWrapper"]');
        if (!panel) return false;
        panel.style.maxHeight = '918px';
        panel.style.overflow  = 'hidden';
        return true;
    }
    var tries = 0;
    var timer = setInterval(function() {
        if (fixCol3() || ++tries > 20) clearInterval(timer);
    }, 200);
})();
</script>
""", height=0)

with col3:
    with st.container(border=True):
        st.markdown('<div class="section-title-tight"> 최근 주요뉴스</div>', unsafe_allow_html=True)
        if news_df.empty:
            st.info("조건에 맞는 뉴스 데이터가 없습니다.")
        else:
            news_items_html = ""
            for _, news in news_df.iterrows():
                news_date = pd.to_datetime(news["date"]).strftime("%Y-%m-%d") if pd.notna(news["date"]) else ""
                title    = html_module.escape(str(news["title"]))
                desc     = html_module.escape(str(news["desc"]))
                risk_tag = html_module.escape(str(news["risk_tag"]))
                tag_bg   = str(news["tag_bg"])
                news_items_html += (
                    '<div class="news-item">'
                    f'<div class="news-badge" style="background:{tag_bg};">{risk_tag}</div>'
                    '<div style="flex:1;min-width:0;">'
                    f'<div class="news-title">{title}</div>'
                    f'<div class="news-desc">{desc}</div>'
                    '</div>'
                    f'<div class="news-date">{news_date}</div>'
                    '</div>'
                )
            st.markdown(
                f'<div class="news-scroll-wrap" style="max-height:{NEWS_SCROLL_H}px;overflow-y:auto;padding-right:4px;">'
                f'<div class="news-wrap">{news_items_html}</div></div>',
                unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="section-title"> 위험 키워드 추이</div>', unsafe_allow_html=True)
        fig_kw = px.pie(keyword_df, names="키워드", values="비율", hole=0.55,
            color="키워드",
            color_discrete_sequence=["#FF4D4D","#FF8C42","#FFD666","#2ECC71","#7DB7E5"])
        fig_kw.update_traces(textinfo="percent", textfont=dict(size=15, color="black"))
        fig_kw.update_layout(height=KEYWORD_CHART_H, margin=dict(l=10,r=10,t=6,b=6),
            paper_bgcolor=TRANSPARENT, plot_bgcolor=TRANSPARENT, font_color="white",
            showlegend=True, legend=dict(font=dict(size=13), x=1.02, y=0.96, itemsizing="constant"))
        st.plotly_chart(fig_kw, use_container_width=True, config={"displayModeBar": False})
