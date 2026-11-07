# -*- coding: utf-8 -*-
"""CỤM 6 – Phân hệ mô hình và tri thức của DSS (mục 3.5.2 → 3.5.5), sinh dữ liệu cho 5 màn hình và SQL ghi kho.
Đầu vào: data/dataset.csv, data/orders.csv, data/lines.csv, results/cum5/customer_risk_score_*.csv
Đầu ra:  results/cum6/*.csv|png|md, results/cum6/dss_khach.csv (bảng khách cho app), results/cum6/CUM6_0x_*.sql
Chạy:    python python/phan_tich/cum6_phan_tich_dss.py   (khoảng 1–2 phút)"""
import os, sys, json, itertools, warnings
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LinearRegression
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); D = f'{ROOT}/data'; R = f'{ROOT}/results/cum6'; R5 = f'{ROOT}/results/cum5'
os.makedirs(R, exist_ok=True); out = []
def log(s=''): print(s, flush=True); out.append(s)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
E0 = pd.Timestamp(C.SCORING_DATE); TAG = C.SCORING_TRAIN_DATE.replace('-', ''); G = C.GROSS_MARGIN
R_, C_, B_ = C.BASE_SCENARIO['r'], C.BASE_SCENARIO['c'], C.BASE_SCENARIO['B']
rng = np.random.default_rng(C.RANDOM_STATE)
V_NB, V_TREE, V_KM = f'NB_T{TAG}_v1', f'TREE_T{TAG}_v1', f'KMEANS_E{C.SCORING_DATE.replace("-", "")}_v1'

ds = pd.read_csv(f'{D}/dataset.csv', parse_dates=['T']); sc = ds[ds['T'] == E0].reset_index(drop=True)
score = pd.read_csv(f'{R5}/customer_risk_score_{TAG}.csv')
sc = sc.merge(score[['CustomerID', 'RiskScore', 'RiskPercentile', 'RiskLevel', 'TreeScore', 'LeafID', 'TopFactors', 'Flag']], on='CustomerID')
sc['p'] = sc.RiskScore; sc['v'] = G * sc.AOV
orders = pd.read_csv(f'{D}/orders.csv', header=None, names=['SalesOrderID', 'CustomerID', 'OrderDate', 'ShipDate', 'SubTotal', 'TaxAmt', 'Freight', 'TotalDue', 'TerritoryID'], parse_dates=['OrderDate', 'ShipDate'])
lines = pd.read_csv(f'{D}/lines.csv', header=None, names=['SalesOrderID', 'SalesOrderDetailID', 'ProductID', 'Category', 'Subcategory', 'OrderQty', 'UnitPrice', 'UnitPriceDiscount', 'LineTotal'])
lines = lines.merge(orders[['SalesOrderID', 'CustomerID', 'OrderDate', 'ShipDate']], on='SalesOrderID')
log(f'# Cụm 6 – Phân hệ mô hình và tri thức của DSS tại mốc {C.SCORING_DATE}\n\nKhách: {len(sc)}, g = {G}, kịch bản cơ sở r = {R_}, c = {C_}, B = {B_:.0f}')
log(f'Giá trị v = g·AOV: trung vị {sc.v.median():.1f} USD, khách có v < c/r = {C_ / R_:.0f} USD: {(sc.v < C_ / R_).mean():.1%}')

# ---------- 1. ABC (3.5.3, công thức 3.19) ----------
s = sc.sort_values('Monetary', ascending=False).copy(); s['cum'] = s.Monetary.cumsum() / s.Monetary.sum(); s['prev'] = s.cum.shift(fill_value=0)
s['ABC'] = np.where(s.prev < .8, 'A', np.where(s.prev < .95, 'B', 'C')); sc = sc.merge(s[['CustomerID', 'ABC', 'prev']].rename(columns={'prev': 'CumShare'}), on='CustomerID')
abc = sc.groupby('ABC').agg(so_khach=('CustomerID', 'size'), ty_le_khach=('CustomerID', lambda x: len(x) / len(sc)), ty_trong_M=('Monetary', lambda x: x.sum() / sc.Monetary.sum()), M_trung_vi=('Monetary', 'median'), p_TB=('p', 'mean'), v_trung_vi=('v', 'median')).round(3)
abc.to_csv(f'{R}/bang_4_4_abc.csv'); log('\n## 1. Phân hạng ABC (ngưỡng 80% / 95%)\n' + abc.to_string())

# ---------- 2. K-means (3.5.3, bước 1–6) ----------
X = sc[['Recency', 'Frequency', 'Monetary']].copy(); X['Frequency'] = np.log1p(X.Frequency); X['Monetary'] = np.log1p(X.Monetary)
mu, sd = X.mean(), X.std(ddof=0); Xz = ((X - mu) / sd).values
H = []
for i in range(10):
    r = np.random.default_rng(i); samp = r.choice(len(Xz), 500, replace=False)
    nn = NearestNeighbors(n_neighbors=2).fit(Xz); yd = nn.kneighbors(Xz[samp])[0][:, 1]
    U = r.uniform(Xz.min(0), Xz.max(0), (500, 3)); xd = NearestNeighbors(n_neighbors=1).fit(Xz).kneighbors(U)[0][:, 0]
    H.append(yd.sum() / (xd.sum() + yd.sum()))
log(f'\n## 2. K-means trên (R, ln(1+F), ln(1+M)) z-score. Hopkins trung bình 10 lần: H = {np.mean(H):.3f} (gần 0 → có cấu trúc cụm)')
sidx = np.random.default_rng(0).choice(len(Xz), 10000, replace=False); kres = {}; krows = []
for k in range(2, 11):
    km = KMeans(k, n_init=20, random_state=42).fit(Xz); kres[k] = km; sil = silhouette_score(Xz[sidx], km.labels_[sidx])
    krows.append(dict(k=k, WCSS=round(km.inertia_, 1), Silhouette=round(sil, 3))); log(f'  k={k}: WCSS={km.inertia_:.0f}, silhouette={sil:.3f}')
