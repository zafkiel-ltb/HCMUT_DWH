"""Vẽ các hình của chương Tiền xử lý và khám phá dữ liệu (EDA) cho báo cáo LaTeX.

Nguồn: results/cum6/dss_khach.csv (18.360 khách tại mốc 08/07/2014), data/orders.csv, data/lines.csv, data/dataset.csv
(trích từ kho CompanyX_DW), results/cum3b/bang_4_3_1c_khoang.csv.
Ra (latex/IMAGE): eda_phan_bo_rfm.png, eda_tuong_quan.png, eda_xu_huong_thang.png, eda_y_theo_khoang.png,
eda_lech_moc.png, eda_pareto.png, moc_thoi_gian.png (chép từ results/cum3b)
Chạy: .venv/bin/python python/bao_cao/ve_hinh_eda.py
"""
import os
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RA = os.path.join(GOC, "latex", "IMAGE")
os.makedirs(RA, exist_ok=True)

plt.rcParams["font.family"] = "Arial"
plt.rcParams["axes.unicode_minus"] = False
NAVY, DO, XANH, CAM, XAM = "#1f3a5f", "#c0392b", "#2e7d5b", "#e08e45", "#9aa5b1"


def vn(x, nd=0):
    """Số kiểu Việt: dấu chấm hàng nghìn, dấu phẩy thập phân."""
    s = f"{x:,.{nd}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def luu(ten):
    plt.savefig(os.path.join(RA, ten), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()


def dep(a):
    a.spines[["top", "right"]].set_visible(False)


truc_vn = FuncFormatter(lambda v, _: vn(v))
d = pd.read_csv(os.path.join(GOC, "results", "cum6", "dss_khach.csv"))
assert len(d) == 18360, len(d)

# Hình 1: phân bố R, F, M (Monetary tô màu theo việc khách đã mua xe đạp)
fig, ax = plt.subplots(1, 3, figsize=(11.5, 3.6))
ax[0].hist(d["Recency"], bins=40, color=NAVY)
ax[0].axvline(d["Recency"].median(), color=DO, lw=1.3, ls="--")
ax[0].set_title("Recency (ngày)", fontsize=11)
ax[0].set_ylabel("Số khách")
ax[0].text(0.97, 0.93, f"trung vị {vn(d['Recency'].median())}", transform=ax[0].transAxes, ha="right", va="top", color=DO, fontsize=9.5)

f = d["Frequency"].clip(upper=5).value_counts().sort_index()
ax[1].bar([str(i) if i < 5 else "5+" for i in f.index], f.values, color=NAVY)
ax[1].set_title("Frequency (số đơn)", fontsize=11)
for i, v in enumerate(f.values):
    ax[1].text(i, v, vn(v), ha="center", va="bottom", fontsize=8.5)

bins = np.logspace(np.log10(d["Monetary"].min()), np.log10(d["Monetary"].max()), 40)
ax[2].hist([d.loc[d.BikeBuyer == 0, "Monetary"], d.loc[d.BikeBuyer == 1, "Monetary"]], bins=bins, stacked=True,
           color=[CAM, NAVY], label=["Chưa mua xe đạp", "Đã mua xe đạp"])
ax[2].set_xscale("log")
ax[2].axvline(d["Monetary"].median(), color=DO, lw=1.3, ls="--")
ax[2].set_title("Monetary (USD, trục log)", fontsize=11)
ax[2].legend(fontsize=8.5, frameon=False, loc="upper left")
for a in ax:
    dep(a)
    a.yaxis.set_major_formatter(truc_vn)
plt.tight_layout()
luu("eda_phan_bo_rfm.png")

# Hình 2: ma trận tương quan hạng Spearman
cot = ["Recency", "Frequency", "Monetary", "AOV", "Tenure", "NSub"]
c = d[cot].corr(method="spearman")
fig, a = plt.subplots(figsize=(5.6, 4.6))
im = a.imshow(c.values, cmap="RdBu_r", vmin=-1, vmax=1)
a.set_xticks(range(len(cot)), cot, rotation=35, ha="right")
a.set_yticks(range(len(cot)), cot)
for i in range(len(cot)):
    for j in range(len(cot)):
        v = c.values[i, j]
        a.text(j, i, f"{v:.2f}".replace(".", ","), ha="center", va="center", fontsize=9, color="white" if abs(v) > 0.6 else "black")
plt.colorbar(im, ax=a, fraction=0.046, pad=0.04)
plt.tight_layout()
luu("eda_tuong_quan.png")

# Hình 3: xu hướng theo tháng (số đơn, doanh thu, số dòng chi tiết theo danh mục)
o = pd.read_csv(os.path.join(GOC, "data", "orders.csv"), header=None,
                names=["OrderID", "CustomerID", "OrderDate", "ShipDate", "SubTotal", "Tax", "Freight", "TotalDue", "Terr"], parse_dates=["OrderDate"])
li = pd.read_csv(os.path.join(GOC, "data", "lines.csv"), header=None,
                 names=["OrderID", "LineID", "ProductID", "Cat", "Sub", "Qty", "Price", "Disc", "LineTotal"])
assert len(o) == 27382 and len(li) == 59795
o["thang"] = o.OrderDate.dt.to_period("M").dt.to_timestamp()
g = o.groupby("thang").agg(don=("OrderID", "size"), dt=("SubTotal", "sum"))
x = li.merge(o[["OrderID", "thang"]], on="OrderID")
dong = x.pivot_table(index="thang", columns="Cat", values="LineID", aggfunc="count", fill_value=0)
thang = g.index
fig, (a1, a3) = plt.subplots(2, 1, figsize=(10.5, 6.6), sharex=True, gridspec_kw={"hspace": 0.28})
a1.bar(thang, g.don, width=24, color=[NAVY] * (len(g) - 1) + [DO])
a1.set_ylabel("Số đơn mỗi tháng", color=NAVY)
a2 = a1.twinx()
a2.plot(thang, g.dt / 1e6, color=DO, lw=2, marker="o", ms=3)
a2.set_ylabel("Doanh thu SubTotal (triệu USD)", color=DO)
a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: vn(v, 1)))
a1.yaxis.set_major_formatter(truc_vn)
a1.set_title("Số đơn và doanh thu theo tháng", fontsize=11)
a1.text(pd.Timestamp("2011-07-01"), g.don.max() * 0.93,
        f"Cột đỏ: tháng 6/2014 có {vn(g.don.iloc[-1])} đơn nhưng doanh thu chỉ {vn(g.dt.iloc[-1] / 1e3, 1)} nghìn USD",
        fontsize=9.5, color=DO, va="center")
