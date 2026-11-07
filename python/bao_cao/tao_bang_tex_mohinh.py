"""Sinh bảng và chép hình LaTeX cho chương 5 (Mô hình) và chương 7 (Đánh giá) từ file kết quả.

Mọi con số trong bảng lấy thẳng từ results/ nên không gõ tay.
Ra: latex/bang/m_*.tex (được \\input trong latex/5_mo_hinh.tex) và latex/IMAGE/m_*.png
Chạy: .venv/bin/python python/bao_cao/tao_bang_tex_mohinh.py
"""
import json
import os
import shutil
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RA = os.path.join(GOC, "latex", "bang")
HINH = os.path.join(GOC, "latex", "IMAGE")
os.makedirs(RA, exist_ok=True)
R = lambda *p: os.path.join(GOC, "results", *p)


def so(x, nd=0):
    """Số kiểu Việt: 18.360 và 0,837."""
    if pd.isna(x):
        return "--"
    s = f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "$-$" + s[1:] if s.startswith("-") else s


def pct(x, nd=1):
    """Phần trăm, làm tròn nửa lên."""
    if pd.isna(x):
        return "--"
    v = (Decimal(str(round(float(x), 6))) * 100).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)
    return so(float(v), nd) + "\\%"


def ngay(s):
    s = str(s)
    if "-" in s:
        y, m, d = s.split("-")
        return f"{d}/{m}/{y}"
    return s