kt = pd.DataFrame(krows); kt.to_csv(f'{R}/bang_4_4_chon_k.csv', index=False)
K = 5; km = kres[K]; sc['cluster'] = km.labels_
aris = [adjusted_rand_score(km.labels_, KMeans(K, n_init=20, random_state=s_).fit(Xz).labels_) for s_ in (1, 2, 3)]
ward = AgglomerativeClustering(K, linkage='ward').fit(Xz[sidx]); ari_w = adjusted_rand_score(km.labels_[sidx], ward.labels_)
log(f'  Chọn k = {K}. ARI với 3 khởi tạo khác: {np.round(aris, 3).tolist()}. ARI với Ward (10.000 mẫu): {ari_w:.3f}')
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4), dpi=150); ax[0].plot(kt.k, kt.WCSS, 'o-'); ax[0].set_xlabel('k'); ax[0].set_ylabel('WCSS'); ax[0].set_title('Elbow'); ax[0].axvline(K, color='r', ls='--')
ax[1].plot(kt.k, kt.Silhouette, 'o-'); ax[1].set_xlabel('k'); ax[1].set_ylabel('Silhouette'); ax[1].set_title('Silhouette (10.000 mẫu)'); ax[1].axvline(K, color='r', ls='--'); plt.tight_layout(); plt.savefig(f'{R}/hinh_4_4_chon_k.png', facecolor='white'); plt.close()
prof = sc.groupby('cluster').agg(n=('CustomerID', 'size'), R_med=('Recency', 'median'), F_mean=('Frequency', 'mean'), M_med=('Monetary', 'median'), M_share=('Monetary', lambda x: x.sum() / sc.Monetary.sum()))
# đặt tên N1–N5 theo hồ sơ mục 3.5.3
name = {}
multi = [c for c in prof.index if prof.F_mean[c] >= 1.5]; single = [c for c in prof.index if c not in multi]
if multi: n1 = max(multi, key=lambda c: prof.M_med[c]); name[n1] = 'N1'; multi.remove(n1)        # mua nhiều lần, giá trị cao
if multi: n4 = min(multi, key=lambda c: prof.M_med[c]); name[n4] = 'N4'; multi.remove(n4)        # mua lặp lại, giá trị thấp
if single: n3 = max(single, key=lambda c: prof.R_med[c]); name[n3] = 'N3'; single.remove(n3)    # mua một lần, đã lâu không quay lại
single = sorted(single + multi, key=lambda c: -prof.M_med[c])
for c, nm in zip(single, ['N2', 'N5', 'N4', 'N1']):
    name.setdefault(c, nm)                                                                        # N2 giá trị trung bình, N5 giá trị thấp
sc['Nhom'] = sc.cluster.map(name)
desc = {'N1': 'Mua nhiều lần, giá trị cao', 'N2': 'Mua một lần, giá trị trung bình', 'N3': 'Mua một lần, đã lâu không quay lại', 'N4': 'Mua lặp lại, giá trị thấp', 'N5': 'Mua một lần, giá trị thấp'}
hs = sc.groupby('Nhom').agg(so_khach=('CustomerID', 'size'), ty_le=('CustomerID', lambda x: len(x) / len(sc)), R_trung_vi=('Recency', 'median'), F_trung_binh=('Frequency', 'mean'), M_trung_vi=('Monetary', 'median'),
                            ty_trong_M=('Monetary', lambda x: x.sum() / sc.Monetary.sum()), hang_A=('ABC', lambda x: (x == 'A').sum()), hang_B=('ABC', lambda x: (x == 'B').sum()), hang_C=('ABC', lambda x: (x == 'C').sum()),
                            RiskScore_TB=('p', 'mean'), ty_le_Cao=('RiskLevel', lambda x: (x == 'Cao').mean())).round(3)
hs['mo_ta'] = [desc[i] for i in hs.index]; hs.to_csv(f'{R}/bang_4_4_ho_so_nhom.csv'); log('\nHồ sơ 5 nhóm (Bảng 3.24):\n' + hs.to_string())
sc['DistanceToCenter'] = np.round(np.linalg.norm(Xz - km.cluster_centers_[km.labels_], axis=1), 6)   # làm tròn để kết quả không đổi theo thư viện số học của từng máy
json.dump(dict(features=['Recency', 'ln1p_Frequency', 'ln1p_Monetary'], mean=mu.round(6).tolist(), std=sd.round(6).tolist(), centers=km.cluster_centers_.round(6).tolist(), cluster_to_name={int(k): v for k, v in name.items()}, k=K, n_init=20, random_state=42, hopkins=round(float(np.mean(H)), 4), silhouette=float(kt.loc[kt.k == K, 'Silhouette'].iloc[0]), ari_seeds=[round(a, 4) for a in aris], ari_ward=round(ari_w, 4)), open(f'{ROOT}/models/kmeans_E{C.SCORING_DATE.replace("-", "")}.json', 'w'), indent=1)

# ---------- 3. Ma trận Rủi ro × Giá trị (Bảng 3.25) và cơ cấu sản phẩm (Bảng 3.28) ----------
mx = pd.crosstab(sc.ABC, sc.RiskLevel); mx.to_csv(f'{R}/bang_4_4_ma_tran_rui_ro_gia_tri.csv'); log('\n## 3. Ma trận Rủi ro × Giá trị (số khách)\n' + mx.to_string())
cc = sc.groupby('Nhom').agg(ty_trong_Bikes=('Share_Bikes', 'mean'), ty_trong_Accessories=('Share_Accessories', 'mean'), ty_trong_Clothing=('Share_Clothing', 'mean'), ty_le_da_mua_xe=('Share_Bikes', lambda x: (x > 0).mean()), NSub_TB=('NSub', 'mean')).round(3)
cc.to_csv(f'{R}/bang_4_4_co_cau_san_pham.csv'); log('\nCơ cấu sản phẩm theo nhóm (Bảng 3.28):\n' + cc.to_string())

