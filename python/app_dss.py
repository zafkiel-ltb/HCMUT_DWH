# -*- coding: utf-8 -*-
"""DSS CompanyX – giao diện 5 màn hình theo Bảng 3.32 (mục 3.5.6), viết cho người quản lý không chuyên kỹ thuật.
Chạy:  streamlit run python/app_dss.py   (theme sáng trong .streamlit/config.toml)
Dữ liệu: results/cum6/dss_khach.csv (sinh bởi cum6_phan_tich_dss.py). Đặt DSS_SOURCE=db để đọc trực tiếp CompanyX_DW khi có pyodbc."""
import os, sys, json
import pandas as pd, numpy as np
import streamlit as st
import altair as alt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); R6 = f'{ROOT}/results/cum6'; R4 = f'{ROOT}/results/cum4'
st.set_page_config(page_title='DSS CompanyX', layout='wide', initial_sidebar_state='expanded')


# ---------------- giao diện (chỉ thay lớp trình bày, giữ nguyên dữ liệu và logic DSS) ----------------
NAVY, GREY, RED, GREEN, LIGHT = '#1F3A5F', '#5B6474', '#B42318', '#067647', '#F3F5F8'
AMBER, NEUTRAL = '#C4711C', '#98A2B3'
st.markdown("""
<style>
:root {
 --ink:#101828; --navy:#1F3A5F; --muted:#5B6474; --faint:#8A93A3;
 --line:#DCE1E8; --line-soft:#EDF0F4; --bg:#F3F5F8; --panel:#FFFFFF;
 --risk:#B42318; --risk-bg:#FEF3F2; --risk-line:#F4C5BF;
 --ok:#067647; --ok-bg:#EFFAF4; --ok-line:#B7E4CB;
}
/* Không bo tròn ở bất kỳ đâu */
.stApp *, .stApp *::before, .stApp *::after { border-radius:0 !important; }
[data-testid="stAppDeployButton"], [data-testid="stHeaderActionElements"] { display:none !important; }
[data-testid="stHeader"] { position:relative !important; inset:auto !important; background:var(--bg) !important;
 backdrop-filter:none !important; box-shadow:none !important; height:2.25rem; min-height:2.25rem; }
[data-testid="stAppViewContainer"] { background:var(--bg) !important; }
.block-container { padding:.2rem 2.25rem 5rem !important; max-width:1440px !important; }
.block-container p, .block-container li { font-size:.92rem; line-height:1.55; }
.block-container h3 { font-size:.98rem !important; font-weight:650 !important; color:var(--ink) !important;
 padding:0 0 .2rem !important; letter-spacing:-.005em; }
.block-container [data-testid="stCaptionContainer"] p { color:var(--faint) !important; font-size:.8rem !important; }

/* Thanh bên (sáng) */
[data-testid="stSidebar"] { border-right:1px solid var(--line) !important; }
[data-testid="stSidebarUserContent"] { padding-top:0 !important; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { font-size:.68rem !important; letter-spacing:.12em;
 text-transform:uppercase; font-weight:700 !important; color:var(--faint) !important; }
[data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stRadio"]), [data-testid="stSidebar"] [data-testid="stRadio"], [data-testid="stSidebar"] [data-testid="stRadio"] > div, [data-testid="stSidebar"] [role="radiogroup"] { width:100% !important; }
[data-testid="stSidebar"] [role="radiogroup"] { gap:0 !important; }
[data-testid="stSidebar"] [role="radiogroup"] label { width:100%; margin:0 !important; padding:.62rem .8rem !important;
 transition:background .12s ease; }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display:none !important; }
[data-testid="stSidebar"] [role="radiogroup"] label > div:last-child { padding-left:0 !important; margin-left:0 !important; }
[data-testid="stSidebar"] [role="radiogroup"] label p { font-size:.9rem !important; color:#344054; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background:var(--bg); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:var(--navy); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color:#FFFFFF; font-weight:650; }
[data-testid="stSidebar"] .stButton button { background:var(--panel); border:1px solid var(--line); color:var(--ink); }
[data-testid="stSidebar"] .stButton button:hover { border-color:var(--navy); color:var(--navy); }
.cx-brand { display:flex; align-items:center; gap:.7rem; padding:.2rem 0 1rem; margin-bottom:.3rem;
 border-bottom:1px solid var(--line); }
.cx-mark { flex:none; width:36px; height:36px; display:flex; align-items:center; justify-content:center;
 background:var(--navy); color:#FFFFFF; font-weight:800; font-size:.84rem; letter-spacing:.02em; }
.cx-brand-name { color:var(--ink); font-weight:700; font-size:1.05rem; line-height:1.2; }
.cx-side-foot { color:var(--faint); font-size:.76rem; line-height:1.7; padding-top:.9rem; margin-top:.4rem;
 border-top:1px solid var(--line); }
.cx-side-foot b { color:var(--ink); font-weight:600; }

/* Tiêu đề màn hình */
.cx-head { display:flex; justify-content:space-between; align-items:flex-end; gap:1.5rem;
 padding:.6rem 0 .95rem; border-bottom:2px solid var(--ink); margin-bottom:1.3rem; }
.cx-code { font-size:.72rem; font-weight:700; letter-spacing:.14em; color:var(--muted); text-transform:uppercase; margin-bottom:.3rem; }
.cx-title { font-size:1.9rem; font-weight:700; letter-spacing:-.025em; color:var(--ink); line-height:1.15; }
.cx-meta { display:flex; gap:.35rem; flex-wrap:wrap; justify-content:flex-end; }
.cx-chip, .tag { display:inline-block; font-size:.68rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
 padding:.3rem .55rem; border:1px solid var(--line); background:var(--panel); color:var(--ink); white-space:nowrap; }
.cx-chip-dark { background:var(--ink); border-color:var(--ink); color:#FFFFFF; }
.tag-du-lieu { color:#1F3A5F; }
.tag-du-doan { color:#9A4A12; }
.tag-gia-dinh { color:#5B3F8C; }
.cx-lead { font-size:1.05rem !important; color:var(--ink); max-width:62rem; margin:0 0 1rem; }

/* Tiêu đề khối */
.cx-sec { display:flex; align-items:center; gap:.8rem; font-size:.72rem; font-weight:700; letter-spacing:.13em;
 text-transform:uppercase; color:var(--muted); margin:1.7rem 0 .7rem; }
.cx-sec::after { content:""; flex:1; height:1px; background:var(--line); }

/* Dải chỉ số */
.cx-kpis { display:grid; grid-template-columns:repeat(var(--n),minmax(0,1fr)); background:var(--panel);
 border:1px solid var(--line); margin:0 0 .5rem; }
.cx-kpi { padding:1rem 1.15rem 1.05rem; border-left:1px solid var(--line); min-width:0; }
.cx-kpi:first-child { border-left:0; }
.cx-kpi-label { font-size:.76rem; color:var(--muted); font-weight:600; margin-bottom:.5rem; }
.cx-kpi-value { font-size:1.8rem; font-weight:700; color:var(--ink); letter-spacing:-.025em; line-height:1.1;
 font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
.cx-kpi-unit { font-size:.85rem; font-weight:600; color:var(--faint); margin-left:.3rem; letter-spacing:0; }
.cx-kpi-sub { font-size:.78rem; color:var(--faint); margin-top:.4rem; line-height:1.4; }
.tone-risk .cx-kpi-value { color:var(--risk); }
.tone-ok .cx-kpi-value { color:var(--ok); }

/* Khung nội dung */
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] { background:var(--panel); border-color:var(--line) !important; }
[data-testid="stDataFrame"] { border:1px solid var(--line); }
[data-testid="stExpander"] details { background:var(--panel); border-color:var(--line) !important; }
.stButton > button, .stDownloadButton > button { font-weight:600; }
.stButton > button:hover { border-color:var(--navy) !important; color:var(--navy) !important; }
.stDownloadButton > button { background:var(--navy) !important; color:#FFFFFF !important; border-color:var(--navy) !important; }
[data-testid="stBaseButton-pills"] { background:var(--panel); border-color:var(--line); color:var(--muted); }
[data-testid="stBaseButton-pillsActive"] { background:var(--navy) !important; border-color:var(--navy) !important; }
[data-testid="stBaseButton-pillsActive"] p { color:#FFFFFF !important; }

/* Nút chọn dạng thanh phân đoạn (màn hình 3) */
[data-testid="stMain"] [role="radiogroup"] { gap:0 !important; flex-wrap:wrap; }
[data-testid="stMain"] [role="radiogroup"] label { border:1px solid var(--line); background:var(--panel);
 padding:.55rem .9rem !important; margin:0 -1px -1px 0 !important; }
[data-testid="stMain"] [role="radiogroup"] label > div:first-child { display:none !important; }
[data-testid="stMain"] [role="radiogroup"] label > div:last-child { padding-left:0 !important; margin-left:0 !important; }
[data-testid="stMain"] [role="radiogroup"] label p { font-size:.86rem !important; color:var(--muted); font-weight:600; }
[data-testid="stMain"] [role="radiogroup"] label:has(input:checked) { background:var(--navy); border-color:var(--navy); position:relative; z-index:1; }
[data-testid="stMain"] [role="radiogroup"] label:has(input:checked) p { color:#FFFFFF; }

/* Hộp trạng thái: viền đủ bốn cạnh, không vạch màu bên trái */
.cx-note { border:1px solid var(--line); background:var(--panel); padding:.75rem .95rem; margin:.5rem 0;
 font-size:.9rem; line-height:1.55; color:var(--ink); }
.cx-note.risk { background:var(--risk-bg); border-color:var(--risk-line); }
.cx-note.ok { background:var(--ok-bg); border-color:var(--ok-line); }
.cx-note .lbl { display:block; font-size:.7rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.2rem; }
.cx-note.risk .lbl { color:var(--risk); }
.cx-note.ok .lbl { color:var(--ok); }
.cx-muted { color:var(--faint); font-size:.8rem; margin-top:.4rem; }

/* Ma trận rủi ro × giá trị */
.cx-matrix { width:100%; border-collapse:collapse; margin:.2rem 0 .3rem; font-variant-numeric:tabular-nums; }
.cx-matrix th { font-size:.74rem; font-weight:700; color:var(--muted); text-align:right; padding:.45rem .8rem;
 letter-spacing:.04em; text-transform:uppercase; }
.cx-matrix tbody th { text-align:left; color:var(--ink); }
.cx-matrix td { text-align:right; padding:1.05rem .8rem; font-size:1.3rem; font-weight:700; color:var(--ink);
 border:1px solid #FFFFFF; }
.cx-matrix td.hot { box-shadow:inset 0 0 0 2px var(--risk); color:var(--risk); }

/* Hồ sơ khách: lưới thông tin */
.cx-field-grid { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); background:var(--panel);
 border:1px solid var(--line); margin:.6rem 0 0; }
.cx-field { padding:.75rem .9rem; border-left:1px solid var(--line-soft); min-width:0; }
.cx-field:first-child { border-left:0; }
.cx-field-label { color:var(--faint); font-size:.74rem; margin-bottom:.3rem; }
.cx-field-value { color:var(--ink); font-size:.95rem; font-weight:650; line-height:1.4; overflow-wrap:anywhere; }
.cx-action-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); background:var(--panel); border:1px solid var(--line); }
.cx-action-item { padding:.85rem 1rem; border-left:1px solid var(--line-soft); border-top:1px solid var(--line-soft); }
.cx-action-item:nth-child(3n+1) { border-left:0; }
.cx-action-item:nth-child(-n+3) { border-top:0; }
.cx-action-label { display:block; color:var(--faint); font-size:.74rem; margin-bottom:.3rem; }
.cx-action-item b { display:block; font-size:1rem; color:var(--ink); line-height:1.4; }
.cx-action-item small { display:block; color:var(--faint); font-size:.74rem; margin-top:.25rem; }
.cx-decision { margin-top:-1px; padding:.8rem 1rem; font-weight:650; font-size:.92rem; border:1px solid; }
.cx-decision.ok { background:var(--ok-bg); border-color:var(--ok-line); color:var(--ok); }
.cx-decision.risk { background:var(--risk-bg); border-color:var(--risk-line); color:var(--risk); }

/* Tab kiểu BI */
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap:0; border-bottom:1px solid var(--line); margin-bottom:.5rem; }
[data-testid="stTabs"] [data-baseweb="tab"] { padding:.75rem 1.15rem; height:auto; background:transparent; }
[data-testid="stTabs"] [data-baseweb="tab"] p { font-size:.9rem !important; font-weight:600; color:var(--muted); }
[data-testid="stTabs"] [data-baseweb="tab"]:hover p { color:var(--navy); }
[data-testid="stTabs"] [aria-selected="true"] p { color:var(--ink); }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background:var(--navy) !important; height:3px; }
[data-testid="stTabs"] [data-baseweb="tab-border"] { display:none; }
/* Thanh lọc chéo đang áp dụng */
.cx-filter { display:flex; flex-wrap:wrap; gap:.4rem; align-items:center; font-size:.78rem; color:var(--muted); font-weight:600; }
.cx-filter .lbl { text-transform:uppercase; letter-spacing:.12em; font-size:.68rem; margin-right:.2rem; }
.cx-chip-filter { background:#E8EEF6; border:1px solid #C9D6E8; color:var(--navy); padding:.32rem .62rem; font-weight:650; font-size:.78rem; }
/* Ma trận Rủi ro × Giá trị dạng ô bấm được */
.cx-mhead { font-size:.72rem; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; text-align:right; padding-right:1rem; }
.cx-mrow { font-size:.74rem; font-weight:700; color:var(--ink); text-transform:uppercase; letter-spacing:.04em; }
[class*="st-key-cx_cell_"] button { height:4.4rem; justify-content:flex-end; padding-right:1rem; border:1px solid transparent !important; }
[class*="st-key-cx_cell_"] button p { font-size:1.35rem !important; font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums; }
[class*="st-key-cx_cell_"] button:hover { box-shadow:inset 0 0 0 2px var(--navy); }
[class*="st-key-cx_vung_"] button { height:4rem; flex-direction:column; align-items:flex-end; justify-content:center; gap:.1rem; padding:0 .7rem; border:1px solid transparent !important; }
[class*="st-key-cx_vung_"] button p { font-size:1.05rem !important; font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums; line-height:1.1; }
[class*="st-key-cx_vung_"] button::after { content:var(--sub); font-size:.7rem; font-weight:600; color:var(--muted); line-height:1.1; white-space:nowrap; }
[class*="st-key-cx_gc_"] button { min-height:0; padding:.15rem 0; }
[class*="st-key-cx_gc_"] button p { font-size:.78rem !important; font-weight:600; color:#C4711C; }
[class*="st-key-cx_gc_"] button:hover p { text-decoration:underline; }
[class*="st-key-cx_gc_"] button span { color:#C4711C !important; }
[class*="st-key-cx_gc_"] button:focus, [class*="st-key-cx_gc_"] button:focus-visible { outline:none !important; box-shadow:none !important; }
[data-testid="stDialog"] [data-testid="stElementContainer"]:has([data-testid="stImage"]), [data-testid="stDialog"] [data-testid="stImage"], [data-testid="stDialog"] [data-testid="stImageContainer"] { width:100% !important; }
[data-testid="stDialog"] [data-testid="stImage"] img { width:100% !important; max-width:100% !important; height:auto !important; border:1px solid var(--line); }
[data-testid="stDialog"] [role="dialog"], [data-testid="stDialog"] [role="dialog"] * { border-radius:0 !important; }
.cx-gc-lead { font-size:1rem; font-weight:600; color:var(--ink); border-left:0; padding:.2rem 0 .6rem; }
.cx-gc-pt { margin:.55rem 0; font-size:.9rem; line-height:1.55; color:var(--ink); }
.cx-gc-pt b { display:block; font-size:.7rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-bottom:.1rem; }
.cx-gc-src { margin-top:.8rem; padding-top:.5rem; border-top:1px solid var(--line); font-size:.75rem; color:var(--muted); }
[class*="st-key-cx_vung_"] button:hover { box-shadow:inset 0 0 0 2px var(--navy); }

/* Các khung đặt cạnh nhau luôn cao bằng nhau */
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] { height:100%; }
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:last-child { flex-grow:1; }
[data-testid="stColumn"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:last-child > [data-testid="stVerticalBlock"] { flex-grow:1; }
.stButton > button[kind="primary"] { background:var(--navy) !important; border-color:var(--navy) !important; color:#FFFFFF !important; }
.stButton > button[kind="primary"]:hover { background:#2B4C77 !important; color:#FFFFFF !important; }
.stButton > button[kind="primary"] p { color:#FFFFFF !important; }
.cx-matrix td { height:4.1rem; }

@media(max-width:1100px) {
 .block-container { padding-left:1rem !important; padding-right:1rem !important; }
 .cx-kpis, .cx-field-grid, .cx-action-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
 .cx-kpi, .cx-field, .cx-action-item { border-left:0 !important; border-top:1px solid var(--line-soft) !important; }
 .cx-head { flex-direction:column; align-items:flex-start; }
 .cx-meta { justify-content:flex-start; } }
</style>""", unsafe_allow_html=True)
def tag(kind): return {'du_lieu': '<span class="tag tag-du-lieu">Dữ liệu thực tế</span>', 'du_doan': '<span class="tag tag-du-doan">Dự đoán của mô hình</span>', 'gia_dinh': '<span class="tag tag-gia-dinh">Theo giả định</span>'}[kind]
def vn(x, d=0):
    if x is None or (isinstance(x, float) and np.isnan(x)): return '—'
    s = f'{x:,.{d}f}'; return s.replace(',', '#').replace('.', ',').replace('#', '.')
