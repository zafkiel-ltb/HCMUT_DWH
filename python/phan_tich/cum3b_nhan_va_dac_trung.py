"""CỤM 3B – Nhãn 90 ngày, bộ dữ liệu huấn luyện và các bảng/hình cho mục 4.3.1.
Đầu vào: data/snapshot.csv, data/orders.csv, data/lines.csv (trích từ CompanyX_DW bằng python/kiem_chung/extract.sql).
Đầu ra:  data/dataset.csv (đặc trưng + nhãn + AOV cho 20 mốc), results/cum3b/*.csv|png|md, models/chuan_hoa_T20140301.json
Chạy:    python python/phan_tich/cum3b_nhan_va_dac_trung.py
Mọi hằng số thiết kế lấy từ config.py (Chương 3)."""
import os, json, sys
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); D = f'{ROOT}/data'; R = f'{ROOT}/results/cum3b'; M = f'{ROOT}/models'
os.makedirs(R, exist_ok=True); os.makedirs(M, exist_ok=True)
out = []
def log(s=''): print(s, flush=True); out.append(s)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)

snap = pd.read_csv(f'{D}/snapshot.csv', header=None, names=['CustomerID','T','CustomerKey','Recency','Frequency','Monetary','Orders90','Orders180','Tenure','Share_Bikes','Share_Accessories','Share_Clothing','NSub'], parse_dates=['T'])
orders = pd.read_csv(f'{D}/orders.csv', header=None, names=['SalesOrderID','CustomerID','OrderDate','ShipDate','SubTotal','TaxAmt','Freight','TotalDue','TerritoryID'], parse_dates=['OrderDate','ShipDate'])
DATA_END = orders.OrderDate.max()
log(f'# Cụm 3B – Nhãn và bộ dữ liệu huấn luyện\n\nSnapshot: {len(snap)} dòng, {snap["T"].nunique()} mốc. Đơn: {len(orders)}, ngày đặt cuối {DATA_END.date()}.')

# ---------- 1. nhãn theo (3.1): y = 1 nếu không có đơn trong [T, T + 90) ----------
parts = []
for T in sorted(snap['T'].unique()):
    s = snap[snap['T'] == T].copy()
    win = orders[(orders.OrderDate >= T) & (orders.OrderDate < T + pd.Timedelta(days=C.LABEL_DAYS))]
    s['y'] = (~s.CustomerID.isin(win.CustomerID)).astype(int)
    s['label_complete'] = int((T + pd.Timedelta(days=C.LABEL_LAG_DAYS) <= DATA_END) and (T + pd.Timedelta(days=C.LABEL_DAYS) <= pd.Timestamp(C.LABEL_WINDOW_MUST_END_BEFORE)))
    past = orders[(orders.OrderDate < T) & (orders.ShipDate < T)].groupby('CustomerID').SubTotal.mean().rename('AOV')
    s = s.merge(past, left_on='CustomerID', right_index=True, how='left')
    parts.append(s)
ds = pd.concat(parts, ignore_index=True)
ds['BikeBuyer'] = (ds.Share_Bikes > 0.5).astype(int)
ds.to_csv(f'{D}/dataset.csv', index=False)
log(f'Bộ dữ liệu: {len(ds)} dòng, nhãn đủ ở {ds[ds.label_complete == 1]["T"].nunique()} mốc, mốc chấm điểm {C.SCORING_DATE} không có nhãn.')

# ---------- 2. Bảng 4.3.1a: số khách và tỷ lệ y = 1 theo mốc ----------
tab = ds.groupby('T').agg(so_khach=('CustomerID', 'size'), y1=('y', 'sum'), nhan_du=('label_complete', 'max'),
                           mot_don=('Frequency', lambda v: (v == 1).mean()), bike=('BikeBuyer', 'mean'), nsub2=('NSub', lambda v: (v >= 2).mean())).reset_index()
