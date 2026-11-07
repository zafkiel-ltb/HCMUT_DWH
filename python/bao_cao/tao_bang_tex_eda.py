"""Sinh các bảng LaTeX cho chương "Tiền xử lý và khám phá dữ liệu" từ file kết quả.

Mọi con số trong bảng lấy thẳng từ results/ nên không gõ tay.
Ra: latex/bang/*.tex (được \\input trong latex/4_tien_xu_ly_eda.tex)
Chạy: .venv/bin/python python/bao_cao/tao_bang_tex_eda.py
"""
import os
import pandas as pd

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RA = os.path.join(GOC, "latex", "bang")
os.makedirs(RA, exist_ok=True)
R = lambda *p: os.path.join(GOC, "results", *p)


def so(x, nd=0):
    """Số kiểu Việt."""
    if pd.isna(x):
        return "--"
    s = f"{x:,.{nd}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return "$-$" + s[1:] if s.startswith("-") else s


def pct(x, nd=1):
    """Phần trăm, làm tròn nửa lên (tránh lệch do làm tròn nhị phân)."""
    if pd.isna(x):
        return "--"
    from decimal import Decimal, ROUND_HALF_UP
    v = (Decimal(str(round(float(x), 6))) * 100).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return so(float(v), nd) + "\\%"


def ngay(s):
    """2013-12-15 hoặc 15/12/2013 -> 15/12/2013."""
    s = str(s)
    if "-" in s:
        y, m, d = s.split("-")
        return f"{d}/{m}/{y}"
    return s


def ghi(ten, dong_tieu_de, cot, dong, ghi_chu_cot=None):
    spec = cot
    out = [f"\\begin{{tabular}}{{{spec}}}", "\\toprule", dong_tieu_de + " \\\\", "\\midrule"]
    for r in dong:
        out.append(" & ".join(r) + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}"]
    with open(os.path.join(RA, ten), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


# Bảng bốn fold + mốc chấm điểm
f = pd.read_csv(R("cum3b", "bang_4_3_1b_fold.csv"))
dong = []
for _, r in f.iterrows():
    cs = str(r["cua_so_nhan"]).split("→")
    dong.append([ngay(r["moc_huan_luyen"]), so(r["khach_huan_luyen"]), pct(r["ty_le_y1_huan_luyen"]),
                 ngay(r["moc_danh_gia"]), so(r["khach_danh_gia"]),
                 pct(r["ty_le_y1_danh_gia"]) if not pd.isna(r["ty_le_y1_danh_gia"]) else "--",
                 f"{ngay(cs[0].strip())} đến {ngay(cs[1].strip())}"])
ghi("fold.tex",
    "Mốc huấn luyện & Số khách & $y=1$ & Mốc đánh giá & Số khách & $y=1$ & Cửa sổ nhãn của mốc huấn luyện",
    "lrrlrrl", dong)

# Thống kê mô tả tại mốc chấm điểm
d = pd.read_csv(R("cum6", "dss_khach.csv"))
assert len(d) == 18360
dong = []
for c, nd in [("Recency", 0), ("Frequency", 0), ("Monetary", 2), ("AOV", 2), ("Tenure", 0), ("NSub", 0)]:
    s = d[c]
    dong.append([c, so(s.mean(), 2), so(s.std(), 2), so(s.min(), nd), so(s.quantile(.25), nd),
                 so(s.median(), nd), so(s.quantile(.75), nd), so(s.max(), nd)])
ghi("thong_ke.tex", "Thuộc tính & Trung bình & Độ lệch chuẩn & Nhỏ nhất & Q1 & Trung vị & Q3 & Lớn nhất",
    "lrrrrrrr", dong)

print("đã ghi:", sorted(os.listdir(RA)))