def usd(x): return vn(x) + ' USD'
def pct(x, d=1): return '—' if x is None or (isinstance(x, float) and np.isnan(x)) else vn(100 * x, d) + '%'
def fmt(d=0): return lambda x: vn(x, d)          # dùng trong Styler.format để mọi bảng hiển thị số kiểu Việt
def fpct(d=1): return lambda x: pct(x, d)

# Tương thích Streamlit: altair_chart ở các bản cũ chưa nhận tham số width. Cấu hình trục chỉ đổi cách hiển thị.
def altair_wide(chart, **kw):
    import inspect
    chart = (chart.configure_axis(labelColor=GREY, titleColor=GREY, labelFontSize=11, titleFontSize=11, titleFontWeight='normal',
                                  gridColor='#EDF0F4', domainColor='#C9D0D9', tickColor='#C9D0D9')
                  .configure_axisQuantitative(tickCount=6).configure_view(strokeWidth=0)
                  .configure_legend(labelColor=GREY, labelFontSize=11).configure(background='#FFFFFF'))
    if "width" in inspect.signature(st.altair_chart).parameters:
        return st.altair_chart(chart, width="stretch", **kw)
    return st.altair_chart(chart, use_container_width=True, **kw)

AX_VN = "replace(format(datum.value, ',.0f'), regexp(',', 'g'), '.')"   # số kiểu Việt trên trục: 40.000
def html(s): st.markdown(s, unsafe_allow_html=True)

def page_header(code, title, *kinds):
    meta = ''.join(tag(k) for k in kinds) + f'<span class="cx-chip">Mốc {pd.Timestamp(C.SCORING_DATE):%d/%m/%Y}</span><span class="cx-chip cx-chip-dark">{vai_tro}</span>'
    html(f'<div class="cx-head"><div><div class="cx-code">{code}</div><div class="cx-title">{title}</div></div><div class="cx-meta">{meta}</div></div>')

def section(label): html(f'<div class="cx-sec">{label}</div>')

def kpis(items):
    """items: (nhãn, giá trị, dòng phụ, tông) – tông 'risk' hoặc 'ok' chỉ đổi màu chữ."""
    cells = []
    for it in items:
        label, value, sub, tone = (list(it) + [None, None])[:4]; unit = ''
        if isinstance(value, str) and value.endswith(' USD'): value, unit = value[:-4], '<span class="cx-kpi-unit">USD</span>'
        cells.append(f'<div class="cx-kpi{" tone-" + tone if tone else ""}"><div class="cx-kpi-label">{label}</div><div class="cx-kpi-value">{value}{unit}</div>'
                     + (f'<div class="cx-kpi-sub">{sub}</div>' if sub else '') + '</div>')
    html(f'<div class="cx-kpis" style="--n:{len(items)}">{"".join(cells)}</div>')

def note(s, tone='', label=''):
    html(f'<div class="cx-note {tone}">' + (f'<span class="lbl">{label}</span>' if label else '') + f'{s}</div>')

def risk_matrix(mx):
    vmax = max(int(mx.values.max()), 1); rows = ''
    for h in mx.index:
        cells = ''.join(f'<td class="{"hot" if (h, lv) == ("A", "Cao") else ""}" style="background:rgba({"180,35,24" if lv == "Cao" else "31,58,95"},{.05 + .3 * mx.loc[h, lv] / vmax:.3f})">{vn(mx.loc[h, lv])}</td>' for lv in mx.columns)
        rows += f'<tr><th>Hạng {h}</th>{cells}</tr>'
    html(f'<table class="cx-matrix"><thead><tr><th></th><th>Rủi ro Cao</th><th>Rủi ro Thấp</th></tr></thead><tbody>{rows}</tbody></table>')

def chon_o(o):
    """Bấm một ô ma trận để lọc chéo; bấm lại ô đang chọn để bỏ."""
    st.session_state['cx_cell'] = None if st.session_state.get('cx_cell') == o else o

def bo_loc_cheo():
    st.session_state['cx_cell'] = None
    st.session_state['cx_xf_ver'] = st.session_state.get('cx_xf_ver', 0) + 1   # đổi key biểu đồ để xoá lựa chọn trên biểu đồ

def risk_matrix_buttons(mx, o):
    """Ma trận Rủi ro × Giá trị: mỗi ô là một nút, màu đậm theo số khách, ô A–Cao viền đỏ, ô đang lọc viền xanh."""
    vmax = max(int(mx.values.max()), 1); css = []
    hd = st.columns([1, 2, 2], gap='small')
    with hd[1]: html('<div class="cx-mhead">Rủi ro Cao</div>')
    with hd[2]: html('<div class="cx-mhead">Rủi ro Thấp</div>')
    for h in mx.index:
        cols = st.columns([1, 2, 2], gap='small', vertical_alignment='center')
        with cols[0]: html(f'<div class="cx-mrow">Hạng {h}</div>')
        for j, lv in enumerate(['Cao', 'Thấp']):
            k = f'cx_cell_{h}_{"Cao" if lv == "Cao" else "Thap"}'; v = int(mx.loc[h, lv])
            rgb = '180,35,24' if lv == 'Cao' else '31,58,95'
            ring = f'inset 0 0 0 3px {NAVY}' if o == (h, lv) else (f'inset 0 0 0 2px {RED}' if (h, lv) == ('A', 'Cao') else 'none')
            css.append(f'.st-key-{k} button {{ background:rgba({rgb},{.06 + .32 * v / vmax:.3f}) !important; box-shadow:{ring}; }}')
            if (h, lv) == ('A', 'Cao'): css.append(f'.st-key-{k} button p {{ color:{RED} !important; }}')
            cols[j + 1].button(vn(v), key=k, on_click=chon_o, args=((h, lv),), width='stretch')
    html('<style>' + ''.join(css) + '</style>')

def mo_ho_so(table_key, ids_key):
    """Chọn một dòng trong bảng thì mở Hồ sơ khách hàng của dòng đó (chạy trước khi trang vẽ lại)."""
    rows = st.session_state[table_key].selection.rows
    if rows:
        st.session_state['companyx_customer_id'] = int(st.session_state[ids_key][rows[0]])
        st.session_state['cx_tu_man'] = st.session_state['companyx_nav']
        st.session_state['companyx_nav'] = PAGES[2]

IMG = f'{ROOT}/latex/IMAGE'
_KENH = ', '.join(f"{k} {v['cost']:.0f} USD và {v['success']:.0%}" for k, v in C.CHANNELS.items())
GHI_CHU = {   # nội dung lấy từ báo cáo (Chương 4, 5, 7, 8), hình lấy từ latex/IMAGE
    'recency': dict(nut='Vì sao khách lâu không mua lại có 0% rủi ro Cao?', title='Khách mua gần đây bị chấm rủi ro cao hơn',
        lead='Đây là quy luật của dữ liệu tại mốc mô hình học, không phải lỗi hiển thị.',
        img=[('eda_y_theo_khoang.png', 'Tỷ lệ không mua lại trong 90 ngày theo khoảng Recency, NSub, Monetary tại mốc huấn luyện 01/03/2014'),
             ('eda_lech_moc.png', 'Phân bố Recency ở mốc học và mốc dự đoán (trái), PSI của từng thuộc tính (phải)')],
        pts=[('Dữ liệu cho thấy gì', 'Tại mốc 01/03/2014, khách mua trong 270 ngày gần nhất có 88,9% đến 91,9% không mua lại trong 90 ngày, còn khách đã từ 270 ngày không mua chỉ 28,5% đến 36,7%. Đây không phải chu kỳ mua dài của khách mà do thành phần khách khác nhau ở từng mốc.'),
             ('Đối chiếu', 'Quy tắc Recency đảo chiều (xếp khách mới mua lên trước) đạt ROC-AUC 0,717, gần bằng Naive Bayes 0,720, nên mô hình đang học đúng quy luật này.'),
             ('Cần đọc thận trọng', 'Recency lệch nhiều nhất giữa mốc học và mốc dự đoán (PSI 0,37). Khoảng 270–364 ngày chiếm 3,6% khách ở mốc học nhưng 19,0% ở mốc dự đoán, vì nhóm khách đợt tăng vọt tháng 7/2013 nay rơi vào khoảng này. Xác suất của khoảng này chỉ dựa trên 507 khách.')],
        src='Chương 4: Chia thuộc tính thành khoảng; Mốc dự đoán có khác mốc học không. Chương 5: Bảng so sánh mô hình.'),
    'muc_cao': dict(nut='Mức rủi ro Cao được xác định thế nào?', title='Mức rủi ro Cao là thứ tự ưu tiên trong từng hạng',
        lead=f'Khách mức Cao là {100 - C.RISK_HIGH_PERCENTILE}% khách có xác suất không mua lại cao nhất trong cùng hạng ABC.',
        img=[('m_diem_theo_hang.png', 'Phân bố RiskScore của khách mức Cao (đỏ) và mức Thấp (xám) theo hạng tại mốc 08/07/2014. Đường chấm là RiskScore thấp nhất của khách mức Cao')],
        pts=[('Cách tính', f'RiskPercentile là thứ hạng phần trăm của RiskScore trong từng hạng ABC. Phân vị từ {C.RISK_HIGH_PERCENTILE} trở lên là mức Cao; các khách đồng điểm xếp theo Recency giảm dần.'),
             ('Vì sao tính trong hạng', 'Nếu tính chung, khách mức Cao dồn vào hạng C và ma trận Rủi ro × Giá trị không còn phân biệt được.'),
             ('Cách đọc', 'Không có một ngưỡng chung. RiskScore thấp nhất của khách mức Cao là 0,935 ở hạng A, 0,886 ở hạng B và 0,986 ở hạng C, đều trên tỷ lệ nền 0,82. Mức rủi ro là thứ tự ưu tiên, còn RiskScore mới là xác suất.')],
        src='Chương 5: Chấm điểm và mức rủi ro (Bảng kết quả chấm điểm theo hạng ABC).'),
    'diem_cao': dict(nut='Vì sao phần lớn khách có xác suất trên 80%?', title='Tỷ lệ nền cao và nhãn 90 ngày',
        lead='82,0% khách tại mốc huấn luyện không mua lại trong 90 ngày, nên xác suất của mô hình cũng cao.',
        img=[('m_nhan180.png', 'Tỷ lệ không mua lại theo nhãn 90 ngày và 180 ngày tại 13 mốc, và tỷ lệ khách bị gắn nhãn 90 ngày nhưng mua lại trong ngày 90 đến 180')],
        pts=[('Phân bố điểm', 'RiskScore của Naive Bayes trên toàn bộ khách có trung vị 0,922, hai tứ phân vị 0,803 và 0,975.'),
             ('Nhãn lẫn khách chưa đến kỳ', 'Trung bình 26,2% khách bị gắn nhãn không mua lại vẫn mua lại trong ngày 90 đến 180. Với nhãn 180 ngày, tỷ lệ này giảm từ 80,8% xuống 59,6% và ROC-AUC của Naive Bayes tăng từ 0,694 lên 0,752.'),
             ('Cách đọc', 'Xác suất cao không có nghĩa khách chắc chắn bỏ đi. DSS xếp ưu tiên theo xác suất nhân giá trị khách và so với chi phí chăm sóc, không dùng một ngưỡng tuyệt đối.')],
        src='Chương 5: Nhãn 90 ngày so với 180 ngày. Chương 8: Hướng phát triển.'),
    'auc': dict(nut='Vì sao chọn Naive Bayes khi ROC-AUC chỉ khoảng 0,72?', title='Chọn mô hình theo giá trị quyết định',
        lead='Naive Bayes xếp hạng gần như không hơn quy tắc đơn giản, lợi thế của nó nằm ở chất lượng xác suất.',
        img=[('m_z_mo_hinh.png', 'Ba tiêu chí của chín phương án, trung bình bốn fold. Đường đứt là mốc so sánh của từng tiêu chí'),
             ('m_roc_pr.png', 'Đường ROC và Precision-Recall của các mô hình')],
        pts=[('Thừa nhận', 'ROC-AUC của Naive Bayes là 0,7207, chỉ nhỉnh hơn quy tắc Recency đảo chiều (0,7191).'),
             ('Ba điều kiện đặt trước', 'ĐK1 xếp hạng: ROC-AUC không thấp hơn quy tắc Recency đảo chiều. ĐK2 xác suất: Brier thấp hơn cách dự đoán một xác suất hằng. ĐK3 quyết định: Z cao hơn khi chỉ chọn theo giá trị khách.'),
             ('Kết quả', 'Naive Bayes có Brier 0,125 (quy tắc Recency 0,269) và đứng đầu về Z. Mạng nơ-ron có ROC-AUC cao nhất (0,751) nhưng Z thấp hơn Naive Bayes ở cả bốn mốc, chênh trung bình 3.504 USD.'),
             ('Vì sao xác suất quan trọng', 'DSS nhân xác suất với giá trị khách rồi trừ chi phí chăm sóc, nên cần xác suất sát thực tế chứ không chỉ thứ tự.')],
        src='Chương 5: Điều kiện chọn mô hình, Kết quả so sánh. Chương 7: Đánh giá.'),
    'du_lieu': dict(nut='Dữ liệu cập nhật đến khi nào?', title='Mốc dữ liệu của hệ thống',
        lead=f'Điểm rủi ro được chấm tại mốc {pd.Timestamp(C.SCORING_DATE):%d/%m/%Y}, hệ thống không cập nhật theo thời gian thực.',
        img=[('moc_thoi_gian.png', 'Lịch các mốc huấn luyện, cửa sổ 90 ngày xác định nhãn và mốc đánh giá'),
             ('eda_xu_huong_thang.png', 'Số đơn, doanh thu và số dòng chi tiết theo nhóm sản phẩm của từng tháng')],
        pts=[('Mốc học và mốc chấm', f'Mô hình học tại mốc {pd.Timestamp(C.SCORING_TRAIN_DATE):%d/%m/%Y} rồi chấm điểm 18.360 khách tại mốc {pd.Timestamp(C.SCORING_DATE):%d/%m/%Y}, cách nhau 129 ngày; bốn cặp thử cách nhau 105 đến 106 ngày.'),
             ('Nguồn dữ liệu', 'Mặc định DSS đọc kết quả chấm điểm đã xuất (results/cum6/dss_khach.csv). Khi chạy với DSS_SOURCE=db, DSS đọc điểm trong kho (analytics.CustomerRiskScore) theo phiên bản mô hình đang dùng. Muốn có điểm mới phải nạp dữ liệu và chấm lại.'),
             ('Tháng 6/2014', 'Tháng này có 930 đơn nhưng không có xe đạp nào, doanh thu khoảng 48,7 nghìn USD, nên không dùng để xác định khách rời bỏ.'),
             ('Hướng phát triển', f'Đối chiếu điểm đã chấm tại {pd.Timestamp(C.SCORING_DATE):%d/%m/%Y} với hành vi mua thật khi có dữ liệu sau ngày này.')],
        src='Chương 4: Lịch các mốc, Xu hướng theo thời gian, Mốc dự đoán có khác mốc học không. Chương 8: Hướng phát triển.'),
    'vong': dict(nut='Tỷ lệ chăm sóc thành công là giả định', title='Giả định về hiệu quả chăm sóc',
        lead='Tỷ lệ thành công và chi phí chăm sóc chưa được đo bằng chiến dịch thật, nên Z dùng để so sánh các lựa chọn, không phải dự báo doanh thu.',
        img=[('d_do_nhay.png', 'Thay đổi của Z khi từng tham số của kịch bản cơ sở tăng hoặc giảm 20%'),
             ('d_mo_phong.png', 'Phân bố của Z trong 10.000 lần mô phỏng với r theo phân phối Beta (trung bình 10%)')],
        pts=[('Giả định đang dùng', f"Kịch bản cơ sở r = {C.BASE_SCENARIO['r']:.0%}, c = {C.BASE_SCENARIO['c']:.0f} USD. Theo kênh (chi phí và tỷ lệ thành công): {_KENH}."),
             ('Kết quả có vững không', 'Z nhạy nhất với r, p và g (cùng đổi 22,7% khi giảm 20%). Nếu trừ khách chưa đến kỳ khỏi lợi ích, Z cơ sở còn 205.555 USD với tỷ lệ thành công hoà vốn 1,63%. Mô phỏng 10.000 lần cho Z trung bình 290.490 USD, xác suất lỗ 1,7%.'),
             ('Chưa khép vòng', 'DSS hiện dừng ở bước xuất danh sách CSV, kết quả chiến dịch chưa quay lại hệ thống. Hướng phát triển: chạy chiến dịch có nhóm đối chứng để đo tỷ lệ thật, và kết nối CRM để kết quả quay về DSS.')],
        src='Chương 7: DSS so với cách chọn khách đơn giản, độ nhạy và mô phỏng. Chương 8: Hướng phát triển.'),
}