tab['ty_le_y1'] = tab.y1 / tab.so_khach
tab.loc[tab.nhan_du == 0, ['y1', 'ty_le_y1']] = np.nan
tab['T'] = tab['T'].dt.strftime('%d/%m/%Y')
tab = tab[['T', 'so_khach', 'y1', 'ty_le_y1', 'mot_don', 'bike', 'nsub2', 'nhan_du']].round(4)
tab.to_csv(f'{R}/bang_4_3_1a_moc.csv', index=False)
log('\n## Bảng 4.3.1a. Số khách, số khách y = 1 và các đại lượng theo dõi (Bảng 3.13) tại 20 mốc\n' + tab.to_string(index=False))

# ---------- 3. Bảng 4.3.1b: lịch fold Bảng 3.12 với số liệu thật ----------
rows = []
for E, T in C.FOLDS + [(C.SCORING_DATE, C.SCORING_TRAIN_DATE)]:
    tr = ds[ds['T'] == T]; ev = ds[ds['T'] == E]
    rows.append(dict(moc_danh_gia=E, moc_huan_luyen=T, khach_huan_luyen=len(tr), y1_huan_luyen=int(tr.y.sum()), ty_le_y1_huan_luyen=round(tr.y.mean(), 4),
                     khach_danh_gia=len(ev), y1_danh_gia=int(ev.y.sum()) if ev.label_complete.max() else None, ty_le_y1_danh_gia=round(ev.y.mean(), 4) if ev.label_complete.max() else None,
                     cua_so_nhan=f'{T} → {(pd.Timestamp(T) + pd.Timedelta(days=C.LABEL_DAYS) - pd.Timedelta(days=1)).date()}', nhan_du_ngay=str((pd.Timestamp(T) + pd.Timedelta(days=C.LABEL_LAG_DAYS)).date())))
fold = pd.DataFrame(rows); fold.to_csv(f'{R}/bang_4_3_1b_fold.csv', index=False)
log('\n## Bảng 4.3.1b. Bốn fold phát triển và mốc chấm điểm (Bảng 3.12) với số khách thật\n' + fold.to_string(index=False))

# ---------- 4. Bảng 4.3.1c: tỷ lệ y = 1 theo khoảng rời rạc (Bảng 3.10) tại mốc huấn luyện cuối ----------
tr = ds[ds['T'] == C.SCORING_TRAIN_DATE]
desc = []
for col, bins, labels in [('Recency', C.RECENCY_BINS, ['<90', '90–179', '180–269', '270–364', '365–539', '≥540']), ('Frequency', C.FREQUENCY_BINS, ['1', '2', '≥3']), ('NSub', C.NSUB_BINS, ['1', '2', '3–4', '≥5'])]:
    g = tr.groupby(pd.cut(tr[col], bins, labels=labels), observed=False).y.agg(['size', 'mean'])
    for k, r in g.iterrows(): desc.append(dict(thuoc_tinh=col, khoang=str(k), so_khach=int(r['size']), ty_le_y1=round(r['mean'], 4)))
qM = tr.Monetary.quantile([.25, .5, .75]).values
g = tr.groupby(np.searchsorted(qM, tr.Monetary.values)).y.agg(['size', 'mean'])
for k, r in g.iterrows(): desc.append(dict(thuoc_tinh='Monetary', khoang=f'Q{k + 1}', so_khach=int(r['size']), ty_le_y1=round(r['mean'], 4)))
g = tr.groupby('BikeBuyer').y.agg(['size', 'mean'])
for k, r in g.iterrows(): desc.append(dict(thuoc_tinh='BikeBuyer', khoang=str(k), so_khach=int(r['size']), ty_le_y1=round(r['mean'], 4)))
desc = pd.DataFrame(desc); desc.to_csv(f'{R}/bang_4_3_1c_khoang.csv', index=False)
log(f'\n## Bảng 4.3.1c. Tỷ lệ y = 1 theo khoảng rời rạc hóa tại mốc huấn luyện {C.SCORING_TRAIN_DATE} (chỉ để mô tả)\n' + desc.to_string(index=False))
log(f'\nTứ phân vị Monetary tại {C.SCORING_TRAIN_DATE}: {np.round(qM, 2).tolist()} USD')

