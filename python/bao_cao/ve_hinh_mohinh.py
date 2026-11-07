"""Vẽ các hình của chương 5 (Mô hình) và chương 7 (Đánh giá) cho báo cáo LaTeX.

Mọi số trong hình lấy từ results/ (không huấn luyện lại).
Ra (latex/IMAGE): m_z_mo_hinh.png, m_nb_mlp_seed.png, m_ma_tran.png, m_ty_so_nb.png, m_diem_theo_hang.png,
d_do_nhay.png, d_mo_phong.png
Chạy: .venv/bin/python python/bao_cao/ve_hinh_mohinh.py
"""
import os
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RA = os.path.join(GOC, "latex", "IMAGE")
R = lambda *p: os.path.join(GOC, "results", *p)

plt.rcParams["font.family"] = "Arial"
plt.rcParams["axes.unicode_minus"] = False
NAVY, DO, XANH, CAM, XAM = "#1f3a5f", "#c0392b", "#2e7d5b", "#e08e45", "#9aa5b1"


def vn(x, nd=0):
    s = f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s.replace("-", "−")


def fmt_vn(nd=0):
    return FuncFormatter(lambda v, _: vn(v, nd))


def luu(ten):
    plt.savefig(os.path.join(RA, ten), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close()


def dep(a):
    a.spines[["top", "right"]].set_visible(False)


# ---------- 1. Z và ROC-AUC/Brier theo mô hình ----------
t = pd.read_csv(R("cum4", "bang_4_3_2b_trung_binh.csv")).set_index("mo_hinh")
ten = {"Naive Bayes rời rạc": "Naive Bayes", "MLP (32,16)": "Mạng nơ-ron MLP", "Cây Gini sâu 4, lá 400": "Cây Gini",
       "Logistic one-hot": "Hồi quy logistic", "Lớp đa số": "Luôn lớp đa số", "Recency đảo chiều": "Recency đảo chiều",
       "Random Forest 300": "Random Forest", "Gradient boosting": "Gradient boosting", "kNN k=200": "kNN"}
t = t.sort_values("Z_pv")
zv, zo = float(t.Z_v.iloc[0]), float(t.Z_oracle.iloc[0])
fig, ax = plt.subplots(1, 3, figsize=(9.2, 4.0), sharey=True, gridspec_kw={"width_ratios": [1.3, 1, 1]})
mau = [NAVY if m == "Naive Bayes rời rạc" else XAM for m in t.index]
yy = range(len(t))
ax[0].hlines(yy, zv, t.Z_pv, color=mau, lw=2)
ax[0].scatter(t.Z_pv, yy, color=mau, s=55, zorder=3)
ax[0].axvline(zv, color=DO, ls="--", lw=1.2)
ax[0].axvline(zo, color=XANH, ls="--", lw=1.2)
ax[0].text(zv - 1500, len(t) - 0.4, "chỉ chọn\ntheo $v$", color=DO, fontsize=8, ha="right", va="bottom")
ax[0].text(zo - 1500, len(t) - 0.4, "biết trước\nnhãn", color=XANH, fontsize=8, ha="right", va="bottom")
ax[0].set_yticks(list(yy))
ax[0].set_yticklabels([ten[m] for m in t.index], fontsize=9)
ax[0].set_ylim(-0.6, len(t) + 0.9)
ax[0].set_xticks([260000, 300000, 340000])
ax[0].xaxis.set_major_formatter(fmt_vn())
ax[0].set_xlabel("Giá trị ròng Z (USD)\ncao hơn là tốt")
ax[1].scatter(t.Brier, yy, color=mau, s=55, zorder=3)
ax[1].hlines(yy, t.loc["Lớp đa số", "Brier"], t.Brier, color=mau, lw=2)
ax[1].axvline(t.loc["Lớp đa số", "Brier"], color=DO, ls="--", lw=1.2)
ax[1].text(t.loc["Lớp đa số", "Brier"] - 0.003, len(t) - 0.4, "xác suất\nhằng", color=DO, fontsize=8, ha="right", va="bottom")
ax[1].set_xticks([0.12, 0.15, 0.20, 0.25])
ax[1].xaxis.set_major_formatter(fmt_vn(2))
ax[1].set_xlabel("Brier\nthấp hơn là tốt")
ax[2].scatter(t.AUC, yy, color=mau, s=55, zorder=3)
ax[2].hlines(yy, 0.5, t.AUC, color=mau, lw=2)
ax[2].axvline(t.loc["Recency đảo chiều", "AUC"], color=DO, ls="--", lw=1.2)
ax[2].text(t.loc["Recency đảo chiều", "AUC"] - 0.006, len(t) - 0.4, "Recency\nđảo chiều", color=DO, fontsize=8, ha="right", va="bottom")
ax[2].xaxis.set_major_formatter(fmt_vn(2))
ax[2].set_xlabel("ROC-AUC\ncao hơn là tốt")
for a in ax:
    dep(a)
plt.tight_layout()
luu("m_z_mo_hinh.png")

# ---------- 2. Naive Bayes và MLP theo hạt giống ----------
c = pd.read_csv(R("cum4", "bang_4_3_2c_nb_vs_mlp.csv"))
s = pd.read_csv(R("cum4", "bang_4_3_2e_mlp_seed.csv"))
fig, ax = plt.subplots(figsize=(7, 3.6))
x = np.arange(len(c))
ax.plot(x, c.Z_NB, "o-", color=NAVY, lw=2, label="Naive Bayes")
for sd, g in s.groupby("seed"):
    ax.scatter(x + (sd - 1) * 0.08, g.sort_values("E").Z, color=CAM, s=36, zorder=3, label="Mạng nơ-ron (ba hạt giống)" if sd == 0 else None)
ax.set_xticks(x)
ax.set_xticklabels([f"{e[8:]}/{e[5:7]}/{e[:4]}" for e in c.E])
ax.yaxis.set_major_formatter(fmt_vn())
ax.set_xlabel("Mốc đánh giá $E$")
ax.set_ylabel("Giá trị ròng Z (USD)")
ax.legend(frameon=False, fontsize=9)
dep(ax)
plt.tight_layout()
luu("m_nb_mlp_seed.png")

# ---------- 3. Ma trận nhầm lẫn ở ba cách đặt ngưỡng ----------
l1 = pd.read_csv(R("cum5", "bang_4_3_3a_lop1_ba_nguong.csv"), index_col=0)
tieu = ["Youden, chọn trên mốc huấn luyện\n(RiskScore từ 0,729)", "Youden, chọn ngoài mẫu\n(RiskScore từ 0,878)", "Mức Cao của DSS\n(phân vị 75 trong từng hạng ABC)"]
fig, ax = plt.subplots(1, 3, figsize=(8.6, 3.4))
for i, col in enumerate(l1.columns[:3]):
    tp, fn, fp, tn = (l1.loc[k, col] for k in ("TP", "FN", "FP", "TN"))
    m = np.array([[tp, fn], [fp, tn]])
    ax[i].imshow(m / m.sum(axis=1, keepdims=True), cmap="Blues", vmin=0, vmax=1.15)
    for (a, b), v in np.ndenumerate(m):
        ax[i].text(b, a, vn(v), ha="center", va="center", fontsize=11, color="white" if m[a, b] / m[a].sum() > 0.6 else "black")
    ax[i].set_xticks([0, 1])
    ax[i].set_xticklabels(["Dự đoán $y=1$", "Dự đoán $y=0$"], fontsize=9)
    ax[i].set_yticks([0, 1])
    ax[i].set_yticklabels(["Thật $y=1$", "Thật $y=0$"] if i == 0 else ["", ""], fontsize=9)
    ax[i].set_title(tieu[i], fontsize=9.5)
    ax[i].tick_params(length=0)
plt.tight_layout()
luu("m_ma_tran.png")

# ---------- 4. Tỷ số xác suất có điều kiện của Naive Bayes ----------
x = pd.read_csv(R("cum5", "bang_4_3_4_xac_suat_co_dieu_kien_NB.csv"))
nhan = [f"{a}: {b}".replace("Q1", "Q1 (thấp)").replace("Q4", "Q4 (cao)") for a, b in zip(x.thuoc_tinh, x.khoang)]
fig, ax = plt.subplots(figsize=(6.5, 6.4))
y = np.arange(len(x))[::-1]
ax.barh(y, np.log(x.ty_so), color=[DO if v > 1 else NAVY for v in x.ty_so])
ax.axvline(0, color="black", lw=0.8)
ax.set_yticks(y)
ax.set_yticklabels(nhan, fontsize=8.5)
tick = [0.1, 0.25, 0.5, 1, 2, 4]
ax.set_xticks(np.log(tick))
ax.set_xticklabels([vn(v, 2 if v < 1 else 0) if v != 0.25 else "0,25" for v in tick])
for yy, v in zip(y, x.ty_so):
    ax.text(np.log(v) + (0.05 if v > 1 else -0.05), yy, vn(v, 2), va="center", ha="left" if v > 1 else "right", fontsize=8)
ax.set_xlim(np.log(0.05), np.log(4.3))
ax.set_xlabel("Tỷ số $P(x\\mid y=1)/P(x\\mid y=0)$, trục logarit (đỏ: tăng rủi ro, xanh: giảm rủi ro)")
dep(ax)
plt.tight_layout()
luu("m_ty_so_nb.png")

# ---------- 5. RiskScore theo hạng ABC tại mốc chấm điểm ----------
d = pd.read_csv(R("cum6", "dss_khach.csv"), usecols=["RiskScore", "RiskLevel", "ABC"])
fig, ax = plt.subplots(1, 3, figsize=(9, 3.1), sharey=False)
for i, h in enumerate("ABC"):
    g = d[d.ABC == h]
    cao = g[g.RiskLevel == "Cao"].RiskScore
    bins = np.linspace(0, 1, 41)
    ax[i].hist(g[g.RiskLevel != "Cao"].RiskScore, bins=bins, color=XAM, label="Mức Thấp")
    ax[i].hist(cao, bins=bins, color=DO, label="Mức Cao")
    ax[i].axvline(cao.min(), color="black", ls=":", lw=1)
    ax[i].set_title(f"Hạng {h} ({vn(len(g))} khách), Cao từ {vn(cao.min(), 3)}", fontsize=9.5)
    ax[i].set_xlabel("RiskScore")
    ax[i].yaxis.set_major_formatter(fmt_vn())
    ax[i].xaxis.set_major_formatter(fmt_vn(1))
    dep(ax[i])
ax[0].set_ylabel("Số khách")
ax[0].legend(frameon=False, fontsize=8.5, loc="upper left")
plt.tight_layout()
luu("m_diem_theo_hang.png")

# ---------- 5b. Phân bố RiskScore toàn bộ khách (thay hình cũ có chú thích dễ hiểu nhầm) ----------
d2 = pd.read_csv(R("cum6", "dss_khach.csv"), usecols=["RiskScore"])
p75 = float(np.percentile(d2.RiskScore, 75))
fig, ax = plt.subplots(figsize=(7, 3.4))
ax.hist(d2.RiskScore, bins=np.linspace(0, 1, 41), color=NAVY)
ax.axvline(p75, color=DO, ls="--", lw=1.2)
ax.text(p75 - 0.01, ax.get_ylim()[1] * 0.92, "phân vị 75 của toàn bộ khách (" + vn(p75, 3) + "), chỉ để tham khảo", color=DO, fontsize=8.5, ha="right")
ax.set_xlabel("RiskScore của Naive Bayes tại mốc 08/07/2014")
ax.set_ylabel("Số khách")
ax.yaxis.set_major_formatter(fmt_vn())
ax.xaxis.set_major_formatter(fmt_vn(1))
dep(ax)
plt.tight_layout()
luu("m_phan_bo_diem.png")
print("median", np.median(d2.RiskScore), "p25", np.percentile(d2.RiskScore, 25), "p75", p75)

# ---------- 6. Độ nhạy của Z (chương 7) ----------
dn = pd.read_csv(R("cum6", "bang_4_4_do_nhay.csv"))
ten_tb = {"r": "$r$ (tỷ lệ thành công)", "p": "$p$ (xác suất rủi ro)", "g (qua v)": "$g$ (tỷ lệ lợi nhuận gộp)", "c": "$c$ (chi phí mỗi khách)", "B": "$B$ (ngân sách)"}
dn["ab"] = dn.delta_Z.abs()
thu_tu = dn.groupby("tham_so").ab.max().sort_values().index.tolist()
fig, ax = plt.subplots(figsize=(7.4, 3.4))
for i, p in enumerate(thu_tu):
    for _, r in dn[dn.tham_so == p].iterrows():
        ax.barh(i + (0.19 if r.thay_doi.startswith("+") else -0.19), r.delta_Z, height=0.36,
                color=NAVY if r.thay_doi.startswith("+") else CAM)
        ax.text(r.delta_Z + (1500 if r.delta_Z > 0 else -1500), i + (0.19 if r.thay_doi.startswith("+") else -0.19),
                vn(r.delta_pct, 1) + "%", va="center", ha="left" if r.delta_Z > 0 else "right", fontsize=7.5)
ax.axvline(0, color="black", lw=0.8)
ax.set_yticks(range(len(thu_tu)))
ax.set_yticklabels([ten_tb[p] for p in thu_tu], fontsize=9)
ax.xaxis.set_major_formatter(fmt_vn())
ax.set_xlim(-85000, 85000)
ax.set_xlabel("Thay đổi của Z so với kịch bản cơ sở (USD) khi tham số tăng 20% (xanh) hoặc giảm 20% (cam)")
dep(ax)
plt.tight_layout()
luu("d_do_nhay.png")

# ---------- 7. Mô phỏng Z (chương 7): dùng hình do cum6 sinh ----------
# d_mo_phong.png được vẽ lại trong ve_hinh_dss.py (trục theo nghìn USD)
print("xong")