def mo_ghi_chu(k):
    g = GHI_CHU[k]
    @st.dialog(g['title'], width='large')
    def _hop():
        html(f'<div class="cx-gc-lead">{g["lead"]}</div>')
        for col, (f, cap) in zip(st.columns(len(g['img']), gap='medium'), g['img']):
            with col: st.image(f'{IMG}/{f}', caption=cap, width='stretch')
        html(''.join(f'<div class="cx-gc-pt"><b>{a}</b>{b}</div>' for a, b in g['pts']) + f'<div class="cx-gc-src">Nguồn: báo cáo, {g["src"]}</div>')
    _hop()

def ghi_chu(*keys, noi=''):
    """Hàng liên kết 'lưu ý' nhỏ; bấm thì mở modal có hình minh hoạ và giải thích."""
    with st.container(horizontal=True, gap='medium'):
        for k in keys:
            if st.button(GHI_CHU[k]['nut'], key=f'cx_gc_{k}_{noi}', type='tertiary', icon=':material/info:'): mo_ghi_chu(k)

def nav_to(target):
    # on_click được thực thi trước khi radio widget khởi tạo lại.
    st.session_state['companyx_nav'] = target


# Diễn giải luật lá cây (TopFactors) sang lời cho người quản lý. Dữ liệu gốc trong kho giữ nguyên, chỉ đổi cách hiển thị.
_TEN_TT = {'Recency': ('lần mua gần nhất cách đây', 'ngày'), 'Monetary': ('tổng chi tiêu', 'USD'), 'Tenure': ('đã là khách được', 'ngày'), 'Frequency': ('số đơn đã mua', 'đơn'),
           'Orders90': ('số đơn trong 90 ngày gần nhất', 'đơn'), 'Orders180': ('số đơn trong 180 ngày gần nhất', 'đơn'), 'NSub': ('số danh mục đã mua', 'danh mục')}
def de_hieu(top):
    import re
    if not isinstance(top, str) or ':' not in top: return top
    head, rest = top.split(':', 1); rule, _, info = rest.partition('|'); parts = []; bound = {}
    for f, op, val in re.findall(r'(\w+) (<=|>) ([\d.]+)', rule):                 # gộp các điều kiện cùng thuộc tính thành một khoảng (lo, hi]
        lo, hi = bound.get(f, (None, None)); v = float(val)
        bound[f] = (max(lo, v) if (op == '>' and lo is not None) else (v if op == '>' else lo), min(hi, v) if (op == '<=' and hi is not None) else (v if op == '<=' else hi))
    for f, (lo, hi) in bound.items():
        if f == 'BikeBuyer': parts.append('chủ yếu mua xe đạp' if lo is not None else 'chủ yếu mua phụ kiện, quần áo'); continue
        if f.startswith('Share_'): ten, show = 'tỷ trọng ' + dict(Share_Bikes='xe đạp', Share_Accessories='phụ kiện', Share_Clothing='quần áo')[f], (lambda x: pct(x, 0))
        else: ten, dv = _TEN_TT.get(f, (f, '')); show = (lambda x, dv=dv: f'{vn(int(x))} {dv}')
        parts.append(f'{ten} từ {show(lo)} đến {show(hi)}' if lo is not None and hi is not None else f'{ten} trên {show(lo)}' if lo is not None else f'{ten} không quá {show(hi)}')
    m = re.search(r'nhóm (\d+) khách, tỷ lệ không mua lại ([\d.]+)%', info)
    tail = f'. Lúc huấn luyện nhóm này có {vn(int(m.group(1)))} khách, {vn(float(m.group(2)), 1)}% không mua lại trong 90 ngày' if m else ''
    return f'{head.strip()}: ' + ', '.join(parts) + tail + '.'

CHAN = {'R3': ('Liên hệ cá nhân kèm ưu đãi', 25.0, 0.15), 'R4': ('Mời quay lại kèm ưu đãi', 15.0, 0.12), 'R5': ('Email cá nhân hoá tự động', 3.0, 0.05)}
TEN = {'N1': 'N1 – Mua nhiều lần, giá trị cao', 'N2': 'N2 – Mua một lần, giá trị trung bình', 'N3': 'N3 – Mua một lần, đã lâu không quay lại', 'N4': 'N4 – Mua lặp lại, giá trị thấp', 'N5': 'N5 – Mua một lần, giá trị thấp'}
MAU_NHOM = {'N1': NAVY, 'N2': '#4A7FB5', 'N3': '#9B2C2C', 'N4': '#7A4E00', 'N5': '#8A94A6'}

@st.cache_data
def load():
    df = pd.read_csv(f'{R6}/dss_khach.csv'); df[['SanPhamGoiY', 'QuyTacSP']] = df[['SanPhamGoiY', 'QuyTacSP']].fillna('')
    if os.getenv('DSS_SOURCE') == 'db':
        try:
            con = C.connect(); live = pd.read_sql("SELECT r.CustomerID, r.RiskScore, r.RiskPercentile, r.RiskLevel, r.TreeScore, r.TopFactors, s.ABCClass AS ABC FROM analytics.CustomerRiskScore r JOIN analytics.CustomerSegment s ON s.CustomerID=r.CustomerID AND s.SnapshotDate=r.ScoreDate JOIN analytics.ModelRegistry m ON m.ModelVersion=r.ModelVersion AND m.IsActive=1 AND m.ModelRole='SCORING'", con)
            df = df.drop(columns=['RiskScore', 'RiskPercentile', 'RiskLevel', 'TreeScore', 'TopFactors', 'ABC']).merge(live, on='CustomerID')
        except Exception as e: st.sidebar.warning(f'Không nối được kho, dùng dữ liệu đã xuất: {e}')
    return df
df = load()
folds = pd.read_csv(f'{R4}/bang_4_3_2a_theo_fold.csv'); moc = pd.read_csv(f'{ROOT}/results/cum3b/bang_4_3_1a_moc.csv')

def solve(d, r, c, B, kenh=False):
    """Chọn khách theo giá trị kỳ vọng trong ngân sách (mục 3.5.4). kenh=True: chi phí và tỷ lệ thành công theo kênh R3–R5."""
    p, v = d.RiskScore.values, d.v.values
    ck, rk = (d.c_k.values, d.r_k.values) if kenh else (np.full(len(d), c), np.full(len(d), r))
    ev = p * rk * v - ck; ok = ev > 0; order = np.argsort(-(ev / ck)) if kenh else np.argsort(-(p * v))
    cum = np.cumsum(ck[order]); sel = order[(cum <= B) & ok[order]]; return sel, ev
def hist_chart(series, title, color=NAVY, x_title='RiskScore'):
    cnt, edges = np.histogram(series, bins=20, range=(0, 1))
    h = pd.DataFrame({'lo': edges[:-1], 'hi': edges[1:], 'so_khach': cnt})
    h['khoang'] = [f'{a:.2f}–{b:.2f}'.replace('.', ',') for a, b in zip(h.lo, h.hi)]
    return alt.Chart(h).mark_bar(color=color).encode(x=alt.X('lo:Q', bin='binned', title=x_title, axis=alt.Axis(format='.0%', tickCount=10)), x2='hi:Q',
                                                     y=alt.Y('so_khach:Q', title='Số khách', axis=alt.Axis(labelExpr=AX_VN)),
                                                     tooltip=[alt.Tooltip('khoang:N', title='Khoảng'), alt.Tooltip('so_khach:Q', title='Số khách', format=',.0f')]).properties(height=270, title=title)


# -------- VISUAL-ONLY: charts generated from existing, already computed data --------
def chart_high_risk_by_group(grouped):
    """Existing metric 'ty_le_rui_ro_cao' from the overview table; no new risk definition."""
    source = grouped.reset_index()[['Nhom', 'so_khach', 'ty_le_rui_ro_cao']].copy()
    source['NhomDayDu'] = source['Nhom'].map(TEN)
    bars = alt.Chart(source).mark_bar(color=RED, size=22).encode(
        y=alt.Y('NhomDayDu:N', title=None, sort=None, axis=alt.Axis(labelLimit=280)),
        x=alt.X('ty_le_rui_ro_cao:Q', title='Tỷ lệ khách rủi ro Cao trong nhóm',
                axis=alt.Axis(format='.0%', tickCount=5), scale=alt.Scale(domain=[0, 1])),
        tooltip=[alt.Tooltip('NhomDayDu:N', title='Nhóm'),
                 alt.Tooltip('so_khach:Q', title='Số khách trong nhóm', format=',.0f'),
                 alt.Tooltip('ty_le_rui_ro_cao:Q', title='Tỷ lệ rủi ro Cao', format='.1%')])
    labels = bars.mark_text(align='left', dx=6, color='#101828', fontWeight=600).encode(text=alt.Text('ty_le_rui_ro_cao:Q', format='.0%'))
    return (bars + labels).properties(height=250)


def chart_customer_scores(customer):
    """Plot actual two scores; TreeScore is the independent CART reference, not NB attribution."""
    source = pd.DataFrame({
        'Mô hình': ['Naive Bayes · RiskScore', 'Decision Tree · TreeScore'],
        'Giá trị': [float(customer.RiskScore), float(customer.TreeScore)],
    })
    bars = alt.Chart(source).mark_bar(size=26).encode(
        y=alt.Y('Mô hình:N', title=None, sort=None, axis=alt.Axis(labelLimit=265)),
        x=alt.X('Giá trị:Q', title='Điểm (0–1)', scale=alt.Scale(domain=[0, 1.1]),
                axis=alt.Axis(format='.0%', values=[0, .2, .4, .6, .8, 1])),
        color=alt.Color('Mô hình:N', legend=None,
                        scale=alt.Scale(domain=source['Mô hình'].tolist(), range=[NAVY, AMBER])),
        tooltip=[alt.Tooltip('Mô hình:N'), alt.Tooltip('Giá trị:Q', format='.3f')])
    labels = bars.mark_text(align='left', dx=6, fontWeight=600).transform_calculate(lbl="replace(format(datum['Giá trị'], '.1%'), '.', ',')").encode(text='lbl:N', color=alt.value('#101828'))
    return (bars + labels).properties(height=120)


def chart_what_if_z(what_if):
    """Visualize existing what-if Z columns; no recalculation."""
    source = what_if[['Kịch bản', 'Z (USD)']].copy()
    source['Loại'] = np.where(source['Kịch bản'].eq('Cơ sở'), 'Cơ sở', 'Kịch bản khác')
    return alt.Chart(source).mark_bar(size=22).encode(
        y=alt.Y('Kịch bản:N', title=None, sort=source['Kịch bản'].tolist(),
                axis=alt.Axis(labelLimit=220)),
        x=alt.X('Z (USD):Q', title='Giá trị ròng kỳ vọng Z (USD)', axis=alt.Axis(labelExpr=AX_VN)),
        color=alt.Color('Loại:N', legend=None,
                        scale=alt.Scale(domain=['Cơ sở', 'Kịch bản khác'], range=[AMBER, NAVY])),
        tooltip=[alt.Tooltip('Kịch bản:N'), alt.Tooltip('Z (USD):Q', title='Z (USD)', format=',.0f')]
    ).properties(height=max(230, 33 * len(source)))


def chart_payoff_by_budget(payoff):
    """Plot only the three r values provided in bang_4_4_payoff.csv."""
    source = payoff[['Ngân sách B (USD)', 'Z nếu r = 2% (bi quan)',
                     'Z nếu r = 10% (cơ sở)', 'Z nếu r = 20% (lạc quan)']].melt(
        id_vars='Ngân sách B (USD)', var_name='Giả định thành công', value_name='Z (USD)')
    return alt.Chart(source).mark_line(point=alt.OverlayMarkDef(size=55, shape='square'), strokeWidth=2.4).encode(
        x=alt.X('Ngân sách B (USD):Q', title='Ngân sách B (USD)', axis=alt.Axis(labelExpr=AX_VN)),
        y=alt.Y('Z (USD):Q', title='Giá trị ròng kỳ vọng Z (USD)', axis=alt.Axis(labelExpr=AX_VN)),
        color=alt.Color('Giả định thành công:N', title=None,
                        scale=alt.Scale(domain=['Z nếu r = 2% (bi quan)', 'Z nếu r = 10% (cơ sở)',
                                                'Z nếu r = 20% (lạc quan)'],
                                        range=[RED, NAVY, GREEN]),
                        legend=alt.Legend(orient='bottom', labelLimit=255, symbolType='square')),
        tooltip=[alt.Tooltip('Ngân sách B (USD):Q', title='B (USD)', format=',.0f'),
                 alt.Tooltip('Giả định thành công:N'), alt.Tooltip('Z (USD):Q', title='Z (USD)', format=',.0f')]
    ).properties(height=280)


def chart_care_channels(selected):
    """Distribution of the actual selected list after user's manual add/remove."""
    source = selected['KenhRule'].value_counts().reindex(list(CHAN), fill_value=0).reset_index()
    source.columns = ['Quy tắc', 'Số khách']
    source['Hình thức'] = source['Quy tắc'].map(lambda code: code + ' · ' + CHAN[code][0])
    source = source[source['Số khách'] > 0].copy()  # ẩn kênh không có khách trong danh sách hiện tại
    bars = alt.Chart(source).mark_bar(size=26).encode(
        y=alt.Y('Hình thức:N', title=None, sort=None, axis=alt.Axis(labelLimit=260)),
        x=alt.X('Số khách:Q', title='Số khách trong danh sách', axis=alt.Axis(labelExpr=AX_VN, tickCount=6)),
        color=alt.Color('Quy tắc:N', legend=None,
                        scale=alt.Scale(domain=['R3', 'R4', 'R5'], range=[AMBER, NAVY, GREEN])),
        tooltip=[alt.Tooltip('Hình thức:N'), alt.Tooltip('Số khách:Q', format=',.0f')])
    labels = bars.mark_text(align='left', dx=6, fontWeight=600).transform_calculate(lbl="replace(format(datum['Số khách'], ',.0f'), regexp(',', 'g'), '.')").encode(text='lbl:N', color=alt.value('#101828'))
    return (bars + labels).properties(height=160)