# ---------- 4. Luật kết hợp (3.5.5, công thức 3.29–3.31) ----------
pl = lines[(lines.OrderDate < E0) & (lines.ShipDate < E0)]
baskets = pl.groupby('CustomerID').Subcategory.apply(set); N = len(baskets)
cnt = pd.Series([x for b in baskets for x in b]).value_counts() / N
pairs = pd.Series([frozenset(c) for b in baskets for c in itertools.combinations(sorted(b), 2)]).value_counts() / N
def rule(a, b):
    sup = pairs.get(frozenset([a, b]), 0.0); conf = sup / cnt.get(a, np.nan); return sup, conf, conf / cnt.get(b, np.nan)
cand = [('R6', 'Touring Bikes', 'Helmets'), ('R6b', 'Touring Bikes', 'Bottles and Cages'), ('R7', 'Mountain Bikes', 'Fenders'), ('R8', 'Gloves', 'Helmets'), ('R8b', 'Hydration Packs', 'Bottles and Cages')]
ar = pd.DataFrame([dict(quy_tac=q, A=a, B=b, support=rule(a, b)[0], confidence=rule(a, b)[1], lift=rule(a, b)[2]) for q, a, b in cand]).round(4)
ar['chap_nhan'] = (ar.support >= 0.01) & (ar.confidence >= 0.2) & (ar.lift > 1)
ar.to_csv(f'{R}/bang_4_4_luat_ket_hop.csv', index=False); log(f'\n## 4. Luật kết hợp trên giỏ tích luỹ (N = {N} khách, {(baskets.apply(len) >= 2).mean():.1%} có ≥ 2 danh mục con)\n' + ar.to_string(index=False))

