"""Chuẩn hoá bước 4: tính lại độc lập 11 đặc trưng tại 20 mốc từ Fact, so với analytics.CustomerSnapshot,
tính nhãn 90 ngày theo (3.1) và Bảng 3.12, kiểm tra miền giá trị, bảng số khách / tỷ lệ y = 1 từng mốc (4.3.1),
so với nhãn sandbox cũ. Chạy: ../.venv/bin/python labels_checks.py"""
import pandas as pd, numpy as np, os, hashlib
H = os.path.dirname(os.path.abspath(__file__)); D = f'{H}/data'; R = f'{H}/results'; os.makedirs(R, exist_ok=True)
out = []
def log(s=''): print(s, flush=True); out.append(s)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)

snap = pd.read_csv(f'{D}/snapshot.csv', header=None, names=['CustomerID','T','CustomerKey','Recency','Frequency','Monetary','Orders90','Orders180','Tenure','Share_Bikes','Share_Accessories','Share_Clothing','NSub'], parse_dates=['T'])
orders = pd.read_csv(f'{D}/orders.csv', header=None, names=['SalesOrderID','CustomerID','OrderDate','ShipDate','SubTotal','TaxAmt','Freight','TotalDue','TerritoryID'], parse_dates=['OrderDate','ShipDate'])
lines = pd.read_csv(f'{D}/lines.csv', header=None, names=['SalesOrderID','SalesOrderDetailID','ProductID','Category','Subcategory','OrderQty','UnitPrice','UnitPriceDiscount','LineTotal'])
lines = lines.merge(orders[['SalesOrderID','CustomerID','OrderDate','ShipDate']], on='SalesOrderID')
DATA_END = orders.OrderDate.max()
log(f'# Kiểm định dữ liệu đặc trưng và nhãn (từ CompanyX_DW)\n\nĐơn trong kho: {len(orders)}, dòng: {len(lines)}, ngày đặt cuối: {DATA_END.date()}, ngày gửi cuối: {orders.ShipDate.max().date()}')
log(f'Snapshot trong kho: {len(snap)} dòng, {snap["T"].nunique()} mốc')

# ---------- 1. tính lại 11 đặc trưng tại từng mốc ----------
def features(T):
    past = orders[(orders.OrderDate < T) & (orders.ShipDate < T)]
    g = past.groupby('CustomerID')
    f = pd.DataFrame({'Recency': (T - g.OrderDate.max()).dt.days, 'Frequency': g.SalesOrderID.count(), 'Monetary': g.TotalDue.sum(),
                      'Tenure': (T - g.OrderDate.min()).dt.days, 'AOV': g.SubTotal.mean(),
                      'Orders90': past[past.OrderDate >= T - pd.Timedelta(days=90)].groupby('CustomerID').SalesOrderID.count(),
                      'Orders180': past[past.OrderDate >= T - pd.Timedelta(days=180)].groupby('CustomerID').SalesOrderID.count()}).fillna({'Orders90': 0, 'Orders180': 0})
    pl = lines[(lines.OrderDate < T) & (lines.ShipDate < T)]
    tot = pl.groupby('CustomerID').LineTotal.sum()
    for cat in ['Bikes', 'Accessories', 'Clothing']:
        f['Share_' + cat] = (pl[pl.Category == cat].groupby('CustomerID').LineTotal.sum() / tot).reindex(f.index).fillna(0)
    f['NSub'] = pl.groupby('CustomerID').Subcategory.nunique().reindex(f.index).fillna(0)
    f['T'] = T; return f.reset_index()

def label(T, days=90):
    win = orders[(orders.OrderDate >= T) & (orders.OrderDate < T + pd.Timedelta(days=days))]
    return win.groupby('CustomerID').size()

mocs = sorted(snap['T'].unique())
rows = []; mism_total = 0; keymism = 0
for T in mocs:
    f = features(T); s = snap[snap['T'] == T]
    m = s.merge(f, on=['CustomerID', 'T'], how='outer', suffixes=('_dw', '_py'), indicator=True)
    km = (m._merge != 'both').sum(); keymism += km
    diffs = {}
    for c in ['Recency', 'Frequency', 'Monetary', 'Orders90', 'Orders180', 'Tenure', 'Share_Bikes', 'Share_Accessories', 'Share_Clothing', 'NSub']:
        tol = 1e-5 if c.startswith('Share') else 0.0051
        diffs[c] = int((abs(m[c + '_dw'] - m[c + '_py']) > tol).sum())
    mism_total += sum(diffs.values())
    n1 = label(T); s2 = s.set_index('CustomerID')
    y = (~s2.index.isin(n1.index)).astype(int)
    complete = (T + pd.Timedelta(days=97) <= DATA_END) and (T + pd.Timedelta(days=90) <= pd.Timestamp('2014-06-01'))
    rows.append(dict(T=T.date(), khach=len(s), y1=int(y.sum()), ty_le_y1=round(y.mean(), 4), nhan_du=complete,
                     mot_don=round((s.Frequency == 1).mean(), 4), bike=round((s.Share_Bikes > 0.5).mean(), 4), nsub2=round((s.NSub >= 2).mean(), 4),
                     khoa_lech=km, gia_tri_lech=sum(diffs.values())))