def chart_matured_snapshot_trends(snapshots):
    """Use only historical snapshots with an available 90-day label. 08/07/2014 is excluded."""
    source = snapshots.loc[snapshots['ty_le_y1'].notna(), ['T', 'ty_le_y1', 'mot_don']].copy()
    source['Ngày'] = pd.to_datetime(source['T'], format='%d/%m/%Y')
    source = source.rename(columns={
        'ty_le_y1': 'Tỷ lệ không mua lại trong 90 ngày',
        'mot_don': 'Tỷ lệ khách mới mua một đơn',
    }).melt(id_vars='Ngày', value_vars=['Tỷ lệ không mua lại trong 90 ngày',
                                        'Tỷ lệ khách mới mua một đơn'],
            var_name='Chỉ số', value_name='Tỷ lệ')
    return alt.Chart(source).mark_line(point=alt.OverlayMarkDef(size=45, shape='square'), strokeWidth=2.3).encode(
        x=alt.X('Ngày:T', title='Mốc Snapshot', axis=alt.Axis(format='%m/%Y')),
        y=alt.Y('Tỷ lệ:Q', title='Tỷ lệ', axis=alt.Axis(format='.0%'),
                scale=alt.Scale(domain=[0, 1])),
        color=alt.Color('Chỉ số:N', title=None,
                        scale=alt.Scale(domain=['Tỷ lệ không mua lại trong 90 ngày',
                                                'Tỷ lệ khách mới mua một đơn'],
                                        range=[NAVY, AMBER]),
                        legend=alt.Legend(orient='bottom', labelLimit=310, symbolType='square')),
        tooltip=[alt.Tooltip('Ngày:T', title='Mốc', format='%d/%m/%Y'),
                 alt.Tooltip('Chỉ số:N'), alt.Tooltip('Tỷ lệ:Q', format='.1%')]
    ).properties(height=260)

def chart_group_select(grouped):
    """Tỷ lệ rủi ro Cao theo nhóm, bấm vào cột để lọc chéo cả màn hình."""
    source = grouped.reset_index()[['Nhom', 'so_khach', 'ty_le_rui_ro_cao']].copy()
    source['Nhãn'] = [f'{TEN[n]} · {pct(v, 0)}' for n, v in zip(source.Nhom, source.ty_le_rui_ro_cao)]
    sel = alt.selection_point(name='chon_nhom', fields=['Nhom'])
    return alt.Chart(source).mark_bar(color=RED, size=22, cursor='pointer').encode(
        y=alt.Y('Nhãn:N', title=None, sort=None, axis=alt.Axis(labelLimit=300)),
        x=alt.X('ty_le_rui_ro_cao:Q', title='Tỷ lệ khách rủi ro Cao trong nhóm', axis=alt.Axis(format='.0%', tickCount=5), scale=alt.Scale(domain=[0, 1])),
        opacity=alt.condition(sel, alt.value(1), alt.value(.3)),
        tooltip=[alt.Tooltip('Nhãn:N', title='Nhóm'), alt.Tooltip('so_khach:Q', title='Số khách trong nhóm', format=',.0f'), alt.Tooltip('ty_le_rui_ro_cao:Q', title='Tỷ lệ rủi ro Cao', format='.1%')]
    ).add_params(sel).properties(height=250)


# -------- Biểu đồ bổ sung: chỉ vẽ lại dữ liệu đã có (dss_khach.csv và các bảng trong results/), không tạo số liệu mới --------
SQ = alt.OverlayMarkDef(size=45, shape='square')
LEGEND_B = dict(orient='bottom', symbolType='square', labelLimit=300)

def chart_value_at_risk(d):
    """Tổng chi tiêu đã mua theo hạng ABC, tách theo mức rủi ro."""
    s = d.groupby(['ABC', 'RiskLevel']).Monetary.sum().reset_index(); s['Hạng'] = 'Hạng ' + s.ABC
    s['Mức'] = 'Rủi ro ' + s.RiskLevel; s['thu_tu'] = (s.RiskLevel != 'Cao').astype(int)
    return alt.Chart(s).mark_bar().encode(
        y=alt.Y('Hạng:N', title=None, sort=['Hạng A', 'Hạng B', 'Hạng C']),
        x=alt.X('sum(Monetary):Q', title='Tổng chi tiêu đã mua (triệu USD)', stack='zero', axis=alt.Axis(labelExpr="replace(format(datum.value / 1000000, ',.0f'), regexp(',', 'g'), '.')", tickCount=6)),
        color=alt.Color('Mức:N', title=None, scale=alt.Scale(domain=['Rủi ro Cao', 'Rủi ro Thấp'], range=[RED, '#B8C4D6']), legend=alt.Legend(**LEGEND_B)),
        order=alt.Order('thu_tu:Q'),
        tooltip=[alt.Tooltip('Hạng:N'), alt.Tooltip('Mức:N'), alt.Tooltip('sum(Monetary):Q', title='Tổng chi tiêu (USD)', format=',.0f')]
    ).properties(height=300)


VUNG = [f'{lo + 1}–{hi}' if hi < 10**6 else f'≥ {lo + 1}' for lo, hi in zip(C.RECENCY_BINS[:-1], C.RECENCY_BINS[1:])]   # nhóm Recency theo Bảng 3.10

def chon_vung(v):
    st.session_state['cx_vung'] = None if st.session_state.get('cx_vung') == v else v

def recency_value_grid(d, sel):
    """Lưới Hạng ABC × số ngày từ lần mua gần nhất: số khách mỗi ô, màu đỏ đậm theo tỷ lệ rủi ro Cao; bấm ô để xem danh sách khách."""
    b = pd.cut(d.Recency, C.RECENCY_BINS, labels=VUNG)
    n = pd.crosstab(d.ABC, b).reindex(index=['A', 'B', 'C'], columns=VUNG).fillna(0).astype(int)
    cao = pd.crosstab(d.ABC, b, values=(d.RiskLevel == 'Cao').astype(int), aggfunc='sum').reindex(index=['A', 'B', 'C'], columns=VUNG).fillna(0).astype(int)
    w = [.8] + [1] * len(VUNG); css = []
    hd = st.columns(w, gap='small')
    for c, lab in zip(hd[1:], VUNG):
        with c: html(f'<div class="cx-mhead">{lab}</div>')
    for h in n.index:
        cols = st.columns(w, gap='small', vertical_alignment='center')
        with cols[0]: html(f'<div class="cx-mrow">Hạng {h}</div>')
        for j, lab in enumerate(VUNG):
            k = f'cx_vung_{h}_{j}'; v, vc = int(n.loc[h, lab]), int(cao.loc[h, lab]); r = vc / v if v else 0
            ring = f'inset 0 0 0 3px {NAVY}' if sel == (h, lab) else 'none'
            css.append(f'.st-key-{k} button {{ --sub:"{pct(r, 0)} Cao"; background:rgba(180,35,24,{.04 + .4 * r:.3f}) !important; box-shadow:{ring}; }}')
            cols[j + 1].button(vn(v), key=k, on_click=chon_vung, args=((h, lab),), width='stretch', disabled=v == 0)
    html('<style>' + ''.join(css) + '</style>')
    html('<div class="cx-mhead" style="text-align:center;padding:.4rem 0 0">Số ngày từ lần mua gần nhất · mỗi ô: số khách và tỷ lệ rủi ro Cao</div>')


def chart_product_mix_by_group():
    """Tỷ trọng doanh thu theo danh mục của từng nhóm (bang_4_4_co_cau_san_pham.csv)."""
    s = pd.read_csv(f'{R6}/bang_4_4_co_cau_san_pham.csv').rename(columns={'ty_trong_Bikes': 'Xe đạp', 'ty_trong_Accessories': 'Phụ kiện', 'ty_trong_Clothing': 'Quần áo'})
    s['NhomDayDu'] = s.Nhom.map(TEN)
    s = s.melt(id_vars=['Nhom', 'NhomDayDu'], value_vars=['Xe đạp', 'Phụ kiện', 'Quần áo'], var_name='Danh mục', value_name='Tỷ trọng')
    s['thu_tu'] = s['Danh mục'].map({'Xe đạp': 0, 'Phụ kiện': 1, 'Quần áo': 2})
    return alt.Chart(s).mark_bar().encode(
        y=alt.Y('NhomDayDu:N', title=None, sort=list(TEN.values()), axis=alt.Axis(labelLimit=280)),
        x=alt.X('Tỷ trọng:Q', title='Tỷ trọng chi tiêu theo danh mục', stack='normalize', axis=alt.Axis(format='.0%', tickCount=5)),
        color=alt.Color('Danh mục:N', title=None, scale=alt.Scale(domain=['Xe đạp', 'Phụ kiện', 'Quần áo'], range=[NAVY, '#7FA6D6', AMBER]), legend=alt.Legend(orient='right', symbolType='square')),
        order=alt.Order('thu_tu:Q'),
        tooltip=[alt.Tooltip('NhomDayDu:N', title='Nhóm'), alt.Tooltip('Danh mục:N'), alt.Tooltip('Tỷ trọng:Q', format='.1%')]
    ).properties(height=250)


def chart_monthly_revenue():
    """Doanh thu theo tháng (chuoi_thang.csv) và dự báo hồi quy tuyến tính 04–06/2014 (bang_4_4_du_bao.csv)."""
    m = pd.read_csv(f'{R6}/chuoi_thang.csv', parse_dates=['OrderDate'])[['OrderDate', 'rev']]; m['Chuỗi'] = 'Thực tế'
    fc = pd.read_csv(f'{R6}/bang_4_4_du_bao.csv'); pred = json.loads(fc.loc[fc.chi_so == 'rev', 'du_bao_04_06_2014'].iloc[0])
    f = pd.DataFrame({'OrderDate': pd.to_datetime(['2014-04-01', '2014-05-01', '2014-06-01']), 'rev': pred, 'Chuỗi': 'Dự báo hồi quy tuyến tính'})
    s = pd.concat([m, f], ignore_index=True)
    return alt.Chart(s).mark_line(point=SQ, strokeWidth=2.3).encode(
        x=alt.X('OrderDate:T', title=None, axis=alt.Axis(format='%m/%Y', labelAngle=0)),
        y=alt.Y('rev:Q', title='Doanh thu (USD)', axis=alt.Axis(labelExpr=AX_VN)),
        color=alt.Color('Chuỗi:N', title=None, scale=alt.Scale(domain=['Thực tế', 'Dự báo hồi quy tuyến tính'], range=[NAVY, AMBER]), legend=alt.Legend(**LEGEND_B)),
        strokeDash=alt.StrokeDash('Chuỗi:N', scale=alt.Scale(domain=['Thực tế', 'Dự báo hồi quy tuyến tính'], range=[[1, 0], [5, 3]]), legend=None),
        tooltip=[alt.Tooltip('OrderDate:T', title='Tháng', format='%m/%Y'), alt.Tooltip('Chuỗi:N'), alt.Tooltip('rev:Q', title='Doanh thu (USD)', format=',.0f')]
    ).properties(height=260)


def chart_customer_position(data, customer):
    """Vị trí xác suất của khách trong phân bố của cùng hạng ABC; ngưỡng Cao = điểm thấp nhất của khách mức Cao trong hạng."""
    tier = data[data.ABC == customer.ABC]; nguong = tier.loc[tier.RiskLevel == 'Cao', 'RiskScore'].min()
    cnt, edges = np.histogram(tier.RiskScore, bins=20, range=(0, 1))
    h = pd.DataFrame({'lo': edges[:-1], 'hi': edges[1:], 'so_khach': cnt}); h['Vùng'] = np.where(h.hi > nguong, 'Vùng rủi ro Cao', 'Vùng rủi ro Thấp')
    bars = alt.Chart(h).mark_bar().encode(
        x=alt.X('lo:Q', bin='binned', title=f'Xác suất không mua lại – khách hạng {customer.ABC}', axis=alt.Axis(format='.0%', tickCount=5)), x2='hi:Q',
        y=alt.Y('so_khach:Q', title='Số khách', axis=alt.Axis(labelExpr=AX_VN)),
        color=alt.Color('Vùng:N', title=None, scale=alt.Scale(domain=['Vùng rủi ro Cao', 'Vùng rủi ro Thấp'], range=['#E8A39C', '#C9D3E0']), legend=alt.Legend(**LEGEND_B)),
        tooltip=[alt.Tooltip('lo:Q', title='Từ', format='.2f'), alt.Tooltip('hi:Q', title='Đến', format='.2f'), alt.Tooltip('so_khach:Q', title='Số khách', format=',.0f')])
    k = pd.DataFrame({'x': [float(customer.RiskScore)], 'nhan': [f'Khách {int(customer.CustomerID)}']})
    rule = alt.Chart(k).mark_rule(color=NAVY, strokeWidth=2.5).encode(x='x:Q')
    text = alt.Chart(k).mark_text(align='left', dx=5, dy=-6, color=NAVY, fontWeight=700).encode(x='x:Q', y=alt.value(8), text='nhan:N')
    return (bars + rule + text).properties(height=260)


def chart_vs_group(data, customer):
    """Chỉ số của khách chia cho trung vị cùng nhóm (1 = bằng trung vị nhóm)."""
    g = data[data.Nhom == customer.Nhom]; rows = []
    for ten, col in [('Ngày từ lần mua gần nhất', 'Recency'), ('Số đơn', 'Frequency'), ('Tổng chi tiêu', 'Monetary'), ('Thời gian là khách', 'Tenure'), ('Số danh mục', 'NSub')]:
        med = float(g[col].median())
        if med > 0: rows.append(dict(chi_so=ten, khach=float(customer[col]), trung_vi=med, ty_le=float(customer[col]) / med))
    s = pd.DataFrame(rows); s['Hướng'] = np.where(s.ty_le >= 1, 'Cao hơn trung vị', 'Thấp hơn trung vị')
    bars = alt.Chart(s).mark_bar().encode(
        y=alt.Y('chi_so:N', title=None, sort=None, axis=alt.Axis(labelLimit=200)),
        x=alt.X('ty_le:Q', title=f'Khách ÷ trung vị nhóm {customer.Nhom}', scale=alt.Scale(type='log'), axis=alt.Axis(labelExpr="replace(format(datum.value, '.2~f'), '.', ',') + '×'")), x2=alt.datum(1),
        color=alt.Color('Hướng:N', title=None, scale=alt.Scale(domain=['Cao hơn trung vị', 'Thấp hơn trung vị'], range=[NAVY, AMBER]), legend=alt.Legend(**LEGEND_B)),
        tooltip=[alt.Tooltip('chi_so:N', title='Chỉ số'), alt.Tooltip('khach:Q', title='Khách', format=',.0f'), alt.Tooltip('trung_vi:Q', title='Trung vị nhóm', format=',.0f'), alt.Tooltip('ty_le:Q', title='Tỷ lệ', format='.2f')])
    one = alt.Chart(pd.DataFrame({'x': [1]})).mark_rule(color='#101828', strokeWidth=1).encode(x='x:Q')
    return (bars + one).properties(height=260)