mau = {"Bikes": NAVY, "Accessories": CAM, "Clothing": XANH}
ten = {"Bikes": "Xe đạp", "Accessories": "Phụ kiện", "Clothing": "Trang phục"}
duoi = np.zeros(len(thang))
for k in ("Bikes", "Accessories", "Clothing"):
    a3.bar(thang, dong[k].reindex(thang).fillna(0).values, width=24, bottom=duoi, color=mau[k], label=ten[k])
    duoi += dong[k].reindex(thang).fillna(0).values
a3.set_ylabel("Số dòng chi tiết đơn")
a3.yaxis.set_major_formatter(truc_vn)
a3.set_title("Số dòng chi tiết đơn theo danh mục sản phẩm", fontsize=11)
a3.legend(frameon=False, ncol=3, loc="upper left", fontsize=9.5)
a3.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
a3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
for a in (a1, a2, a3):
    a.spines["top"].set_visible(False)
luu("eda_xu_huong_thang.png")
dongxe = li[li.Cat == "Bikes"].merge(o[["OrderID", "OrderDate"]], on="OrderID")
tt = li.LineTotal.sum()
print("đơn theo năm", o.groupby(o.OrderDate.dt.year).size().to_dict())
print("doanh thu theo năm (triệu)", (o.groupby(o.OrderDate.dt.year).SubTotal.sum() / 1e6).round(2).to_dict())
print("tỷ trọng doanh thu xe đạp", round(li[li.Cat == "Bikes"].LineTotal.sum() / tt * 100, 1), "| số dòng theo danh mục", li.Cat.value_counts().to_dict())
print("tháng đỉnh", g.don.idxmax().date(), g.don.max(), "| 5/2011:", g.don.iloc[0], "đơn")

