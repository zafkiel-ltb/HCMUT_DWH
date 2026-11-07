"""Vẽ các biểu đồ cho hồ sơ giới thiệu CompanyX (docs/ho_so_companyx/).

Số liệu là kết quả truy vấn cơ sở dữ liệu nguồn CompanyX ngày 05/11/2026 (SQL Server, chỉ đọc):
Sales.SalesOrderHeader/Detail, Production.Product, Production.WorkOrder, Purchasing.PurchaseOrderHeader.
Ra: docs/ho_so_companyx/IMAGE/*.png
Chạy: .venv/bin/python python/bao_cao/ve_ho_so_companyx.py
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RA = os.path.join(GOC, "docs", "ho_so_companyx", "IMAGE")
os.makedirs(RA, exist_ok=True)
plt.rcParams["font.family"] = "Arial"
NAVY, CAM, XANH, XAM = "#1f3a5f", "#d98324", "#2e7d5b", "#8a96a3"


def luu(fig, ten):
    fig.savefig(os.path.join(RA, ten), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("đã vẽ", ten)


# 1. Chuỗi giá trị
fig, ax = plt.subplots(figsize=(12.2, 3.0))
ax.set_xlim(-1, 125); ax.set_ylim(0, 30); ax.axis("off")
buoc = [("Mua hàng", "104 nhà cung cấp", "4.012 đơn mua"),
        ("Sản xuất", "72.591 lệnh sản xuất", "14 khu vực sản xuất"),
        ("Tồn kho", "432 mã có tồn", "335.974 đơn vị"),
        ("Bán hàng", "31.465 đơn bán", "qua đại lý và trực tuyến")]
W, G = 26, 6.7
for i, (t, a, b) in enumerate(buoc):
    x = i * (W + G)
    ax.add_patch(FancyBboxPatch((x, 4), W, 22, boxstyle="round,pad=0.2,rounding_size=1.2", fc="white", ec=NAVY, lw=1.6))
    ax.text(x + W / 2, 23, t, ha="center", va="top", fontsize=11, fontweight="bold", color=NAVY)
    ax.text(x + W / 2, 15.5, a, ha="center", va="top", fontsize=9, color="#222")
    ax.text(x + W / 2, 10, b, ha="center", va="top", fontsize=9, color="#222")
    if i < 3:
        ax.add_patch(FancyArrowPatch((x + W + 0.5, 15), (x + W + G - 0.5, 15), arrowstyle="-|>", mutation_scale=14, lw=1.6, color="#444"))
luu(fig, "chuoi_gia_tri.png")

# 2. Doanh thu theo năm và kênh (triệu USD, tiền hàng SubTotal)
nam = ["2011\n(từ 31/05)", "2012", "2013", "2014\n(đến 30/06)"]
dai_ly = [8.717, 27.134, 32.890, 11.685]
truc_tuyen = [3.863, 6.391, 10.732, 8.373]
fig, ax = plt.subplots(figsize=(7.6, 3.9))
ax.bar(nam, dai_ly, color=NAVY, label="Đại lý (qua nhân viên bán hàng)")
ax.bar(nam, truc_tuyen, bottom=dai_ly, color=CAM, label="Trực tuyến")
for i in range(4):
    tong = dai_ly[i] + truc_tuyen[i]
    ax.text(i, tong + 0.8, f"{tong:.1f}".replace(".", ","), ha="center", fontsize=9, fontweight="bold")
ax.set_ylabel("Triệu USD (tiền hàng)")
ax.set_ylim(0, 52)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, fontsize=9, loc="upper left")
luu(fig, "doanh_thu_nam_kenh.png")

# 3. Doanh thu theo nhóm hàng và năm (triệu USD, thành tiền dòng LineTotal)
nhom = {"Xe đạp (Bikes)": [11.892, 28.986, 36.267, 17.453],
        "Linh kiện (Components)": [0.633, 3.881, 5.613, 1.670],
        "Trang phục (Clothing)": [0.035, 0.556, 1.068, 0.461],
        "Phụ kiện (Accessories)": [0.020, 0.102, 0.675, 0.474]}
mau = [NAVY, CAM, XANH, XAM]
fig, ax = plt.subplots(figsize=(7.6, 3.9))
day = [0, 0, 0, 0]
for (ten, v), m in zip(nhom.items(), mau):
    ax.bar(nam, v, bottom=day, color=m, label=ten)
    day = [a + b for a, b in zip(day, v)]
for i, t in enumerate(day):
    ax.text(i, t + 0.8, f"{t:.1f}".replace(".", ","), ha="center", fontsize=9, fontweight="bold")
ax.set_ylabel("Triệu USD (thành tiền dòng chi tiết)")
ax.set_ylim(0, 52)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
luu(fig, "doanh_thu_nhom_nam.png")

# 4. Doanh thu theo vùng bán hàng (triệu USD, tiền hàng)
vung = [("Southwest (Mỹ)", 24.154, "Bắc Mỹ"), ("Canada", 16.347, "Bắc Mỹ"), ("Northwest (Mỹ)", 16.085, "Bắc Mỹ"),
        ("Australia", 10.655, "Thái Bình Dương"), ("Central (Mỹ)", 7.909, "Bắc Mỹ"), ("Southeast (Mỹ)", 7.866, "Bắc Mỹ"),
        ("Anh (UK)", 7.671, "Châu Âu"), ("Pháp", 7.252, "Châu Âu"), ("Northeast (Mỹ)", 6.932, "Bắc Mỹ"), ("Đức", 4.915, "Châu Âu")]
cm = {"Bắc Mỹ": NAVY, "Châu Âu": CAM, "Thái Bình Dương": XANH}
fig, ax = plt.subplots(figsize=(7.6, 4.2))
ten = [v[0] for v in vung][::-1]
gt = [v[1] for v in vung][::-1]
mm = [cm[v[2]] for v in vung][::-1]
ax.barh(ten, gt, color=mm)
for i, g in enumerate(gt):
    ax.text(g + 0.3, i, f"{g:.1f}".replace(".", ","), va="center", fontsize=9)
ax.set_xlabel("Triệu USD (tiền hàng)")
ax.set_xlim(0, 28)
for s in ("top", "right"): ax.spines[s].set_visible(False)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=c, label=k) for k, c in cm.items()], frameon=False, fontsize=9, loc="lower right")
luu(fig, "doanh_thu_vung.png")
