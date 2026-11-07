# -*- coding: utf-8 -*-
"""CỤM 6B – Các phân tích DSS mà Chương 3 hẹn trình bày ở Chương 4 (bổ sung ngày 03/11/2026).
  1. Khai phá luật kết hợp bằng Apriori với ngưỡng support/confidence (3.5.5, Lecture 5 slide 84) → bang_4_4_apriori_*.csv
  2. Độ nhạy ngưỡng ABC 70%/90% so với 80%/95% (3.5.3)                                         → bang_4_4_abc_do_nhay.csv
  3. Quy mô nhóm không mua lại và phần chi tiêu liên quan (3.5.1)                                → bang_4_4_quy_mo_y1.csv
  4. Số đơn và giá trị đơn khi khách quay lại trong 90 ngày (3.5.2)                               → bang_4_4_khi_quay_lai.csv
  5. Tỷ lệ lợi nhuận gộp g theo nhóm sản phẩm (3.5.2)                                             → bang_4_4_g_theo_nhom.csv
Đầu vào: data/*.csv, results/cum6/dss_khach.csv, results/cum6/tom_tat.json.  Đầu ra: results/cum6b/*.csv, cum6b_ket_qua.md, tom_tat.json
Chạy:    python python/phan_tich/cum6b_bo_sung_chuong3.py   (dưới 1 phút)"""
import os, sys, json, itertools, warnings
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
from models_def import abc_class, pct_within_class
warnings.filterwarnings('ignore')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); D = f'{ROOT}/data'; R = f'{ROOT}/results/cum6b'; R6 = f'{ROOT}/results/cum6'
os.makedirs(R, exist_ok=True); out = []; tom = {}
def log(s=''): print(s, flush=True); out.append(s)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
E0 = pd.Timestamp(C.SCORING_DATE); G = C.GROSS_MARGIN; B_ = C.BASE_SCENARIO['B']
orders = pd.read_csv(f'{D}/orders.csv', header=None, names=['SalesOrderID', 'CustomerID', 'OrderDate', 'ShipDate', 'SubTotal', 'TaxAmt', 'Freight', 'TotalDue', 'TerritoryID'], parse_dates=['OrderDate', 'ShipDate'])
lines = pd.read_csv(f'{D}/lines.csv', header=None, names=['SalesOrderID', 'SalesOrderDetailID', 'ProductID', 'Category', 'Subcategory', 'OrderQty', 'UnitPrice', 'UnitPriceDiscount', 'LineTotal'])
lines = lines.merge(orders[['SalesOrderID', 'CustomerID', 'OrderDate', 'ShipDate']], on='SalesOrderID')
ds = pd.read_csv(f'{D}/dataset.csv', parse_dates=['T'])
k = pd.read_csv(f'{R6}/dss_khach.csv'); t6 = json.load(open(f'{R6}/tom_tat.json'))
log(f'# Cụm 6B – Phân tích DSS bổ sung theo lời hẹn của Chương 3, mốc {C.SCORING_DATE}\n')

# ---------- 1. Apriori trên giỏ danh mục con tích luỹ của từng khách (cùng giỏ với Bảng 3.29) ----------
MIN_SUP, MIN_CONF = 0.01, 0.20     # support 1% theo ví dụ Lecture 5 slide 13, confidence 20%: cứ 5 khách mua A có 1 khách mua B, đủ để làm gợi ý trong nội dung chăm sóc
pl = lines[(lines.OrderDate < E0) & (lines.ShipDate < E0)]
baskets = pl.groupby('CustomerID').Subcategory.apply(frozenset); N = len(baskets); BL = list(baskets)
def support(itemsets):
    cnt = dict.fromkeys(itemsets, 0)
    for b in BL:
        for s in itemsets:
            if s <= b: cnt[s] += 1
    return {s: c / N for s, c in cnt.items()}