def chart_customer_mix(data, customer):
    """Cơ cấu chi tiêu theo danh mục: khách so với trung bình nhóm."""
    g = data[data.Nhom == customer.Nhom]
    s = pd.DataFrame([{'Đối tượng': f'Khách {int(customer.CustomerID)}', 'Xe đạp': customer.Share_Bikes, 'Phụ kiện': customer.Share_Accessories, 'Quần áo': customer.Share_Clothing},
                      {'Đối tượng': f'Trung bình nhóm {customer.Nhom}', 'Xe đạp': g.Share_Bikes.mean(), 'Phụ kiện': g.Share_Accessories.mean(), 'Quần áo': g.Share_Clothing.mean()}])
    s = s.melt(id_vars='Đối tượng', var_name='Danh mục', value_name='Tỷ trọng'); s['thu_tu'] = s['Danh mục'].map({'Xe đạp': 0, 'Phụ kiện': 1, 'Quần áo': 2})
    return alt.Chart(s).mark_bar().encode(
        y=alt.Y('Đối tượng:N', title=None, sort=None, axis=alt.Axis(labelLimit=220)),
        x=alt.X('Tỷ trọng:Q', title='Tỷ trọng chi tiêu', stack='normalize', axis=alt.Axis(format='.0%', tickCount=5)),
        color=alt.Color('Danh mục:N', title=None, scale=alt.Scale(domain=['Xe đạp', 'Phụ kiện', 'Quần áo'], range=[NAVY, '#7FA6D6', AMBER]), legend=alt.Legend(**LEGEND_B)),
        order=alt.Order('thu_tu:Q'), tooltip=[alt.Tooltip('Đối tượng:N'), alt.Tooltip('Danh mục:N'), alt.Tooltip('Tỷ trọng:Q', format='.1%')]
    ).properties(height=170)


def chart_z_by_budget_live(curve, B_now):
    """Z và số khách theo ngân sách, giải lại bằng solve() với r, c đang chọn."""
    base = alt.Chart(curve).encode(x=alt.X('B:Q', title='Ngân sách B (USD)', axis=alt.Axis(labelExpr=AX_VN, tickCount=8)))
    line = base.mark_line(color=NAVY, strokeWidth=2.4).encode(
        y=alt.Y('Z:Q', title='Giá trị ròng kỳ vọng Z (USD)', axis=alt.Axis(labelExpr=AX_VN)),
        tooltip=[alt.Tooltip('B:Q', title='B (USD)', format=',.0f'), alt.Tooltip('Z:Q', title='Z (USD)', format=',.0f'), alt.Tooltip('K:Q', title='Số khách', format=',.0f')])
    pts = base.mark_square(size=30, color=NAVY).encode(y='Z:Q')
    now = curve[curve.B == B_now]
    hl = alt.Chart(now).mark_square(size=140, color=AMBER).encode(x='B:Q', y='Z:Q', tooltip=[alt.Tooltip('B:Q', title='B đang chọn', format=',.0f'), alt.Tooltip('Z:Q', title='Z (USD)', format=',.0f')])
    rule = alt.Chart(now).mark_rule(color=AMBER, strokeDash=[4, 3]).encode(x='B:Q')
    return (line + pts + rule + hl).properties(height=290)


def chart_selected_mix(sel_df):
    """Cơ cấu khách được chọn theo nhóm N1–N5 và hạng ABC."""
    s = sel_df.groupby(['Nhom', 'ABC']).size().reset_index(name='so_khach'); s['NhomDayDu'] = s.Nhom.map(TEN)
    return alt.Chart(s).mark_bar().encode(
        y=alt.Y('NhomDayDu:N', title=None, sort=list(TEN.values()), axis=alt.Axis(labelLimit=280)),
        x=alt.X('sum(so_khach):Q', title='Số khách được chọn', axis=alt.Axis(labelExpr=AX_VN, tickCount=4)),
        color=alt.Color('ABC:N', title=None, scale=alt.Scale(domain=['A', 'B', 'C'], range=[NAVY, '#7FA6D6', '#C9D3E0']), legend=alt.Legend(**LEGEND_B, labelExpr="'Hạng ' + datum.label")),
        order=alt.Order('ABC:N'),
        tooltip=[alt.Tooltip('NhomDayDu:N', title='Nhóm'), alt.Tooltip('ABC:N', title='Hạng'), alt.Tooltip('sum(so_khach):Q', title='Số khách', format=',.0f')]
    ).properties(height=290)


def chart_cumulative_value(sel_df, cost_col):
    """Đường tích luỹ theo thứ tự ưu tiên của solve() (EV / chi phí giảm dần): tổng chi phí (trục x) và Z (trục y)."""
    sel_df = sel_df.assign(_ratio=sel_df.EV / sel_df[cost_col]).sort_values('_ratio', ascending=False)
    s = pd.DataFrame({'chi_phi': np.cumsum(sel_df[cost_col].values), 'Z': np.cumsum(sel_df.EV.values)}); s['so_khach'] = np.arange(1, len(s) + 1)
    s = s.iloc[np.unique(np.linspace(0, len(s) - 1, min(len(s), 400)).astype(int))]
    return alt.Chart(s).mark_line(color=GREEN, strokeWidth=2.4).encode(
        x=alt.X('chi_phi:Q', title='Chi phí tích luỹ (USD)', axis=alt.Axis(labelExpr=AX_VN, tickCount=6)),
        y=alt.Y('Z:Q', title='Z tích luỹ (USD)', axis=alt.Axis(labelExpr=AX_VN)),
        tooltip=[alt.Tooltip('so_khach:Q', title='Số khách đầu danh sách', format=',.0f'), alt.Tooltip('chi_phi:Q', title='Chi phí (USD)', format=',.0f'), alt.Tooltip('Z:Q', title='Z (USD)', format=',.0f')]
    ).properties(height=290)


def chart_model_compare(metric, title, fmt_axis):
    """AUC hoặc Brier trung bình bốn mốc (bang_4_3_2b_trung_binh.csv); Naive Bayes đang dùng được tô màu."""
    s = pd.read_csv(f'{R4}/bang_4_3_2b_trung_binh.csv')[['mo_hinh', metric]].copy()
    s['Loại'] = np.where(s.mo_hinh.eq('Naive Bayes rời rạc'), 'Đang dùng', 'Khác')
    bars = alt.Chart(s).mark_bar(size=16).encode(
        y=alt.Y('mo_hinh:N', title=None, sort=s.sort_values(metric, ascending=metric != 'AUC').mo_hinh.tolist(), axis=alt.Axis(labelLimit=200)),
        x=alt.X(f'{metric}:Q', title=title, scale=alt.Scale(domain=[0, float(s[metric].max()) * 1.15], nice=False), axis=alt.Axis(labelExpr=fmt_axis, tickCount=5)),
        color=alt.Color('Loại:N', legend=None, scale=alt.Scale(domain=['Đang dùng', 'Khác'], range=[AMBER, '#9AAAC0'])),
        tooltip=[alt.Tooltip('mo_hinh:N', title='Mô hình'), alt.Tooltip(f'{metric}:Q', format='.4f')])
    labels = bars.mark_text(align='left', dx=4, fontWeight=600).transform_calculate(lbl=f"replace(format(datum['{metric}'], '.3f'), '.', ',')").encode(text='lbl:N', color=alt.value('#101828'))
    return (bars + labels).properties(height=280)


def chart_tree_leaves():
    """Số khách và tỷ lệ không mua lại của 11 lá cây đối chứng (bang_4_3_2f_la_cay.csv)."""
    s = pd.read_csv(f'{R4}/bang_4_3_2f_la_cay.csv'); s['Lá'] = 'Lá ' + s.leaf.astype(str)
    return alt.Chart(s).mark_bar().encode(
        y=alt.Y('Lá:N', title=None, sort=alt.EncodingSortField('mean', order='descending')),
        x=alt.X('count:Q', title='Số khách huấn luyện trong lá', axis=alt.Axis(labelExpr=AX_VN, tickCount=6)),
        color=alt.Color('mean:Q', title='Tỷ lệ không mua lại', scale=alt.Scale(domain=[0, 1], range=['#C9D3E0', RED]), legend=alt.Legend(orient='bottom', format='.0%', gradientLength=220)),
        tooltip=[alt.Tooltip('Lá:N'), alt.Tooltip('count:Q', title='Số khách', format=',.0f'), alt.Tooltip('mean:Q', title='Tỷ lệ không mua lại', format='.1%')]
    ).properties(height=400)


def chart_choose_k():
    """Silhouette và WCSS theo k (bang_4_4_chon_k.csv); k = 5 là cấu hình đang dùng."""
    s = pd.read_csv(f'{R6}/bang_4_4_chon_k.csv'); s['Chọn'] = np.where(s.k == 5, 'k đang dùng', 'khác')
    base = alt.Chart(s).encode(x=alt.X('k:O', title='Số nhóm k', axis=alt.Axis(labelAngle=0)))
    sil = base.mark_line(color=NAVY, strokeWidth=2.3).encode(y=alt.Y('Silhouette:Q', title='Silhouette', scale=alt.Scale(zero=False), axis=alt.Axis(labelExpr="replace(format(datum.value, '.2f'), '.', ',')")))
    pts = base.mark_square(size=60).encode(y='Silhouette:Q', color=alt.Color('Chọn:N', legend=None, scale=alt.Scale(domain=['k đang dùng', 'khác'], range=[AMBER, NAVY])),
                                           tooltip=[alt.Tooltip('k:O'), alt.Tooltip('Silhouette:Q', format='.3f'), alt.Tooltip('WCSS:Q', format=',.0f')])
    wcss = base.mark_bar(color='#DCE3EC', size=22).encode(y=alt.Y('WCSS:Q', title='WCSS', axis=alt.Axis(labelExpr=AX_VN)))
    return alt.layer(wcss, sil + pts).resolve_scale(y='independent').properties(height=400)


def chart_assoc_rules():
    """Lift và độ tin cậy của các luật kết hợp sản phẩm R6–R8 (bang_4_4_luat_ket_hop.csv)."""
    s = pd.read_csv(f'{R6}/bang_4_4_luat_ket_hop.csv'); s['Luật'] = s.quy_tac + ' · ' + s.A + ' → ' + s.B
    bars = alt.Chart(s).mark_bar(size=20, color=NAVY).encode(
        y=alt.Y('Luật:N', title=None, sort=alt.EncodingSortField('lift', order='descending'), axis=alt.Axis(labelLimit=320)),
        x=alt.X('lift:Q', title='Lift (> 1 nghĩa là hay mua cùng nhau hơn ngẫu nhiên)', axis=alt.Axis(labelExpr="replace(format(datum.value, '.1f'), '.', ',')", tickCount=5)),
        tooltip=[alt.Tooltip('Luật:N'), alt.Tooltip('support:Q', title='Support', format='.2%'), alt.Tooltip('confidence:Q', title='Confidence', format='.1%'), alt.Tooltip('lift:Q', title='Lift', format='.2f')])
    labels = bars.mark_text(align='left', dx=4, fontWeight=600).transform_calculate(lbl="'conf. ' + replace(format(datum.confidence, '.0%'), '.', ',')").encode(text='lbl:N', color=alt.value('#101828'))
    one = alt.Chart(pd.DataFrame({'x': [1]})).mark_rule(color=RED, strokeDash=[4, 3]).encode(x='x:Q')
    return (bars + labels + one).properties(height=200)


# ---------------- thanh bên: điểm bắt đầu theo vai trò, 5 màn hình cũ giữ nguyên ----------------
PAGES = ['Hướng dẫn sử dụng', '1. Tổng quan rủi ro', '2. Hồ sơ khách hàng', '3. Phân tích kịch bản', '4. Danh sách chăm sóc', '5. Theo dõi mô hình và quy tắc']
ROLES = ['Quản lý Marketing/Sales', 'Nhân viên phân tích dữ liệu', 'Nhân viên chăm sóc khách hàng']
ROLE_START = {ROLES[0]: PAGES[1], ROLES[1]: PAGES[5], ROLES[2]: PAGES[4]}

def role_changed():
    st.session_state['companyx_nav'] = ROLE_START[st.session_state['companyx_role']]

st.session_state.setdefault('companyx_nav', PAGES[1])
st.sidebar.markdown('<div class="cx-brand"><span class="cx-mark">CX</span><div class="cx-brand-name">CompanyX DSS</div></div>', unsafe_allow_html=True)
ROLE_SHORT = {ROLES[0]: 'Quản lý', ROLES[1]: 'Phân tích dữ liệu', ROLES[2]: 'Chăm sóc khách hàng'}   # chỉ đổi nhãn hiển thị cho vừa thanh bên
vai_tro = st.sidebar.selectbox('Vai trò', ROLES, key='companyx_role', on_change=role_changed, format_func=ROLE_SHORT.get)
NAV_LABEL = dict(zip(PAGES, ['Hướng dẫn sử dụng', '01 Tổng quan rủi ro', '02 Hồ sơ khách hàng', '03 Phân tích kịch bản', '04 Danh sách chăm sóc', '05 Theo dõi mô hình']))   # chỉ đổi nhãn hiển thị
man = st.sidebar.radio('Màn hình', PAGES, key='companyx_nav', format_func=NAV_LABEL.get, on_change=lambda: st.session_state.pop('cx_tu_man', None))
st.sidebar.button('Đến màn hình ưu tiên', on_click=lambda: st.session_state.update({'companyx_nav': ROLE_START[vai_tro]}), width='stretch')
st.sidebar.markdown(f'<div class="cx-side-foot">Mốc chấm điểm <b>{pd.Timestamp(C.SCORING_DATE):%d/%m/%Y}</b><br>Mô hình chấm điểm <b>Naive Bayes</b></div>', unsafe_allow_html=True)
with st.sidebar: ghi_chu('du_lieu', noi='sb')

