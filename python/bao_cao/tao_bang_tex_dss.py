"""Sinh bảng LaTeX cho chương 6 (Hệ hỗ trợ ra quyết định) từ file kết quả cụm 6 và 6b.

Mọi con số trong bảng lấy thẳng từ results/ nên không gõ tay.
Ra: latex/bang/d_*.tex (được \\input trong latex/6_dss.tex)
Chạy: .venv/bin/python python/bao_cao/tao_bang_tex_dss.py
"""
import os
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RA = os.path.join(GOC, "latex", "bang")
os.makedirs(RA, exist_ok=True)
R = lambda *p: os.path.join(GOC, "results", *p)


def so(x, nd=0):
    if pd.isna(x):
        return "--"
    s = f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "$-$" + s[1:] if s.startswith("-") else s


def pct(x, nd=1):
    if pd.isna(x):
        return "--"
    v = (Decimal(str(round(float(x), 6))) * 100).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return so(float(v), nd) + "\\%"


def dau(x):
    """Số có dấu +/-, kiểu Việt, nguyên."""
    return ("+" if x > 0 else "") + so(x)


def ghi(ten, tieu_de, cot, dong):
    out = [f"\\begin{{tabular}}{{{cot}}}", "\\toprule", tieu_de + " \\\\", "\\midrule"]
    out += [" & ".join(r) + " \\\\" for r in dong]
    out += ["\\bottomrule", "\\end{tabular}"]
    with open(os.path.join(RA, ten), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


# ---------- phân hạng ABC ----------
a = pd.read_csv(R("cum6", "bang_4_4_abc.csv"))
assert list(a.so_khach) == [5137, 2581, 10642]
ghi("d_abc.tex", "Hạng & Số khách & Tỷ lệ khách & Tỷ trọng Monetary & Monetary trung vị (USD) & RiskScore trung bình & $v$ trung vị (USD)", "lR{1.5cm}R{1.5cm}R{1.9cm}R{2.2cm}R{2.1cm}R{2.2cm}",
    [[f"Hạng {r.ABC}", so(r.so_khach), pct(r.ty_le_khach), pct(r.ty_trong_M, 0), so(r.M_trung_vi, 2), so(r.p_TB, 3), so(r.v_trung_vi, 2)] for r in a.itertuples()])

# ---------- độ nhạy ngưỡng ABC ----------
n = pd.read_csv(R("cum6b", "bang_4_4_abc_do_nhay.csv")).set_index("nguong")
x, y = n.loc["80% / 95%"], n.loc["70% / 90%"]
ba = lambda r, k: " / ".join(so(r[c]) for c in k)
dong = [["Số khách hạng A / B / C", ba(x, "ABC"), ba(y, "ABC")],
        ["Khách mức Cao hạng A / B / C", ba(x, ["Cao_A", "Cao_B", "Cao_C"]), ba(y, ["Cao_A", "Cao_B", "Cao_C"])],
        ["Khách đủ điều kiện R3", so(x.R3_du_dk), so(y.R3_du_dk)],
        ["Khách được chọn R3 / R5", f"{so(x.R3_chon)} / {so(x.R5_chon)}", f"{so(y.R3_chon)} / {so(y.R5_chon)}"],
        ["Tổng khách được chọn", so(x.so_chon), so(y.so_chon)],
        ["Chi phí (USD)", so(x.chi), so(y.chi)],
        ["$Z$ (USD)", so(x.Z), so(y.Z)],
        ["Chênh $Z$ so với thiết kế (USD)", so(x.chenh_Z), so(y.chenh_Z)],
        ["Số khách đổi hạng", so(x.khach_doi_hang), so(y.khach_doi_hang)]]
ghi("d_abc_nguong.tex", "Chỉ số & Ngưỡng 80\\%/95\\% (thiết kế) & Ngưỡng 70\\%/90\\%", "lrr", dong)
assert int(y.chenh_Z) == -1802 and int(y.khach_doi_hang) == 2278

# ---------- chọn k ----------
k = pd.read_csv(R("cum6", "bang_4_4_chon_k.csv"))
ghi("d_chon_k.tex", "$k$ & WCSS & Silhouette", "crr", [[str(int(r.k)), so(r.WCSS, 1), so(r.Silhouette, 3)] for r in k.itertuples()])

# ---------- hồ sơ năm nhóm ----------
g = pd.read_csv(R("cum6", "bang_4_4_ho_so_nhom.csv")).set_index("Nhom")
cs = list(g.index)
dong = [["Số khách"] + [so(g.so_khach[i]) for i in cs],
        ["Tỷ lệ khách"] + [pct(g.ty_le[i]) for i in cs],
        ["Recency trung vị (ngày)"] + [so(g.R_trung_vi[i], 1 if g.R_trung_vi[i] % 1 else 0) for i in cs],
        ["Frequency trung bình"] + [so(g.F_trung_binh[i], 2) for i in cs],
        ["Monetary trung vị (USD)"] + [so(g.M_trung_vi[i], 2) for i in cs],
        ["Tỷ trọng Monetary"] + [pct(g.ty_trong_M[i]) for i in cs],
        ["Khách hạng A / B / C"] + [f"{so(g.hang_A[i])} / {so(g.hang_B[i])} / {so(g.hang_C[i])}" for i in cs],
        ["RiskScore trung bình"] + [so(g.RiskScore_TB[i], 3) for i in cs],
        ["Tỷ lệ mức Cao"] + [pct(g.ty_le_Cao[i]) for i in cs],
        ["Tỷ lệ khách $EV>0$"] + [pct(g.ty_le_EV_duong[i]) for i in cs],
        ["Được chọn theo kênh"] + [so(g.duoc_chon_kenh[i]) for i in cs]]
ghi("d_ho_so_nhom.tex", "Chỉ số & " + " & ".join(cs), "lrrrrr", dong)
assert abs(g.ty_trong_M["N1"] + g.ty_trong_M["N2"] - 0.936) < 1e-9 and int(g.so_khach.sum()) == 18360

# ---------- cơ cấu sản phẩm ----------
p = pd.read_csv(R("cum6", "bang_4_4_co_cau_san_pham.csv"))
ghi("d_co_cau_sp.tex", "Nhóm & Bikes & Accessories & Clothing & Tỷ lệ đã mua xe & NSub trung bình", "lrrrrr",
    [[r.Nhom, pct(r.ty_trong_Bikes), pct(r.ty_trong_Accessories), pct(r.ty_trong_Clothing), pct(r.ty_le_da_mua_xe), so(r.NSub_TB, 2)] for r in p.itertuples()])

# ---------- luật kết hợp ----------
ap = pd.read_csv(R("cum6b", "bang_4_4_apriori_luat_goi_y.csv"))
assert len(ap) == 26
top = ap.sort_values("lift", ascending=False).head(10)
ghi("d_apriori.tex", "Hạng & Vế trái & Vế phải & Support & Confidence & Lift", "clllrr",
    [[str(i + 1), r.A, r.B, pct(r.support, 2), pct(r.confidence), so(r.lift, 2)] for i, r in enumerate(top.itertuples())])
dc = pd.read_csv(R("cum6b", "bang_4_4_apriori_doi_chieu.csv"))
ghi("d_apriori_doichieu.tex", "Quy tắc & Luật & Lift theo khách & Hạng trong 26 luật & Confidence theo đơn & Lift theo đơn", "lp{4.6cm}R{1.9cm}R{1.9cm}R{2.1cm}R{1.9cm}",
    [[r.quy_tac, f"{r.A} $\\rightarrow$ {r.B}", so(r.lift, 2), str(int(r.hang_trong_luat_goi_y)), pct(r.confidence_theo_don), so(r.lift_theo_don, 2)] for r in dc.itertuples()])

# ---------- đại lượng đo được ----------
t = pd.read_csv(R("cum6b", "bang_4_4_tham_so_do_duoc.csv"))


def tx(v):
    v = str(v).replace('"', "").replace("%", "\\%").replace("<", "$<$").replace("y = 1", "$y=1$").replace("_", "\\_")
    return v.replace("Khách loại B ở mục 3.5.2: chăm sóc riêng", "Chăm sóc riêng")


ghi("d_tham_so.tex", "Đại lượng & Giá trị & Ghi chú", "p{4.6cm}p{3.6cm}p{6.2cm}",
    [[tx(r.dai_luong), tx(r.gia_tri), tx(r.ghi_chu)] for r in t.itertuples()])

# ---------- what-if ----------
w = pd.read_csv(R("cum6", "bang_4_4_what_if.csv"))
ten = {"Cơ sở": "Cơ sở ($r=10\\%$, $c=10$ USD, $B=40.000$ USD)", "r = 5%": "$r=5\\%$", "r = 20%": "$r=20\\%$", "c = 5 USD": "$c=5$ USD",
       "c = 20 USD": "$c=20$ USD", "B = 20.000": "$B=20.000$ USD", "B = 60.000": "$B=60.000$ USD", "B = 100.000": "$B=100.000$ USD"}
ghi("d_what_if.tex", "Kịch bản & Số khách & Chi phí (USD) & $Z$ (USD) & Chênh so với cơ sở (USD)", "lrrrr",
    [[ten[r.kich_ban], so(r.K), so(r.C), so(r.Z), dau(r.delta_Z) if r.delta_Z else "0"] for r in w.itertuples()])
assert int(w.Z[0]) == 292595

# ---------- độ nhạy ±20% ----------
d = pd.read_csv(R("cum6", "bang_4_4_do_nhay.csv"))
tt = {"r": "$r$", "p": "$p$", "g (qua v)": "$g$ (qua $v$)", "c": "$c$", "B": "$B$"}
dong = []
for ts in ["r", "p", "g (qua v)", "c", "B"]:
    g_ = d[d.tham_so == ts].set_index("thay_doi")
    sg = lambda v: ("+" if v > 0 else "") + pct(v / 100)
    dong.append([tt[ts], so(g_.loc["−20%", "Z"]), sg(g_.loc["−20%", "delta_pct"]), so(g_.loc["+20%", "Z"]), sg(g_.loc["+20%", "delta_pct"])])
ghi("d_do_nhay.tex", "Tham số & $Z$ khi giảm 20\\% (USD) & Chênh & $Z$ khi tăng 20\\% (USD) & Chênh", "lrrrr", dong)

# ---------- payoff ----------
pf = pd.read_csv(R("cum6", "bang_4_4_payoff.csv"))
ghi("d_payoff.tex", "Ngân sách $B$ (USD) & Số khách & $r=2\\%$ & $r=10\\%$ & $r=20\\%$ & Giá trị kỳ vọng", "rrrrrr",
    [[so(r.B), so(r.K), so(r._3), so(r._4), so(r._5), so(r.gia_tri_ky_vong)] for r in pf.itertuples()])

# ---------- theo kênh ----------
k3 = pd.read_csv(R("cum6", "bang_4_4_theo_kenh.csv"))
dong = [[r.KenhRule, so(r.so_khach), so(r.duoc_chon), so(r.chi_phi), so(r.EV_tong)] for r in k3.itertuples()]
dong.append(["Tổng", so(k3.so_khach.sum()), so(k3.duoc_chon.sum()), so(k3.chi_phi.sum()), so(k3.EV_tong.sum())])
ghi("d_theo_kenh.tex", "Kênh & Khách đủ điều kiện & Được chọn & Chi phí (USD) & EV tổng (USD)", "lrrrr", dong)
assert int(k3.duoc_chon.sum()) == 6124

# ---------- dự báo ----------
f = pd.read_csv(R("cum6", "bang_4_4_du_bao.csv")).set_index("chi_so")
ghi("d_du_bao.tex", "Chỉ số & MAPE tháng 4--5/2014 & MAPE mức nền (cùng tháng năm trước) & Dự báo vượt thực tế tháng 6/2014", "lrrr",
    [["Số đơn", pct(f.loc["n", "MAPE_04_05"]), pct(f.loc["n", "MAPE_nen_04_05"]), pct(f.loc["n", "lech_thang_6"], 0)],
     ["Doanh thu", pct(f.loc["rev", "MAPE_04_05"]), pct(f.loc["rev", "MAPE_nen_04_05"]), pct(f.loc["rev", "lech_thang_6"], 0)]])
print("xong")