# Bộ dữ liệu 20 mốc (dùng cho các hình dưới)
ds = pd.read_csv(os.path.join(GOC, "data", "dataset.csv"), parse_dates=["T"])
# Hình 4: tỷ lệ y = 1 theo khoảng rời rạc hoá tại mốc huấn luyện 01/03/2014 (từ bảng của chuỗi phân tích)
kh = pd.read_csv(os.path.join(GOC, "results", "cum3b", "bang_4_3_1c_khoang.csv"))
chung = ds[ds["T"] == "2014-03-01"].y.mean() * 100
fig, ax = plt.subplots(1, 3, figsize=(11.5, 3.6), gridspec_kw={"wspace": 0.22}, sharey=True)
for a, (tt_, tieu) in zip(ax, [("Recency", "Recency (ngày)"), ("NSub", "NSub (số danh mục con)"), ("Monetary", "Monetary (nhóm tứ phân vị)")]):
    s = kh[kh.thuoc_tinh == tt_]
    nhan = [str(k).replace("<", "<").replace("≥", "≥") for k in s.khoang]
    v = s.ty_le_y1.values * 100
    a.bar(range(len(s)), v, color=[DO if x_ < chung - 5 else NAVY for x_ in v])
    a.set_xticks(range(len(s)), nhan, fontsize=8.5, rotation=35 if len(s) > 4 and tt_ == "Recency" else 0, ha="right" if tt_ == "Recency" else "center")
    for i, val in enumerate(v):
        a.text(i, val + 1, f"{vn(val, 1)}%", ha="center", va="bottom", fontsize=8.5)
    a.axhline(chung, color="#444", lw=1, ls="--")
    a.set_title(tieu, fontsize=10.5)
    dep(a)
ax[0].set_ylabel("Tỷ lệ y = 1 (%)")
ax[0].set_ylim(0, 108)
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
fig.legend(handles=[Line2D([0], [0], color="#444", ls="--", lw=1.2, label=f"Tỷ lệ y = 1 chung tại mốc 01/03/2014 ({vn(chung, 1)}%)"),
                    Patch(color=DO, label="Nhóm thấp hơn mức chung quá 5 điểm phần trăm")],
           loc="lower center", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.14))
luu("eda_y_theo_khoang.png")

# Hình lịch mốc thời gian do python/phan_tich/cum3b_nhan_va_dac_trung.py vẽ (results/cum3b/), sao chép sang thư mục hình của LaTeX
shutil.copyfile(os.path.join(GOC, "results", "cum3b", "hinh_4_3_1_moc_thoi_gian.png"), os.path.join(RA, "moc_thoi_gian.png"))
print("đã vẽ xong")


# ---- Phần bổ sung: độ lệch giữa các mốc, Recency theo mốc, Pareto ----
B_REC = [-1, 89, 179, 269, 364, 539, 1e6]
L_REC = ["<90", "90–179", "180–269", "270–364", "365–539", "≥540"]


def psi(a, b):
    """Population Stability Index giữa hai phân bố rời rạc a (cơ sở) và b."""
    ks = sorted(set(a) | set(b))
    pa = np.array([(a == k).mean() for k in ks]).clip(1e-4)
    pb = np.array([(b == k).mean() for k in ks]).clip(1e-4)
    return float(((pb - pa) * np.log(pb / pa)).sum())


def roi_rac(df, q):
    return {"Recency": pd.cut(df.Recency, B_REC, labels=False).values,
            "Frequency": pd.cut(df.Frequency, [0, 1, 2, 1e6], labels=False).values,
            "Monetary": np.searchsorted(q, df.Monetary.values),
            "NSub": pd.cut(df.NSub, [-1, 1, 2, 4, 1e6], labels=False).values,
            "BikeBuyer": df.BikeBuyer.values}


# Hình 5: lệch phân bố giữa mốc học 01/03/2014 và mốc chấm điểm 08/07/2014
tr_ = ds[ds["T"] == "2014-03-01"]
sc_ = ds[ds["T"] == "2014-07-08"]
q_ = tr_.Monetary.quantile([.25, .5, .75]).values
ba, bb = roi_rac(tr_, q_), roi_rac(sc_, q_)
psi_mocs = {k: psi(ba[k], bb[k]) for k in ba}
psi_fold = []
for T, E in [("2013-09-01", "2013-12-15"), ("2013-10-01", "2014-01-15"), ("2013-11-01", "2014-02-15"), ("2013-11-15", "2014-03-01")]:
    a_, b_ = ds[ds["T"] == T], ds[ds["T"] == E]
    ra, rb = roi_rac(a_, a_.Monetary.quantile([.25, .5, .75]).values), roi_rac(b_, a_.Monetary.quantile([.25, .5, .75]).values)
    psi_fold.append(psi(ra["Recency"], rb["Recency"]))
