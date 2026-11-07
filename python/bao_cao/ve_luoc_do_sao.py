"""Vẽ lược đồ hình sao của CompanyX_DW trên MỘT hình, mọi mũi tên thẳng đứng và không cắt nhau.

Bố cục: FactSalesOrder ở trên, ba Dimension dùng chung (DimCustomer, DimTerritory, DimDate) ở giữa,
FactSalesOrderLine bên dưới, DimProduct (chỉ nối với FactSalesOrderLine) ở dưới cùng.
Tên cột và kiểu dữ liệu đọc thẳng từ sql/0_Nen_DWH_ETL/00_create_6_tables.sql (DDL thật của kho), không gõ tay.
Ra: latex/IMAGE/luoc_do_sao.png
Chạy: .venv/bin/python python/bao_cao/ve_luoc_do_sao.py
"""
import math
import os
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
plt.rcParams["font.family"] = "Arial"

ddl = open(os.path.join(GOC, "sql", "0_Nen_DWH_ETL", "00_create_6_tables.sql"), encoding="utf-8").read()
bang = {}
for m in re.finditer(r"CREATE TABLE dbo\.(\w+)\s*\((.*?)\n\s*\);?\s*\n", ddl, re.S):
    cot = []
    for dong in m.group(2).splitlines():
        dong = dong.split("--")[0].strip().rstrip(",")
        mm = re.match(r"^\[?(\w+)\]?\s+(INT|SMALLINT|DATE|NVARCHAR\(\d+\)|DECIMAL\(\d+,\d+\)|BIGINT|TINYINT)", dong)
        if mm:
            cot.append((mm.group(1), mm.group(2).lower()))
    bang[m.group(1)] = cot
for t in ["DimCustomer", "DimDate", "DimProduct", "DimTerritory", "FactSalesOrder", "FactSalesOrderLine"]:
    assert t in bang and len(bang[t]) >= 4, (t, bang.get(t))

PK_DIM = {"DimCustomer": "CustomerKey", "DimDate": "DateKey", "DimProduct": "ProductKey", "DimTerritory": "TerritoryKey"}
FK = {"CustomerKey", "OrderDateKey", "TerritoryKey", "ProductKey"}
PK_FACT = {"FactSalesOrder": {"SalesOrderID"}, "FactSalesOrderLine": {"SalesOrderID", "SalesOrderDetailID"}}
for f, khoa in (("FactSalesOrder", {"CustomerKey", "OrderDateKey", "TerritoryKey"}),
                ("FactSalesOrderLine", {"CustomerKey", "OrderDateKey", "TerritoryKey", "ProductKey"})):
    assert khoa <= {c for c, _ in bang[f]}, f         # mọi khoá ngoại phải có thật trong DDL

NAVY, DO = "#1f3a5f", "#b03a2e"
DONG = 2.9          # khoảng cách giữa hai dòng cột (đơn vị 0,1 inch)
TIEU_DE = 5.6


def cao(n):
    return TIEU_DE + 2.4 + n * DONG


def ve_ten_cot(ax, ten, c, k, x, y, w, co=12):
    la_pk = (ten in PK_DIM and PK_DIM[ten] == c) or (ten in PK_FACT and c in PK_FACT[ten])
    la_fk = ten in PK_FACT and c in FK
    ghi = c + ("  (PK)" if la_pk else "  (FK)" if la_fk else "")
    ax.text(x, y, ghi, ha="left", va="center", fontsize=co, fontweight="bold" if la_pk else "normal", color="#222")
    ax.text(x + w, y, k, ha="right", va="center", fontsize=co - 2.5, color="#777")


def khung(ax, ten, x, y, w, h, mau):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.9", fc="white", ec=mau, lw=2.0))
    ax.add_patch(FancyBboxPatch((x, y + h - TIEU_DE), w, TIEU_DE, boxstyle="round,pad=0.1,rounding_size=0.9", fc=mau, ec=mau, lw=2.0))
    ax.text(x + w / 2, y + h - TIEU_DE / 2, ten, ha="center", va="center", fontsize=15, fontweight="bold", color="white")


def hop_dim(ax, ten, x, y, w, h):
    khung(ax, ten, x, y, w, h, NAVY)
    for i, (c, k) in enumerate(bang[ten]):
        ve_ten_cot(ax, ten, c, k, x + 1.4, y + h - TIEU_DE - 2.0 - i * DONG, w - 2.8)