# ================= 0. HƯỚNG DẪN SỬ DỤNG =================
if man.startswith('Hướng dẫn'):
    page_header('Bắt đầu', 'Hướng dẫn sử dụng DSS CompanyX', 'du_lieu', 'du_doan', 'gia_dinh')
    html('<p class="cx-lead">Với ngân sách có hạn, nên chăm sóc những khách nào để giữ được nhiều giá trị nhất? Làm lần lượt 5 bước dưới đây, mỗi bước là một màn hình ở thanh bên trái.</p>')
    a, b, c = st.columns(3)
    with a:
        st.button('Tổng quan rủi ro', width='stretch', on_click=nav_to, args=(PAGES[1],))
    with b:
        st.button('Hồ sơ khách hàng', width='stretch', on_click=nav_to, args=(PAGES[2],))
    with c:
        st.button('Danh sách chăm sóc', width='stretch', on_click=nav_to, args=(PAGES[4],))

    section('Khái niệm cần biết')
    st.markdown(f"""
| Khái niệm | Nghĩa đơn giản | Ở đâu trên màn hình |
|---|---|---|
| **Xác suất không mua lại** | Khả năng (0 đến 1) khách này không đặt đơn nào trong 90 ngày tới, do mô hình tính từ lịch sử mua | Cột "Xác suất không mua lại", nhãn {tag('du_doan')} |
| **Mức rủi ro Cao / Thấp** | Cao = thuộc 25% khách có xác suất cao nhất **trong cùng hạng giá trị** (A, B hoặc C). Là mức ưu tiên tương đối, không phải lời khẳng định khách sẽ bỏ đi | Thẻ số và cột "Mức rủi ro" |
| **Giá trị ròng Z** | Lợi nhuận kỳ vọng từ những khách được giữ lại, trừ đi chi phí chăm sóc. Phụ thuộc ba con số bạn nhập: r, c, B | Màn hình 3 và 4, nhãn {tag('gia_dinh')} |
""", unsafe_allow_html=True)
    st.markdown(f"""
Ba con số bạn sẽ nhập ở màn hình 3:
- **r** – tỷ lệ chăm sóc thành công: trong 100 khách được chăm sóc mà lẽ ra sẽ bỏ đi, bao nhiêu người quay lại mua. Mặc định 10%.
- **c** – chi phí cho mỗi khách được chăm sóc (liên hệ cộng ưu đãi). Mặc định 10 USD.
- **B** – ngân sách chiến dịch. Mặc định 40.000 USD.
""")
    section('Năm bước')
    buoc = [
        ('Bước 1 – Xem tình hình chung', '1. Tổng quan rủi ro', [
            'Nhìn dải chỉ số ở trên: tổng số khách, số khách rủi ro Cao, tổng tiền họ đã mua, số khách hạng A rủi ro Cao, số khách cần xem xét thêm.',
            'Nhìn **Ma trận Rủi ro × Giá trị**. Ô đáng chú ý nhất là **A – Cao** (viền đỏ): khách giá trị lớn nhưng có nguy cơ rời bỏ.',
            'Dùng hai bộ lọc phía trên để thu hẹp theo nhóm khách hoặc hạng giá trị, mọi số bên dưới tự tính lại.',
            'Bảng **Năm nhóm khách hàng** cho biết mỗi nhóm mua như thế nào. Bảng cuối liệt kê 20 khách rủi ro Cao có giá trị lớn nhất, ghi lại vài mã khách để xem ở bước 2.']),
        ('Bước 2 – Xem một khách cụ thể', '2. Hồ sơ khách hàng', [
            'Nhập mã khách vào ô "Mã khách" (ví dụ một mã lấy từ bước 1).',
            'Đọc năm chỉ số: lần mua gần nhất cách đây bao nhiêu ngày, đã mua mấy đơn, tổng chi tiêu, xác suất không mua lại, mức rủi ro.',
            'Khung "Nhóm theo cây đối chứng" mô tả nhóm khách có đặc điểm giống nhau và tỷ lệ bỏ đi của nhóm đó. Đây là cách nhìn thứ hai để đối chiếu.',
            'Nếu thấy hộp đỏ **Cần xem xét thêm**: hai cách nhìn không thống nhất, nên hỏi thêm đội bán hàng trước khi quyết định. Hộp xanh nghĩa là hai cách nhìn khớp nhau.',
            'Phần **Khuyến nghị chăm sóc** cho biết nên liên hệ bằng hình thức nào, tốn bao nhiêu, kỳ vọng thu về bao nhiêu và gợi ý sản phẩm gì.']),
        ('Bước 3 – Thử các kịch bản ngân sách', '3. Phân tích kịch bản', [
            'Kéo ba thanh trượt r, c, B. Bốn chỉ số bên dưới (Z, số khách, chi phí, số khách giữ lại) tự tính lại ngay.',
            'Bấm **Lưu kịch bản này** sau mỗi lần thử để so sánh các phương án trong bảng bên cạnh.',
            'Chọn một kỹ thuật ở hàng nút: **So sánh các kịch bản** (bảng có sẵn), **Độ nhạy** (tham số nào ảnh hưởng Z nhiều nhất), **Tìm mục tiêu** (cần r bao nhiêu để hoà vốn hoặc đạt Z mong muốn), **Z theo ngân sách khi chưa biết r** (ba tiêu chí lạc quan, bi quan, kỳ vọng), **Mô phỏng** (xác suất lỗ), **Theo kênh** (chi phí khác nhau cho từng hình thức liên hệ).',
            'Nhớ rằng mọi số ở đây mang nhãn THEO GIẢ ĐỊNH: đúng trong phạm vi r, c, B bạn nhập.']),
        ('Bước 4 – Duyệt danh sách chăm sóc', '4. Danh sách chăm sóc', [
            'Nhập ngân sách B. Giữ ô "theo kênh" được tích để chi phí và tỷ lệ thành công khác nhau theo hình thức liên hệ.',
            'Đọc ba chỉ số: số khách, tổng chi phí (có báo nếu vượt ngân sách) và Z sau điều chỉnh.',
            'Muốn thêm hoặc bớt khách: gõ mã khách vào ô, dấu trừ phía trước để bớt (ví dụ 11000, -19785), và **bắt buộc ghi lý do**. Hệ thống tính lại ngay.',
            'Mỗi dòng trong bảng có hình thức liên hệ, sản phẩm gợi ý và cột **Giải thích** nói vì sao khách được chọn.',
            'Bấm **Xuất danh sách đã duyệt (CSV)** để gửi cho đội chăm sóc. Vai trò "Nhân viên phân tích" không có nút này.']),
        ('Bước 5 – Kiểm tra mô hình còn tốt không', '5. Theo dõi mô hình và quy tắc', [
            'Biểu đồ đầu so mô hình đang dùng với quy tắc đơn giản "khách lâu không mua thì rủi ro cao". Đường mô hình phải nằm bằng hoặc trên đường quy tắc, nếu không thì cần huấn luyện lại.',
            'Bảng **Cơ cấu khách thay đổi theo thời gian** giải thích vì sao mỗi kỳ phải huấn luyện lại.',
            'Bảng **Phiên bản** cho biết mô hình và quy tắc nào đang được dùng, để ghi vào biên bản chiến dịch.',
            'Quản lý và nhân viên phân tích có thể đề xuất quy tắc mới ở cuối trang, quy tắc sẽ ở trạng thái chờ duyệt.']),
    ]
    for i, (ten, man_hinh, cac_buoc) in enumerate(buoc):
        with st.expander(f'{ten}  —  màn hình "{man_hinh}"', expanded=(i == 0)):
            for j, b in enumerate(cac_buoc, 1): st.markdown(f'{j}. {b}')
    section('Câu hỏi thường gặp')
    st.markdown("""
- **Tại sao một khách giá trị lớn lại ở mức rủi ro Thấp?** Mức rủi ro so sánh trong cùng hạng giá trị. Khách đó có xác suất không mua lại thấp hơn 75% khách cùng hạng với mình.
- **Z có phải là lợi nhuận chắc chắn không?** Không. Z là giá trị kỳ vọng theo giả định r, c, B. Màn hình 3 có phần Mô phỏng để xem xác suất lỗ.
- **Tôi có thể bỏ một khách mà hệ thống chọn không?** Có, ở màn hình 4, nhưng phải ghi lý do. Hệ thống tính lại chi phí và Z.
- **Số liệu được cập nhật khi nào?** Mỗi kỳ chấm điểm (ghi ở thanh bên trái). Khi kho dữ liệu có đơn mới, nhân viên phân tích chạy lại chấm điểm và phiên bản mới xuất hiện ở màn hình 5.
- **Hệ thống có tự gửi email hay gọi khách không?** Không. Hệ thống chỉ đề xuất danh sách và hình thức, việc thực hiện do đội chăm sóc làm theo CSV đã xuất.
""")
    st.caption('Thiết kế theo các bảng quy trình ra quyết định, vai trò và năm màn hình ở Chương 6 của báo cáo.')

# ================= 1. TỔNG QUAN =================
elif man.startswith('1'):
    page_header('01 · Tổng quan', 'Tổng quan rủi ro khách hàng', 'du_lieu', 'du_doan')
    with st.container(border=True):
        nhom = st.pills('Nhóm khách', list(TEN), selection_mode='multi', default=list(TEN), format_func=lambda x: TEN[x])
        abc = st.pills('Hạng giá trị (ABC)', ['A', 'B', 'C'], selection_mode='multi', default=['A', 'B', 'C'], format_func=lambda x: {'A': 'A – 28% khách giữ 80% doanh thu', 'B': 'B – 14% khách giữ 15% doanh thu', 'C': 'C – 58% khách giữ 5% doanh thu'}[x])
    if not nhom or not abc: note('Chọn ít nhất một nhóm và một hạng ở trên.', 'risk', 'Chưa có dữ liệu'); st.stop()
    d0 = df[df.Nhom.isin(nhom) & df.ABC.isin(abc)]
    # Lọc chéo kiểu BI: bấm cột nhóm (tab Nhóm khách hàng) hoặc ô ma trận (tab Rủi ro × giá trị). Chỉ lọc phần hiển thị của màn hình này.
    grp_key = f'cx_grp_{st.session_state.setdefault("cx_xf_ver", 0)}'
    try: chon_nhom = [x['Nhom'] for x in st.session_state[grp_key]['selection']['chon_nhom'] if 'Nhom' in x]
    except (KeyError, TypeError): chon_nhom = []
    o = st.session_state.get('cx_cell')
    d_mx = d0[d0.Nhom.isin(chon_nhom)] if chon_nhom else d0                                   # ma trận chịu lọc theo nhóm
    d_grp = d0[(d0.ABC == o[0]) & (d0.RiskLevel == o[1])] if o else d0                         # biểu đồ nhóm chịu lọc theo ô
    d = d_grp[d_grp.Nhom.isin(chon_nhom)] if chon_nhom else d_grp                               # mọi phần còn lại chịu cả hai
    if chon_nhom or o:
        chips = ''.join(f'<span class="cx-chip-filter">{TEN[n]}</span>' for n in chon_nhom) + (f'<span class="cx-chip-filter">Hạng {o[0]} · Rủi ro {o[1]}</span>' if o else '')
        with st.container(border=True):
            c1, c2 = st.columns([6, 1], vertical_alignment='center')
            with c1: html(f'<div class="cx-filter"><span class="lbl">Đang lọc chéo</span>{chips}</div>')
            c2.button('Bỏ lọc', on_click=bo_loc_cheo, width='stretch')
    section('Chỉ số tổng quan')
    so_cao = int((d.RiskLevel == 'Cao').sum()); so_a_cao = int(((d.ABC == 'A') & (d.RiskLevel == 'Cao')).sum())
    kpis([('Số khách đang xem', vn(len(d)), f'{len(nhom)} nhóm · hạng {", ".join(abc)}' + (' · đang lọc chéo' if chon_nhom or o else '')),
          ('Khách rủi ro Cao', vn(so_cao), f'{pct((d.RiskLevel == "Cao").mean()) if len(d) else "—"} · top 25% trong cùng hạng', 'risk'),
          ('Đã mua (khách Cao)', usd(d.loc[d.RiskLevel == 'Cao', 'Monetary'].sum()), 'Tổng chi tiêu đến mốc chấm điểm'),
          ('Hạng A · rủi ro Cao', vn(so_a_cao), 'Nhóm cần ưu tiên', 'risk'),
          ('Cần xem xét thêm', vn(int(d.Flag.sum())), f'Hai mô hình lệch nhau > {vn(C.TREE_FLAG_GAP, 1)}')])

    tab1, tab2, tab3, tab4 = st.tabs(['Rủi ro × giá trị', 'Nhóm khách hàng', 'Xu hướng kinh doanh', 'Khách cần xem xét'])
    with tab1:
        a, b = st.columns([3, 2])
        with a:
            with st.container(border=True):
                st.subheader('Phân bố xác suất không mua lại'); altair_wide(hist_chart(d.RiskScore, '', x_title='Xác suất không mua lại (RiskScore)'))
                ghi_chu('diem_cao', noi='p1')
        with b:
            with st.container(border=True):
                st.subheader('Ma trận Rủi ro × Giá trị · bấm ô để lọc')
                mx = pd.crosstab(d_mx.ABC, d_mx.RiskLevel).reindex(index=['A', 'B', 'C'], columns=['Cao', 'Thấp']).fillna(0).astype(int); risk_matrix_buttons(mx, o)
                ghi_chu('muc_cao', noi='p1')
        a, b = st.columns([2, 3])
        with a:
            with st.container(border=True):
                st.subheader('Giá trị đã mua theo hạng và mức rủi ro'); altair_wide(chart_value_at_risk(d))
        with b:
            with st.container(border=True):
                st.subheader('Hạng giá trị × thời gian chưa mua lại · bấm ô để xem khách')
                vung = st.session_state.get('cx_vung'); recency_value_grid(d, vung)
                ghi_chu('recency', noi='p1')
        if vung:
            h, lab = vung; dv = d[(d.ABC == h) & (pd.cut(d.Recency, C.RECENCY_BINS, labels=VUNG) == lab)]
            with st.container(border=True):
                c1, c2 = st.columns([6, 1], vertical_alignment='center')
                c1.subheader(f'Hạng {h} · {lab} ngày chưa mua lại · chọn một dòng để mở hồ sơ')
                c2.button('Đóng', on_click=chon_vung, args=(vung,), width='stretch')
                kpis([('Số khách trong ô', vn(len(dv)), ''), ('Rủi ro Cao', vn(int((dv.RiskLevel == 'Cao').sum())), pct((dv.RiskLevel == 'Cao').mean()) if len(dv) else '—', 'risk'),
                      ('Đã mua (khách Cao)', usd(dv.loc[dv.RiskLevel == 'Cao', 'Monetary'].sum()), 'Tổng chi tiêu đến mốc chấm điểm'),
                      ('Xác suất không mua lại TB', vn(dv.RiskScore.mean(), 3) if len(dv) else '—', '')])
                t = dv.assign(_c=dv.RiskLevel == 'Cao').sort_values(['_c', 'Monetary'], ascending=False)[['CustomerID', 'Nhom', 'RiskLevel', 'Recency', 'Frequency', 'Monetary', 'RiskScore']]
                t.columns = ['Mã khách', 'Nhóm', 'Mức rủi ro', 'Ngày từ lần mua gần nhất', 'Số đơn', 'Tổng chi tiêu (USD)', 'Xác suất không mua lại']
                st.session_state['cx_ids_vung'] = t['Mã khách'].tolist()
                st.dataframe(t.style.format({'Ngày từ lần mua gần nhất': fmt(), 'Tổng chi tiêu (USD)': fmt(), 'Xác suất không mua lại': fmt(3)}), hide_index=True, width='stretch', height=320,
                             on_select=lambda: mo_ho_so('cx_vung_tbl', 'cx_ids_vung'), selection_mode='single-row', key='cx_vung_tbl')
    with tab2:
        def ho_so_nhom(x): return x.groupby('Nhom').agg(so_khach=('CustomerID', 'size'), recency_trung_vi=('Recency', 'median'), so_don_TB=('Frequency', 'mean'), chi_tieu_trung_vi=('Monetary', 'median'), ty_le_rui_ro_cao=('RiskLevel', lambda v: (v == 'Cao').mean()), hang_A=('ABC', lambda v: (v == 'A').sum())).reindex(list(TEN)).dropna(how='all')
        g_src, g = ho_so_nhom(d_grp), ho_so_nhom(d)
        with st.container(border=True):
            a, b = st.columns(2)
            with a:
                st.subheader('Tỷ lệ rủi ro Cao trong nhóm · bấm cột để lọc')
                if len(g_src): altair_wide(chart_group_select(g_src), on_select='rerun', key=grp_key)
            with b: st.subheader('Cơ cấu chi tiêu theo danh mục (toàn bộ khách)'); altair_wide(chart_product_mix_by_group())
        with st.container(border=True):
            st.subheader('Hồ sơ năm nhóm khách hàng')
            out = pd.DataFrame({'Nhóm': [TEN[i] for i in g.index], 'Số khách': g.so_khach.values, 'Ngày từ lần mua gần nhất (trung vị)': g.recency_trung_vi.values, 'Số đơn trung bình': g.so_don_TB.values, 'Chi tiêu trung vị (USD)': g.chi_tieu_trung_vi.values, 'Tỷ lệ rủi ro Cao': g.ty_le_rui_ro_cao.values, 'Khách hạng A': g.hang_A.values})
            st.dataframe(out.style.format({'Số khách': fmt(), 'Ngày từ lần mua gần nhất (trung vị)': fmt(), 'Số đơn trung bình': fmt(2), 'Chi tiêu trung vị (USD)': fmt(), 'Tỷ lệ rủi ro Cao': fpct(), 'Khách hạng A': fmt()}), hide_index=True, width="stretch")
    with tab3:
        with st.container(border=True):
            st.subheader('Doanh thu theo tháng và dự báo 04–06/2014'); altair_wide(chart_monthly_revenue())
            st.caption('Toàn bộ khách, không theo bộ lọc. Tháng 06/2014 trong kho chỉ ghi nhận 930 đơn, 48.651 USD (chuoi_thang.csv).')
    with tab4:
        with st.container(border=True):
            st.subheader('20 khách rủi ro Cao có giá trị lớn nhất · chọn một dòng để mở hồ sơ')
            t = d[d.RiskLevel == 'Cao'].nlargest(20, 'Monetary')[['CustomerID', 'Nhom', 'ABC', 'Recency', 'Frequency', 'Monetary', 'RiskScore', 'RiskPercentile']].copy()
            t.columns = ['Mã khách', 'Nhóm', 'Hạng', 'Ngày từ lần mua gần nhất', 'Số đơn', 'Tổng chi tiêu (USD)', 'Xác suất không mua lại', 'Phân vị rủi ro trong hạng']
            st.session_state['cx_ids_top20'] = t['Mã khách'].tolist()
            st.dataframe(t.style.format({'Ngày từ lần mua gần nhất': fmt(), 'Tổng chi tiêu (USD)': fmt(), 'Xác suất không mua lại': fmt(3), 'Phân vị rủi ro trong hạng': fmt(1)}), hide_index=True, width="stretch",
                         on_select=lambda: mo_ho_so('cx_top20', 'cx_ids_top20'), selection_mode='single-row', key='cx_top20')

