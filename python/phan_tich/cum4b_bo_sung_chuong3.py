# -*- coding: utf-8 -*-
"""CỤM 4B – Các phân tích mô hình mà Chương 3 hẹn trình bày ở Chương 4 (bổ sung ngày 03/11/2026).
  1. Độ nhạy với nhãn 180 ngày (mục 3.4.1)                       → bang_4_3_1d_nhan_180_moc.csv, bang_4_3_1e_nhan_180_mo_hinh.csv
  2. Tương quan giữa các thuộc tính (mục 3.4.2, Lecture 5 slide 53) → bang_4_3_2g_tuong_quan.csv, bang_4_3_2g2_cramer_nb.csv
  3. Naive Bayes theo tập thuộc tính, mức hữu ích của NSub (3.4.2) → bang_4_3_2h_tap_thuoc_tinh.csv, bang_4_3_2i_do_quan_trong_cay.csv
Đầu vào: data/dataset.csv (cụm 3B), data/orders.csv.   Đầu ra: results/cum4b/*.csv, cum4b_ket_qua.md, tom_tat.json
Chạy:    python python/phan_tich/cum4b_bo_sung_chuong3.py   (khoảng 2 phút)"""
import os, sys, json, time, warnings
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
from models_def import NB, GiniTree, RecencyRev
from sklearn.naive_bayes import CategoricalNB
from sklearn.metrics import roc_auc_score, brier_score_loss, average_precision_score
warnings.filterwarnings('ignore')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); D = f'{ROOT}/data'; R = f'{ROOT}/results/cum4b'
os.makedirs(R, exist_ok=True); out = []; tom = {}
def log(s=''): print(s, flush=True); out.append(s)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
t0 = time.time()