items = sorted({x for b in BL for x in b}); Lk = {s_: v for s_, v in support([frozenset([i]) for i in items]).items() if v >= MIN_SUP}
freq = dict(Lk); size = {1: len(Lk)}; k_ = 1
while Lk:
    prev = list(Lk); cand = {a | b for a, b in itertools.combinations(prev, 2) if len(a | b) == k_ + 1}
    cand = [c for c in cand if all(frozenset(sub) in Lk for sub in itertools.combinations(c, k_))]      # bước cắt tỉa Apriori: mọi tập con phải phổ biến
    Lk = {s: v for s, v in support(cand).items() if v >= MIN_SUP}; k_ += 1
    if Lk: size[k_] = len(Lk); freq.update(Lk)
rules = []
for s, sup in freq.items():
    if len(s) < 2: continue
    for r in range(1, len(s)):
        for A in map(frozenset, itertools.combinations(sorted(s), r)):
            Bset = s - A; conf = sup / freq[A]; lift = conf / freq[Bset]
            rules.append(dict(A=' + '.join(sorted(A)), B=' + '.join(sorted(Bset)), so_muc=len(s), support=sup, confidence=conf, lift=lift))
ru = pd.DataFrame(rules); ok = ru[(ru.confidence >= MIN_CONF) & (ru.lift > 1)].sort_values(['lift', 'support'], ascending=False).reset_index(drop=True)
ok.round(4).to_csv(f'{R}/bang_4_4_apriori_luat.csv', index=False)
pd.DataFrame([dict(kich_thuoc=kk, so_tap_pho_bien=v) for kk, v in size.items()]).to_csv(f'{R}/bang_4_4_apriori_tap_pho_bien.csv', index=False)
CAT = lines.drop_duplicates('Subcategory').set_index('Subcategory').Category.to_dict()
ok['ve_phai_phu_kien'] = ok.B.apply(lambda b: all(CAT[x] in ('Accessories', 'Clothing') for x in b.split(' + ')))
pk = ok[ok.ve_phai_phu_kien & (ok.so_muc == 2)].reset_index(drop=True)          # luật dùng được làm gợi ý trong nội dung chăm sóc: một mục mỗi vế, vế phải là phụ kiện hoặc quần áo
pk.round(4).to_csv(f'{R}/bang_4_4_apriori_luat_goi_y.csv', index=False)
cand5 = [('R6', 'Touring Bikes', 'Helmets'), ('R6b', 'Touring Bikes', 'Bottles and Cages'), ('R7', 'Mountain Bikes', 'Fenders'), ('R8', 'Gloves', 'Helmets'), ('R8b', 'Hydration Packs', 'Bottles and Cages')]
pos = []
for q, a, b in cand5:
    m = ok[(ok.A == a) & (ok.B == b)]; m2 = pk[(pk.A == a) & (pk.B == b)]
    s_ab = freq.get(frozenset([a, b]), 0.0); conf_ = s_ab / freq[frozenset([a])] if frozenset([a]) in freq else np.nan; lift_ = conf_ / freq[frozenset([b])] if frozenset([b]) in freq else np.nan
    pos.append(dict(quy_tac=q, A=a, B=b, support=round(s_ab, 4), confidence=round(conf_, 4), lift=round(lift_, 3), co_trong_ket_qua_Apriori=len(m) > 0, hang_trong_moi_luat=int(m.index[0]) + 1 if len(m) else None,
                    hang_trong_luat_goi_y=int(m2.index[0]) + 1 if len(m2) else None))
