"""Sinh các bảng LaTeX cho chương ETL từ nhật ký ETL và kết quả kiểm tra chất lượng.

Nguồn số liệu: python/bao_cao/etl_nhat_ky.py (đọc results/doc/kiem_chung_chuong_4.html, kết quả chạy trực tiếp trên kho).
Ra: latex/bang/etl_11_buoc.tex, etl_kt44.tex, etl_kt21.tex
Chạy: .venv/bin/python python/bao_cao/tao_bang_tex_etl.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import etl_nhat_ky as nk

RA = os.path.join(nk.GOC, "latex", "bang")
os.makedirs(RA, exist_ok=True)


def so(n):
    return f"{n:,}".replace(",", ".")


def ghi(ten, tieu_de, cot, dong):
    out = [f"\\begin{{tabular}}{{{cot}}}", "\\toprule", tieu_de + " \\\\", "\\midrule"]
    out += [" & ".join(r) + " \\\\" for r in dong]
    out += ["\\bottomrule", "\\end{tabular}"]
    open(os.path.join(RA, ten), "w", encoding="utf-8").write("\n".join(out) + "\n")


MO_TA = {
    "Extract.Customer": "Trích bảng khách hàng và họ tên vào staging",
    "Extract.Product": "Trích sản phẩm cùng danh mục con và danh mục",
    "Extract.Territory": "Trích vùng bán hàng",
    "Extract.Order": "Trích đầu đơn hàng, chưa lọc",
    "Extract.OrderLine": "Trích dòng chi tiết đơn, chưa lọc",
    "Load.DimCustomer": "Cập nhật và bổ sung khách cá nhân",
    "Load.DimProduct": "Cập nhật và bổ sung sản phẩm",
    "Load.DimTerritory": "Cập nhật và bổ sung vùng",
    "Load.DimDate": "Sinh lịch liên tục theo ngày đặt",
    "Load.FactSalesOrder": "Kiểm tra rồi nạp đơn đã gửi của khách cá nhân",
    "Load.FactSalesOrderLine": "Nạp dòng chi tiết của các đơn đã nạp",
}
dong = []
for b in nk.buoc_etl():
    assert b["ten"] in MO_TA, b["ten"]
    dong.append([str(b["no"]), "\\texttt{" + b["ten"] + "}", MO_TA[b["ten"]], so(b["nguon"]), so(b["nap"]), so(b["loai"]), so(b["tuchoi"])])
ghi("etl_11_buoc.tex", "Bước & Tên bước & Việc làm & Nguồn & Nạp & Loại & Từ chối", "rlp{4.0cm}rrrr", dong)

N44 = {"Số dòng": "Số lượng bản ghi (đầy đủ)", "Mã nguồn": "Mã định danh nguồn", "Khóa": "Khoá và quan hệ (duy nhất, nhất quán)",
       "Phạm vi/ánh xạ": "Phạm vi và ánh xạ (hợp lệ)", "Tiền": "Giá trị tài chính (chính xác)", "Rejection": "Bản ghi bất thường",
       "Nhật ký": "Nhật ký ETL (truy vết)"}
dong = [[N44[g["ten"]], str(g["so_phep"]), f"{g['so_phep'] - g['loi']} đạt"] for g in nk.nhom_44()]
dong.append(["\\textbf{Tổng cộng}", "\\textbf{44}", "\\textbf{44 đạt, 0 lỗi}"])
ghi("etl_kt44.tex", "Nhóm kiểm tra & Số phép & Kết quả", "lrr", dong)

N21 = {"Calendar": "Lịch mốc", "Coverage": "Độ phủ khách", "Domain": "Miền giá trị", "RFM verification": "Tính lại RFM từ nguồn",
       "Product verification": "Tính lại thuộc tính sản phẩm"}
dong = [[N21[g["ten"]], str(g["so_phep"]), f"{g['so_phep'] - g['loi']} đạt"] for g in nk.nhom_21()]
dong.append(["\\textbf{Tổng cộng}", "\\textbf{21}", "\\textbf{21 đạt, 0 lỗi}"])
ghi("etl_kt21.tex", "Nhóm kiểm tra & Số phép & Kết quả", "lrr", dong)

print("đã ghi", sorted(f for f in os.listdir(RA) if f.startswith("etl_")))


# Bảng sáu bảng của kho: số bản ghi lấy từ etl.StepLog (cột nạp vào kho)
nap = {b["ten"]: b["nap"] for b in nk.buoc_etl()}
CAC_BANG = [
    ("DimCustomer", "Một khách hàng cá nhân", "Mã khách, mã cá nhân nguồn, họ tên, mã vùng", "Load.DimCustomer"),
    ("DimDate", "Một ngày", "Ngày, tháng, quý, năm", "Load.DimDate"),
    ("DimProduct", "Một sản phẩm", "Mã sản phẩm nguồn, tên, danh mục con, danh mục", "Load.DimProduct"),
    ("DimTerritory", "Một vùng bán hàng", "Mã vùng nguồn, tên vùng, quốc gia, nhóm vùng", "Load.DimTerritory"),
    ("FactSalesOrder", "Một đơn hàng", "SubTotal, TaxAmt, Freight, TotalDue", "Load.FactSalesOrder"),
    ("FactSalesOrderLine", "Một dòng chi tiết đơn", "OrderQty, UnitPrice, UnitPriceDiscount, LineTotal", "Load.FactSalesOrderLine"),
]
ghi("etl_cac_bang.tex", "Bảng & Mỗi dòng là & Nội dung chính & Số bản ghi", "lp{3.3cm}p{5.6cm}r",
    [["\\texttt{" + t + "}", g, n, so(nap[k])] for t, g, n, k in CAC_BANG])