fig, (p1, p2) = plt.subplots(1, 2, figsize=(11.5, 3.9), gridspec_kw={"wspace": 0.28, "width_ratios": [1.25, 1]})
r1 = pd.cut(tr_.Recency, B_REC, labels=L_REC).value_counts(normalize=True).reindex(L_REC) * 100
r2 = pd.cut(sc_.Recency, B_REC, labels=L_REC).value_counts(normalize=True).reindex(L_REC) * 100
xx = np.arange(len(L_REC))
p1.bar(xx - 0.2, r1.values, 0.4, color=NAVY, label="Mốc học 01/03/2014")
p1.bar(xx + 0.2, r2.values, 0.4, color=DO, label="Mốc chấm điểm 08/07/2014")
p1.set_xticks(xx, L_REC)
p1.set_ylabel("% khách")
p1.set_xlabel("Khoảng Recency (ngày)")
p1.set_title("Phân bố Recency tại hai mốc", fontsize=11)
p1.legend(frameon=False, fontsize=9)
for i_, (u, w) in enumerate(zip(r1.values, r2.values)):
    p1.text(i_ - 0.2, u + 0.6, vn(u, 1), ha="center", fontsize=7.8)
    p1.text(i_ + 0.2, w + 0.6, vn(w, 1), ha="center", fontsize=7.8)
ten_psi = ["Recency", "NSub", "Frequency", "Monetary", "BikeBuyer"]
vals = [psi_mocs[k] for k in ten_psi]
p2.barh(ten_psi[::-1], vals[::-1], color=[DO if v > 0.25 else NAVY for v in vals[::-1]])
for xv, lb in ((0.1, "0,1"), (0.25, "0,25")):
    p2.axvline(xv, color="#444", ls="--", lw=1)
    p2.text(xv + 0.004, -0.45, lb, ha="left", va="bottom", fontsize=8.5, color="#444")
for i_, v in enumerate(vals[::-1]):
    p2.text(v + 0.006, i_, vn(v, 3), va="center", fontsize=8.8)
p2.set_xlim(0, 0.45)
p2.xaxis.set_major_formatter(FuncFormatter(lambda v, _: vn(v, 1)))
p2.set_xlabel("PSI giữa hai mốc")
p2.set_title("Mức lệch của từng thuộc tính", fontsize=11)
for a in (p1, p2):
    dep(a)
luu("eda_lech_moc.png")
print("PSI mốc học → mốc chấm điểm:", {k: round(v, 3) for k, v in psi_mocs.items()})
print("PSI Recency của 4 cặp kiểm định:", [round(v, 3) for v in psi_fold])
print("Recency % tại hai mốc:", r1.round(1).tolist(), r2.round(1).tolist())

# Hình 6: Pareto của Monetary và hạng ABC (mốc chấm điểm)
xs = d.sort_values("Monetary", ascending=False).reset_index(drop=True)
cum = xs.Monetary.cumsum() / xs.Monetary.sum() * 100
pct = (np.arange(1, len(xs) + 1) / len(xs)) * 100
nA, nB, nC = [(xs.ABC == h).sum() for h in "ABC"]
fig, a = plt.subplots(figsize=(8.6, 4.2))
a.plot(pct, cum, color=NAVY, lw=2.4)
a.axhline(80, color="#444", ls="--", lw=1)
a.axhline(95, color="#444", ls="--", lw=1)
xa, xb = nA / len(xs) * 100, (nA + nB) / len(xs) * 100
a.axvspan(0, xa, color=DO, alpha=0.12)
a.axvspan(xa, xb, color=CAM, alpha=0.15)
a.axvspan(xb, 100, color=XAM, alpha=0.18)
a.text(xa / 2, 12, f"Hạng A\n{vn(nA)} khách\n({vn(xa, 1)}%)\ntạo 80% tổng chi", ha="center", fontsize=9, color=DO)
a.text((xa + xb) / 2, 12, f"Hạng B\n{vn(nB)} khách\n({vn(xb - xa, 1)}%)\ntạo 15%", ha="center", fontsize=9, color="#a8651f")
a.text((xb + 100) / 2, 12, f"Hạng C\n{vn(nC)} khách\n({vn(100 - xb, 1)}%)\ntạo 5%", ha="center", fontsize=9, color="#555")
a.set_xlim(0, 100)
a.set_ylim(0, 102)
a.set_xlabel("% khách, xếp theo Monetary giảm dần")
a.set_ylabel("% tổng chi tiêu cộng dồn")
a.set_title("Tập trung giá trị theo khách và hạng ABC tại mốc 08/07/2014", fontsize=11)
dep(a)
luu("eda_pareto.png")
print("ABC:", nA, nB, nC, "| 10% khách đầu:", round(cum.iloc[int(len(xs) * 0.1) - 1], 1), "% tổng chi | ngưỡng A, B (USD):",
      round(xs[xs.ABC == "A"].Monetary.min(), 2), round(xs[xs.ABC == "B"].Monetary.min(), 2))