pos = pd.DataFrame(pos)
# Đối chiếu: cùng 5 luật nhưng giỏ là TỪNG ĐƠN (mua kèm trong một lần thanh toán) thay vì giỏ tích luỹ của khách
ob = pl.groupby('SalesOrderID').Subcategory.agg(frozenset); NO = len(ob); OL = list(ob)
def sup_don(s): return sum(1 for x in OL if s <= x) / NO
for col in ('support_theo_don', 'confidence_theo_don', 'lift_theo_don'): pos[col] = np.nan
for i, (q, a, b) in enumerate(cand5):
    sa, sb, sab = sup_don(frozenset([a])), sup_don(frozenset([b])), sup_don(frozenset([a, b]))
    pos.loc[i, ['support_theo_don', 'confidence_theo_don', 'lift_theo_don']] = [round(sab, 4), round(sab / sa, 4) if sa else np.nan, round(sab / sa / sb, 3) if sa and sb else np.nan]
pos.to_csv(f'{R}/bang_4_4_apriori_doi_chieu.csv', index=False)
log(f'\nCùng 5 luật tính theo giỏ TỪNG ĐƠN ({NO} đơn): ' + ' | '.join(f'{r.quy_tac} sup {r.support_theo_don:.4f} conf {r.confidence_theo_don:.3f} lift {r.lift_theo_don:.2f}' for r in pos.itertuples()))
two = ok[ok.so_muc == 2]
log(f'## 1. Apriori trên {N} giỏ danh mục con tích luỹ (đơn đặt và gửi trước {C.SCORING_DATE}), {len(items)} danh mục con, min support {MIN_SUP:.0%}, min confidence {MIN_CONF:.0%}, lift > 1')
log(f'Tập phổ biến theo kích thước: {size}. Luật đạt ngưỡng: {len(ok)} (luật 2 mục: {len(two)}, luật 3 mục: {len(ok) - len(two)}). Luật confidence ≥ 50%: {int((ok.confidence >= .5).sum())}.')
log('15 luật lift cao nhất:\n' + ok.head(15).round(4).to_string(index=False))
log(f'\nLuật dùng được làm gợi ý (1 mục mỗi vế, vế phải là phụ kiện hoặc quần áo): {len(pk)}.\n' + pk.head(12).round(4).to_string(index=False))
log('\nNăm luật ứng viên Bảng 3.29 trong kết quả Apriori:\n' + pos.to_string(index=False))
tom['apriori'] = dict(N=int(N), so_danh_muc=len(items), min_sup=MIN_SUP, min_conf=MIN_CONF, tap={int(a_): int(b_) for a_, b_ in size.items()}, so_luat=int(len(ok)), so_luat_2=int(len(two)), so_luat_conf50=int((ok.confidence >= .5).sum()), so_luat_goi_y=int(len(pk)),
                      top=[dict(A=r.A, B=r.B, sup=round(r.support, 4), conf=round(r.confidence, 4), lift=round(r.lift, 3)) for r in ok.head(3).itertuples()],
                      top_goi_y=[dict(A=r.A, B=r.B, sup=round(r.support, 4), conf=round(r.confidence, 4), lift=round(r.lift, 3)) for r in pk.head(5).itertuples()],
                      ung_vien={r.quy_tac: dict(co=bool(r.co_trong_ket_qua_Apriori), hang=None if pd.isna(r.hang_trong_moi_luat) else int(r.hang_trong_moi_luat),
                                                hang_goi_y=None if pd.isna(r.hang_trong_luat_goi_y) else int(r.hang_trong_luat_goi_y), lift=float(r.lift), lift_don=float(r.lift_theo_don), conf_don=float(r.confidence_theo_don)) for r in pos.itertuples()},
                      so_don=int(NO))