# ---------- 5. Mô hình quyết định: kịch bản cơ sở, what-if, độ nhạy, goal seeking (3.5.2, 3.5.4) ----------
def solve(df, r, c, B, pcol='p', vcol='v'):
    p, v = df[pcol].values, df[vcol].values; ev = p * r * v - c; order = np.argsort(-(p * v)); npos = int((ev > 0).sum()); K = min(int(B // c), npos); sel = order[:K]
    return dict(Z=float(ev[sel].sum()), K=K, C=float(c * K), n_pos=npos, giu_lai_ky_vong=float((p[sel] * r).sum()), sel=sel)
base = solve(sc, R_, C_, B_); sc['selected_base'] = 0; sc.loc[base['sel'], 'selected_base'] = 1
log(f'\n## 5. Kịch bản cơ sở: Z = {base["Z"]:,.0f} USD, chọn K = {base["K"]} khách, chi phí {base["C"]:,.0f}, khách có EV > 0: {base["n_pos"]}, khách giữ lại kỳ vọng {base["giu_lai_ky_vong"]:.1f}')
wi = []
for name_, r, c, B in [('Cơ sở', R_, C_, B_), ('r = 5%', .05, C_, B_), ('r = 20%', .20, C_, B_), ('c = 5 USD', R_, 5.0, B_), ('c = 20 USD', R_, 20.0, B_), ('B = 20.000', R_, C_, 20000.0), ('B = 60.000', R_, C_, 60000.0), ('B = 100.000', R_, C_, 100000.0)]:
    z = solve(sc, r, c, B); wi.append(dict(kich_ban=name_, r=r, c=c, B=B, Z=round(z['Z']), K=z['K'], C=round(z['C']), giu_lai_ky_vong=round(z['giu_lai_ky_vong'], 1), delta_Z=round(z['Z'] - base['Z'])))
wi = pd.DataFrame(wi); wi.to_csv(f'{R}/bang_4_4_what_if.csv', index=False); log('\nWhat-if (Bảng 3.26):\n' + wi.to_string(index=False))
sens = []
for name_, kw in [('r', dict(r=R_ * 1.2)), ('p', dict(pmul=1.2)), ('g (qua v)', dict(gmul=1.2)), ('c', dict(c=C_ * 1.2)), ('B', dict(B=B_ * 1.2))]:
    d = sc.copy()
    if 'pmul' in kw: d['p'] = (d.p * kw['pmul']).clip(upper=1)
    if 'gmul' in kw: d['v'] = d.v * kw['gmul']
    z = solve(d, kw.get('r', R_), kw.get('c', C_), kw.get('B', B_)); sens.append(dict(tham_so=name_, thay_doi='+20%', Z=round(z['Z']), delta_Z=round(z['Z'] - base['Z']), delta_pct=round((z['Z'] - base['Z']) / base['Z'] * 100, 1), K=z['K']))
    d = sc.copy()
    if 'pmul' in kw: d['p'] = d.p * 0.8
    if 'gmul' in kw: d['v'] = d.v * 0.8
    z = solve(d, R_ * 0.8 if 'r' in kw else R_, C_ * 0.8 if 'c' in kw else C_, B_ * 0.8 if 'B' in kw else B_); sens.append(dict(tham_so=name_, thay_doi='−20%', Z=round(z['Z']), delta_Z=round(z['Z'] - base['Z']), delta_pct=round((z['Z'] - base['Z']) / base['Z'] * 100, 1), K=z['K']))
sens = pd.DataFrame(sens); sens.to_csv(f'{R}/bang_4_4_do_nhay.csv', index=False); log('\nĐộ nhạy ±20%:\n' + sens.to_string(index=False))
fig, ax = plt.subplots(figsize=(7, 3.4), dpi=150); piv = sens.pivot(index='tham_so', columns='thay_doi', values='delta_Z').loc[['r', 'p', 'g (qua v)', 'c', 'B']]
ax.barh(piv.index, piv['+20%'], color='#4472c4', label='+20%'); ax.barh(piv.index, piv['−20%'], color='#ed7d31', label='−20%'); ax.axvline(0, color='k', lw=0.8); ax.set_xlabel('Thay đổi Z so với kịch bản cơ sở (USD)'); ax.legend(); plt.tight_layout(); plt.savefig(f'{R}/hinh_4_4_do_nhay.png', facecolor='white'); plt.close()
S = float((sc.p.values[base['sel']] * sc.v.values[base['sel']]).sum()); r_be = C_ * base['K'] / S; r_100k = (100000 + C_ * base['K']) / S
log(f'\nTìm mục tiêu (3.25), K = {base["K"]} cố định: r* hoà vốn = {r_be:.2%}, r* để Z = 100.000 USD = {r_100k:.2%}')
Ps = {0.02: .3, 0.10: .5, 0.20: .2}; prows = []
for B in [20000, 40000, 60000, 100000]:
    z = solve(sc, R_, C_, B); sel = z['sel']; zs = {r: float((sc.p.values[sel] * r * sc.v.values[sel] - C_).sum()) for r in Ps}
    prows.append(dict(B=B, K=z['K'], **{f'r={int(r * 100)}%': round(v) for r, v in zs.items()}, gia_tri_ky_vong=round(sum(Ps[r] * v for r, v in zs.items()))))
pf = pd.DataFrame(prows); pf.to_csv(f'{R}/bang_4_4_payoff.csv', index=False)
log('\nBảng Z theo ngân sách × r (Bảng 3.27, danh sách chốt tại r = 10%):\n' + pf.to_string(index=False))
log(f'  Lạc quan: B = {pf.loc[pf["r=20%"].idxmax(), "B"]:,}. Bi quan: B = {pf.loc[pf["r=2%"].idxmax(), "B"]:,}. Giá trị kỳ vọng lớn nhất: B = {pf.loc[pf.gia_tri_ky_vong.idxmax(), "B"]:,}')
# mô phỏng r ~ Beta (trung bình 10%)
rs = rng.beta(2.2, 19.8, 10000); Zs = rs * S - C_ * base['K']; Zb = []
for _ in range(2000):
    yb = rng.random(base['K']) < sc.p.values[base['sel']]; Zb.append(rng.beta(2.2, 19.8) * (yb * sc.v.values[base['sel']]).sum() - C_ * base['K'])
sim = dict(r_mean=float(rs.mean()), r_P5=float(np.percentile(rs, 5)), r_P95=float(np.percentile(rs, 95)), Z_mean=float(Zs.mean()), Z_P5=float(np.percentile(Zs, 5)), Z_P50=float(np.percentile(Zs, 50)), Z_P95=float(np.percentile(Zs, 95)), P_Z_am=float((Zs < 0).mean()), Z_nhan_va_r_P5=float(np.percentile(Zb, 5)), Z_nhan_va_r_P50=float(np.percentile(Zb, 50)), Z_nhan_va_r_P95=float(np.percentile(Zb, 95)), kiem_dinh_r10=float(0.10 * S - C_ * base['K']))
json.dump(sim, open(f'{R}/mo_phong.json', 'w'), indent=1); log('\nMô phỏng r ~ Beta(2,2; 19,8), 10.000 lần: ' + ', '.join(f'{k}={v:,.3f}' if abs(v) < 10 else f'{k}={v:,.0f}' for k, v in sim.items()))
fig, ax = plt.subplots(figsize=(7, 3.4), dpi=150); ax.hist(Zs, bins=60, color='#4472c4', alpha=0.8); ax.axvline(0, color='r', ls='--', label='Z = 0'); ax.axvline(base['Z'], color='k', ls=':', label='Kịch bản cơ sở r = 10%'); ax.set_xlabel('Z (USD)'); ax.set_ylabel('Số lần mô phỏng'); ax.legend(); plt.tight_layout(); plt.savefig(f'{R}/hinh_4_4_mo_phong.png', facecolor='white'); plt.close()
# dự báo hồi quy tuyến tính (xu hướng + tháng)
m = orders.set_index('OrderDate').resample('MS').agg(n=('SalesOrderID', 'count'), rev=('SubTotal', 'sum')); m = m[m.index >= '2013-01-01']; m['t'] = np.arange(len(m)); m['month'] = m.index.month
Xf = pd.get_dummies(m[['t', 'month']], columns=['month'], drop_first=True).astype(float); train, test = m.index < '2014-04-01', m.index >= '2014-04-01'; frows = []
for col in ['n', 'rev']:
    lr = LinearRegression().fit(Xf[train], m.loc[train, col]); pred = lr.predict(Xf[test]); act = m.loc[test, col].values; naive = m.loc[m.index[test] - pd.DateOffset(years=1), col].values
    frows.append(dict(chi_so=col, du_bao_04_06_2014=np.round(pred).astype(int).tolist(), thuc_te=act.astype(int).tolist(), MAPE_04_05=round(float(np.mean(np.abs(pred[:2] - act[:2]) / act[:2])), 3), MAPE_nen_04_05=round(float(np.mean(np.abs(naive[:2] - act[:2]) / act[:2])), 3), lech_thang_6=round(float((pred[2] - act[2]) / act[2]), 2)))
fc = pd.DataFrame(frows); fc.to_csv(f'{R}/bang_4_4_du_bao.csv', index=False); log('\nDự báo hồi quy tuyến tính (huấn luyện 01/2013–03/2014, kiểm 04–06/2014):\n' + fc.to_string(index=False))
m[['n', 'rev']].to_csv(f'{R}/chuoi_thang.csv')

# ---------- 6. Kho quy tắc R1–R9, kênh theo R3–R5, bài toán cái túi, danh sách chăm sóc ----------
rules = [('R1', 'Loại trừ', 'Khách đã được liên hệ trong 90 ngày trước (nhật ký CRM)', 'Không đưa vào danh sách mới', 'Chính sách đề xuất, chưa có dữ liệu CRM', None, None),
         ('R2', 'Loại trừ', 'p·r·v − c ≤ 0', 'Không đưa vào danh sách chăm sóc cá nhân', 'Mục 3.5.2', None, None),
         ('R3', 'Hình thức liên hệ', 'Nhóm N1 và RiskLevel = Cao', 'Liên hệ cá nhân kèm ưu đãi', 'N1 giá trị cao, mua nhiều lần', 25.0, 0.15),
         ('R4', 'Hình thức liên hệ', 'Nhóm N3', 'Nội dung mời quay lại kèm ưu đãi', 'N3 mua một lần, đã lâu không quay lại', 15.0, 0.12),
         ('R5', 'Hình thức liên hệ', 'Các trường hợp còn lại', 'Email cá nhân hóa gửi tự động', 'Chi phí liên hệ thấp', 3.0, 0.05),
         ('R6', 'Sản phẩm gợi ý', 'Đã mua Touring Bikes, chưa mua Helmets', 'Gợi ý Helmets', 'Bảng 3.29', None, None),
         ('R7', 'Sản phẩm gợi ý', 'Đã mua Mountain Bikes, chưa mua Fenders', 'Gợi ý Fenders', 'Bảng 3.29', None, None),
         ('R8', 'Sản phẩm gợi ý', 'Đã mua Gloves chưa mua Helmets, hoặc đã mua Hydration Packs chưa mua Bottles and Cages', 'Gợi ý sản phẩm vế phải', 'Bảng 3.29', None, None),
         ('R9', 'Giám sát mô hình', 'Đã đủ nhãn 90 ngày sau chiến dịch', 'So ROC-AUC với Recency trên nhóm đối chứng, cảnh báo nếu không hơn', 'Mục 3.4.7', None, None)]
chan = np.where((sc.Nhom == 'N1') & (sc.RiskLevel == 'Cao'), 'R3', np.where(sc.Nhom == 'N3', 'R4', 'R5'))
sc['KenhRule'] = chan; sc['c_k'] = pd.Series(chan).map({'R3': 25.0, 'R4': 15.0, 'R5': 3.0}).values; sc['r_k'] = pd.Series(chan).map({'R3': .15, 'R4': .12, 'R5': .05}).values
sc['EV_k'] = sc.p * sc.r_k * sc.v - sc.c_k
ok = sc.EV_k > 0; order = np.argsort(-(sc.EV_k / sc.c_k).where(ok, -np.inf).values); cum = np.cumsum(sc.c_k.values[order]); sel = order[(cum <= B_) & ok.values[order]]
sc['selected_kenh'] = 0; sc.loc[sel, 'selected_kenh'] = 1; Zk = float(sc.EV_k.values[sel].sum())
try:
    from scipy.optimize import milp, LinearConstraint, Bounds
    ev = sc.EV_k.values.copy(); ev[~ok.values] = -1e9; res = milp(c=-ev, constraints=LinearConstraint(sc.c_k.values[None, :], -np.inf, B_), integrality=np.ones(len(ev)), bounds=Bounds(0, 1), options=dict(time_limit=60))
    x = np.round(res.x).astype(int) if res.x is not None else None; Zip = float(sc.EV_k.values[x == 1].sum()) if x is not None else None
except Exception as e: x, Zip = None, None
o2 = np.argsort(-(sc.p * sc.v).values); cum2 = np.cumsum(sc.c_k.values[o2]); sel2 = o2[(cum2 <= B_) & ok.values[o2]]; Zpv = float(sc.EV_k.values[sel2].sum())
log(f'\n## 6. Bài toán cái túi theo kênh (Bảng 3.26a): R3 {int((chan == "R3").sum())} khách, R4 {int((chan == "R4").sum())}, R5 {int((chan == "R5").sum())}. R2 loại {int((~ok).sum())} khách có EV ≤ 0.')
log(f'  Tham lam EV/chi phí: Z = {Zk:,.0f} USD, chọn {len(sel)} khách, chi {sc.c_k.values[sel].sum():,.0f} USD, theo kênh {pd.Series(chan[sel]).value_counts().to_dict()}')
log(f'  Quy hoạch nguyên (scipy milp): Z = {Zip:,.0f} USD, chọn {int(x.sum())} khách' if Zip is not None else '  scipy milp không chạy được, dùng tham lam')
log(f'  Xếp theo p·v bỏ qua chi phí kênh: Z = {Zpv:,.0f} USD ({len(sel2)} khách) → chênh {(Zk - Zpv) / Zpv:+.1%}')
kenh = sc.groupby('KenhRule').agg(so_khach=('CustomerID', 'size'), duoc_chon=('selected_kenh', 'sum'), chi_phi=('c_k', lambda v: v[sc.loc[v.index, 'selected_kenh'] == 1].sum()), EV_tong=('EV_k', lambda v: v[sc.loc[v.index, 'selected_kenh'] == 1].sum())).round(0)
kenh.to_csv(f'{R}/bang_4_4_theo_kenh.csv'); log(kenh.to_string())
# sản phẩm gợi ý R6–R8 cho khách được chọn
bk = baskets.reindex(sc.CustomerID).apply(lambda s_: s_ if isinstance(s_, set) else set())
def goi_y(b):
    g, rr = [], []
    if 'Touring Bikes' in b and 'Helmets' not in b: g.append('Helmets'); rr.append('R6')
    if 'Mountain Bikes' in b and 'Fenders' not in b: g.append('Fenders'); rr.append('R7')
    if ('Gloves' in b and 'Helmets' not in b) or ('Hydration Packs' in b and 'Bottles and Cages' not in b):
        g += [x for x in (['Helmets'] if 'Gloves' in b and 'Helmets' not in b else []) + (['Bottles and Cages'] if 'Hydration Packs' in b and 'Bottles and Cages' not in b else []) if x not in g]; rr.append('R8')
    return ','.join(dict.fromkeys(g)), ','.join(rr)
gy = [goi_y(b) for b in bk]; sc['SanPhamGoiY'] = [g for g, _ in gy]; sc['QuyTacSP'] = [r for _, r in gy]
sc['GiaiThich'] = ('Kênh ' + sc.KenhRule + ' (' + sc.Nhom + ', RiskLevel ' + sc.RiskLevel + ') | EV = ' + sc.EV_k.round(2).astype(str) + ' USD | ' + np.where(sc.QuyTacSP != '', 'Sản phẩm: ' + sc.QuyTacSP + ' → ' + sc.SanPhamGoiY + ' | ', 'Nội dung mặc định | ') + sc.TopFactors)
dsach = sc[sc.selected_kenh == 1].sort_values('EV_k', ascending=False)
# mức khớp của từng nhóm với mô hình giá trị kỳ vọng (3.5.3 hẹn ở Chương 4): tỷ lệ khách có EV > 0 ở kịch bản cơ sở và số khách vào danh sách theo kênh
hs.insert(len(hs.columns) - 1, 'ty_le_EV_duong', (sc.p * R_ * sc.v - C_ > 0).groupby(sc.Nhom).mean().round(3))
hs.insert(len(hs.columns) - 1, 'duoc_chon_kenh', sc.groupby('Nhom').selected_kenh.sum())
hs.to_csv(f'{R}/bang_4_4_ho_so_nhom.csv'); log('Mức khớp với mô hình giá trị kỳ vọng theo nhóm:\n' + hs[['so_khach', 'ty_le_EV_duong', 'duoc_chon_kenh']].to_string())
log(f'  Danh sách chăm sóc kịch bản cơ sở theo kênh: {len(dsach)} khách, có sản phẩm gợi ý: {(dsach.QuyTacSP != "").mean():.1%}')

# ---------- 7. bảng khách cho app và SQL ----------
cols = ['CustomerID', 'Recency', 'Frequency', 'Monetary', 'AOV', 'Orders90', 'Orders180', 'Tenure', 'Share_Bikes', 'Share_Accessories', 'Share_Clothing', 'NSub', 'BikeBuyer', 'RiskScore', 'RiskPercentile', 'RiskLevel', 'TreeScore', 'LeafID', 'TopFactors', 'Flag', 'ABC', 'CumShare', 'Nhom', 'DistanceToCenter', 'v', 'KenhRule', 'c_k', 'r_k', 'EV_k', 'selected_base', 'selected_kenh', 'SanPhamGoiY', 'QuyTacSP', 'GiaiThich']
sc[cols].to_csv(f'{R}/dss_khach.csv', index=False)
def q(s): return "N'" + str(s).replace("'", "''") + "'"
hdr = "USE [CompanyX_DW];\nSET NOCOUNT ON; SET XACT_ABORT ON; SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON;\n"
kmcfg = json.load(open(f'{ROOT}/models/kmeans_E{C.SCORING_DATE.replace("-", "")}.json'))
sql1 = hdr + f"""/* CUM6_01 – Đăng ký mô hình phân cụm K-means (ModelRole CLUSTERING) + 9 quy tắc chăm sóc (Bảng 3.30). Cần đã chạy Cluster1b. */
IF OBJECT_ID(N'analytics.CareRule') IS NULL THROW 56001, N'Chưa chạy sql/4_Cum1b_Schema_DSS_DE_XUAT.sql.', 1;
IF EXISTS (SELECT 1 FROM analytics.ModelRegistry WHERE ModelVersion={q(V_KM)}) THROW 56002, N'K-means đã đăng ký. Xoá bằng RESET_DSS.sql nếu muốn ghi lại.', 1;
BEGIN TRANSACTION;
INSERT analytics.ModelRegistry(ModelVersion,ModelRole,ModelType,TrainingSnapshot,FeatureList,ConfigurationJSON,EffectiveFrom,IsActive)
VALUES ({q(V_KM)},N'CLUSTERING',N'K-means k = 5 trên (R, ln(1+F), ln(1+M)) z-score','{C.SCORING_DATE}',N'Recency,Frequency,Monetary',{q(json.dumps(kmcfg, ensure_ascii=False))},'{C.SCORING_DATE}',1);
INSERT analytics.CareRule(RuleCode,RuleVersion,RuleType,ConditionText,ActionText,Rationale,ChannelCost,ChannelSuccess,IsActive,EffectiveFrom,UpdatedBy) VALUES
""" + ',\n'.join(f"({q(rc)},1,{q(rt)},{q(ct)},{q(at)},{q(ra)},{'NULL' if cc_ is None else cc_},{'NULL' if rk is None else rk},{0 if rc in ('R1', 'R9') else 1},'{C.SCORING_DATE}',N'Nhóm TA_DSS')" for rc, rt, ct, at, ra, cc_, rk in rules) + """;
COMMIT TRANSACTION;
SELECT RuleCode, RuleType, ChannelCost, ChannelSuccess, IsActive, LEFT(ConditionText,60) AS DieuKien FROM analytics.CareRule ORDER BY RuleCode;
PRINT N'CUM6_01_OK: K-means đăng ký, 9 quy tắc (R1, R9 tạm tắt vì chưa có dữ liệu CRM).';
"""
open(f'{R}/CUM6_01_ModelRegistry_CareRule.sql', 'w', encoding='utf-8-sig').write(sql1)
chunks = []
for i in range(0, len(sc), 500):
    part = sc.iloc[i:i + 500]
    chunks.append("INSERT analytics.CustomerSegment(CustomerID,SnapshotDate,ClusterModelVersion,ABCClass,CumShare,ClusterID,ClusterName,DistanceToCenter) VALUES\n" + ',\n'.join(
        f"({r.CustomerID},'{C.SCORING_DATE}',{q(V_KM)},N'{r.ABC}',{r.CumShare:.6f},{int(r.Nhom[1])},{q(r.Nhom + ' – ' + desc[r.Nhom])},{r.DistanceToCenter:.6f})" for r in part.itertuples()) + ';')
sql2 = hdr + f"""/* CUM6_02 – Hạng ABC và nhóm K-means của {len(sc)} khách tại {C.SCORING_DATE} */
IF EXISTS (SELECT 1 FROM analytics.CustomerSegment WHERE SnapshotDate='{C.SCORING_DATE}') THROW 56003, N'Đã có phân nhóm cho mốc này.', 1;
BEGIN TRANSACTION;
""" + '\n'.join(chunks) + f"""
COMMIT TRANSACTION;
SELECT ClusterName, ABCClass, COUNT(*) AS SoKhach FROM analytics.CustomerSegment WHERE SnapshotDate='{C.SCORING_DATE}' GROUP BY ClusterName, ABCClass ORDER BY ClusterName, ABCClass;
PRINT N'CUM6_02_OK: {len(sc)} khách đã có hạng ABC và nhóm.';
"""
open(f'{R}/CUM6_02_CustomerSegment.sql', 'w', encoding='utf-8-sig').write(sql2)
SCEN = f'BASE_r10_c10_B40000_{C.SCORING_DATE.replace("-", "")}_{V_NB}'
chunks = []
for i in range(0, len(dsach), 500):
    part = dsach.iloc[i:i + 500]
    chunks.append("INSERT analytics.CareRecommendation(ScenarioID,CustomerID,ScoreDate,ModelVersion,RiskScore,CustomerValue,ExpectedValue,ChannelRule,ChannelCost,ProductRules,SuggestedProducts,Explanation,IsSelected,CreatedBy) VALUES\n" + ',\n'.join(
        f"({q(SCEN)},{r.CustomerID},'{C.SCORING_DATE}',{q(V_NB)},{r.RiskScore:.6f},{r.v:.4f},{r.EV_k:.4f},{q(r.KenhRule)},{r.c_k:.2f},{q(r.QuyTacSP) if r.QuyTacSP else 'NULL'},{q(r.SanPhamGoiY) if r.SanPhamGoiY else 'NULL'},{q(r.GiaiThich)},1,N'DSS kịch bản cơ sở')" for r in part.itertuples()) + ';')
sql3 = hdr + f"""/* CUM6_03 – Danh sách chăm sóc kịch bản cơ sở theo kênh: {len(dsach)} khách, Z = {Zk:,.0f} USD */
IF EXISTS (SELECT 1 FROM analytics.CareRecommendation WHERE ScenarioID={q(SCEN)}) THROW 56004, N'Kịch bản đã có.', 1;
BEGIN TRANSACTION;
""" + '\n'.join(chunks) + f"""
COMMIT TRANSACTION;
SELECT ChannelRule, COUNT(*) AS SoKhach, SUM(ChannelCost) AS ChiPhi, SUM(ExpectedValue) AS Z FROM analytics.CareRecommendation WHERE ScenarioID={q(SCEN)} GROUP BY ChannelRule ORDER BY ChannelRule;
PRINT N'CUM6_03_OK: {len(dsach)} khuyến nghị.';
"""
open(f'{R}/CUM6_03_CareRecommendation.sql', 'w', encoding='utf-8-sig').write(sql3)
sql4 = f"""USE [CompanyX_DW];
SET NOCOUNT ON;
/* CUM6_04 – Kiểm tra chỉ đọc. Mong đợi: {len(sc)} khách có nhóm, 5 nhóm, 9 quy tắc, {len(dsach)} khuyến nghị, Z ≈ {Zk:,.0f} */
SELECT COUNT(*) AS KhachCoNhom, COUNT(DISTINCT ClusterID) AS SoNhom FROM analytics.CustomerSegment WHERE SnapshotDate='{C.SCORING_DATE}';
SELECT s.ClusterName, COUNT(*) AS SoKhach, AVG(r.RiskScore) AS RiskScore_TB, SUM(CASE WHEN r.RiskLevel=N'Cao' THEN 1 ELSE 0 END) AS SoCao
FROM analytics.CustomerSegment s JOIN analytics.CustomerRiskScore r ON r.CustomerID=s.CustomerID AND r.ScoreDate=s.SnapshotDate GROUP BY s.ClusterName ORDER BY s.ClusterName;
SELECT COUNT(*) AS SoQuyTac, SUM(CAST(IsActive AS INT)) AS DangBat FROM analytics.CareRule;
SELECT ScenarioID, COUNT(*) AS SoKhach, SUM(ChannelCost) AS ChiPhi, SUM(ExpectedValue) AS Z FROM analytics.CareRecommendation GROUP BY ScenarioID;
-- Màn hình 2: hồ sơ một khách (ví dụ {int(dsach.CustomerID.iloc[0])})
SELECT r.CustomerID, s.ClusterName, s.ABCClass, r.RiskScore, r.RiskLevel, r.TreeScore, c.ChannelRule, c.SuggestedProducts, c.ExpectedValue
FROM analytics.CustomerRiskScore r JOIN analytics.CustomerSegment s ON s.CustomerID=r.CustomerID AND s.SnapshotDate=r.ScoreDate
LEFT JOIN analytics.CareRecommendation c ON c.CustomerID=r.CustomerID AND c.ScenarioID={q(SCEN)} WHERE r.CustomerID={int(dsach.CustomerID.iloc[0])};
"""
open(f'{R}/CUM6_04_Verify_READ_ONLY.sql', 'w', encoding='utf-8-sig').write(sql4)
open(f'{ROOT}/sql/RESET_DSS.sql', 'w', encoding='utf-8-sig').write(f"""/* RESET_DSS.sql – Xoá kết quả cụm 6 (khuyến nghị, phân nhóm, quy tắc, đăng ký K-means) để chạy lại CUM6_01..03. Không chạm điểm rủi ro. */
USE [CompanyX_DW];
SET NOCOUNT ON; SET XACT_ABORT ON; SET QUOTED_IDENTIFIER ON;
BEGIN TRANSACTION;
DELETE FROM analytics.CareRecommendation; DELETE FROM analytics.CustomerSegment; DELETE FROM analytics.CareRule;
DELETE FROM analytics.ModelRegistry WHERE ModelRole=N'CLUSTERING';
COMMIT TRANSACTION;
PRINT N'Đã xoá kết quả cụm 6. Điểm rủi ro và Snapshot giữ nguyên.';
""")
log(f'\nĐã sinh: dss_khach.csv ({len(sc)} dòng), CUM6_01..04.sql, sql/RESET_DSS.sql. Mong đợi khi chạy: 5 nhóm, 9 quy tắc, {len(dsach)} khuyến nghị, Z = {Zk:,.0f} USD.')

# ---------- 8. tự kiểm (dừng nếu sai) và tóm tắt số cho hướng dẫn ----------
assert len(sc) == sc.CustomerID.nunique() == len(score), 'Mỗi khách phải đúng một dòng'
assert (sc.ABC == score.set_index('CustomerID').loc[sc.CustomerID, 'ABC'].values).all(), 'Hạng ABC của cụm 6 phải trùng hạng dùng để tính RiskPercentile ở cụm 5'
assert sorted(sc.Nhom.unique()) == ['N1', 'N2', 'N3', 'N4', 'N5'], 'Phải đủ 5 nhóm N1–N5'
assert sc.c_k.values[sel].sum() <= B_ and (sc.EV_k.values[sel] > 0).all(), 'Danh sách theo kênh phải trong ngân sách và EV > 0'
assert Zip is None or abs(Zip - Zk) < 1, 'Tham lam và quy hoạch nguyên phải cho cùng Z'
ab = abc.to_dict('index'); hsd = hs.to_dict('index'); kn = kenh.to_dict('index')
tom = dict(n=int(len(sc)), g=G, v_median=round(float(sc.v.median()), 1), v_duoi_cr=round(float((sc.v < C_ / R_).mean()), 4),
           abc={k: dict(n=int(v['so_khach']), ty_le=float(v['ty_le_khach']), ty_trong_M=float(v['ty_trong_M'])) for k, v in ab.items()},
           hopkins=round(float(np.mean(H)), 3), k=K, sil=float(kt.loc[kt.k == K, 'Silhouette'].iloc[0]), ari=[round(float(a_), 3) for a_ in aris], ari_ward=round(float(ari_w), 3),
           nhom={k: dict(n=int(v['so_khach']), ty_le=float(v['ty_le']), R=float(v['R_trung_vi']), F=float(v['F_trung_binh']), M=float(v['M_trung_vi']), ty_trong_M=float(v['ty_trong_M']), A=int(v['hang_A']), ty_le_Cao=float(v['ty_le_Cao']),
                         EV_duong=float(v['ty_le_EV_duong']), chon=int(v['duoc_chon_kenh'])) for k, v in hsd.items()},
           ma_tran={a_: {lv_: int(mx.loc[a_, lv_]) for lv_ in mx.columns} for a_ in mx.index},
           luat=[dict(q=r.quy_tac, A=r.A, B=r.B, sup=float(r.support), conf=float(r.confidence), lift=float(r.lift), ok=bool(r.chap_nhan)) for r in ar.itertuples()], da_danh_muc=round(float((baskets.apply(len) >= 2).mean()), 4),
           base=dict(Z=round(base['Z']), K=int(base['K']), n_pos=int(base['n_pos']), giu=round(base['giu_lai_ky_vong'], 1)), r_be=round(r_be, 4), r_100k=round(r_100k, 4),
           what_if={r.kich_ban: dict(Z=int(r.Z), K=int(r.K), C=int(r.C)) for r in wi.itertuples()}, do_nhay={f'{r.tham_so} {r.thay_doi}': float(r.delta_pct) for r in sens.itertuples()},
           payoff={int(r.B): dict(r2=int(r._3), r10=int(r._4), r20=int(r._5), kv=int(r.gia_tri_ky_vong)) for r in pf.itertuples()}, mo_phong={k_: round(v_, 4) for k_, v_ in sim.items()},
           du_bao={r.chi_so: dict(mape=float(r.MAPE_04_05), mape_nen=float(r.MAPE_nen_04_05), lech6=float(r.lech_thang_6)) for r in fc.itertuples()},
           kenh=dict(R3=int((chan == 'R3').sum()), R4=int((chan == 'R4').sum()), R5=int((chan == 'R5').sum()), R2_loai=int((~ok).sum()), Z=round(Zk), so=int(len(sel)), chi=round(float(sc.c_k.values[sel].sum())),
                     chon={k: int(v['duoc_chon']) for k, v in kn.items()}, Zpv=round(Zpv), so_pv=int(len(sel2)), hon_pv=round((Zk - Zpv) / Zpv, 4), co_sp=round(float((dsach.QuyTacSP != '').mean()), 4),
                     R4_ev_duong=int(((chan == 'R4') & ok.values).sum()), R4_evc_max=round(float((sc.EV_k / sc.c_k)[(chan == 'R4') & ok.values].max()), 3), evc_cat=round(float((sc.EV_k / sc.c_k).values[sel].min()), 3)),
           ds_id=int(dsach.CustomerID.iloc[0]))
json.dump(tom, open(f'{R}/tom_tat.json', 'w'), ensure_ascii=False, indent=1)
log('Tự kiểm: đạt (mỗi khách một dòng, hạng ABC trùng cụm 5, đủ 5 nhóm, danh sách trong ngân sách, tham lam = quy hoạch nguyên).')
open(f'{R}/cum6_ket_qua.md', 'w').write('\n'.join(out))
