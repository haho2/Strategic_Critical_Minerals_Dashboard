# dashboard_css.py
# st를 파라미터로 받아서 circular import 완전 차단

def inject_css(st):
    st.markdown("""
<style>
[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
.stApp { background-color: #0A0C10 !important; }
.block-container {
    max-width: 100% !important;
    padding-top: 0rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 1rem !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    height: auto !important;
    max-height: none !important;
    overflow: visible !important;
    box-sizing: border-box !important;
}
div.stButton > button {
    background-color: #111827 !important;
    color: white !important;
    border: 1px solid #374151 !important;
    border-radius: 10px !important;
    padding: 0.45rem 1rem !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    height: 44px !important;
}
div.stButton > button:hover {
    border: 1px solid #60A5FA !important;
    color: #60A5FA !important;
}
.active-tab {
    background-color: #2563EB !important;
    color: white !important;
    border: 1px solid #2563EB !important;
    border-radius: 10px !important;
    padding: 0.65rem 1rem !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    text-align: center;
    height: 44px !important;
    display: flex;
    align-items: center;
    justify-content: center;
}
h1, h2, h3, h4, p, label, b, span, div { font-family: 'Pretendard', sans-serif; }
h1, h2, h3, h4, label, b { color: #FFFFFF !important; }
.col1-top-kor   { font-size:30px; font-weight:800; color:#FFFFFF; margin-bottom:8px; }
.col1-section-title { font-size:28px; font-weight:900; color:#FFFFFF; margin-bottom:6px; }
.col1-value-label   { font-size:16px; color:#9CA3AF; font-weight:600; margin-bottom:6px; }
.col1-value-big     { font-size:42px; font-weight:900; color:#FFFFFF; line-height:1.1; margin-bottom:8px; }
.col1-subtitle      { font-size:17px; font-weight:800; color:#FFFFFF; margin-top:6px; margin-bottom:8px; }
.section-title       { font-size:28px; font-weight:800; color:#FFFFFF; margin:0 0 4px 0; line-height:1.15; }
.section-title-tight { font-size:28px; font-weight:800; color:#FFFFFF; margin:0 0 2px 0; line-height:1.05; }
.table-wrap { overflow-y:auto; border:1px solid rgba(255,255,255,0.08); border-radius:10px; }
.table-wrap table { width:100%; border-collapse:collapse; font-size:14px; }
.table-wrap thead th {
    position:sticky; top:0; background-color:#1C1F26; color:#D1D5DB;
    padding:10px 12px; border-bottom:1px solid #4B5563; font-weight:700; z-index:2; white-space:nowrap;
}
.table-wrap tbody td {
    padding:10px 12px; border-bottom:1px solid rgba(255,255,255,0.08); color:white; white-space:nowrap;
}
.news-scroll-wrap { overflow-y:auto; flex:1; padding-right:4px; }
.news-scroll-wrap::-webkit-scrollbar { width:5px; }
.news-scroll-wrap::-webkit-scrollbar-track { background:rgba(255,255,255,0.05); border-radius:4px; }
.news-scroll-wrap::-webkit-scrollbar-thumb { background:#4B5563; border-radius:4px; }
.news-scroll-wrap::-webkit-scrollbar-thumb:hover { background:#6B7280; }
.news-wrap { margin:0; }
.news-item {
    display:flex; align-items:flex-start; gap:16px;
    height:115px; min-height:115px; max-height:115px;
    overflow:hidden; padding:14px 0;
    border-bottom:1px solid #3A4759; box-sizing:border-box;
}
.news-item:first-child { border-top:1px solid #3A4759; }
.news-item:last-child  { border-bottom:1px solid #3A4759; }
.news-badge {
    color:white !important; padding:6px 14px; border-radius:8px;
    font-size:13px; font-weight:700; min-width:60px; text-align:center;
    line-height:1.2; margin-top:2px; flex-shrink:0;
}
.news-title {
    font-size:15px; font-weight:800; color:white !important;
    margin-bottom:3px; line-height:1.3;
    display:-webkit-box; -webkit-line-clamp:2;
    -webkit-box-orient:vertical; overflow:hidden;
}
.news-desc {
    font-size:12px; color:#D1D5DB !important; line-height:1.4;
    display:-webkit-box; -webkit-line-clamp:2;
    -webkit-box-orient:vertical; overflow:hidden;
}
.news-date {
    font-size:12px; color:#E5E7EB !important; white-space:nowrap;
    padding-top:3px; min-width:90px; text-align:right; flex-shrink:0;
}
</style>
""", unsafe_allow_html=True)