# ---------- 2. Độ nhạy ngưỡng ABC (3.5.3): 70%/90% so với 80%/95% ----------
CH = C.CHANNELS
def run_abc(a_cut, b_cut):
    m = k.Monetary.values; s = pd.Series(m).sort_values(ascending=False); prev = (s.cumsum() / s.sum()).shift(fill_value=0)
    cls = pd.Series(np.where(prev < a_cut, 'A', np.where(prev < b_cut, 'B', 'C')), index=s.index).reindex(range(len(m))).values
    pct = pct_within_class(k.RiskScore.values, cls, k.Recency.values); cao = pct >= C.RISK_HIGH_PERCENTILE
    chan = np.where((k.Nhom == 'N1') & cao, 'R3', np.where(k.Nhom == 'N3', 'R4', 'R5'))
    c = pd.Series(chan).map({q: v['cost'] for q, v in CH.items()}).values; r = pd.Series(chan).map({q: v['success'] for q, v in CH.items()}).values
    ev = k.RiskScore.values * r * k.v.values - c; okm = ev > 0; order = np.argsort(-np.where(okm, ev / c, -np.inf)); cum = np.cumsum(c[order]); sel = order[(cum <= B_) & okm[order]]
    cnt = {x: int((cls == x).sum()) for x in 'ABC'}; cao_h = {x: int((cao & (cls == x)).sum()) for x in 'ABC'}
    return dict(nguong=f'{a_cut:.0%} / {b_cut:.0%}', A=cnt['A'], B=cnt['B'], C=cnt['C'], Cao_A=cao_h['A'], Cao_B=cao_h['B'], Cao_C=cao_h['C'], R3_du_dk=int((chan == 'R3').sum()),
                R3_chon=int((chan[sel] == 'R3').sum()), R5_chon=int((chan[sel] == 'R5').sum()), so_chon=int(len(sel)), Z=round(float(ev[sel].sum())), chi=round(float(c[sel].sum()))), cls
base, cls80 = run_abc(.80, .95); alt, cls70 = run_abc(.70, .90)
assert base['Z'] == t6['kenh']['Z'] and base['so_chon'] == t6['kenh']['so'], f'Không tái lập được kịch bản theo kênh của cụm 6: {base}'
dn = pd.DataFrame([base, alt]); dn['chenh_Z'] = dn.Z - base['Z']; dn['khach_doi_hang'] = [0, int((cls70 != cls80).sum())]
dn.to_csv(f'{R}/bang_4_4_abc_do_nhay.csv', index=False)
log(f'\n## 2. Độ nhạy ngưỡng ABC (thiết kế 80%/95% so với 70%/90%)\n' + dn.to_string(index=False))
tom['abc_do_nhay'] = {r['nguong']: {kk: (int(v) if isinstance(v, (int, np.integer)) else v) for kk, v in r.items() if kk != 'nguong'} for r in dn.to_dict('records')}

# ---------- 3. Quy mô nhóm y = 1 và phần chi tiêu liên quan (3.5.1), tại 19 mốc có nhãn ----------
lab = ds[ds.label_complete == 1].copy(); lab['v'] = G * lab.AOV
qm = lab.groupby('T').apply(lambda d: pd.Series(dict(so_khach=len(d), ty_le_y1=d.y.mean(), ty_trong_Monetary_y1=d.Monetary[d.y == 1].sum() / d.Monetary.sum(), ty_trong_v_y1=d.v[d.y == 1].sum() / d.v.sum())))
qm.index = qm.index.strftime('%d/%m/%Y'); qm = qm.round(4); qm.to_csv(f'{R}/bang_4_4_quy_mo_y1.csv')
last = qm.iloc[-1]
log(f'\n## 3. Quy mô nhóm không mua lại trong 90 ngày (y = 1) và phần chi tiêu liên quan, 19 mốc có nhãn\n' + qm.tail(6).to_string() + f'\nTrung bình 19 mốc: y = 1 chiếm {qm.ty_le_y1.mean():.1%} số khách và {qm.ty_trong_Monetary_y1.mean():.1%} tổng Monetary.')
tom['quy_mo_y1'] = dict(ty_le=round(float(qm.ty_le_y1.mean()), 4), ty_trong_M=round(float(qm.ty_trong_Monetary_y1.mean()), 4), moc_cuoi=qm.index[-1], ty_le_cuoi=float(last.ty_le_y1), ty_trong_M_cuoi=float(last.ty_trong_Monetary_y1))

