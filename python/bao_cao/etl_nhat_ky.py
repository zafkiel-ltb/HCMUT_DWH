"""Đọc nhật ký ETL và kết quả kiểm tra chất lượng từ notebook kiểm chứng.

Nguồn: results/doc/kiem_chung_chuong_4.html. File này sinh từ python/kiem_chung/tao_ipynb_kiem_chung_4.py,
chạy trực tiếp trên kho CompanyX_DW (etl.StepLog, C2_03_Verify_and_Quality.sql, C3_03_Verify_Snapshot_Quality_READ_ONLY.sql).
Mọi số liệu về luồng ETL trong báo cáo LaTeX lấy qua module này, không gõ tay.
"""
import os
import re

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HTML = os.path.join(GOC, "results", "doc", "kiem_chung_chuong_4.html")


def _van_ban():
    h = open(_HTML, encoding="utf-8").read()
    h = re.sub(r"<style[\s\S]*?</style>", " ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", h)


def buoc_etl():
    """11 dòng của etl.StepLog trong lần chạy cuối: StepNo, StepName, SourceRows, LoadedRows, ExcludedRows, RejectedRows."""
    vt = _van_ban()
    i = vt.index("etl.StepLog")
    out = []
    for m in re.finditer(r"(\d+) ((?:Extract|Load)\.\w+) (\d+) (\d+) (\d+) (\d+)", vt[i:i + 3000]):
        out.append(dict(no=int(m.group(1)), ten=m.group(2), nguon=int(m.group(3)), nap=int(m.group(4)),
                        loai=int(m.group(5)), tuchoi=int(m.group(6))))
    assert [b["no"] for b in out] == list(range(1, 12)), out
    return out


def lan_chay_cuoi():
    """Trạng thái và thời gian chạy của etl.RunLog (lần chạy cuối)."""
    vt = _van_ban()
    i = vt.index("etl.RunLog")
    m = re.search(r"([0-9A-F-]{36}) (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (\w+)", vt[i:i + 600])
    assert m, "không đọc được etl.RunLog"
    return dict(bat_dau=m.group(2), ket_thuc=m.group(3), trang_thai=m.group(4))


def _nhom(vt, tieu_de, cot_ten):
    i = vt.index(tieu_de)
    j = vt.index(cot_ten, i)
    seg = vt[j + len(cot_ten): j + len(cot_ten) + 700]
    out = []
    for m in re.finditer(r"(0\d)\. ([^\d]+?) (\d+) (\d+)(?= 0\d\.|\s|$)", seg):
        out.append(dict(ma=m.group(1), ten=m.group(2).strip(), so_phep=int(m.group(3)), loi=int(m.group(4))))
    return out


def nhom_44():
    """Bảy nhóm của 44 phép kiểm tra sau ETL (C2_03)."""
    vt = _van_ban()
    r = _nhom(vt, "B. 44 phép kiểm tra chất lượng sau ETL", "GroupName SoPhep Fail")
    assert len(r) == 7 and sum(x["so_phep"] for x in r) == 44 and sum(x["loi"] for x in r) == 0, r
    return r


def nhom_21():
    """Năm nhóm của 21 phép kiểm tra Customer Snapshot (C3_03)."""
    vt = _van_ban()
    r = _nhom(vt, "C. 21 phép kiểm tra Customer Snapshot", "Category SoPhep Fail")
    assert len(r) == 5 and sum(x["so_phep"] for x in r) == 21 and sum(x["loi"] for x in r) == 0, r
    return r


if __name__ == "__main__":
    for b in buoc_etl():
        print(b)
    print(lan_chay_cuoi())
    print(nhom_44())
    print(nhom_21())