def ghi(ten, tieu_de, cot, dong):
    out = [f"\\begin{{tabular}}{{{cot}}}", "\\toprule", tieu_de + " \\\\", "\\midrule"]
    out += [" & ".join(r) + " \\\\" for r in dong]
    out += ["\\bottomrule", "\\end{tabular}"]
    with open(os.path.join(RA, ten), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def tex(s):
    return (str(s).replace("≥", "$\\geq$").replace("<", "$<$").replace("≤", "$\\leq$")
            .replace("&", "\\&").replace("_", "\\_").replace("–", "--"))


# ---------- Bảng: kết quả trung bình bốn fold ----------
t = pd.read_csv(R("cum4", "bang_4_3_2b_trung_binh.csv"))
ten = {"Naive Bayes rời rạc": "Naive Bayes rời rạc", "MLP (32,16)": "Mạng nơ-ron MLP (32, 16)",
       "Cây Gini sâu 4, lá 400": "Cây Gini (sâu 4, 400 khách mỗi lá)", "Logistic one-hot": "Hồi quy logistic",
       "Lớp đa số": "Luôn dự đoán lớp đa số", "Recency đảo chiều": "Recency đảo chiều",
       "Random Forest 300": "Random Forest (300 cây)", "Gradient boosting": "Gradient boosting", "kNN k=200": "kNN ($k=200$)"}
thu_tu = ["Naive Bayes rời rạc", "MLP (32,16)", "Cây Gini sâu 4, lá 400", "Logistic one-hot", "Recency đảo chiều",
          "Lớp đa số", "Random Forest 300", "Gradient boosting", "kNN k=200"]
t = t.set_index("mo_hinh").loc[thu_tu].reset_index()
dong = [[ten[r.mo_hinh], so(r.AUC, 3), so(r.Brier, 3), so(r.Z_pv), f"{r.DK1}/4", f"{r.DK2}/4", f"{r.DK3}/4"] for r in t.itertuples()]
ghi("m_trungbinh.tex", "Mô hình & ROC-AUC & Brier & $Z$ (USD) & ĐK1 & ĐK2 & ĐK3", "lrrrccc", dong)
Z_V, Z_ORA = t.Z_v.iloc[0], t.Z_oracle.iloc[0]
assert round(Z_V) == 269043 and round(Z_ORA) == 346378

# ---------- Bảng: Naive Bayes và MLP theo mốc ----------
c = pd.read_csv(R("cum4", "bang_4_3_2c_nb_vs_mlp.csv"))
dong = [[ngay(r.E), so(r.Z_NB), so(r.Z_MLP), so(r.Z_NB - r.Z_MLP)] for r in c.itertuples()]
dong.append(["Trung bình", so(c.Z_NB.mean()), so(c.Z_MLP.mean()), so((c.Z_NB - c.Z_MLP).mean())])
ghi("m_nb_mlp.tex", "Mốc đánh giá $E$ & $Z$ Naive Bayes & $Z$ MLP & Chênh lệch", "lrrr", dong)
assert c.NB_cao_hon.all()

# ---------- Bảng: Z của bốn cách chọn khách theo mốc (Naive Bayes, quy tắc Recency, chỉ theo v, trần) ----------
f = pd.read_csv(R("cum4", "bang_4_3_2a_theo_fold.csv"))
nb = f[f.mo_hinh == "Naive Bayes rời rạc"].set_index("E")
rc = f[f.mo_hinh == "Recency đảo chiều"].set_index("E").loc[nb.index]
lap = lambda z, zv, zo: (z - zv) / (zo - zv)          # phần khoảng cách từ "chỉ theo v" lên mức trần mà cách chọn lấp được
dong = [[ngay(E), so(nb.Z_pv[E]), so(rc.Z_pv[E]), so(nb.Z_v[E]), so(nb.Z_oracle[E]),
         pct(nb.Z_pv[E] / rc.Z_pv[E] - 1), pct(lap(nb.Z_pv[E], nb.Z_v[E], nb.Z_oracle[E])), pct(lap(rc.Z_pv[E], nb.Z_v[E], nb.Z_oracle[E]))] for E in nb.index]
dong.append(["Trung bình", so(nb.Z_pv.mean()), so(rc.Z_pv.mean()), so(nb.Z_v.mean()), so(nb.Z_oracle.mean()),
             pct(nb.Z_pv.mean() / rc.Z_pv.mean() - 1), pct(lap(nb.Z_pv, nb.Z_v, nb.Z_oracle).mean()), pct(lap(rc.Z_pv, nb.Z_v, nb.Z_oracle).mean())])
ghi("m_z_recency.tex", "Mốc $E$ & Naive Bayes & Quy tắc Recency & Chỉ theo $v$ & Trần & NB hơn quy tắc & NB lấp & Quy tắc lấp", "lrrrrrrr", dong)
assert (nb.Z_pv > rc.Z_pv).all() and (nb.K == 4000).all()

# ---------- Bảng: cấu hình so sánh ----------
d = pd.read_csv(R("cum4", "bang_4_3_2d_cau_hinh.csv"))
ten_cf = {"NB, học mốc gần nhất (thiết kế)": "Naive Bayes, học tại mốc gần nhất (thiết kế)",
          "NB, học một lần ở mốc đầu": "Naive Bayes, học một lần ở mốc đầu",
          "NB, gộp mọi mốc đủ nhãn": "Naive Bayes, gộp mọi mốc đủ nhãn",
          "Cây sâu 4 (thiết kế)": "Cây sâu 4 (thiết kế)", "Cây lá 200": "Cây, 200 khách mỗi lá",
          "Cây lá 800": "Cây, 800 khách mỗi lá", "Cây m = 0": "Cây, $m=0$", "Cây m = 200": "Cây, $m=200$"}
dong = []
for r in d.itertuples():
    nm = ten_cf.get(r.cau_hinh, r.cau_hinh.replace("Cây sâu", "Cây sâu"))
    nm = nm.replace("MLP (16,)", "MLP (16)").replace("MLP (32,16)", "MLP (32, 16)").replace("MLP (64,32)", "MLP (64, 32)")
    dong.append([nm, so(r.AUC, 3), so(r.Brier, 3), so(r.Z)])
ghi("m_cauhinh.tex", "Cấu hình & ROC-AUC & Brier & $Z$ (USD)", "lrrr", dong)

# ---------- Bảng: tập thuộc tính ----------
h = pd.read_csv(R("cum4b", "bang_4_3_2h_tap_thuoc_tinh.csv"))
dong = []
for r in h.itertuples():
    nm = (r.tap.replace("Thiết kế: R, F, M, BikeBuyer, NSub", "Thiết kế: R, F, M, BikeBuyer, NSub")
          .replace("Thêm Orders180 (0, 1, ≥ 2)", "Thêm Orders180").replace("Thêm Tenure (tứ phân vị)", "Thêm Tenure"))
    dong.append([nm, so(r.AUC, 3), so(r.Brier, 3), so(r.Z), "--" if r.chenh_Z_so_thiet_ke == 0 else so(r.chenh_Z_so_thiet_ke),
                 "--" if r.chenh_Z_so_thiet_ke == 0 else f"{r.so_fold_Z_hon_thiet_ke}/4", f"{r.DK1}/4"])
ghi("m_tapthuoctinh.tex", "Tập thuộc tính & ROC-AUC & Brier & $Z$ (USD) & Chênh $Z$ & Số fold $Z$ cao hơn & ĐK1", "lrrrrcc", dong)

# ---------- Bảng: nhãn 90 và 180 ngày ----------
n = pd.read_csv(R("cum4b", "bang_4_3_1d_nhan_180_moc.csv"))
dong = [[r.T, so(r.so_khach), pct(r.ty_le_y90), pct(r.ty_le_y180), so(r.y90_1_mua_trong_90_180), pct(r.ty_le_chua_den_ky)] for r in n.itertuples()]
ghi("m_nhan180.tex", "Mốc $T$ & Số khách & $y=1$ (90 ngày) & $y=1$ (180 ngày) & Khách $y=1$ mua lại trong ngày 90--180 & Tỷ lệ chưa đến kỳ",
    "lR{1.6cm}R{2.0cm}R{2.0cm}R{3.6cm}R{2.2cm}", dong)
assert len(dong) == 13

# ---------- Bảng: chỉ số lớp 1 ----------
l1 = pd.read_csv(R("cum5", "bang_4_3_3a_lop1_ba_nguong.csv"), index_col=0)
cot = list(l1.columns)
dong = []
for ch in ["Số khách bị cảnh báo (dự đoán y = 1)", "Tỷ lệ khách bị cảnh báo", "TP", "FN", "FP", "TN", "Accuracy", "Tỷ lệ lỗi",
           "Precision", "Sensitivity (recall)", "Specificity", "F1"]:
    row = l1.loc[ch]
    if ch.startswith("Số khách") or ch in ("TP", "FN", "FP", "TN"):
        vals = [so(v) for v in row]
    elif ch.startswith("Tỷ lệ khách"):
        vals = [pct(v) for v in row]
    else:
        vals = [so(v, 3) for v in row]
    nm = {"Số khách bị cảnh báo (dự đoán y = 1)": "Số khách dự đoán $y=1$", "Tỷ lệ khách bị cảnh báo": "Tỷ lệ khách dự đoán $y=1$",
          "Sensitivity (recall)": "Sensitivity (recall)", "Tỷ lệ lỗi": "Tỷ lệ lỗi (error rate)"}.get(ch, ch)
    dong.append([nm] + vals)
ghi("m_lop1.tex", "Chỉ số & Youden, mốc huấn luyện & Youden, ngoài mẫu & Mức Cao của DSS & Luôn $y=1$",
    "lrrrr", dong)
assert len(cot) == 4

# ---------- Bảng: lớp 2 và lớp 3 ----------
l23 = pd.read_csv(R("cum5", "bang_4_3_3b_lop2_lop3.csv"))
gtri = dict(zip(l23["Chỉ số"], l23.iloc[:, 2]))
dong = [["Xếp hạng", "ROC-AUC của Naive Bayes", so(gtri["ROC-AUC"], 4)],
        ["", "ROC-AUC của Recency đảo chiều", so(gtri["ROC-AUC Recency đảo chiều"], 4)],
        ["", "Average precision, lớp $y=1$", so(gtri["AP lớp 1"], 3)],
        ["", "Average precision, lớp $y=0$", so(gtri["AP lớp 0"], 3)],
        ["", "Precision@4.000", pct(gtri["Precision@K (K = 4000)"], 2)],
        ["Chất lượng xác suất", "Brier của Naive Bayes", so(gtri["Brier"], 4)],
        ["", "Brier của cách dự đoán một xác suất hằng", so(gtri["Brier dự đoán hằng số"], 4)],
        ["Giá trị quyết định", "$Z$ khi chọn theo $p\\cdot v$ (USD)", so(gtri["Z theo p·v (USD)"], 2)],
        ["", "$Z$ khi chỉ chọn theo $v$ (USD)", so(gtri["Z chỉ theo v (USD)"], 2)],
        ["", "$Z$ khi biết trước nhãn (USD)", so(gtri["Z biết trước nhãn (USD)"], 2)]]
ghi("m_lop23.tex", "Lớp & Chỉ số & Giá trị tại mốc 01/03/2014", "llr", dong)
zpv, zv, zo = gtri["Z theo p·v (USD)"], gtri["Z chỉ theo v (USD)"], gtri["Z biết trước nhãn (USD)"]
print("tăng so với chỉ theo v: %.1f%%, thu hẹp khoảng cách đến trần: %.1f%%" % ((zpv / zv - 1) * 100, (zpv - zv) / (zo - zv) * 100))

# ---------- Bảng: xác suất có điều kiện của Naive Bayes ----------
x = pd.read_csv(R("cum5", "bang_4_3_4_xac_suat_co_dieu_kien_NB.csv"))
dong, truoc = [], None
for r in x.itertuples():
    tt = r.thuoc_tinh if r.thuoc_tinh != truoc else ""
    truoc = r.thuoc_tinh
    dong.append([tt, tex(str(r.khoang).replace("Q1", "Q1 (thấp nhất)").replace("Q4", "Q4 (cao nhất)")), pct(r.P_x_y0, 1), pct(r.P_x_y1, 1), so(r.ty_so, 2)])
ghi("m_xacsuat.tex", "Thuộc tính & Khoảng & $P(x\\mid y=0)$ & $P(x\\mid y=1)$ & Tỷ số", "llrrr", dong)

# ---------- Bảng: các lá của cây đối chứng ----------
LUAT = [  # (số nút trong sklearn, luật), thứ tự duyệt cây từ trái sang phải
    (4, "Recency $\\leq$ 275,5, Monetary $\\leq$ 4.640,88, chưa mua xe đạp, Monetary $\\leq$ 150,94"),
    (5, "Recency $\\leq$ 275,5, Monetary $\\leq$ 4.640,88, chưa mua xe đạp, Monetary $>$ 150,94"),
    (7, "Recency $\\leq$ 275,5, Monetary $\\leq$ 4.640,88, đã mua xe đạp, Monetary $\\leq$ 1.956,81"),
    (8, "Recency $\\leq$ 275,5, Monetary $\\leq$ 4.640,88, đã mua xe đạp, Monetary $>$ 1.956,81"),
    (10, "Recency $\\leq$ 275,5, Monetary từ 4.640,88 đến 4.960,65"),
    (12, "Recency $\\leq$ 275,5, Monetary từ 4.960,65 đến 6.587,16"),
    (13, "Recency $\\leq$ 275,5, Monetary $>$ 6.587,16"),
    (16, "Recency $>$ 275,5, Tenure $\\leq$ 744, Monetary $\\leq$ 1.684,87"),
    (18, "Recency $>$ 275,5, Tenure $\\leq$ 744, Monetary từ 1.684,87 đến 2.349,77"),
    (19, "Recency $>$ 275,5, Tenure $\\leq$ 744, Monetary $>$ 2.349,77"),
    (20, "Recency $>$ 275,5, Tenure $>$ 744"),
]
lc = pd.read_csv(R("cum4", "bang_4_3_2f_la_cay.csv")).set_index("leaf")
assert [a for a, _ in LUAT] == list(lc.index) and int(lc["count"].sum()) == 14167
dong = [[str(i + 1), luat, so(lc.loc[nut, "count"]), pct(lc.loc[nut, "mean"]), so(lc.loc[nut, "TreeScore_m50"], 3)]
        for i, (nut, luat) in enumerate(LUAT)]
ghi("m_la_cay.tex", "Lá & Luật (IF) & Số khách & $y=1$ thô & TreeScore", "cp{8.6cm}rrr", dong)

# ---------- Bảng: ba khách minh hoạ ----------
k = pd.read_csv(R("cum5", "bang_4_3_4_khach_minh_hoa.csv"))
lanum = {12201: 1, 26339: 5, 26774: 8}
dong = [[str(r.CustomerID), so(r.Recency), so(r.Frequency), so(r.Monetary, 2), so(r.RiskScore, 3), so(r.RiskPercentile, 1), r.RiskLevel,
         so(r.TreeScore, 3), "Có" if r.Flag else "Không", str(lanum[r.CustomerID])] for r in k.itertuples()]
ghi("m_khach_minh_hoa.tex", "Mã khách & Recency & Frequency & Monetary & RiskScore & Phân vị & Mức & TreeScore & Cờ lệch & Lá", "rrrrrrlrcc", dong)
for r in k.itertuples():  # lá nêu trong TopFactors phải đúng số đã gán
    assert f"Lá {lanum[r.CustomerID]}:" in r.TopFactors

# ---------- Bảng: kết quả chấm điểm theo hạng ABC ----------
j = json.load(open(R("cum5", "tom_tat.json"), encoding="utf-8"))
dong, tong_n, tong_c = [], 0, 0
for h_ in "ABC":
    n_ = j["cao_hang"][h_] + j["thap_hang"][h_]
    tong_n += n_
    tong_c += j["cao_hang"][h_]
    dong.append([f"Hạng {h_}", so(n_), so(j["cao_hang"][h_]), pct(j["cao_hang"][h_] / n_), so(j["cao_min"][h_], 3), so(j["cao_median"][h_], 3)])
dong.append(["Cộng", so(tong_n), so(tong_c), pct(tong_c / tong_n), "--", "--"])
assert tong_n == j["n"] == 18360 and tong_c == j["cao"] == 4592
ghi("m_hang_abc.tex", "Hạng & Số khách & Số khách mức Cao & Tỷ lệ & Thấp nhất & Trung vị", "lrrrrr", dong)

# ---------- Chương 7, dư địa cải tiến mô hình (results/cum4c) ----------
if os.path.isdir(R("cum4c")):
    # lift theo decile của Naive Bayes tại mốc 01/03/2014
    lf = pd.read_csv(R("cum4c", "bang_7_lift_moc_cuoi.csv"))
    dong = [[f"{int(r.decile)}", so(r.so_khach), pct(r.ty_le_y1), so(r.lift, 2), pct(r.tich_luy_bat_duoc)] for r in lf.itertuples()]
    ghi("m_lift.tex", "Decile (10\\% khách, rủi ro giảm dần) & Số khách & Tỷ lệ $y=1$ & Lift & Tích luỹ khách $y=1$ bắt được", "crrrr", dong)
    # trần theo ô thuộc tính
    tr = pd.read_csv(R("cum4c", "bang_7_tran_trung_binh.csv"), index_col=0).gia_tri
    nb_z = tr.NB_thuc_te
    dong = [["Naive Bayes thực tế (học ở mốc trước, dự đoán mốc sau)", so(nb_z), "--"],
            [f"Trần của 5 thuộc tính đang dùng ({so(tr.so_o_5)} ô)", so(tr.tran_5_thuoc_tinh), pct(tr.tran_5_thuoc_tinh / nb_z - 1)],
            ["Trần khi thêm vùng bán hàng", so(tr.tran_them_vung), pct(tr.tran_them_vung / nb_z - 1)],
            [f"Trần khi thêm vùng, đơn gần nhất có xe đạp, thu nhập ({so(tr.so_o_8)} ô)", so(tr.tran_them_vung_xe_thunhap), pct(tr.tran_them_vung_xe_thunhap / nb_z - 1)],
            ["Trần khi biết trước nhãn", so(tr.tran_biet_nhan), pct(tr.tran_biet_nhan / nb_z - 1)]]
    ghi("m_du_dia_tran.tex", "Cách chọn khách & $Z$ (USD) & So với Naive Bayes", "p{8.6cm}rr", dong)
    # dữ liệu nguồn chưa dùng
    ng = pd.read_csv(R("cum4c", "bang_7_nguon_trung_binh.csv"))
    ten_mh = {"Naive Bayes rời rạc": "Naive Bayes rời rạc (đang dùng)", "GB 11 thuộc tính + trọng số dịch chuyển": "Gradient boosting, 11 thuộc tính, trọng số dịch chuyển",
              "GB 11 + nhân khẩu học + hành vi mới": "Gradient boosting, thêm nhân khẩu học và hành vi theo đơn", "Trung bình Naive Bayes và GB đủ": "Trung bình Naive Bayes và gradient boosting đủ thuộc tính"}
    dong = [[ten_mh[r.mo_hinh], so(r.AUC, 3), so(r.Brier, 3), so(r.Z_pv), f"{int(r.fold_Z_hon_NB)}/4"] for r in ng.itertuples()]
    ghi("m_du_dia_nguon.tex", "Mô hình & ROC-AUC & Brier & $Z$ (USD) & Mốc có $Z$ cao hơn Naive Bayes", "p{6.6cm}rrrc", dong)
    # Z theo ngân sách
    zb = pd.read_csv(R("cum4c", "bang_7_z_ngan_sach.csv"), index_col=0); cols = list(zb.columns)
    ten_zb = dict(ten_mh, **{"Chỉ theo giá trị v": "Chỉ theo giá trị $v$", "Trần khi biết nhãn": "Trần khi biết trước nhãn"})
    thu_tu = ["Naive Bayes rời rạc", "Trung bình Naive Bayes và GB đủ", "Chỉ theo giá trị v", "Trần khi biết nhãn"]
    dong = [[ten_zb[k]] + [so(zb.loc[k, c]) for c in cols] for k in thu_tu]
    ghi("m_z_ngan_sach.tex", "Cách chọn khách & " + " & ".join(f"$B = {so(float(c))}$" for c in cols), "p{6.2cm}" + "r" * len(cols), dong)

# ---------- Hình ----------
for nguon, dich in [(("cum4", "hinh_4_3_2_roc_pr.png"), "m_roc_pr.png")]:  # m_phan_bo_diem.png do python/bao_cao/ve_hinh_mohinh.py vẽ
    shutil.copyfile(R(*nguon), os.path.join(HINH, dich))
print("xong")