# ---------- 4. Khi khách quay lại trong 90 ngày (y = 0): số đơn và giá trị đơn so với AOV trước đó (3.5.2) ----------
rows = []
for T, d in lab.groupby('T'):
    back = d[d.y == 0]; w = orders[(orders.OrderDate >= T) & (orders.OrderDate < T + pd.Timedelta(days=C.LABEL_DAYS)) & orders.CustomerID.isin(back.CustomerID)]
    g = w.groupby('CustomerID').agg(so_don=('SalesOrderID', 'size'), gia_tri_TB=('SubTotal', 'mean')).join(back.set_index('CustomerID').AOV)
    rows.append(dict(T=T.strftime('%d/%m/%Y'), khach_quay_lai=len(g), so_don_TB=g.so_don.mean(), ty_le_1_don=(g.so_don == 1).mean(), ty_le_2_don=(g.so_don == 2).mean(), ty_le_3_don_tro_len=(g.so_don >= 3).mean(),
                     gia_tri_don_quay_lai_TB=g.gia_tri_TB.mean(), AOV_truoc_TB=g.AOV.mean(), ty_so_trung_vi=(g.gia_tri_TB / g.AOV).median(), ty_so_tong=(g.gia_tri_TB * g.so_don).sum() / (g.AOV * g.so_don).sum()))
ql = pd.DataFrame(rows).round(4); ql.to_csv(f'{R}/bang_4_4_khi_quay_lai.csv', index=False)
wq = (ql.khach_quay_lai * ql.so_don_TB).sum() / ql.khach_quay_lai.sum()
log(f'\n## 4. Khách quay lại trong 90 ngày: số đơn và giá trị đơn (19 mốc)\n' + ql.tail(6).to_string(index=False) +
    f'\nTrung bình có trọng số 19 mốc: {wq:.2f} đơn mỗi khách quay lại, {np.average(ql.ty_le_1_don, weights=ql.khach_quay_lai):.1%} chỉ một đơn. Trung vị tỷ số giá trị đơn quay lại / AOV trước: {np.average(ql.ty_so_trung_vi, weights=ql.khach_quay_lai):.2f}.')
tom['quay_lai'] = dict(so_don=round(float(wq), 3), mot_don=round(float(np.average(ql.ty_le_1_don, weights=ql.khach_quay_lai)), 4), ty_so_tv=round(float(np.average(ql.ty_so_trung_vi, weights=ql.khach_quay_lai)), 3),
                       gia_tri_quay_lai=round(float(np.average(ql.gia_tri_don_quay_lai_TB, weights=ql.khach_quay_lai)), 1), aov_truoc=round(float(np.average(ql.AOV_truoc_TB, weights=ql.khach_quay_lai)), 1))

