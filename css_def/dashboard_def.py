# dashboard_def.py
# streamlit import 없음 → circular import 완전 차단
import math
import re
import pandas as pd

# =========================
# 공통 상수
# =========================
CHART_H         = 292
TABLE_H         = 324
KEYWORD_CHART_H = 329
NEWS_SCROLL_H   = 350
COUNTRY_CHART_H = 333
MAP_H           = 330
TRANSPARENT     = "rgba(0,0,0,0)"

COUNTRY_MAP = {
    "중국": "China", "칠레": "Chile",
    "콩고민주공화국": "Democratic Republic of the Congo",
    "콩고": "Democratic Republic of the Congo",
    "호주": "Australia", "미국": "United States",
    "브라질": "Brazil", "대한민국": "South Korea",
    "일본": "Japan", "인도네시아": "Indonesia",
    "남아프리카공화국": "South Africa", "캐나다": "Canada",
    "아르헨티나": "Argentina", "독일": "Germany",
    "프랑스": "France", "홍콩": "Hong Kong"
}

# =========================
# 공통 함수
# =========================
def format_date_col(df: pd.DataFrame, col: str):
    out = df.copy()
    if col in out.columns:
        out[col] = pd.to_datetime(out[col], errors="coerce").dt.strftime("%Y-%m-%d")
    return out

def nice_dtick(min_val, max_val, target_ticks=8):
    if pd.isna(min_val) or pd.isna(max_val):
        return None
    span = max_val - min_val
    if span <= 0:
        return 1
    raw = span / target_ticks
    magnitude = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    residual = raw / magnitude
    if residual <= 1:     nice = 1
    elif residual <= 2:   nice = 2
    elif residual <= 2.5: nice = 2.5
    elif residual <= 5:   nice = 5
    else:                 nice = 10
    return nice * magnitude

def make_category_date_labels(df: pd.DataFrame, date_col: str, mode="price"):
    temp = df.copy()
    temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
    temp = temp.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    if mode == "price":
        temp["date_label"] = temp[date_col].dt.strftime("%m-%d")
    else:
        temp["date_label"] = temp[date_col].dt.strftime("%Y-%m")
    return temp

def style_category_xaxis(fig):
    fig.update_xaxes(
        type="category", categoryorder="array",
        tickangle=0, showgrid=False,
        tickfont=dict(size=12, color="white"), automargin=True
    )
    return fig

def add_horizontal_yaxis_title(fig, title_text, x_pos=-0.10):
    fig.update_yaxes(title_text="")
    fig.add_annotation(
        xref="paper", yref="paper", x=x_pos, y=0.5,
        text=title_text, showarrow=False, textangle=0,
        font=dict(color="white", size=15),
        xanchor="center", yanchor="middle"
    )
    return fig

def render_delta_html(delta_value, label_text):
    if delta_value is None or pd.isna(delta_value):
        arrow, value_text, color = "•", "0.00%", "#A0A7B4"
    elif float(delta_value) > 0:
        arrow, value_text, color = "▲", f"{abs(float(delta_value)):.2f}%", "#FF5A5F"
    elif float(delta_value) < 0:
        arrow, value_text, color = "▼", f"{abs(float(delta_value)):.2f}%", "#2F80FF"
    else:
        arrow, value_text, color = "•", "0.00%", "#A0A7B4"
    return (
        f"<div style='display:flex;align-items:center;gap:12px;white-space:nowrap;"
        f"line-height:1;margin-top:2px;margin-bottom:8px;'>"
        f"<font color='{color}' style='font-size:19px;font-weight:900;"
        f"letter-spacing:-0.45px;'>{arrow} {value_text}</font>"
        f"<span style='color:#F2F4F7 !important;font-size:18px;font-weight:900;"
        f"letter-spacing:-0.45px;'>{label_text}</span>"
        f"</div>"
    )

def render_scrollable_table_html(df: pd.DataFrame, right_align_cols=None, height_px=300):
    if df is None or df.empty:
        return "<div style='color:#9CA3AF;padding:12px;'>데이터 없음</div>"
    if right_align_cols is None:
        right_align_cols = []
    def align(col): return "right" if col in right_align_cols else "left"
    header_html = "".join(f'<th style="text-align:{align(col)};">{col}</th>' for col in df.columns)
    rows = []
    for _, row in df.iterrows():
        row_html = "".join(f'<td style="text-align:{align(col)};">{row[col]}</td>' for col in df.columns)
        rows.append(f"<tr>{row_html}</tr>")
    return (f'<div class="table-wrap" style="height:{height_px}px;max-height:{height_px}px;">'
            f'<table><thead><tr>{header_html}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')

def clean_text(value: str, max_len: int = 90) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip() + "..."
    return text

