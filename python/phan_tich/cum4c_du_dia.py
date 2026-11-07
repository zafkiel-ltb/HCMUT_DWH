"""CỤM 4C – Dư địa cải tiến mô hình (Chương 7): mô hình chấm điểm còn cách trần bao xa, dữ liệu nguồn chưa dùng có giúp không, lift theo decile.
Đầu vào:  data/dataset.csv (cum3b), data/orders.csv, data/lines.csv, và hai trích xuất bổ sung từ CSDL nguồn CompanyX:
          data/khach_nhan_khau.csv (Sales.vPersonDemographics + Person.EmailPromotion + TerritoryID của khách cá nhân)
          data/don_ly_do.csv       (Sales.SalesOrderHeader + lý do mua SalesOrderHeaderSalesReason + CurrencyRateID)
          Nếu nối được CSDL nguồn (config.connect hoặc pymssql với SQL_PASSWORD) thì trích lại hai file này, không thì dùng file sẵn có.
Đầu ra:   results/cum4c/*.csv, cum4c_ket_qua.md. Không ghi models/, không đụng results/cum4.
Chạy:     .venv/bin/python python/phan_tich/cum4c_du_dia.py
Mọi phép tính Z dùng đúng chính sách 3.5.4 như cum4_huan_luyen.py (xếp theo p·v, K = min(B/c, số khách EV > 0))."""
import os, sys, json, time, warnings
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
from models_def import NB, discretize
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss
warnings.filterwarnings('ignore')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); D = f'{ROOT}/data'; R = f'{ROOT}/results/cum4c'; os.makedirs(R, exist_ok=True)
out = []
def log(s=''): print(s, flush=True); out.append(s)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
G = C.GROSS_MARGIN; R_, C_, B_ = C.BASE_SCENARIO['r'], C.BASE_SCENARIO['c'], C.BASE_SCENARIO['B']; ALL = C.FEATURES
NGAN_SACH = [20000, 40000, 60000, 100000]          # các mức B xét ở Bảng 7 (40.000 là kịch bản cơ sở)
GB_CFG = dict(max_depth=4, learning_rate=0.05, max_iter=300, random_state=C.RANDOM_STATE)   # cùng cấu hình gradient boosting của cum4

# ---------- 0. trích xuất bổ sung từ CSDL nguồn (nếu nối được) ----------
SQL_KHACH = """SELECT c.CustomerID, c.TerritoryID, d.BirthDate, d.MaritalStatus, d.YearlyIncome, d.Gender, d.TotalChildren, d.NumberChildrenAtHome,
                      d.Education, d.Occupation, d.HomeOwnerFlag, d.NumberCarsOwned, p.EmailPromotion
               FROM Sales.Customer c JOIN Person.Person p ON p.BusinessEntityID = c.PersonID
               LEFT JOIN Sales.vPersonDemographics d ON d.BusinessEntityID = c.PersonID WHERE c.StoreID IS NULL"""
SQL_DON = """SELECT h.SalesOrderID, h.CustomerID, h.OrderDate, h.CurrencyRateID,
                    (SELECT STRING_AGG(CONVERT(varchar, sr.SalesReasonID), ',') FROM Sales.SalesOrderHeaderSalesReason sr WHERE sr.SalesOrderID = h.SalesOrderID) AS ly_do
             FROM Sales.SalesOrderHeader h JOIN Sales.Customer c ON c.CustomerID = h.CustomerID AND c.StoreID IS NULL"""
def trich_nguon():
    con = None
    try: con = C.connect(C.SOURCE_DATABASE)
    except Exception:
        try:
            import pymssql; host = C.SQL_SERVER.split(',')[0]; port = int(C.SQL_SERVER.split(',')[1]) if ',' in C.SQL_SERVER else 1433
            con = pymssql.connect(host, C.SQL_USER or 'sa', C.SQL_PASSWORD, C.SOURCE_DATABASE, port=port, login_timeout=10)
        except Exception as e: log(f'Không nối CSDL nguồn ({str(e)[:80]}), dùng data/khach_nhan_khau.csv và data/don_ly_do.csv sẵn có.'); return
    pd.read_sql(SQL_KHACH, con).to_csv(f'{D}/khach_nhan_khau.csv', index=False); pd.read_sql(SQL_DON, con).to_csv(f'{D}/don_ly_do.csv', index=False); log('Đã trích lại hai file bổ sung từ CSDL nguồn.')
trich_nguon()

