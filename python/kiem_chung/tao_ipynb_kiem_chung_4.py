# -*- coding: utf-8 -*-
"""Sinh và chạy python/kiem_chung/kiem_chung_chuong_4.ipynb: kiểm chứng số liệu Chương 4 (mục 4.1–4.2 và cụm 6) trực tiếp trên kho.
Chỉ đọc: chỉ chạy SELECT và các file *_READ_ONLY / C2_03 (chỉ ghi bảng tạm #). Không chạy lại ETL hay huấn luyện.
Chạy: python python/kiem_chung/tao_ipynb_kiem_chung_4.py  (cần pyodbc, pandas, nbformat, nbclient, nbconvert, ipykernel)
Kết quả: python/kiem_chung/kiem_chung_chuong_4.ipynb (đã chạy) và results/doc/kiem_chung_chuong_4.html (dùng chụp Hình 4.7 và Hình 4.22)."""
import os, nbformat as nbf
from nbclient import NotebookClient
from nbconvert import HTMLExporter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = [
md('# Kiểm chứng số liệu Chương 4 trên kho CompanyX_DW\n'
   'Notebook chỉ đọc. Mỗi mục đối chiếu một nhận định trong Chương 4 với dữ liệu thật trên `.\\SQLEXPRESS`.'),
code('''import os, re, warnings, pyodbc, pandas as pd
from IPython.display import display, HTML
warnings.filterwarnings('ignore', message='pandas only supports SQLAlchemy')
pd.set_option('display.max_columns', 30)
ROOT = os.path.abspath(os.path.join(os.getcwd(), '..', '..')) if os.path.basename(os.getcwd()) == 'kiem_chung' else os.getcwd()
def ket_noi():
    return pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=.\\\\SQLEXPRESS;DATABASE=CompanyX_DW;'
                          'Trusted_Connection=yes;TrustServerCertificate=yes', readonly=True)
cn = ket_noi()
def q(sql, *a):
    return pd.read_sql(sql, cn, params=a or None)
def chay_file(path):
    """Chạy một file .sql (tách theo GO) trên một kết nối riêng (bảng tạm # không lẫn giữa các file), trả về mọi bảng kết quả."""
    text = open(os.path.join(ROOT, path), encoding='utf-8-sig').read()
    out, cur = [], ket_noi().cursor()
    for batch in re.split(r'^\\s*GO\\s*$', text, flags=re.M | re.I):
        if not batch.strip(): continue
        cur.execute(batch)
        while True:
            if cur.description:
                out.append(pd.DataFrame.from_records(cur.fetchall(), columns=[c[0] for c in cur.description]))
            if not cur.nextset(): break
    return out
def bang(df, tieu_de):
    display(HTML(f'<div class="kc"><b>{tieu_de}</b>{df.to_html(index=False)}</div>'))'''),
md('## A. Nhật ký lần chạy ETL cuối (mục 4.2.2, Hình 4.7)\nQuy trình ETL ghi mỗi lần chạy vào `etl.RunLog` và từng bước vào `etl.StepLog`.'),
code('''run = q("SELECT TOP 1 RunID, StartedAt, FinishedAt, Status FROM etl.RunLog ORDER BY StartedAt DESC")
steps = q("SELECT StepNo, StepName, SourceRows, LoadedRows, ExcludedRows, RejectedRows FROM etl.StepLog WHERE RunID=? ORDER BY StepNo", run.RunID[0])
bang(run, 'etl.RunLog – lần chạy cuối')
bang(steps, f'etl.StepLog – {len(steps)} bước của lần chạy cuối')'''),
md('## B. 44 phép kiểm tra chất lượng sau ETL (mục 4.2.3, Bảng 4.3)\nChạy `sql/2_Cum2_ETL_moi/C2_03_Verify_and_Quality.sql` (chỉ ghi bảng tạm). Đếm số phép kiểm tra theo nhóm để đối chiếu câu "44 phép kiểm tra thuộc bảy nhóm".'),
code('''kq = chay_file('sql/2_Cum2_ETL_moi/C2_03_Verify_and_Quality.sql')
chi_tiet = next(d for d in kq if {'GroupName', 'CheckName', 'FailedCount'} <= set(d.columns))
tong = chi_tiet.groupby('GroupName').agg(SoPhep=('CheckName', 'size'), Fail=('FailedCount', lambda s: int((s > 0).sum()))).reset_index()
bang(tong, f'C2_03: {len(chi_tiet)} phép kiểm tra, {int((chi_tiet.FailedCount > 0).sum())} FAIL')'''),
md('## C. 21 phép kiểm tra Customer Snapshot (mục 4.2.2.3, Hình 4.9)\nNhóm "Customer Snapshot và RFM" của Bảng 3.7 được kiểm riêng bằng `C3_03_Verify_Snapshot_Quality_READ_ONLY.sql`.'),
code('''kq3 = chay_file('sql/3_Cum3A_Snapshot/C3_03_Verify_Snapshot_Quality_READ_ONLY.sql')
ct3 = next(d for d in kq3 if {'Category', 'CheckName', 'FailedRows'} <= set(d.columns))
tong3 = ct3.groupby('Category').agg(SoPhep=('CheckName', 'size'), Fail=('FailedRows', lambda s: int((s > 0).sum()))).reset_index()
bang(tong3, f'C3_03: {len(ct3)} phép kiểm tra, {int((ct3.FailedRows > 0).sum())} FAIL')'''),
md('## D. Số bản ghi sau ETL (Bảng 4.1) và số khách theo mốc (Bảng 4.2)'),
code('''dem = q("""SELECT 'DimCustomer' AS Bang, COUNT(*) AS SoDong FROM dbo.DimCustomer UNION ALL SELECT 'DimProduct', COUNT(*) FROM dbo.DimProduct
UNION ALL SELECT 'DimTerritory', COUNT(*) FROM dbo.DimTerritory UNION ALL SELECT 'DimDate', COUNT(*) FROM dbo.DimDate
UNION ALL SELECT 'FactSalesOrder', COUNT(*) FROM dbo.FactSalesOrder UNION ALL SELECT 'FactSalesOrderLine', COUNT(*) FROM dbo.FactSalesOrderLine""")
moc = q("SELECT CONVERT(CHAR(10), SnapshotDate, 103) AS Moc, COUNT(*) AS SoKhach FROM analytics.CustomerSnapshot GROUP BY SnapshotDate ORDER BY SnapshotDate")
bang(dem, 'Bảng 4.1 – số dòng sáu bảng Dimension và Fact')
bang(moc, f'Bảng 4.2 – {len(moc)} mốc trong analytics.CustomerSnapshot')'''),
md('## E. Kiểm tra kết quả cụm 6 (mục 4.4.2, Hình 4.22)\nChạy `results/cum6/CUM6_04_Verify_READ_ONLY.sql`. Mong đợi: 18.360 khách có nhóm, 5 nhóm, 9 quy tắc (7 bật), 6.124 khuyến nghị, Z ≈ 256.502 USD.'),
code('''kq6 = chay_file('results/cum6/CUM6_04_Verify_READ_ONLY.sql')
ten6 = ['Số khách có nhóm và số nhóm', 'Năm nhóm: số khách, RiskScore trung bình, số khách Cao', 'Kho quy tắc CareRule',
        'Danh sách chăm sóc theo kịch bản: số khách, chi phí, Z', 'Hồ sơ khách 19785 (màn hình 2)']
display(HTML('<div id="cum6">' + ''.join(f'<div class="kc"><b>{t}</b>{d.to_html(index=False)}</div>' for t, d in zip(ten6, kq6)) + '</div>'))'''),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}})
out_nb = os.path.join(ROOT, 'python', 'kiem_chung', 'kiem_chung_chuong_4.ipynb')
NotebookClient(nb, timeout=600, kernel_name='python3', resources={'metadata': {'path': os.path.join(ROOT, 'python', 'kiem_chung')}}).execute()
nbf.write(nb, out_nb)
html, _ = HTMLExporter(template_name='classic').from_notebook_node(nb)
html = html.replace('</head>', '<style>.kc{margin:6px 0 14px} .kc b{display:block;font:600 13px Arial;margin-bottom:4px} .kc table{font:12px Arial;border-collapse:collapse} .kc th,.kc td{border:1px solid #bbb;padding:3px 8px;text-align:right} .kc th{background:#f0f0f0}</style></head>')
os.makedirs(os.path.join(ROOT, 'results', 'doc'), exist_ok=True)
open(os.path.join(ROOT, 'results', 'doc', 'kiem_chung_chuong_4.html'), 'w', encoding='utf-8').write(html)
print('Đã ghi', out_nb)
