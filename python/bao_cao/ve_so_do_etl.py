"""Vẽ sơ đồ luồng ETL (nguồn, staging, kiểm tra và lọc phạm vi, Dimension, Fact, Snapshot) cho báo cáo LaTeX.

Số bản ghi lấy từ etl.StepLog qua python/bao_cao/etl_nhat_ky.py. Cấu trúc luồng theo sql/2_Cum2_ETL_moi/C2_01_Update_ETL_Procedure.sql.
Ra: latex/IMAGE/etl_luong.png
Chạy: .venv/bin/python python/bao_cao/ve_so_do_etl.py
"""
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import etl_nhat_ky as nk

GOC = nk.GOC
plt.rcParams["font.family"] = "Arial"

b = {x["ten"]: x for x in nk.buoc_etl()}
import re
_md = open(os.path.join(GOC, 'results', 'cum3b', 'cum3b_ket_qua.md'), encoding='utf-8').read()
_m = re.search(r'Snapshot: (\d+) dòng, (\d+) mốc', _md)
SNAP_DONG, SNAP_MOC = int(_m.group(1)), int(_m.group(2))


def vn(n):
    return f"{n:,}".replace(",", ".")


NAVY, XAM, DO, XANH = "#1f3a5f", "#eef1f5", "#b03a2e", "#2e7d5b"
fig, ax = plt.subplots(figsize=(12.6, 5.6))
ax.set_xlim(0, 126)
ax.set_ylim(0, 56)
ax.axis("off")


def hop(x, y, w, h, tieu_de, dong, mau=NAVY, nen="white", co=8.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.2",
                                fc=nen, ec=mau, lw=1.6))
    ax.text(x + w / 2, y + h - 2.2, tieu_de, ha="center", va="top", fontsize=co + 0.8, fontweight="bold", color=mau)
    for i, d in enumerate(dong):
        ax.text(x + w / 2, y + h - 6.0 - i * 2.7, d, ha="center", va="top", fontsize=co - 0.6, color="#222")


def mui_ten(x1, y1, x2, y2, mau="#444", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, lw=1.6, color=mau, linestyle=ls))


Y, H = 24, 24
hop(1, Y, 19, H, "Dữ liệu gốc", ["CompanyX", "(chỉ đọc)", "", "Customer, Product,", "Territory, Order,", "OrderLine"])
hop(26, Y, 21, H, "Staging (stg)", ["5 bảng thô", f"{vn(b['Extract.Customer']['nguon'])} khách", f"{vn(b['Extract.Product']['nguon'])} sản phẩm",
                                  f"{vn(b['Extract.Territory']['nguon'])} vùng", f"{vn(b['Extract.Order']['nguon'])} đơn", f"{vn(b['Extract.OrderLine']['nguon'])} dòng"])
hop(53, Y, 24, H, "Transform", ["Kiểm tra hợp lệ", "toàn bộ staging", "", "Lọc phạm vi:", "khách cá nhân,", "đơn đã gửi (Status = 5)"])
hop(83, Y, 20, H, "Load Dimension", [f"DimCustomer {vn(b['Load.DimCustomer']['nap'])}", f"DimProduct {vn(b['Load.DimProduct']['nap'])}",
                                     f"DimTerritory {vn(b['Load.DimTerritory']['nap'])}", f"DimDate {vn(b['Load.DimDate']['nap'])}"])
hop(106, Y, 19, H, "Load Fact", ["FactSalesOrder", vn(b["Load.FactSalesOrder"]["nap"]) + " đơn", "FactSalesOrderLine", vn(b["Load.FactSalesOrderLine"]["nap"]) + " dòng"])

for x1, x2 in [(20.2, 25.8), (47.2, 52.8), (77.2, 82.8), (103.2, 105.8)]:
    mui_ten(x1, Y + H / 2, x2, Y + H / 2)

# nhãn bước
for x, w, t in [(26, 21, "Bước 1 đến 5 (Extract)"), (83, 20, "Bước 6 đến 9"), (106, 19, "Bước 10 và 11")]:
    ax.text(x + w / 2, Y + H + 2.4, t, ha="center", fontsize=8.6, color="#555", style="italic")
ax.text(65, Y + H + 2.4, "Thực hiện trong các bước 6 đến 11", ha="center", fontsize=8.6, color="#555", style="italic")

# RejectedRow
hop(53, 5, 24, 11, "etl.RejectedRow", ["Ghi cả bản ghi lỗi và ngoài phạm vi", "kèm cờ IsInScope"], mau=DO, co=8.2)
mui_ten(65, Y - 0.2, 65, 16.4, DO)

# Snapshot
hop(100, 5, 25, 11, "analytics.CustomerSnapshot", [f"{SNAP_MOC} mốc, {vn(SNAP_DONG)} dòng", "(đầu vào của học máy và DSS)"], mau=XANH, co=8.2)
mui_ten(115.5, Y - 0.2, 115.5, 16.4, XANH)

# Nhật ký
hop(1, 5, 46, 11, "etl.RunLog và etl.StepLog", ["Python gọi đoạn lệnh SQL, có lỗi thì huỷ toàn bộ", "StepLog ghi từng bước: nguồn, đã nạp, ngoài phạm vi, bị từ chối"],
    mau="#666", nen=XAM, co=8.2)
ax.text(63, 1.2, "Dimension nạp trước, Fact nạp sau. Fact làm mới toàn bộ mỗi lần chạy, Dimension cập nhật và bổ sung.",
        ha="center", fontsize=8.4, color="#333")

plt.savefig(os.path.join(GOC, "latex", "IMAGE", "etl_luong.png"), dpi=200, bbox_inches="tight", facecolor="white")
print("đã vẽ latex/IMAGE/etl_luong.png")