# ---------- 5. g theo nhóm sản phẩm (giá vốn ProductCostHistory tại ngày đặt) ----------
cost = pd.read_csv(f'{D}/cost.csv', header=None, names=['SalesOrderID', 'SalesOrderDetailID', 'ProductID', 'OrderQty_c', 'StandardCost'])
lc = lines.merge(cost[['SalesOrderID', 'SalesOrderDetailID', 'StandardCost']], on=['SalesOrderID', 'SalesOrderDetailID'], how='left')
assert lc.StandardCost.notna().all() and len(lc) == len(lines), 'Thiếu giá vốn cho một số dòng'
lc['gia_von'] = lc.StandardCost * lc.OrderQty
gt = lc.groupby('Category').agg(so_dong=('LineTotal', 'size'), doanh_thu=('LineTotal', 'sum'), gia_von=('gia_von', 'sum')); gt.loc['Toàn bộ'] = gt.sum()
gt['g'] = 1 - gt.gia_von / gt.doanh_thu; gt['ty_trong_doanh_thu'] = gt.doanh_thu / gt.loc['Toàn bộ', 'doanh_thu']; gt = gt.round(4); gt.to_csv(f'{R}/bang_4_4_g_theo_nhom.csv')
assert abs(gt.loc['Toàn bộ', 'g'] - G) < 5e-4, f'g toàn bộ {gt.loc["Toàn bộ", "g"]} khác config {G}'
log(f'\n## 5. Tỷ lệ lợi nhuận gộp g theo nhóm sản phẩm ({len(lines)} dòng trong phạm vi)\n' + gt.to_string())
# ảnh hưởng nếu dùng g theo nhóm thay cho g chung: v_i = Σ_nhóm g_nhóm × phần doanh thu nhóm của khách × AOV
mix = lc[(lc.OrderDate < E0) & (lc.ShipDate < E0)].pivot_table(index='CustomerID', columns='Category', values='LineTotal', aggfunc='sum').fillna(0)
gk = (mix * gt.g.drop('Toàn bộ')).sum(1) / mix.sum(1); kk = k.set_index('CustomerID'); v2 = gk.reindex(kk.index).values * kk.AOV.values
p, v1 = kk.RiskScore.values, kk.v.values
def zbase(v):
    r_, c_ = C.BASE_SCENARIO['r'], C.BASE_SCENARIO['c']; ev = p * r_ * v - c_; o = np.argsort(-(p * v)); K = min(int(B_ // c_), int((ev > 0).sum())); return float(ev[o[:K]].sum()), o[:K]
z1, s1 = zbase(v1); z2, s2 = zbase(v2); trung = len(set(s1) & set(s2)) / len(s1)
log(f'Nếu dùng g theo nhóm thay cho g chung ở kịch bản cơ sở: Z {z1:,.0f} → {z2:,.0f} USD ({(z2 - z1) / z1:+.1%}), {trung:.1%} khách trong danh sách giữ nguyên.')
tom['g_nhom'] = dict(g={c: float(gt.loc[c, 'g']) for c in gt.index}, ty_trong={c: float(gt.loc[c, 'ty_trong_doanh_thu']) for c in gt.index}, Z_chung=round(z1), Z_nhom=round(z2), trung=round(trung, 4))

# ---------- 5b. Độ nhạy: trừ phần khách "chưa đến kỳ" khỏi lợi ích (khách y = 1 theo 90 ngày nhưng tự mua lại trong ngày 90–180) ----------
o = json.load(open(f'{ROOT}/results/cum4b/tom_tat.json', encoding='utf-8'))['nhan180']['chua_den_ky']
c0, Kb, Zb0 = C.BASE_SCENARIO['c'], t6['base']['K'], t6['base']['Z']; loi_ich = Zb0 + c0 * Kb            # r·Σ p·v trên danh sách cơ sở
Z_o = (1 - o) * loi_ich - c0 * Kb; r_be_o = t6['r_be'] / (1 - o)
log(f'\n## 5b. Nếu {o:.1%} khách "không mua lại" thực ra sẽ tự quay lại trong ngày 90–180 (không nhờ chăm sóc): Z cơ sở {Zb0:,.0f} → {Z_o:,.0f} USD, r hoà vốn {t6["r_be"]:.2%} → {r_be_o:.2%}.')
tom['chua_den_ky'] = dict(o=round(o, 4), Z=round(Z_o), r_be=round(r_be_o, 4))
# ---------- 5c. Ngân sách tối thiểu để kênh R4 (nhóm N3) bắt đầu được chọn ----------
okk = k.EV_k > 0; ratio = (k.EV_k / k.c_k).where(okk); order_ = ratio.sort_values(ascending=False).dropna().index
cum_c = k.c_k.loc[order_].cumsum(); first_r4 = next((i for i in order_ if k.KenhRule[i] == 'R4'), None)
B_r4 = float(cum_c.loc[first_r4]) if first_r4 is not None else None
log(f'## 5c. Kênh R4 (N3) chỉ có khách được chọn khi ngân sách từ khoảng {B_r4:,.0f} USD trở lên (xếp theo EV trên chi phí).')
tom['R4_ngan_sach'] = round(B_r4) if B_r4 else None

# ---------- 6. Bảng gộp các đại lượng đo từ dữ liệu cho mô hình giá trị kỳ vọng (3.5.1, 3.5.2) ----------
tq = tom['quay_lai']; qy = tom['quy_mo_y1']; gg = tom['g_nhom']
def vn(x, d=0): return f'{x:,.{d}f}'.replace(',', '#').replace('.', ',').replace('#', '.')
def pv(x, d=1): return vn(100 * x, d) + '%'
tsd = pd.DataFrame([
    ('Tỷ lệ lợi nhuận gộp g, toàn bộ', vn(gg["g"]["Toàn bộ"], 4), 'Giá vốn ProductCostHistory tại ngày đặt, ' + vn(len(lines)) + ' dòng trong phạm vi', '3.5.2'),
    ('g của Bikes / Accessories / Clothing', f'{vn(gg["g"]["Bikes"], 3)} / {vn(gg["g"]["Accessories"], 3)} / {vn(gg["g"]["Clothing"], 3)}', f'Bikes chiếm {pv(gg["ty_trong"]["Bikes"])} doanh thu', '3.5.2'),
    ('Z kịch bản cơ sở nếu dùng g theo nhóm', f'{vn(gg["Z_nhom"])} USD (g chung {vn(gg["Z_chung"])} USD)', f'{pv(gg["trung"])} khách trong danh sách giữ nguyên', '3.5.2'),
    ('Tỷ lệ khách không mua lại trong 90 ngày (y = 1)', pv(qy["ty_le"]), 'Trung bình 19 mốc có nhãn', '3.5.1'),
    ('Tỷ trọng Monetary của khách y = 1', pv(qy["ty_trong_M"]), 'Trung bình 19 mốc có nhãn', '3.5.1'),
    ('Số đơn trung bình của khách quay lại trong 90 ngày', vn(tq["so_don"], 2), f'{pv(tq["mot_don"])} chỉ đặt một đơn', '3.5.2'),
    ('Giá trị đơn khi quay lại so với AOV trước đó (trung vị tỷ số)', vn(tq["ty_so_tv"], 2), f'Trung bình {vn(tq["gia_tri_quay_lai"])} USD so với {vn(tq["aov_truoc"])} USD', '3.5.2, 3.5.4'),
    ('Khách có v < c/r = 100 USD tại mốc chấm điểm', pv(t6["v_duoi_cr"]), 'Khách loại "B" ở mục 3.5.2: chăm sóc riêng không bù được chi phí', '3.5.2'),
    ('Z cơ sở nếu trừ khách chưa đến kỳ khỏi lợi ích', f'{vn(Z_o)} USD (r hoà vốn {pv(r_be_o, 2)})', f'{pv(o)} khách y = 1 theo nhãn 90 ngày tự mua lại trong ngày 90–180', '3.4.1, 3.5.4'),
    ('Ngân sách để kênh R4 (nhóm N3) bắt đầu có khách', f'khoảng {vn(B_r4)} USD', 'Dưới mức này lợi trên mỗi USD của khách N3 thấp hơn khách khác', '3.5.4'),
], columns=['dai_luong', 'gia_tri', 'ghi_chu', 'muc_chuong_3'])
tsd.to_csv(f'{R}/bang_4_4_tham_so_do_duoc.csv', index=False); log('\n## 6. Các đại lượng của mô hình giá trị kỳ vọng đo từ dữ liệu\n' + tsd.to_string(index=False))
json.dump(tom, open(f'{R}/tom_tat.json', 'w'), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
open(f'{R}/cum6b_ket_qua.md', 'w').write('\n'.join(out))