# ================= 2. HỒ SƠ KHÁCH =================
elif man.startswith('2'):
    page_header('02 · Khách hàng', 'Hồ sơ một khách hàng', 'du_lieu', 'du_doan')
    tu_man = st.session_state.get('cx_tu_man')
    if tu_man in PAGES:
        ten_tu = NAV_LABEL[tu_man].split('\u2003')[-1]
        st.button(f'← Quay lại {ten_tu}', on_click=lambda: (st.session_state.pop('cx_tu_man', None), nav_to(tu_man)))
    vi_du = [ma for ma in (12201, 26339, 26774) if ma in set(df.CustomerID)]
    st.session_state.setdefault('companyx_customer_id', int(df.CustomerID.iloc[0]))
    with st.container(border=True):
        col_example, col_id = st.columns([1, 1])
        if vi_du:
            def chon_khach_mau():
                ma = st.session_state['companyx_customer_example']
                if ma is not None:
                    st.session_state['companyx_customer_id'] = int(ma)
            with col_example:
                st.selectbox('Khách minh họa', [None] + vi_du,
                             format_func=lambda x: 'Chọn một mã có trong kết quả thực nghiệm' if x is None else f'Khách hàng {x}',
                             key='companyx_customer_example', on_change=chon_khach_mau)
        with col_id:
            cid = st.number_input('Mã khách (CustomerID)', min_value=int(df.CustomerID.min()),
                                  max_value=int(df.CustomerID.max()), step=1, key='companyx_customer_id')
    r = df[df.CustomerID == cid]
    if r.empty: note('Không có khách này tại mốc chấm điểm.', 'risk', 'Không tìm thấy')
    else:
        r = r.iloc[0]
        section(f'Khách hàng {cid}')
        kpis([('Ngày từ lần mua gần nhất', vn(r.Recency), 'ngày'), ('Số đơn đã mua', vn(r.Frequency)), ('Tổng chi tiêu', usd(r.Monetary)),
              ('Xác suất không mua lại', vn(r.RiskScore, 3), f'{pct(r.RiskScore)} trong 90 ngày tới'),
              ('Mức rủi ro', r.RiskLevel, f'Phân vị {vn(r.RiskPercentile, 1)} trong hạng {r.ABC}', 'risk' if r.RiskLevel == 'Cao' else 'ok')])
        html(f'<div class="cx-field-grid">'
             f'<div class="cx-field"><div class="cx-field-label">Hạng giá trị</div><div class="cx-field-value">{r.ABC}</div></div>'
             f'<div class="cx-field"><div class="cx-field-label">Nhóm hành vi</div><div class="cx-field-value">{TEN[r.Nhom]}</div></div>'
             f'<div class="cx-field"><div class="cx-field-label">Thời gian là khách</div><div class="cx-field-value">{vn(r.Tenure)} ngày</div></div>'
             f'<div class="cx-field"><div class="cx-field-label">Số danh mục đã mua</div><div class="cx-field-value">{vn(r.NSub)}</div></div>'
             f'<div class="cx-field"><div class="cx-field-label">Tỷ trọng xe đạp</div><div class="cx-field-value">{pct(r.Share_Bikes, 0)}</div></div>'
             f'<div class="cx-field"><div class="cx-field-label">TreeScore (cây đối chứng)</div><div class="cx-field-value">{vn(r.TreeScore, 3)}</div></div>'
             f'</div>')
        section('Giải thích mô hình')
        a, b = st.columns([1, 1])
        with a:
            with st.container(border=True):
                st.subheader('Hai điểm dự đoán để đối chiếu')
                altair_wide(chart_customer_scores(r))
                if r.Flag: note(f'Cây đối chứng cho {vn(r.TreeScore, 3)} nhưng mô hình chấm điểm cho {vn(r.RiskScore, 3)}, lệch nhau quá {vn(C.TREE_FLAG_GAP, 1)}. Nên hỏi thêm đội bán hàng trước khi quyết định.', 'risk', 'Cần xem xét thêm')
                else: note(f'Chênh lệch giữa hai mô hình không vượt ngưỡng {vn(C.TREE_FLAG_GAP, 1)}.', 'ok', 'Hai mô hình thống nhất')
        with b:
            with st.container(border=True):
                st.subheader('Nhóm theo cây đối chứng')
                st.markdown(de_hieu(r.TopFactors))
                html('<div class="cx-muted">Mô tả nhóm khách có đặc điểm giống nhau, không phải lý do của xác suất ở bên trái.</div>')
            with st.container(border=True):
                st.subheader('Cơ cấu chi tiêu theo danh mục'); altair_wide(chart_customer_mix(df, r))
        section('So sánh với khách cùng hạng và cùng nhóm')
        a, b = st.columns(2)
        with a:
            with st.container(border=True):
                st.subheader(f'Vị trí trong phân bố rủi ro của hạng {r.ABC}'); altair_wide(chart_customer_position(df, r))
        with b:
            with st.container(border=True):
                st.subheader(f'So với trung vị nhóm {r.Nhom}'); altair_wide(chart_vs_group(df, r))
        section('Khuyến nghị chăm sóc')
        ten, ck, rk = CHAN[r.KenhRule]; ev = r.RiskScore * rk * r.v - ck
        html(f'<div class="cx-action-grid">'
             f'<div class="cx-action-item"><span class="cx-action-label">Kênh liên hệ · {r.KenhRule}</span><b>{ten}</b></div>'
             f'<div class="cx-action-item"><span class="cx-action-label">Chi phí liên hệ</span><b>{usd(ck)}</b></div>'
             f'<div class="cx-action-item"><span class="cx-action-label">Tỷ lệ thành công giả định</span><b>{pct(rk, 0)}</b></div>'
             f'<div class="cx-action-item"><span class="cx-action-label">Giá trị một lần mua nếu giữ được khách</span><b>{usd(r.v)}</b><small>Lợi nhuận gộp 41,15% × giá trị đơn trung bình</small></div>'
             f'<div class="cx-action-item"><span class="cx-action-label">Giá trị kỳ vọng chăm sóc</span><b>{vn(ev, 2)} USD</b></div>'
             f'<div class="cx-action-item"><span class="cx-action-label">Sản phẩm gợi ý</span><b>{r.SanPhamGoiY or "nội dung mặc định (giới thiệu chung các nhóm phụ kiện)"}</b><small>{("quy tắc " + r.QuyTacSP) if r.QuyTacSP else ""}</small></div>'
             f'</div><div class="cx-decision {"ok" if ev > 0 else "risk"}">{"Đủ điều kiện đưa vào danh sách" if ev > 0 else "Không đưa vào danh sách cá nhân (quy tắc R2: chi phí lớn hơn lợi ích kỳ vọng)"}</div>')

# ================= 3. KỊCH BẢN =================
elif man.startswith('3'):
    page_header('03 · Mô hình quyết định', 'Phân tích kịch bản chăm sóc', 'gia_dinh')
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        r = c1.slider('Tỷ lệ chăm sóc thành công r', 1, 30, int(C.BASE_SCENARIO['r'] * 100), 1, format='%d%%') / 100
        c = c2.slider('Chi phí mỗi khách c', 1, 30, int(C.BASE_SCENARIO['c']), 1, format='%d USD') * 1.0
        B = c3.slider('Ngân sách chiến dịch B', 5000, 150000, int(C.BASE_SCENARIO['B']), 5000, format='%d USD')
    sel, ev = solve(df, r, c, B); Z = ev[sel].sum()
    section('Kết quả')
    kpis([('Giá trị ròng kỳ vọng Z', usd(Z), 'Lợi nhuận kỳ vọng trừ chi phí', 'ok' if Z > 0 else 'risk'), ('Số khách được chọn', vn(len(sel))),
          ('Tổng chi phí', usd(c * len(sel)), f'Ngân sách {usd(B)}'), ('Số khách giữ lại kỳ vọng', vn((df.RiskScore.values[sel] * r).sum()))])
    ghi_chu('vong', noi='p3')
    cl, cm, _ = st.columns([1, 1, 3])
    if cl.button('Lưu kịch bản này', width='stretch', type='primary'): st.session_state.setdefault('kich_ban', []).append({'r': pct(r, 0), 'c': usd(c), 'B': usd(B), 'Z': usd(Z), 'Số khách': vn(len(sel))}); st.toast('Đã lưu kịch bản vào bảng so sánh')
    if st.session_state.get('kich_ban'):
        if cm.button('Xoá các kịch bản đã lưu', width='stretch'): st.session_state['kich_ban'] = []; st.rerun()
        with st.container(border=True):
            st.subheader('Kịch bản đã lưu'); st.dataframe(pd.DataFrame(st.session_state['kich_ban']), hide_index=True, width="stretch")
    curve = []
    for b_ in range(5000, 150001, 5000):
        s_, e_ = solve(df, r, c, b_); curve.append(dict(B=b_, Z=e_[s_].sum(), K=len(s_)))
    a, b = st.columns([3, 2])
    with a:
        with st.container(border=True):
            st.subheader('Z theo ngân sách với r, c đang chọn'); altair_wide(chart_z_by_budget_live(pd.DataFrame(curve), B))
    with b:
        with st.container(border=True):
            st.subheader('Khách được chọn theo nhóm và hạng'); altair_wide(chart_selected_mix(df.iloc[sel]))
    section('Kỹ thuật phân tích')
    kt = st.radio('Kỹ thuật phân tích', ['So sánh các kịch bản (what-if)', 'Độ nhạy: thay đổi từng tham số ±20%', 'Tìm mục tiêu: cần r bao nhiêu để đạt Z', 'Z theo ngân sách khi chưa biết r', 'Mô phỏng khi r không chắc chắn', 'Chi phí và tỷ lệ thành công theo kênh'], horizontal=True, label_visibility='collapsed')
    if kt.startswith('So sánh'):
        w = pd.read_csv(f'{R6}/bang_4_4_what_if.csv'); w = w.rename(columns={'kich_ban': 'Kịch bản', 'r': 'r', 'c': 'c (USD)', 'B': 'B (USD)', 'Z': 'Z (USD)', 'K': 'Số khách', 'C': 'Chi phí (USD)', 'giu_lai_ky_vong': 'Khách giữ lại kỳ vọng', 'delta_Z': 'Chênh so với cơ sở (USD)'})
        with st.container(border=True):
            st.subheader('Giá trị ròng Z giữa các kịch bản')
            altair_wide(chart_what_if_z(w))
            st.dataframe(w.style.format({'r': fpct(0), 'c (USD)': fmt(), 'Z (USD)': fmt(), 'B (USD)': fmt(), 'Số khách': fmt(), 'Chi phí (USD)': fmt(), 'Chênh so với cơ sở (USD)': lambda x: ('+' if x > 0 else '') + vn(x), 'Khách giữ lại kỳ vọng': fmt()}), hide_index=True, width="stretch")
    elif kt.startswith('Độ nhạy'):
        rows = []
        for ten, kw in [('Tỷ lệ thành công r', dict(r=r * 1.2)), ('Xác suất không mua lại p', dict(pm=1.2)), ('Tỷ lệ lợi nhuận gộp g', dict(gm=1.2)), ('Chi phí c', dict(c=c * 1.2)), ('Ngân sách B', dict(B=B * 1.2))]:
            d = df.copy()
            if 'pm' in kw: d['RiskScore'] = (d.RiskScore * 1.2).clip(upper=1)
            if 'gm' in kw: d['v'] = d.v * 1.2
            s_, e_ = solve(d, kw.get('r', r), kw.get('c', c), kw.get('B', B)); rows.append(dict(tham_so=ten, delta=e_[s_].sum() - Z))
        t = pd.DataFrame(rows)
        with st.container(border=True):
            st.subheader('Thay đổi của Z khi từng tham số tăng 20%')
            altair_wide(alt.Chart(t).mark_bar(size=24).encode(x=alt.X('delta:Q', title='Thay đổi của Z (USD)', axis=alt.Axis(labelExpr="replace(format(datum.value, ',.0f'), regexp(',', 'g'), '.')")), y=alt.Y('tham_so:N', title='', sort='-x', axis=alt.Axis(labelLimit=220)),
                        color=alt.condition('datum.delta >= 0', alt.value(NAVY), alt.value(RED)), tooltip=['tham_so', alt.Tooltip('delta:Q', format=',.0f')]).properties(height=230))
    elif kt.startswith('Tìm'):
        S = (df.RiskScore.values[sel] * df.v.values[sel]).sum()
        with st.container(border=True):
            zt = st.number_input('Z mục tiêu (USD)', value=100000, step=10000)
        kpis([('Danh sách đã chốt', vn(len(sel)), 'khách theo tham số ở trên'), ('r tối thiểu để hoà vốn (Z = 0)', pct(c * len(sel) / S, 2)),
              (f'r cần có để Z đạt {usd(zt)}', pct((zt + c * len(sel)) / S, 2), 'r* = (Z* + c·K) / Σ p·v')])
    elif kt.startswith('Z theo'):
        p = pd.read_csv(f'{R6}/bang_4_4_payoff.csv').rename(columns={'B': 'Ngân sách B (USD)', 'K': 'Số khách', 'r=2%': 'Z nếu r = 2% (bi quan)', 'r=10%': 'Z nếu r = 10% (cơ sở)', 'r=20%': 'Z nếu r = 20% (lạc quan)', 'gia_tri_ky_vong': 'Giá trị kỳ vọng (30/50/20%)'})
        kpis([('Lạc quan · tốt nhất của các kết quả tốt nhất', 'B = 100.000 USD'), ('Bi quan · tốt nhất của các kết quả xấu nhất', 'B = 40.000 USD'), ('Giá trị kỳ vọng lớn nhất', 'B = 100.000 USD')])
        with st.container(border=True):
            st.subheader('Z theo ngân sách ở ba mức tỷ lệ thành công')
            altair_wide(chart_payoff_by_budget(p))
            st.dataframe(p.style.format(fmt()), hide_index=True, width="stretch")
    elif kt.startswith('Mô phỏng'):
        sim = json.load(open(f'{R6}/mo_phong.json'))
        kpis([('Z trung bình', usd(sim['Z_mean'])), ('Z xấu nhất 5%', usd(sim['Z_P5'])), ('Z tốt nhất 5%', usd(sim['Z_P95'])), ('Xác suất lỗ (Z < 0)', pct(sim['P_Z_am']), None, 'risk')])
        with st.container(border=True):
            st.subheader('Phân phối Z qua 10.000 lần mô phỏng')
            st.image(f'{R6}/hinh_4_4_mo_phong.png', width='content')
            st.caption('r rút từ phân phối Beta (trung bình 9,9%, 90% khối lượng trong 2–22%), danh sách 4.000 khách của kịch bản cơ sở.')
    else:
        selk, evk = solve(df, r, c, B, kenh=True)
        kpis([('Giá trị ròng Z theo kênh', usd(evk[selk].sum()), None, 'ok' if evk[selk].sum() > 0 else 'risk'), ('Số khách được chọn', vn(len(selk))), ('Tổng chi phí', usd(df.c_k.values[selk].sum()))])
        kk = pd.Series(df.KenhRule.values[selk]).value_counts().rename_axis('Quy tắc').reset_index(name='Số khách'); kk['Hình thức liên hệ'] = kk['Quy tắc'].map(lambda k: CHAN[k][0]); kk['Chi phí mỗi khách (USD)'] = kk['Quy tắc'].map(lambda k: CHAN[k][1]); kk['Tỷ lệ thành công'] = kk['Quy tắc'].map(lambda k: pct(CHAN[k][2], 0))
        with st.container(border=True):
            st.subheader('Phân bổ theo kênh R3–R5')
            altair_wide(chart_care_channels(df.iloc[selk]))
            st.dataframe(kk[['Quy tắc', 'Hình thức liên hệ', 'Chi phí mỗi khách (USD)', 'Tỷ lệ thành công', 'Số khách']], hide_index=True, width="stretch")