tab = pd.DataFrame(rows)
log('\n## 1. Đối chiếu Snapshot kho với tính lại độc lập (Python, từ FactSalesOrder/Line)\n')
log(f'Khoá (CustomerID, T) lệch: {keymism}; giá trị lệch (10 cột, dung sai 0,005 tiền / 1e-5 tỷ trọng): {mism_total}')
log('\n## 2. Số khách, nhãn y = 1 (không mua lại trong [T, T+90)), và đại lượng theo dõi Bảng 3.13 theo mốc\n')
log(tab.to_string(index=False))
tab.to_csv(f'{R}/moc_table.csv', index=False)

# ---------- 3. miền giá trị ----------
log('\n## 3. Kiểm tra miền giá trị trên toàn bộ Snapshot kho\n')
chk = {
 'Frequency >= 1': (snap.Frequency >= 1), 'Recency >= 1 (đơn trước T, không gồm T)': (snap.Recency >= 1), 'Tenure >= Recency': (snap.Tenure >= snap.Recency),
 'Orders90 <= Orders180 <= Frequency': (snap.Orders90 <= snap.Orders180) & (snap.Orders180 <= snap.Frequency), 'Monetary > 0': (snap.Monetary > 0),
 'Tổng Share = 1 (±1e-5)': ((snap.Share_Bikes + snap.Share_Accessories + snap.Share_Clothing - 1).abs() < 1e-5), 'NSub >= 1': (snap.NSub >= 1),
 'Không NULL ở 5 cột mới': snap[['Tenure','Share_Bikes','Share_Accessories','Share_Clothing','NSub']].notna().all(axis=1),
 'Tenure == Recency khi Frequency == 1': ((snap.Frequency != 1) | (snap.Tenure == snap.Recency)),
}
for k, v in chk.items(): log(f'  {"PASS" if v.all() else "FAIL"}  {k}: vi phạm {int((~v).sum())}')
# rò rỉ: khách trong snapshot T phải có đơn OrderDate<T và ShipDate<T; không khách nào chỉ có đơn sau T
leak = 0
for T in mocs:
    ok = set(orders[(orders.OrderDate < T) & (orders.ShipDate < T)].CustomerID); have = set(snap[snap['T'] == T].CustomerID)
    leak += len(have - ok) + len(ok - have)
log(f'  {"PASS" if leak == 0 else "FAIL"}  Tập khách mỗi mốc = khách có đơn đặt và gửi trước T: lệch {leak}')

# ---------- 4. lịch Bảng 3.12 ----------
log('\n## 4. Lịch ghép mốc Bảng 3.12: nhãn của T phải đủ 97 ngày trước E và cửa sổ nhãn kết thúc trước 01/06/2014\n')
PAIRS = [('2013-12-15', '2013-09-01'), ('2014-01-15', '2013-10-01'), ('2014-02-15', '2013-11-01'), ('2014-03-01', '2013-11-15'), ('2014-07-08', '2014-03-01')]
for E, T in PAIRS:
    E, T = pd.Timestamp(E), pd.Timestamp(T); end = T + pd.Timedelta(days=90); ok = (T + pd.Timedelta(days=97) <= E) and (end <= pd.Timestamp('2014-06-01')) and (T in mocs) and (E in mocs)
    log(f'  {"PASS" if ok else "FAIL"}  E={E.date()} T={T.date()} cửa sổ nhãn [{T.date()}, {end.date()}) nhãn đủ ngày {(T + pd.Timedelta(days=97)).date()}')
# tháng 6/2014 không có đơn xe đạp (lý do dừng cửa sổ trước 01/06)
jun = lines[(lines.OrderDate >= '2014-06-01') & (lines.OrderDate <= '2014-06-30')]
log(f'  Tháng 6/2014: {jun.SalesOrderID.nunique()} đơn, dòng Bikes = {(jun.Category == "Bikes").sum()} (lý do kết thúc cửa sổ nhãn trước 01/06/2014)')

# ---------- 5. so với nhãn sandbox cũ ----------
log('\n## 5. Đối chiếu nhãn với sandbox cũ (data/snapshots.csv, label_days = 90)\n')
try:
    old = pd.read_csv(f'{H}/../data/snapshots.csv', parse_dates=['T']); old = old[old.label_days == 90].drop_duplicates(['CustomerID', 'T'])
    lab = []
    for T in mocs:
        s = snap[snap['T'] == T][['CustomerID', 'T']].copy(); n1 = label(T); s['y'] = (~s.CustomerID.isin(n1.index)).astype(int); lab.append(s)
    lab = pd.concat(lab)
    m = lab.merge(old[['CustomerID', 'T', 'y']], on=['CustomerID', 'T'], suffixes=('', '_old'))
    log(f'  cặp (khách, mốc) chung: {len(m)}, nhãn lệch: {int((m.y != m.y_old).sum())}')
    lab.to_csv(f'{R}/labels.csv', index=False)
except Exception as e: log(f'  không so được: {e}')

# ---------- 6. vân tay ----------
h = hashlib.sha256(pd.util.hash_pandas_object(snap.sort_values(['T', 'CustomerID']).reset_index(drop=True), index=False).values.tobytes()).hexdigest()[:16]
log(f'\nVân tay snapshot.csv (sha256 16 ký tự): {h}')
open(f'{R}/labels_checks.md', 'w').write('\n'.join(out))