def normalize_risk_keyword(risk: str) -> str:
    if risk is None:
        return "기타"
    risk_map = {
        "정치·지정학 리스크": "정치리스크",
        "생산·공급 차질": "공급부족",
        "수입·무역 제한": "수출통제",
        "시장 경보": "시장경보",
    }
    return risk_map.get(str(risk).strip(), str(risk).strip())

def classify_news_badge(risk_list_text: str):
    text = str(risk_list_text or "")
    critical_keywords   = ["생산·공급 차질", "수입·무역 제한", "공급부족", "수출통제"]
    structural_keywords = ["정치·지정학 리스크", "정치리스크", "물류 차질"]
    if any(k in text for k in critical_keywords):
        return "위험", "#8A2E2E"
    if any(k in text for k in structural_keywords):
        return "주의", "#A67C37"
    return "경계", "#F5A623"

def build_news_desc(row) -> str:
    source_name     = clean_text(row.get("source_name", ""), 20)
    risk_summary    = clean_text(row.get("risk_summary", ""), 40)
    content_excerpt = clean_text(row.get("content", ""), 85)
    if content_excerpt:               return content_excerpt
    if source_name and risk_summary:  return f"{source_name} | {risk_summary}"
    if risk_summary:                  return risk_summary
    if source_name:                   return source_name
    return "관련 뉴스 데이터입니다."

# =========================
# DB 로드 함수 (get_connection을 파라미터로 받음)
# =========================
def load_price_data(mineral_name: str, get_connection):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT mineral_id, mineral_name, category
                FROM minerals WHERE mineral_name = %s LIMIT 1
            """, (mineral_name,))
            mineral_row = cursor.fetchone()
            if not mineral_row:
                return None, pd.DataFrame(), pd.DataFrame()
            mineral_id = int(mineral_row["mineral_id"])
            cursor.execute("""
                SELECT date, price FROM mineral_prices
                WHERE mineral_id = %s ORDER BY date
            """, (mineral_id,))
            rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        if df.empty:
            return (mineral_row,
                    pd.DataFrame(columns=["날짜","가격","등락률"]),
                    pd.DataFrame(columns=["광물","가격","날짜"]))
        df["날짜"] = pd.to_datetime(df["date"], errors="coerce")
        df["가격"] = pd.to_numeric(df["price"], errors="coerce")
        df = df[["날짜","가격"]].dropna(subset=["날짜","가격"]).sort_values("날짜").reset_index(drop=True)
        df["등락률"] = df["가격"].pct_change() * 100
        chart_df = df.tail(7).reset_index(drop=True)
        table_df = df[df["날짜"] >= chart_df["날짜"].min()].copy()
        table_df["광물"] = mineral_row["mineral_name"]
        table_df = table_df[["광물","가격","날짜"]]
        table_df = table_df.sort_values(["날짜","가격"], ascending=[False,False]).reset_index(drop=True)
        table_df = format_date_col(table_df, "날짜")
        return mineral_row, chart_df, table_df
    finally:
        conn.close()

def load_import_data(mineral_name: str, get_connection):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT mineral_id, mineral_name, category
                FROM minerals WHERE mineral_name = %s LIMIT 1
            """, (mineral_name,))
            mineral_row = cursor.fetchone()
            if not mineral_row:
                return None, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            mineral_id = int(mineral_row["mineral_id"])
            cursor.execute("""
                SELECT mi.date, SUM(mi.import_weight) AS import_weight
                FROM mineral_import mi WHERE mi.mineral_id = %s
                GROUP BY mi.date ORDER BY mi.date
            """, (mineral_id,))
            import_rows = cursor.fetchall()
            cursor.execute("""
                SELECT c.country_name, mi.import_share
                FROM mineral_import mi
                JOIN countries c ON mi.country_id = c.country_id
                WHERE mi.mineral_id = %s
                  AND mi.date = (SELECT MAX(date) FROM mineral_import WHERE mineral_id = %s)
                ORDER BY mi.import_share DESC LIMIT 5
            """, (mineral_id, mineral_id))
            country_rows = cursor.fetchall()
            cursor.execute("""
                SELECT c.country_name, mi.import_weight, mi.date
                FROM mineral_import mi
                JOIN countries c ON mi.country_id = c.country_id
                WHERE mi.mineral_id = %s ORDER BY mi.date, c.country_name
            """, (mineral_id,))
            detail_rows = cursor.fetchall()
        import_df  = pd.DataFrame(import_rows)
        country_df = pd.DataFrame(country_rows)
        detail_df  = pd.DataFrame(detail_rows)
        if not import_df.empty:
            import_df["날짜"]  = pd.to_datetime(import_df["date"], errors="coerce")
            import_df["수입량"] = pd.to_numeric(import_df["import_weight"], errors="coerce")
            import_df = (import_df[["날짜","수입량"]]
                         .dropna(subset=["날짜","수입량"]).sort_values("날짜").reset_index(drop=True))
            import_df["월"] = import_df["날짜"].dt.to_period("M").dt.to_timestamp()
            import_df = (import_df.groupby("월", as_index=False)["수입량"]
                         .sum().rename(columns={"월":"날짜"}))
            import_df["등락률"] = import_df["수입량"].pct_change() * 100
            chart_df = import_df.tail(7).reset_index(drop=True)
        else:
            chart_df = pd.DataFrame(columns=["날짜","수입량","등락률"])
        if not country_df.empty:
            country_df["국가"]  = country_df["country_name"].astype(str)
            country_df["의존도"] = pd.to_numeric(country_df["import_share"], errors="coerce")
            country_df = country_df[["국가","의존도"]].dropna()
        else:
            country_df = pd.DataFrame(columns=["국가","의존도"])
        if not detail_df.empty and not chart_df.empty:
            detail_df["날짜"] = pd.to_datetime(detail_df["date"], errors="coerce")
            detail_df["중량"] = pd.to_numeric(detail_df["import_weight"], errors="coerce")
            detail_df["국가"] = detail_df["country_name"].astype(str)
            detail_df = detail_df[["국가","중량","날짜"]].dropna()
            table_df = detail_df[detail_df["날짜"] >= chart_df["날짜"].min()].copy()
            table_df = table_df.sort_values(["날짜","국가"], ascending=[False,True]).reset_index(drop=True)
            table_df = format_date_col(table_df, "날짜")
        else:
            table_df = pd.DataFrame(columns=["국가","중량","날짜"])
        return mineral_row, chart_df, country_df, table_df
    finally:
        conn.close()

