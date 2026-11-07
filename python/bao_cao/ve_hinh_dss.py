"""Vẽ và chép hình cho chương 6 (Hệ hỗ trợ ra quyết định).

Ra (latex/IMAGE): d_chon_k.png (vẽ lại từ results/cum6/bang_4_4_chon_k.csv),
d_man_hinh_1.png ... d_man_hinh_5.png (ảnh chụp 5 màn hình app ngày 07/11/2026 (độ phân giải cao, chụp bằng python/kiem_chung/chup_man_hinh.mjs), results/doc/hinh_app/app_07_11_man_hinh_1..5.png).
Chạy: .venv/bin/python python/bao_cao/ve_hinh_dss.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter
from PIL import Image

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RA = os.path.join(GOC, "latex", "IMAGE")
R = lambda *p: os.path.join(GOC, "results", *p)
plt.rcParams["font.family"] = "Arial"
plt.rcParams["axes.unicode_minus"] = False
NAVY, DO = "#1f3a5f", "#c0392b"


def vn(x, nd=0):
    return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")


k = pd.read_csv(R("cum6", "bang_4_4_chon_k.csv"))
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
ax[0].plot(k.k, k.WCSS, "o-", color=NAVY)
ax[0].set_title("Elbow (WCSS)", fontsize=10)
ax[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _: vn(v)))
ax[1].plot(k.k, k.Silhouette, "o-", color=NAVY)
ax[1].set_title("Silhouette", fontsize=10)
ax[1].yaxis.set_major_formatter(FuncFormatter(lambda v, _: vn(v, 2)))
for a in ax:
    a.axvline(5, color=DO, ls="--", lw=1.2)
    a.set_xlabel("Số cụm $k$")
    a.spines[["top", "right"]].set_visible(False)
ax[1].text(5.1, k.Silhouette.min() + 0.002, "$k=5$", color=DO, fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(RA, "d_chon_k.png"), dpi=200, bbox_inches="tight", facecolor="white")
plt.close()

for i in range(1, 6):
    # ảnh chụp app chạy lại ngày 06/11/2026 (vai trò Quản lý, khách 26339 ở màn hình 2, bớt khách 26339 có lý do ở màn hình 4)
    im = Image.open(R("doc", "hinh_app", f"app_07_11_man_hinh_{i}.png")).convert("RGB")
    im.save(os.path.join(RA, f"d_man_hinh_{i}.png"), optimize=True)
print("xong")


# Phân bố Z trong 10.000 lần mô phỏng r ~ Beta(2,2; 19,8). Cùng seed và công thức với cum6_phan_tich_dss.py (Z = r.S - c.K),
# S suy ra từ Z của kịch bản cơ sở tại r = 10%. Chạy lại thì ra đúng các số trong results/cum6/mo_phong.json.
import json
import numpy as np
sys_path = os.path.join(GOC, "python")
import sys
sys.path.insert(0, sys_path)
import config as C

tt = json.load(open(R("cum6", "mo_phong.json")))
Z_CS, CK = tt["kiem_dinh_r10"], 10 * 4000
S = (Z_CS + CK) / 0.10
Zs = np.random.default_rng(C.RANDOM_STATE).beta(2.2, 19.8, 10000) * S - CK
assert abs(Zs.mean() - tt["Z_mean"]) < 1e-3, "mô phỏng không khớp mo_phong.json"
fig, ax = plt.subplots(figsize=(7, 3.4))
ax.hist(Zs / 1000, bins=60, color=NAVY, alpha=0.85)
ax.axvline(0, color=DO, ls="--", lw=1.4, label="Z = 0")
ax.axvline(Z_CS / 1000, color="black", ls=":", lw=1.6, label="Kịch bản cơ sở, r = 10% (" + vn(Z_CS / 1000, 1) + ")")
ax.axvspan(tt["Z_P5"] / 1000, tt["Z_P95"] / 1000, color="#9aa7bd", alpha=0.25, zorder=0, label="Khoảng P5 đến P95 (" + vn(tt["Z_P5"] / 1000, 1) + " đến " + vn(tt["Z_P95"] / 1000, 1) + ")")
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: vn(v)))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: vn(v)))
ax.set_xlabel("Giá trị ròng kỳ vọng Z (nghìn USD)")
ax.set_ylabel("Số lần mô phỏng")
ax.legend(fontsize=8, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(RA, "d_mo_phong.png"), dpi=200, facecolor="white")
plt.close()
print("xong d_mo_phong.png: P(Z<0) =", vn(100 * (Zs < 0).mean(), 1) + "%")