# ---------- 1. dữ liệu và đặc trưng bổ sung ----------
ds = pd.read_csv(f'{D}/dataset.csv', parse_dates=['T'])
orders = pd.read_csv(f'{D}/orders.csv', header=None, names=['SalesOrderID', 'CustomerID', 'OrderDate', 'ShipDate', 'SubTotal', 'TaxAmt', 'Freight', 'TotalDue', 'TerritoryID'], parse_dates=['OrderDate', 'ShipDate'])
lines = pd.read_csv(f'{D}/lines.csv', header=None, usecols=[0, 3, 7], names=['SalesOrderID', 'Category', 'Discount'])
kh = pd.read_csv(f'{D}/khach_nhan_khau.csv', parse_dates=['BirthDate']); dl = pd.read_csv(f'{D}/don_ly_do.csv')
od = lines.groupby('SalesOrderID').agg(co_xe=('Category', lambda s: int((s == 'Bikes').any())), giam_gia=('Discount', lambda s: int((s > 0).any())))
dl['ly_do'] = dl.ly_do.fillna('').astype(str); L = dl.ly_do.str.split(',')
dl['khuyen_mai'] = L.apply(lambda x: int('2' in x)); dl['quang_cao'] = L.apply(lambda x: int(any(i in x for i in ['3', '4', '7', '8']))); dl['khong_ly_do'] = (dl.ly_do == '').astype(int); dl['ngoai_te'] = dl.CurrencyRateID.notna().astype(int)
orders = orders.merge(od, left_on='SalesOrderID', right_index=True, how='left').merge(dl[['SalesOrderID', 'khuyen_mai', 'quang_cao', 'khong_ly_do', 'ngoai_te']], on='SalesOrderID', how='left').fillna(0)
kh['thu_nhap'] = kh.YearlyIncome.map({'0-25000': 0, '25001-50000': 1, '50001-75000': 2, '75001-100000': 3, 'greater than 100000': 4})
kh['hoc_van'] = kh.Education.str.strip().map({'Partial High School': 0, 'High School': 1, 'Partial College': 2, 'Bachelors': 3, 'Graduate Degree': 4})
kh['nghe'] = kh.Occupation.map({'Manual': 0, 'Skilled Manual': 1, 'Clerical': 2, 'Professional': 3, 'Management': 4})
kh['nha_rieng'] = kh.HomeOwnerFlag.astype(str).str.lower().isin(['true', '1']).astype(int); kh['ket_hon'] = (kh.MaritalStatus == 'M').astype(int); kh['nam'] = (kh.Gender == 'M').astype(int)
NHAN_KHAU = ['thu_nhap', 'hoc_van', 'nghe', 'NumberCarsOwned', 'TotalChildren', 'NumberChildrenAtHome', 'nha_rieng', 'ket_hon', 'nam', 'EmailPromotion', 'TerritoryID', 'tuoi']
HANH_VI = ['xe_lan_cuoi', 'ngay_tu_mua_xe', 'khuyen_mai_lan_cuoi', 'ty_le_khuyen_mai', 'ty_le_quang_cao', 'khong_ly_do_lan_cuoi', 'tung_giam_gia', 'khoang_cach_TB', 'xu_huong_tien', 'ngoai_te', 'so_don_xe']
TEN_DT = {'TerritoryID': 'Vùng bán hàng', 'ngoai_te': 'Có đơn ngoại tệ', 'xe_lan_cuoi': 'Đơn gần nhất có xe đạp', 'khong_ly_do_lan_cuoi': 'Đơn gần nhất không ghi lý do mua', 'so_don_xe': 'Số đơn có xe đạp',
          'khoang_cach_TB': 'Khoảng cách trung bình giữa các đơn', 'thu_nhap': 'Thu nhập', 'nghe': 'Nghề nghiệp', 'xu_huong_tien': 'Tiền đơn gần nhất / trung bình', 'TotalChildren': 'Số con', 'hoc_van': 'Học vấn',
          'ty_le_khuyen_mai': 'Tỷ lệ đơn mua vì khuyến mãi', 'khuyen_mai_lan_cuoi': 'Đơn gần nhất mua vì khuyến mãi', 'nha_rieng': 'Có nhà riêng', 'nam': 'Giới tính nam', 'NumberChildrenAtHome': 'Số con ở nhà',
          'ty_le_quang_cao': 'Tỷ lệ đơn mua vì quảng cáo', 'tuoi': 'Tuổi', 'ngay_tu_mua_xe': 'Ngày từ lần mua xe đạp', 'ket_hon': 'Đã kết hôn', 'NumberCarsOwned': 'Số xe hơi', 'EmailPromotion': 'Đăng ký nhận email', 'tung_giam_gia': 'Từng được giảm giá'}