def load_news_keyword_data(mineral_keywords: tuple, get_connection):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            placeholders = ", ".join(["%s"] * len(mineral_keywords))
            query = f"""
                SELECT jt_risk.risk_keyword AS risk_keyword, COUNT(*) AS cnt
                FROM news n
                JOIN JSON_TABLE(n.mineral_keyword, '$[*]' COLUMNS (
                    mineral_keyword VARCHAR(100) PATH '$'
                )) jt_mineral
                JOIN JSON_TABLE(n.risk_keyword, '$[*]' COLUMNS (
                    risk_keyword VARCHAR(100) PATH '$'
                )) jt_risk ON 1=1
                WHERE jt_mineral.mineral_keyword IN ({placeholders})
                GROUP BY jt_risk.risk_keyword
                ORDER BY cnt DESC, jt_risk.risk_keyword
            """
            cursor.execute(query, mineral_keywords)
            rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["키워드","비율"])
        df["키워드"] = df["risk_keyword"].apply(normalize_risk_keyword)
        df["비율"]   = pd.to_numeric(df["cnt"], errors="coerce").fillna(0)
        df = df.groupby("키워드", as_index=False)["비율"].sum()
        df = df[df["비율"] > 0].sort_values("비율", ascending=False).reset_index(drop=True)
        return df.head(5)
    finally:
        conn.close()

def load_news_data(mineral_keywords: tuple, get_connection):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            placeholders = ", ".join(["%s"] * len(mineral_keywords))
            query = f"""
                SELECT n.id, n.date, n.title, n.source_name, n.url, n.content,
                    GROUP_CONCAT(DISTINCT jt_risk.risk_keyword
                        ORDER BY jt_risk.risk_keyword SEPARATOR ', ') AS risk_summary
                FROM news n
                JOIN JSON_TABLE(n.mineral_keyword, '$[*]' COLUMNS (
                    mineral_keyword VARCHAR(100) PATH '$'
                )) jt_mineral
                LEFT JOIN JSON_TABLE(n.risk_keyword, '$[*]' COLUMNS (
                    risk_keyword VARCHAR(100) PATH '$'
                )) jt_risk ON 1=1
                WHERE jt_mineral.mineral_keyword IN ({placeholders})
                GROUP BY n.id, n.date, n.title, n.source_name, n.url, n.content
                ORDER BY n.date DESC LIMIT 20
            """
            cursor.execute(query, mineral_keywords)
            rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["date","title","desc","risk_tag","tag_bg","url"])
        df["date"]         = pd.to_datetime(df["date"], errors="coerce")
        df["title"]        = df["title"].fillna("관련 뉴스").astype(str)
        df["source_name"]  = df["source_name"].fillna("").astype(str)
        df["content"]      = df["content"].fillna("").astype(str)
        df["risk_summary"] = df["risk_summary"].fillna("").astype(str)
        df = df.sort_values("date", ascending=False).drop_duplicates(subset=["title"]).reset_index(drop=True)
        out_rows = []
        for _, row in df.iterrows():
            risk_tag, tag_bg = classify_news_badge(row.get("risk_summary",""))
            out_rows.append({
                "date": row.get("date"), "title": row.get("title"),
                "desc": build_news_desc(row),
                "risk_tag": risk_tag, "tag_bg": tag_bg, "url": row.get("url","")
            })
        return pd.DataFrame(out_rows).head(5)
    finally:
        conn.close()