# ---------- 5. tham số chuẩn hóa z-score và ranh giới rời rạc hóa (fit trên mốc huấn luyện, giữ nguyên khi chấm điểm) ----------
num = [f for f in C.FEATURES if f != 'BikeBuyer']
params = dict(train_snapshot=C.SCORING_TRAIN_DATE, zscore={f: dict(mean=float(tr[f].mean()), std=float(tr[f].std(ddof=0))) for f in num},
              monetary_quartiles=[float(v) for v in qM], recency_bins=C.RECENCY_BINS, frequency_bins=C.FREQUENCY_BINS, nsub_bins=C.NSUB_BINS, features=C.FEATURES)
json.dump(params, open(f'{M}/chuan_hoa_T{C.SCORING_TRAIN_DATE.replace("-", "")}.json', 'w'), ensure_ascii=False, indent=1)
log(f'\nĐã lưu tham số chuẩn hóa/rời rạc hóa: models/chuan_hoa_T{C.SCORING_TRAIN_DATE.replace("-", "")}.json')

# ---------- 6. Hình 4.3.1: sơ đồ mốc thời gian ----------
fig, ax = plt.subplots(figsize=(12, 4.2), dpi=150)
t0, t1 = pd.Timestamp('2013-05-15'), pd.Timestamp('2014-07-20')
ax.set_xlim(t0, t1); ax.set_ylim(0, 6.5); ax.axis('off')
ax.plot([t0, t1], [0.8, 0.8], color='black', lw=1.5)
for m in pd.date_range('2013-06-01', '2014-07-01', freq='MS'):
    ax.plot([m, m], [0.65, 0.95], color='black', lw=1); ax.text(m, 0.35, m.strftime('%m/%Y'), ha='center', fontsize=8)
for T in sorted(ds[ds.label_complete == 1]['T'].unique()):
    ax.plot([T], [0.8], marker='o', color='#1f3a5f', ms=4)
ax.text(t0, 1.25, '19 mốc huấn luyện (ngày 1 và 15, 01/06/2013 → 01/03/2014)', fontsize=9, color='#1f3a5f')
colors = ['#4472c4', '#70ad47', '#ed7d31', '#7030a0']
for i, (E, T) in enumerate(C.FOLDS):
    y = 2.0 + i * 0.9; T_, E_ = pd.Timestamp(T), pd.Timestamp(E)
    ax.barh(y, (T_ + pd.Timedelta(days=90)) - T_, left=T_, height=0.5, color=colors[i], alpha=0.75)
    ax.plot([E_], [y], marker='v', color=colors[i], ms=9)
    ax.text(T_ - pd.Timedelta(days=4), y, f'T {T_.strftime("%d/%m")}', ha='right', va='center', fontsize=8)
    ax.text(E_ + pd.Timedelta(days=4), y, f'E {E_.strftime("%d/%m/%Y")}', ha='left', va='center', fontsize=8)
y = 2.0 + 4 * 0.9; T_, E_ = pd.Timestamp(C.SCORING_TRAIN_DATE), pd.Timestamp(C.SCORING_DATE)
ax.barh(y, pd.Timedelta(days=90), left=T_, height=0.5, color='#c00000', alpha=0.75); ax.plot([E_], [y], marker='*', color='#c00000', ms=12)
ax.text(T_ - pd.Timedelta(days=4), y, f'T {T_.strftime("%d/%m")}', ha='right', va='center', fontsize=8); ax.text(E_ + pd.Timedelta(days=4), y, 'Chấm điểm 08/07/2014', ha='left', va='center', fontsize=8, color='#c00000')
ax.axvspan(pd.Timestamp('2014-06-01'), pd.Timestamp('2014-06-30'), color='grey', alpha=0.15); ax.text(pd.Timestamp('2014-06-15'), 6.2, 'Tháng 6/2014\nkhông có đơn xe đạp', ha='center', fontsize=8, color='dimgray')
ax.text(t0, 6.2, 'Thanh màu: cửa sổ nhãn 90 ngày của mốc huấn luyện T. Tam giác: mốc đánh giá E (T + 97 ≤ E).', fontsize=8)
plt.savefig(f'{R}/hinh_4_3_1_moc_thoi_gian.png', bbox_inches='tight', facecolor='white'); plt.close()
log('Đã vẽ results/cum3b/hinh_4_3_1_moc_thoi_gian.png')
open(f'{R}/cum3b_ket_qua.md', 'w').write('\n'.join(out))