# ================= 4. DANH SÁCH =================
elif man.startswith('4'):
    page_header('04 · Hành động', 'Danh sách chăm sóc', 'gia_dinh')
    with st.container(border=True):
        c1, c2 = st.columns([1, 2], vertical_alignment='bottom'); B = c1.number_input('Ngân sách B (USD)', value=int(C.BASE_SCENARIO['B']), step=5000)
        kenh = c2.checkbox('Chi phí và tỷ lệ thành công theo kênh R3–R5', value=True)
        c3, c4 = st.columns([1, 2]); them = c3.text_input('Thêm / bớt khách (CustomerID)', '', placeholder='11000, -19785'); ly_do = c4.text_input('Lý do điều chỉnh (bắt buộc khi thêm hoặc bớt)', '').strip()
    sel, ev = solve(df, C.BASE_SCENARIO['r'], C.BASE_SCENARIO['c'], B, kenh=kenh); d = df.iloc[sel].copy(); d['EV'] = ev[sel]; d = d.sort_values('EV', ascending=False)
    d['NguonChon'] = 'DSS chọn'; d['LyDo'] = ''
    nhat_ky, loi = [], []
    if them.strip():
        ids_all, ids_cur = set(df.CustomerID), set(d.CustomerID)
        for tok in [t_.strip() for t_ in them.split(',') if t_.strip()]:
            bot = tok.startswith('-'); so = tok[1:].strip() if bot else tok
            if not so.isdigit() or int(so) not in ids_all: loi.append(f'{tok} (không có mã khách này)'); continue
            cid_ = int(so)
            if bot:
                if cid_ not in ids_cur: loi.append(f'{tok} (khách không có trong danh sách để bớt)'); continue
                d = d[d.CustomerID != cid_]; ids_cur.discard(cid_); nhat_ky.append(dict(thao_tac='Bớt', ma_khach=cid_, ly_do=ly_do))
            else:
                if cid_ in ids_cur: loi.append(f'{tok} (đã có trong danh sách)'); continue
                x = df[df.CustomerID == cid_].copy(); x['EV'] = (x.RiskScore * x.r_k * x.v - x.c_k) if kenh else (x.RiskScore * C.BASE_SCENARIO['r'] * x.v - C.BASE_SCENARIO['c'])
                x['NguonChon'] = 'Thêm thủ công'; x['LyDo'] = ly_do; d = pd.concat([d, x]); ids_cur.add(cid_); nhat_ky.append(dict(thao_tac='Thêm', ma_khach=cid_, ly_do=ly_do))
        if loi: note(', '.join(loi) + '.', 'risk', 'Bỏ qua')
    am = d[(d.NguonChon == 'Thêm thủ công') & (d.EV <= 0)]
    if len(am): note(f'Mã {", ".join(str(i_) for i_ in am.CustomerID)} có giá trị kỳ vọng không dương, trái quy tắc R2 (chi phí lớn hơn lợi ích kỳ vọng). Thêm khách này làm Z giảm.', 'risk', 'Vi phạm quy tắc R2')
    thieu_ly_do = bool(nhat_ky) and not ly_do
    if thieu_ly_do: note('Ghi lý do ở ô bên phải thì mới xuất được danh sách.', 'risk', 'Chưa có lý do điều chỉnh')
    tong = float(d.c_k.sum()) if kenh else C.BASE_SCENARIO['c'] * len(d); Z = float(d.EV.sum())
    section('Tổng kết danh sách')
    kpis([('Số khách trong danh sách', vn(len(d)), f'{vn(len(nhat_ky))} điều chỉnh thủ công' if nhat_ky else 'Do DSS chọn'),
          ('Tổng chi phí', usd(tong), ('Vượt ngân sách ' if tong > B else 'Trong ngân sách ') + usd(B), 'risk' if tong > B else None),
          ('Giá trị ròng Z sau điều chỉnh', usd(Z), None, 'ok' if Z > 0 else 'risk')])
    ghi_chu('vong', noi='p4')
    if nhat_ky:
        with st.container(border=True):
            st.subheader('Nhật ký điều chỉnh thủ công')
            st.dataframe(pd.DataFrame(nhat_ky).rename(columns={'thao_tac': 'Thao tác', 'ma_khach': 'Mã khách', 'ly_do': 'Lý do'}), hide_index=True, width="stretch")
    section('Danh sách ưu tiên')
    with st.container(border=True):
        st.subheader('Phân bổ khách theo kênh chăm sóc')
        altair_wide(chart_care_channels(d))
    d['ChiPhi'] = d.c_k if kenh else C.BASE_SCENARIO['c']
    a, b = st.columns(2)
    with a:
        with st.container(border=True):
            st.subheader('Z tích luỹ theo chi phí (theo thứ tự chọn của DSS)'); altair_wide(chart_cumulative_value(d, 'ChiPhi'))
    with b:
        with st.container(border=True):
            st.subheader('Cơ cấu danh sách theo nhóm và hạng'); altair_wide(chart_selected_mix(d))
    d['GiaiThichDeDoc'] = [f'Kênh {k_} ({CHAN[k_][0].lower()}) vì khách thuộc {n_}, rủi ro {lv_.lower()}. Giá trị kỳ vọng {vn(e_, 1)} USD. ' + (f'Gợi ý {sp_}. ' if sp_ else '') + de_hieu(tf_)
                           for k_, n_, lv_, e_, sp_, tf_ in zip(d.KenhRule, d.Nhom, d.RiskLevel, d.EV, d.SanPhamGoiY, d.TopFactors)]
    t = d[['CustomerID', 'NguonChon', 'Nhom', 'ABC', 'RiskScore', 'RiskLevel', 'v', 'EV', 'KenhRule', 'SanPhamGoiY', 'GiaiThichDeDoc']].head(500).copy(); t['KenhRule'] = t.KenhRule.map(lambda k: f'{k} – {CHAN[k][0]}')
    t.columns = ['Mã khách', 'Nguồn chọn', 'Nhóm', 'Hạng', 'Xác suất không mua lại', 'Mức rủi ro', 'Giá trị một lần mua (USD)', 'Giá trị kỳ vọng (USD)', 'Hình thức liên hệ', 'Sản phẩm gợi ý', 'Giải thích']
    with st.container(border=True):
        st.subheader('Chi tiết danh sách · chọn một dòng để mở hồ sơ' + (f' · 500 / {vn(len(d))} dòng đầu, xuất CSV để lấy đủ' if len(d) > 500 else ''))
        st.session_state['cx_ids_ds'] = t['Mã khách'].tolist()
        st.dataframe(t.style.format({'Xác suất không mua lại': fmt(3), 'Giá trị một lần mua (USD)': fmt(1), 'Giá trị kỳ vọng (USD)': fmt(1)}), hide_index=True, width="stretch", height=420,
                     on_select=lambda: mo_ho_so('cx_ds', 'cx_ids_ds'), selection_mode='single-row', key='cx_ds')
    if vai_tro == 'Nhân viên phân tích dữ liệu': st.caption('Vai trò phân tích chỉ xem, không duyệt và không xuất danh sách.')
    else:
        xuat = d[['CustomerID', 'NguonChon', 'LyDo', 'Nhom', 'ABC', 'RiskScore', 'RiskLevel', 'v', 'EV', 'KenhRule', 'SanPhamGoiY', 'QuyTacSP', 'GiaiThich']].rename(columns={'LyDo': 'LyDoDieuChinh'})
        bot_ra = [x_['ma_khach'] for x_ in nhat_ky if x_['thao_tac'] == 'Bớt']
        if bot_ra: xuat = pd.concat([xuat, pd.DataFrame({'CustomerID': bot_ra, 'NguonChon': 'Bớt thủ công (không chăm sóc)', 'LyDoDieuChinh': ly_do})])
        st.download_button('Xuất danh sách đã duyệt (CSV)', xuat.to_csv(index=False).encode('utf-8-sig'), file_name=f'danh_sach_cham_soc_{C.SCORING_DATE}.csv', disabled=thieu_ly_do)

# ================= 5. THEO DÕI =================
else:
    page_header('05 · Quản trị mô hình', 'Theo dõi mô hình và quy tắc', 'du_lieu', 'du_doan')
    t = folds[folds.mo_hinh.isin(['Naive Bayes rời rạc', 'Recency đảo chiều', 'MLP (32,16)'])][['E', 'mo_hinh', 'AUC']].copy(); t['mo_hinh'] = t.mo_hinh.map({'Naive Bayes rời rạc': 'Naive Bayes (đang dùng)', 'Recency đảo chiều': 'Recency (quy tắc đơn giản)', 'MLP (32,16)': 'MLP (so sánh)'})
    t['E'] = pd.to_datetime(t.E).dt.strftime('%d/%m/%Y'); t['AUC_vn'] = t.AUC.map(lambda x: vn(x, 3))
    tabs5 = st.tabs(['Hiệu năng mô hình', 'Biến động dữ liệu', 'Cây đối chứng & phân nhóm', 'Hình kiểm định', 'Phiên bản & quy tắc'])
    with tabs5[0]:
        with st.container(border=True):
            st.subheader('Khả năng xếp hạng (ROC-AUC) ở bốn mốc đã đủ nhãn')
            altair_wide(alt.Chart(t).mark_line(point=alt.OverlayMarkDef(size=50, shape='square'), strokeWidth=2.3).encode(x=alt.X('E:N', title='Mốc đánh giá', sort=None, axis=alt.Axis(labelAngle=0)),
                        y=alt.Y('AUC:Q', scale=alt.Scale(domain=[0.6, 0.8]), title='ROC-AUC', axis=alt.Axis(labelExpr="replace(format(datum.value, '.2f'), '.', ',')")),
                        color=alt.Color('mo_hinh:N', title='', scale=alt.Scale(domain=['Naive Bayes (đang dùng)', 'Recency (quy tắc đơn giản)', 'MLP (so sánh)'], range=[NAVY, NEUTRAL, AMBER]), legend=alt.Legend(orient='bottom', labelLimit=300, symbolType='square')), tooltip=[alt.Tooltip('E', title='Mốc'), alt.Tooltip('mo_hinh', title='Mô hình'), alt.Tooltip('AUC_vn', title='ROC-AUC')]).properties(height=300))
        a, b = st.columns(2)
        with a:
            with st.container(border=True):
                st.subheader('ROC-AUC trung bình bốn mốc (cao hơn là tốt)'); altair_wide(chart_model_compare('AUC', 'ROC-AUC', "replace(format(datum.value, '.2f'), '.', ',')"))
        with b:
            with st.container(border=True):
                st.subheader('Brier trung bình bốn mốc (thấp hơn là tốt)'); altair_wide(chart_model_compare('Brier', 'Brier score', "replace(format(datum.value, '.2f'), '.', ',')"))
        ghi_chu('auc', 'diem_cao', noi='p5')
    with tabs5[1]:
        with st.container(border=True):
            st.subheader('Cơ cấu khách thay đổi theo thời gian')
            m = moc.rename(columns={'T': 'Mốc', 'so_khach': 'Số khách', 'ty_le_y1': 'Tỷ lệ không mua lại', 'mot_don': 'Tỷ lệ khách mới mua 1 đơn', 'bike': 'Tỷ lệ mua xe đạp', 'nsub2': 'Tỷ lệ mua từ 2 danh mục'})[['Mốc', 'Số khách', 'Tỷ lệ không mua lại', 'Tỷ lệ khách mới mua 1 đơn', 'Tỷ lệ mua xe đạp', 'Tỷ lệ mua từ 2 danh mục']]
            altair_wide(chart_matured_snapshot_trends(moc))
            st.dataframe(m.style.format({'Số khách': fmt(), 'Tỷ lệ không mua lại': fpct(), 'Tỷ lệ khách mới mua 1 đơn': fpct(), 'Tỷ lệ mua xe đạp': fpct(), 'Tỷ lệ mua từ 2 danh mục': fpct()}), hide_index=True, width="stretch", height=300)
            st.caption('Mốc 08/07/2014 là mốc chấm điểm nên chưa có tỷ lệ không mua lại (—).')
    with tabs5[2]:
        a, b = st.columns(2)
        with a:
            with st.container(border=True):
                st.subheader('11 lá của cây đối chứng'); altair_wide(chart_tree_leaves())
        with b:
            with st.container(border=True):
                st.subheader('Chọn số nhóm k cho K-means (k = 5)'); altair_wide(chart_choose_k())
    with tabs5[3]:
        a, b, c = st.columns([5, 3, 4])
        with a:
            with st.container(border=True):
                st.subheader('Đường ROC và Precision-Recall'); st.image(f'{R4}/hinh_4_3_2_roc_pr.png', width='content')
        with b:
            with st.container(border=True):
                st.subheader('Ma trận nhầm lẫn'); st.image(f'{R4}/hinh_4_3_2_ma_tran_nham_lan.png', width='content')
        with c:
            with st.container(border=True):
                st.subheader('Phân bố RiskScore: NB so với MLP'); st.image(f'{R4}/hinh_4_3_2_phan_bo_diem.png', width='content')
    with tabs5[4]:
        km = json.load(open(f'{ROOT}/models/kmeans_E{C.SCORING_DATE.replace("-", "")}.json'))
        with st.container(border=True):
            st.subheader('Phiên bản mô hình và quy tắc đang dùng')
            st.dataframe(pd.DataFrame([{'Thành phần': 'Mô hình chấm điểm', 'Phiên bản': f'NB_T{C.SCORING_TRAIN_DATE.replace("-", "")}_v1', 'Học ở mốc': '01/03/2014', 'Ghi chú': 'Naive Bayes, 5 thuộc tính rời rạc'}, {'Thành phần': 'Cây đối chứng', 'Phiên bản': f'TREE_T{C.SCORING_TRAIN_DATE.replace("-", "")}_v1', 'Học ở mốc': '01/03/2014', 'Ghi chú': '11 lá, cho TopFactors'}, {'Thành phần': 'Phân nhóm', 'Phiên bản': f'KMEANS_E{C.SCORING_DATE.replace("-", "")}_v1', 'Học ở mốc': '08/07/2014', 'Ghi chú': f'k = 5, silhouette {km["silhouette"]:.3f}'.replace('.', ',')}, {'Thành phần': 'Kho quy tắc', 'Phiên bản': 'R1–R9 bản 1', 'Học ở mốc': '—', 'Ghi chú': 'R1, R9 tạm tắt vì chưa có dữ liệu CRM'}]), hide_index=True, width="stretch")
        with st.container(border=True):
            st.subheader('Luật kết hợp sản phẩm R6–R8 (gợi ý mua kèm)'); altair_wide(chart_assoc_rules())
        if vai_tro != 'Nhân viên chăm sóc khách hàng':
            with st.container(border=True):
                st.subheader('Đề xuất quy tắc mới (chờ duyệt)')
                c1, c2 = st.columns(2); dk = c1.text_input('Điều kiện (IF)', placeholder='Nhóm N2 và đã mua Road Bikes'); kn_ = c2.text_input('Khuyến nghị (THEN)', placeholder='Gợi ý Helmets')
                if st.button('Gửi duyệt'):
                    if dk.strip() and kn_.strip(): note(f'"NẾU {dk.strip()} THÌ {kn_.strip()}" ở trạng thái chờ duyệt. Bản trình diễn chưa lưu đề xuất vào kho, quản lý duyệt rồi nhân viên phân tích thêm vào analytics.CareRule.', 'ok', 'Đã ghi nhận đề xuất')
                    else: note('Cần nhập cả điều kiện và khuyến nghị.', 'risk', 'Thiếu thông tin')