ds = pd.read_csv(f'{D}/dataset.csv', parse_dates=['T'])
orders = pd.read_csv(f'{D}/orders.csv', header=None, names=['SalesOrderID', 'CustomerID', 'OrderDate', 'ShipDate', 'SubTotal', 'TaxAmt', 'Freight', 'TotalDue', 'TerritoryID'], parse_dates=['OrderDate', 'ShipDate'])
G = C.GROSS_MARGIN; R_, C_, B_ = C.BASE_SCENARIO['r'], C.BASE_SCENARIO['c'], C.BASE_SCENARIO['B']
END = pd.Timestamp(C.LABEL_WINDOW_MUST_END_BEFORE)
def get(T): return ds[ds['T'] == pd.Timestamp(T)].reset_index(drop=True)
def Z_pv(ev, p, y=None):
    """Z theo chính sách 3.5.4 như cụm 4: xếp theo p·v, K = min(B/c, số khách EV > 0), Z = Σ r·y·v − c·K."""
    v = G * ev.AOV.values; y = ev.y.values if y is None else y
    order = np.argsort(-(p * v)); evi = p[order] * R_ * v[order] - C_; K = min(int(B_ // C_), int((evi > 0).sum())); sel = order[:K]
    return R_ * (y[sel] * v[sel]).sum() - C_ * K
def boot_ci(y, p1, p2, n=500, seed=C.RANDOM_STATE):
    rng = np.random.default_rng(seed); d = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max(): continue
        d.append(roc_auc_score(y[i], p1[i]) - roc_auc_score(y[i], p2[i]))
    return np.percentile(d, [2.5, 97.5])

log('# Cụm 4B – Phân tích bổ sung theo lời hẹn của Chương 3\n')

# ---------- 1. Nhãn 180 ngày (3.4.1) ----------
def label(T, days):
    s = get(T); win = orders[(orders.OrderDate >= T) & (orders.OrderDate < T + pd.Timedelta(days=days))]
    return (~s.CustomerID.isin(win.CustomerID)).astype(int).values
moc180 = [T for T in sorted(ds['T'].unique()) if pd.Timestamp(T) + pd.Timedelta(days=180) <= END]
rows = []
for T in moc180:
    T = pd.Timestamp(T); s = get(T); y90 = s.y.values; y180 = label(T, 180)
    rows.append(dict(T=T.strftime('%d/%m/%Y'), so_khach=len(s), ty_le_y90=y90.mean(), ty_le_y180=y180.mean(), y90_1_mua_trong_90_180=int(((y90 == 1) & (y180 == 0)).sum()),
                     ty_le_chua_den_ky=((y90 == 1) & (y180 == 0)).sum() / max(1, (y90 == 1).sum())))
t180 = pd.DataFrame(rows).round(4); t180.to_csv(f'{R}/bang_4_3_1d_nhan_180_moc.csv', index=False)
log(f'## 1. Nhãn 180 ngày tại {len(t180)} mốc có cửa sổ 180 ngày kết thúc trước {END.date()} (Bảng 4.3.1d)\n' + t180.to_string(index=False))
log(f'Trung bình: y = 1 theo nhãn 90 ngày {t180.ty_le_y90.mean():.1%}, theo nhãn 180 ngày {t180.ty_le_y180.mean():.1%}. Trong số khách y90 = 1, {t180.ty_le_chua_den_ky.mean():.1%} có mua trong ngày 90–180 (chưa đến kỳ chứ không bỏ đi).')
tom['nhan180'] = dict(so_moc=len(t180), moc_dau=t180['T'].iloc[0], moc_cuoi=t180['T'].iloc[-1], y90=round(float(t180.ty_le_y90.mean()), 4), y180=round(float(t180.ty_le_y180.mean()), 4), chua_den_ky=round(float(t180.ty_le_chua_den_ky.mean()), 4))
# Mô hình: (a) NB thiết kế (học nhãn 90 ngày, T + 97 <= E) chấm ở E rồi so với nhãn 90 và 180 ngày.
#          (b) NB học thẳng nhãn 180 ngày ở mốc đầu 01/06/2013 (cửa sổ kết thúc 27/11/2013), đánh giá ở 01/12/2013.
#          Với dữ liệu kết thúc 30/06/2014 không có cặp mốc nào thoả cả T + 187 <= E lẫn E + 180 <= 01/06/2014, nên (b) thiếu 4 ngày độ trễ ghi nhận đơn.
F180 = [('2013-11-01', '2013-07-15'), ('2013-11-15', '2013-08-01'), ('2013-12-01', '2013-08-15')]
mrows = []
for E, T in F180:
    tr, ev = get(T), get(E); y90 = ev.y.values; y180 = label(pd.Timestamp(E), 180)
    assert pd.Timestamp(T) + pd.Timedelta(days=C.LABEL_LAG_DAYS) <= pd.Timestamp(E) and pd.Timestamp(E) + pd.Timedelta(days=180) <= END
    for name, mk in [('Naive Bayes (nhãn 90 ngày, thiết kế)', NB), ('Cây Gini (nhãn 90 ngày)', GiniTree), ('Recency đảo chiều', RecencyRev)]:
        p = mk().fit(tr).predict(ev)
        mrows.append(dict(E=E, T=T, mo_hinh=name, ty_le_y90=y90.mean(), ty_le_y180=y180.mean(), AUC_nhan90=roc_auc_score(y90, p), AUC_nhan180=roc_auc_score(y180, p),
                          AP_nhan90=average_precision_score(y90, p), AP_nhan180=average_precision_score(y180, p)))
m180 = pd.DataFrame(mrows).round(4); m180.to_csv(f'{R}/bang_4_3_1e_nhan_180_mo_hinh.csv', index=False)
log('\nXếp hạng của mô hình học theo nhãn 90 ngày khi đối chiếu với nhãn 180 ngày (Bảng 4.3.1e):\n' + m180.to_string(index=False))
# Học thẳng nhãn 180 ngày không kiểm được: cần T + 187 <= E và E + 180 <= 01/06/2014, nên T <= 30/05/2013, trước mốc đầu tiên.
# Thử nới 4 ngày (T = 01/06/2013, E = 01/12/2013) cho AUC khoảng 0,49 vì ở 01/06/2013 mọi khách đều có đúng 1 đơn và đều mua xe đạp (Bảng 4.3.1a), mô hình không học được gì.
s0 = get('2013-06-01'); deg = dict(mot_don=float((s0.Frequency == 1).mean()), bike=float(s0.BikeBuyer.mean()), nsub1=float((s0.NSub == 1).mean()))
log(f'Học thẳng nhãn 180 ngày: không có cặp mốc nào thoả T + 187 ≤ E và E + 180 ≤ {END.date()}. Mốc gần nhất 01/06/2013 có {deg["mot_don"]:.0%} khách một đơn, {deg["bike"]:.0%} mua xe đạp, {deg["nsub1"]:.0%} NSub = 1, nên không dùng để huấn luyện.')
a = m180[m180.mo_hinh.str.startswith('Naive Bayes')]; r_ = m180[m180.mo_hinh == 'Recency đảo chiều']; t_ = m180[m180.mo_hinh.str.startswith('Cây')]
tom['nhan180'].update(NB_AUC90=round(float(a.AUC_nhan90.mean()), 4), NB_AUC180=round(float(a.AUC_nhan180.mean()), 4), Rec_AUC90=round(float(r_.AUC_nhan90.mean()), 4), Rec_AUC180=round(float(r_.AUC_nhan180.mean()), 4),
                      Tree_AUC90=round(float(t_.AUC_nhan90.mean()), 4), Tree_AUC180=round(float(t_.AUC_nhan180.mean()), 4), moc_0106=deg)
log(f'Naive Bayes thiết kế: AUC trung bình 3 mốc {a.AUC_nhan90.mean():.3f} với nhãn 90 ngày, {a.AUC_nhan180.mean():.3f} với nhãn 180 ngày. Recency đảo chiều: {r_.AUC_nhan90.mean():.3f} và {r_.AUC_nhan180.mean():.3f}.')

# ---------- 2. Tương quan giữa các thuộc tính (3.4.2) ----------
ALL = C.FEATURES
TR = sorted({T for _, T in C.FOLDS} | {C.SCORING_TRAIN_DATE})
cors = [get(T)[ALL].corr(method='spearman') for T in TR]; cm = sum(cors) / len(cors)
pairs = [dict(thuoc_tinh_1=a_, thuoc_tinh_2=b_, rho_spearman_TB=cm.loc[a_, b_], rho_min=min(c.loc[a_, b_] for c in cors), rho_max=max(c.loc[a_, b_] for c in cors))
         for i, a_ in enumerate(ALL) for b_ in ALL[i + 1:]]
pr = pd.DataFrame(pairs); pr['abs'] = pr.rho_spearman_TB.abs(); pr = pr.sort_values('abs', ascending=False).drop(columns='abs').round(3)
pr.to_csv(f'{R}/bang_4_3_2g_tuong_quan.csv', index=False)
hi = pr[pr.rho_spearman_TB.abs() >= 0.7]
log(f'\n## 2. Tương quan hạng Spearman giữa 11 thuộc tính, trung bình {len(TR)} mốc huấn luyện {TR} (Bảng 4.3.2g)\n' + pr.head(15).to_string(index=False))
log(f'Cặp |ρ| ≥ 0,7: {len(hi)}. ' + '; '.join(f'{r.thuoc_tinh_1}–{r.thuoc_tinh_2} {r.rho_spearman_TB:.2f}' for r in hi.itertuples()))
tom['tuong_quan'] = dict(so_cap_cao=int(len(hi)), cap_cao=[[r.thuoc_tinh_1, r.thuoc_tinh_2, round(float(r.rho_spearman_TB), 2)] for r in hi.itertuples()], moc=TR)
# Cramér's V giữa 5 thuộc tính rời rạc của Naive Bayes (giả định độc lập có điều kiện), tại mốc 01/03/2014, trong từng lớp y
from models_def import discretize
def cramer(x, z):
    t = pd.crosstab(x, z).values; n = t.sum(); e = np.outer(t.sum(1), t.sum(0)) / n; chi2 = ((t - e) ** 2 / np.where(e == 0, 1, e)).sum()
    return float(np.sqrt(chi2 / (n * (min(t.shape) - 1)))) if min(t.shape) > 1 else np.nan
tr = get(C.SCORING_TRAIN_DATE); X, _ = discretize(tr); X.columns = ['Recency', 'Frequency', 'Monetary', 'BikeBuyer', 'NSub']
cv = []
for i, a_ in enumerate(X.columns):
    for b_ in X.columns[i + 1:]:
        cv.append(dict(thuoc_tinh_1=a_, thuoc_tinh_2=b_, V_toan_bo=cramer(X[a_], X[b_]), V_trong_y1=cramer(X[a_][tr.y == 1], X[b_][tr.y == 1]), V_trong_y0=cramer(X[a_][tr.y == 0], X[b_][tr.y == 0])))
cv = pd.DataFrame(cv).round(3).sort_values('V_toan_bo', ascending=False); cv.to_csv(f'{R}/bang_4_3_2g2_cramer_nb.csv', index=False)
log(f'\nCramér V giữa 5 thuộc tính rời rạc của Naive Bayes tại {C.SCORING_TRAIN_DATE} (toàn bộ, trong lớp y = 1, trong lớp y = 0):\n' + cv.to_string(index=False))
tom['cramer'] = [[r.thuoc_tinh_1, r.thuoc_tinh_2, round(float(r.V_toan_bo), 2), round(float(r.V_trong_y1), 2), round(float(r.V_trong_y0), 2)] for r in cv.head(3).itertuples()]

# ---------- 3. Naive Bayes theo tập thuộc tính, mức hữu ích của NSub (3.4.2) ----------
NCAT = dict(Recency=6, Frequency=3, Monetary=4, BikeBuyer=2, NSub=4, Tenure=4, Orders180=3)
def disc(df, feats, q):
    cols = {}
    for f in feats:
        if f == 'Recency': cols[f] = pd.cut(df.Recency, C.RECENCY_BINS, labels=False).values
        elif f == 'Frequency': cols[f] = pd.cut(df.Frequency, C.FREQUENCY_BINS, labels=False).values
        elif f in ('Monetary', 'Tenure'): cols[f] = np.searchsorted(q[f], df[f].values)
        elif f == 'BikeBuyer': cols[f] = df.BikeBuyer.values
        elif f == 'NSub': cols[f] = pd.cut(df.NSub, C.NSUB_BINS, labels=False).values
        elif f == 'Orders180': cols[f] = np.clip(df[f].values, 0, 2)
    return np.column_stack([cols[f] for f in feats])
class NBv:
    def __init__(self, feats): self.f = list(feats)
    def fit(self, df):
        self.q = {k: df[k].quantile([.25, .5, .75]).values for k in ('Monetary', 'Tenure')}
        self.clf = CategoricalNB(alpha=1, min_categories=[NCAT[f] for f in self.f]).fit(disc(df, self.f, self.q), df.y.values); return self
    def predict(self, df): return self.clf.predict_proba(disc(df, self.f, self.q))[:, 1]
BASE = ['Recency', 'Frequency', 'Monetary', 'BikeBuyer', 'NSub']
VARIANTS = [('Thiết kế: R, F, M, BikeBuyer, NSub', BASE), ('Bỏ NSub', [f for f in BASE if f != 'NSub']), ('Bỏ BikeBuyer', [f for f in BASE if f != 'BikeBuyer']),
            ('Bỏ Frequency', [f for f in BASE if f != 'Frequency']), ('Bỏ Monetary', [f for f in BASE if f != 'Monetary']), ('Chỉ R, F, M', ['Recency', 'Frequency', 'Monetary']),
            ('Thêm Tenure (tứ phân vị)', BASE + ['Tenure']), ('Thêm Orders180 (0, 1, ≥ 2)', BASE + ['Orders180'])]
vrows = []
for E, T in C.FOLDS:
    tr, ev = get(T), get(E); y = ev.y.values; bc = brier_score_loss(y, np.full(len(y), tr.y.mean())); prec = RecencyRev().fit(tr).predict(ev)
    zv = (lambda v: R_ * (y[np.argsort(-v)[:int(B_ // C_)]] * v[np.argsort(-v)[:int(B_ // C_)]]).sum() - C_ * int(B_ // C_))(G * ev.AOV.values)
    for name, feats in VARIANTS:
        p = NBv(feats).fit(tr).predict(ev); ci = boot_ci(y, p, prec); z = Z_pv(ev, p)
        vrows.append(dict(tap=name, E=E, AUC=roc_auc_score(y, p), Brier=brier_score_loss(y, p), AP=average_precision_score(y, p), Z=z, DK1=ci[1] >= 0, DK2=brier_score_loss(y, p) < bc, DK3=z > zv))
vr = pd.DataFrame(vrows)
vt = vr.groupby('tap', sort=False).agg(AUC=('AUC', 'mean'), Brier=('Brier', 'mean'), AP=('AP', 'mean'), Z=('Z', 'mean'), DK1=('DK1', 'sum'), DK2=('DK2', 'sum'), DK3=('DK3', 'sum')).reset_index()
d0 = vt.iloc[0]; vt['chenh_Z_so_thiet_ke'] = vt.Z - d0.Z
zf = vr.pivot(index='E', columns='tap', values='Z'); vt['so_fold_Z_hon_thiet_ke'] = [int((zf[t_] > zf[VARIANTS[0][0]] + 1e-9).sum()) for t_ in vt.tap]   # so cặp theo từng fold, không chỉ trung bình
vt['chenh_Z_lon_nhat_giua_fold'] = [float((zf[t_] - zf[VARIANTS[0][0]]).abs().max()) for t_ in vt.tap]
vt = vt.round(4); vt.to_csv(f'{R}/bang_4_3_2h_tap_thuoc_tinh.csv', index=False)
log('\n## 3. Naive Bayes theo tập thuộc tính, trung bình 4 fold Bảng 3.12 (Bảng 4.3.2h)\n' + vt.to_string(index=False))
ref = pd.read_csv(f'{ROOT}/results/cum4/bang_4_3_2b_trung_binh.csv'); ref_nb = ref[ref.mo_hinh == 'Naive Bayes rời rạc'].iloc[0]
assert abs(d0.AUC - ref_nb.AUC) < 1e-3 and abs(d0.Z - ref_nb.Z_pv) < 1, f'Biến thể thiết kế không khớp cụm 4: {d0.AUC} vs {ref_nb.AUC}'
log(f'Kiểm tra: biến thể thiết kế khớp cụm 4 (AUC {d0.AUC:.4f}, Z {d0.Z:,.0f}).')
ns = vt[vt.tap == 'Bỏ NSub'].iloc[0]
tom['tap_thuoc_tinh'] = {r.tap: dict(AUC=round(float(r.AUC), 4), Brier=round(float(r.Brier), 4), Z=round(float(r.Z)), DK=f'{int(r.DK1)}/{int(r.DK2)}/{int(r.DK3)}', chenh_Z=round(float(r.chenh_Z_so_thiet_ke))) for r in vt.itertuples()}
# độ quan trọng Gini của cây đối chứng học ở 01/03/2014
tree = GiniTree().fit(get(C.SCORING_TRAIN_DATE)); imp = pd.DataFrame({'thuoc_tinh': ALL, 'do_quan_trong_Gini': tree.clf.feature_importances_}).sort_values('do_quan_trong_Gini', ascending=False).round(4)
imp.to_csv(f'{R}/bang_4_3_2i_do_quan_trong_cay.csv', index=False)
log('\nĐộ quan trọng Gini của cây đối chứng học ở 01/03/2014:\n' + imp.to_string(index=False))
tom['nsub'] = dict(AUC_bo=round(float(ns.AUC), 4), Brier_bo=round(float(ns.Brier), 4), Z_bo=round(float(ns.Z)), chenh_Z=round(float(ns.chenh_Z_so_thiet_ke)), AUC_tk=round(float(d0.AUC), 4), Brier_tk=round(float(d0.Brier), 4), Z_tk=round(float(d0.Z)),
                   imp_cay=round(float(imp.set_index('thuoc_tinh').loc['NSub', 'do_quan_trong_Gini']), 4))

log(f'\nThời gian chạy: {time.time() - t0:.0f} giây.')
json.dump(tom, open(f'{R}/tom_tat.json', 'w'), ensure_ascii=False, indent=1)
open(f'{R}/cum4b_ket_qua.md', 'w').write('\n'.join(out))