def hop_fact(ax, ten, x, y, w, h):
    """Bảng Fact rộng, các cột chia hai nửa để hộp thấp và vừa bề rộng của ba Dimension."""
    khung(ax, ten, x, y, w, h, DO)
    cot = bang[ten]
    nua = math.ceil(len(cot) / 2)
    for i, (c, k) in enumerate(cot):
        j, hang = divmod(i, nua)
        ve_ten_cot(ax, ten, c, k, x + 1.4 + j * (w / 2), y + h - TIEU_DE - 2.0 - hang * DONG, w / 2 - 2.8)


def mui_ten(ax, x, y1, y2, nhan, ben="phai"):
    ax.add_patch(FancyArrowPatch((x, y1), (x, y2), arrowstyle="-|>", mutation_scale=18, lw=2.0, color="#444"))
    ax.text(x + 1.0, (y1 + y2) / 2, nhan, ha="left", va="center", fontsize=12, color="#222", style="italic")


# Kích thước (đơn vị 0,1 inch). Ba Dimension dùng chung nằm cạnh nhau, hai Fact đối xứng ở hai phía
W_DIM, GAP_X = 34.0, 3.0
X0 = 0.0
W_ROW = 3 * W_DIM + 2 * GAP_X
H_DIM = cao(max(len(bang[d]) for d in ("DimCustomer", "DimTerritory", "DimDate")))
H_F1 = cao(math.ceil(len(bang["FactSalesOrder"]) / 2))
H_F2 = cao(math.ceil(len(bang["FactSalesOrderLine"]) / 2))
H_PROD = cao(math.ceil(len(bang["DimProduct"]) / 2))
GAP_Y = 9.5

y_prod = 1.0
y_f2 = y_prod + H_PROD + GAP_Y
y_dim = y_f2 + H_F2 + GAP_Y
y_f1 = y_dim + H_DIM + GAP_Y
TONG_CAO = y_f1 + H_F1 + 1.0

fig, ax = plt.subplots(figsize=((W_ROW + 2) / 10, TONG_CAO / 10))
ax.set_xlim(-1, W_ROW + 1)
ax.set_ylim(0, TONG_CAO)
ax.axis("off")

dims = [("DimCustomer", "CustomerKey"), ("DimTerritory", "TerritoryKey"), ("DimDate", "OrderDateKey")]
vx = {}
for i, (d, fk) in enumerate(dims):
    x = X0 + i * (W_DIM + GAP_X)
    vx[d] = x
    hop_dim(ax, d, x, y_dim, W_DIM, H_DIM)

hop_fact(ax, "FactSalesOrder", X0, y_f1, W_ROW, H_F1)
hop_fact(ax, "FactSalesOrderLine", X0, y_f2, W_ROW, H_F2)

for d, fk in dims:
    xc = vx[d] + W_DIM / 2
    mui_ten(ax, xc - 4, y_f1, y_dim + H_DIM, fk)       # FactSalesOrder -> Dimension, đi xuống
    mui_ten(ax, xc - 4, y_f2 + H_F2, y_dim, fk)        # FactSalesOrderLine -> Dimension, đi lên

# DimProduct chỉ nối với FactSalesOrderLine, đặt dưới bảng này ở bên phải
W_PROD = 2 * W_DIM + GAP_X
x_prod = X0 + (W_ROW - W_PROD) / 2
khung(ax, "DimProduct", x_prod, y_prod, W_PROD, H_PROD, NAVY)
cot = bang["DimProduct"]
nua = math.ceil(len(cot) / 2)
for i, (c, k) in enumerate(cot):
    j, hang = divmod(i, nua)
    ve_ten_cot(ax, "DimProduct", c, k, x_prod + 1.4 + j * (W_PROD / 2), y_prod + H_PROD - TIEU_DE - 2.0 - hang * DONG, W_PROD / 2 - 2.8)
mui_ten(ax, x_prod + W_PROD / 2 - 4, y_f2, y_prod + H_PROD, "ProductKey")

plt.savefig(os.path.join(GOC, "latex", "IMAGE", "luoc_do_sao.png"), dpi=200, bbox_inches="tight", facecolor="white")
print("đã vẽ luoc_do_sao.png", {k: len(v) for k, v in bang.items()}, f"{W_ROW + 2:.0f}x{TONG_CAO:.0f}")