def dac_trung(snapT, T):
    """Đặc trưng tại mốc T chỉ dùng đơn có OrderDate < T và ShipDate < T (cùng quy ước cum3b)."""
    o = orders[(orders.OrderDate < T) & (orders.ShipDate < T)].sort_values('OrderDate'); g = o.groupby('CustomerID'); last = g.last()
    f = pd.DataFrame(index=last.index)
    f['xe_lan_cuoi'] = last.co_xe; f['khuyen_mai_lan_cuoi'] = last.khuyen_mai; f['khong_ly_do_lan_cuoi'] = last.khong_ly_do
    f['ty_le_khuyen_mai'] = g.khuyen_mai.mean(); f['ty_le_quang_cao'] = g.quang_cao.mean(); f['tung_giam_gia'] = g.giam_gia.max(); f['ngoai_te'] = g.ngoai_te.max(); f['so_don_xe'] = g.co_xe.sum()
    lb = o[o.co_xe == 1].groupby('CustomerID').OrderDate.max(); f['ngay_tu_mua_xe'] = (T - lb.reindex(f.index)).dt.days.fillna(9999)
    f['khoang_cach_TB'] = g.OrderDate.apply(lambda s: s.diff().dt.days.mean() if len(s) > 1 else -1); f['xu_huong_tien'] = last.SubTotal / g.SubTotal.mean()
    x = snapT.merge(f, left_on='CustomerID', right_index=True, how='left').merge(kh[['CustomerID'] + [c for c in NHAN_KHAU if c != 'tuoi'] + ['BirthDate']], on='CustomerID', how='left')
    x['tuoi'] = (T - x.BirthDate).dt.days / 365.25; return x.fillna(0)

# ---------- 2. công cụ ----------
def Z_pv(ev, score, B=B_):
    v = G * ev.AOV.values; y = ev.y.values
    order = np.argsort(-(score * v)); evi = score[order] * R_ * v[order] - C_; K = min(int(B // C_), int((evi > 0).sum())); sel = order[:K]
    return R_ * (y[sel] * v[sel]).sum() - C_ * K
def Z_oracle(ev, B=B_):
    v = G * ev.AOV.values; y = ev.y.values; order = np.lexsort((-v, -y)); K = min(int(B // C_), int(y.sum())); sel = order[:K]; return R_ * (y[sel] * v[sel]).sum() - C_ * K
def Z_v(ev, B=B_):
    v = G * ev.AOV.values; y = ev.y.values; order = np.argsort(-v); K = int(B // C_); sel = order[:K]; return R_ * (y[sel] * v[sel]).sum() - C_ * K
def o_cell(df): return pd.cut(df.Recency, C.RECENCY_BINS, labels=False).astype(int) * 2 + (df.Frequency.values >= 2)
def trong_so_dich_chuyen(train, target, clip=(0.2, 5.0)):
    """Trọng số hiệu chỉnh dịch chuyển phân bố: P_mốc đích(ô Recency × Frequency) / P_mốc học(ô). Chỉ dùng đặc trưng của mốc đích, không dùng nhãn."""
    ct, cg = o_cell(train), o_cell(target); pt = pd.Series(ct).value_counts(normalize=True); pg = pd.Series(cg).value_counts(normalize=True)
    return (pg.reindex(pt.index).fillna(0) / pt).clip(*clip).reindex(ct).fillna(1.0).values
def gb(tr, ev, feats, w):
    m = HistGradientBoostingClassifier(**GB_CFG).fit(tr[feats].values, tr.y.values, sample_weight=w); return m.predict_proba(ev[feats].values)[:, 1]
def tran_o(ev, keys): return ev.groupby(keys).y.transform('mean').values     # xác suất = tỷ lệ y=1 thật của ô tại mốc đánh giá

t0 = time.time(); log('# Cụm 4C – Dư địa cải tiến mô hình\n')
log(f'Cấu hình: fold {C.FOLDS}, kịch bản cơ sở r = {R_}, c = {C_}, B = {B_:.0f}, g = {G}. Gradient boosting {GB_CFG}, có trọng số dịch chuyển phân bố (ngoài nội dung môn học).\n')
MH = ['Naive Bayes rời rạc', 'GB 11 thuộc tính + trọng số dịch chuyển', 'GB 11 + nhân khẩu học + hành vi mới', 'Trung bình Naive Bayes và GB đủ']
r_mh, r_B, r_tran, r_lift = [], [], [], []
for E, T in C.FOLDS:
    T_, E_ = pd.Timestamp(T), pd.Timestamp(E)
    tr = dac_trung(ds[ds['T'] == T_].reset_index(drop=True), T_); ev = dac_trung(ds[ds['T'] == E_].reset_index(drop=True), E_); y = ev.y.values; w = trong_so_dich_chuyen(tr, ev)
    P = {MH[0]: NB().fit(tr).predict(ev), MH[1]: gb(tr, ev, ALL, w), MH[2]: gb(tr, ev, ALL + NHAN_KHAU + HANH_VI, w)}; P[MH[3]] = (P[MH[0]] + P[MH[2]]) / 2
    for k, p in P.items():
        r_mh.append(dict(mo_hinh=k, E=E, AUC=roc_auc_score(y, p), Brier=brier_score_loss(y, p), Z_pv=Z_pv(ev, p)))
        for B in NGAN_SACH: r_B.append(dict(mo_hinh=k, E=E, B=B, Z=Z_pv(ev, p, B)))
    for B in NGAN_SACH: r_B.append(dict(mo_hinh='Chỉ theo giá trị v', E=E, B=B, Z=Z_v(ev, B))); r_B.append(dict(mo_hinh='Trần khi biết nhãn', E=E, B=B, Z=Z_oracle(ev, B)))
    # trần theo ô thuộc tính (trong mẫu tại E): sai số học bằng 0, chỉ còn phần ngẫu nhiên trong ô
    _, qM = discretize(tr); Xe, _ = discretize(ev, qM); ev = pd.concat([ev, Xe.add_prefix('o_')], axis=1); ev['o_vung'] = ev.TerritoryID.astype(int); ev['o_xe'] = ev.xe_lan_cuoi.astype(int); ev['o_tn'] = ev.thu_nhap.astype(int)
    r_tran.append(dict(E=E, NB_thuc_te=Z_pv(ev, P[MH[0]]), tran_5_thuoc_tinh=Z_pv(ev, tran_o(ev, ['o_R', 'o_F', 'o_M', 'o_B', 'o_N'])), so_o_5=ev.groupby(['o_R', 'o_F', 'o_M', 'o_B', 'o_N']).ngroups,
                       tran_them_vung=Z_pv(ev, tran_o(ev, ['o_R', 'o_F', 'o_M', 'o_B', 'o_N', 'o_vung'])), tran_them_vung_xe_thunhap=Z_pv(ev, tran_o(ev, ['o_R', 'o_F', 'o_M', 'o_B', 'o_N', 'o_vung', 'o_xe', 'o_tn'])),
                       so_o_8=ev.groupby(['o_R', 'o_F', 'o_M', 'o_B', 'o_N', 'o_vung', 'o_xe', 'o_tn']).ngroups, tran_biet_nhan=Z_oracle(ev)))
    # lift theo decile của Naive Bayes
    p = P[MH[0]]; order = np.argsort(-p); dec = np.empty(len(p), int); dec[order] = np.arange(len(p)) * 10 // len(p)
    for d_ in range(10):
        m = dec == d_; r_lift.append(dict(E=E, decile=d_ + 1, so_khach=int(m.sum()), ty_le_y1=y[m].mean(), lift=y[m].mean() / y.mean(), tich_luy_bat_duoc=y[dec <= d_].sum() / y.sum(), nen=y.mean()))
    log(f'xong fold {E}')

# ---------- 3. bảng ----------
mh = pd.DataFrame(r_mh); agg = mh.groupby('mo_hinh', sort=False).agg(AUC=('AUC', 'mean'), Brier=('Brier', 'mean'), Z_pv=('Z_pv', 'mean')).reset_index()
nbz = mh[mh.mo_hinh == MH[0]].set_index('E').Z_pv; agg['fold_Z_hon_NB'] = [int((mh[mh.mo_hinh == k].set_index('E').Z_pv > nbz).sum()) for k in agg.mo_hinh]
mh.to_csv(f'{R}/bang_7_nguon_theo_fold.csv', index=False); agg.round(4).to_csv(f'{R}/bang_7_nguon_trung_binh.csv', index=False)
log('\n## 1. Dữ liệu nguồn chưa dùng: trung bình 4 fold (Bảng 7 dư địa nguồn)\n' + agg.round(4).to_string(index=False))
zb = pd.DataFrame(r_B).groupby(['mo_hinh', 'B'], sort=False).Z.mean().unstack('B'); zb.to_csv(f'{R}/bang_7_z_ngan_sach.csv')
log('\n## 2. Z trung bình 4 fold theo ngân sách\n' + zb.round(0).to_string())
tran = pd.DataFrame(r_tran); tran.to_csv(f'{R}/bang_7_tran_theo_fold.csv', index=False); tran_tb = tran.drop(columns='E').mean(); tran_tb.to_csv(f'{R}/bang_7_tran_trung_binh.csv', header=['gia_tri'])
log('\n## 3. Trần theo ô thuộc tính (trong mẫu tại mốc đánh giá), trung bình 4 fold\n' + tran_tb.round(1).to_string())
lift = pd.DataFrame(r_lift); lift.to_csv(f'{R}/bang_7_lift_theo_fold.csv', index=False)
lift_tb = lift.groupby('decile').agg(so_khach=('so_khach', 'mean'), ty_le_y1=('ty_le_y1', 'mean'), lift=('lift', 'mean'), tich_luy_bat_duoc=('tich_luy_bat_duoc', 'mean'), nen=('nen', 'mean')).reset_index()
lc = lift[lift.E == C.FOLDS[-1][0]].drop(columns='E'); lc.to_csv(f'{R}/bang_7_lift_moc_cuoi.csv', index=False); lift_tb.round(4).to_csv(f'{R}/bang_7_lift_trung_binh.csv', index=False)
log('\n## 4. Lift theo decile của Naive Bayes tại mốc 01/03/2014\n' + lc.round(4).to_string(index=False) + '\n\nTrung bình 4 fold\n' + lift_tb.round(4).to_string(index=False))
# AUC đơn lẻ của từng đặc trưng mới tại mốc huấn luyện cuối
T_ = pd.Timestamp(C.SCORING_TRAIN_DATE); trc = dac_trung(ds[ds['T'] == T_].reset_index(drop=True), T_)
dl_ = pd.DataFrame([dict(dac_trung=c, ten=TEN_DT.get(c, c), AUC=abs(roc_auc_score(trc.y, trc[c]) - .5) + .5) for c in NHAN_KHAU + HANH_VI]).sort_values('AUC', ascending=False)
dl_.to_csv(f'{R}/bang_7_auc_don_le.csv', index=False); log('\n## 5. AUC đơn lẻ từng đặc trưng bổ sung tại mốc 01/03/2014 (Recency để so: %.3f)\n' % roc_auc_score(trc.y, trc.Recency) + dl_.round(3).to_string(index=False))
nb_, gb_, en_ = [agg.set_index('mo_hinh').loc[k] for k in (MH[0], MH[2], MH[3])]
tom_tat = dict(AUC_NB=round(nb_.AUC, 4), AUC_GB_du=round(gb_.AUC, 4), AUC_trung_binh=round(en_.AUC, 4), Brier_NB=round(nb_.Brier, 4), Brier_trung_binh=round(en_.Brier, 4), Z_NB=round(nb_.Z_pv), Z_trung_binh=round(en_.Z_pv),
               Z_20000_NB=round(zb.loc[MH[0], 20000]), Z_20000_trung_binh=round(zb.loc[MH[3], 20000]), tran_5=round(tran_tb.tran_5_thuoc_tinh), tran_8=round(tran_tb.tran_them_vung_xe_thunhap), tran_nhan=round(tran_tb.tran_biet_nhan),
               ty_le_dat_tran_5=round(nb_.Z_pv / tran_tb.tran_5_thuoc_tinh, 4), phan_ngau_nhien=round((tran_tb.tran_biet_nhan - tran_tb.tran_them_vung_xe_thunhap) / (tran_tb.tran_biet_nhan - nb_.Z_pv), 4),
               lift_decile1_moc_cuoi=round(float(lc[lc.decile == 1].lift.iloc[0]), 4), lift_toi_da=round(1 / float(lc.nen.iloc[0]), 4), so_khach_nhan_khau=int(kh.CustomerID.nunique()))
json.dump(tom_tat, open(f'{R}/tom_tat.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1); log('\n## Tóm tắt\n' + json.dumps(tom_tat, ensure_ascii=False, indent=1))
log(f'\nThời gian: {time.time() - t0:.0f} s'); open(f'{R}/cum4c_ket_qua.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
