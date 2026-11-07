"""Chuẩn hoá bước 5: huấn luyện các mô hình Bảng 3.14 trên 4 fold Bảng 3.12 với dữ liệu đọc từ kho,
chấm 3 điều kiện mục 3.4.6 theo từng mốc, quyết định MLP hay NB, kiểm tra ổn định seed.
Chạy sau labels_checks.py: ../.venv/bin/python models_check.py"""
import pandas as pd, numpy as np, os, warnings, json
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.naive_bayes import CategoricalNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, brier_score_loss, average_precision_score
warnings.filterwarnings('ignore')
H = os.path.dirname(os.path.abspath(__file__)); D = f'{H}/data'; R = f'{H}/results'
out = []
def log(s=''): print(s, flush=True); out.append(s)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)

snap = pd.read_csv(f'{D}/snapshot.csv', header=None, names=['CustomerID','T','CustomerKey','Recency','Frequency','Monetary','Orders90','Orders180','Tenure','Share_Bikes','Share_Accessories','Share_Clothing','NSub'], parse_dates=['T'])
lab = pd.read_csv(f'{R}/labels.csv', parse_dates=['T'])
orders = pd.read_csv(f'{D}/orders.csv', header=None, names=['SalesOrderID','CustomerID','OrderDate','ShipDate','SubTotal','TaxAmt','Freight','TotalDue','TerritoryID'], parse_dates=['OrderDate','ShipDate'])
snap = snap.merge(lab, on=['CustomerID', 'T'])
snap['BikeBuyer'] = (snap.Share_Bikes > 0.5).astype(int)
# AOV (SubTotal trung bình các đơn trước T) cho v = g·AOV
aov = []
for T in snap['T'].unique():
    past = orders[(orders.OrderDate < T) & (orders.ShipDate < T)].groupby('CustomerID').SubTotal.mean().rename('AOV').reset_index(); past['T'] = T; aov.append(past)
snap = snap.merge(pd.concat(aov), on=['CustomerID', 'T'])
G = 0.4115  # từ cost.csv (ProductCostHistory tại ngày đặt), xem labels/g trong biên bản
R_, C_, B_ = 0.10, 10.0, 40000.0
ALL = ['Recency', 'Frequency', 'Monetary', 'Orders90', 'Orders180', 'Tenure', 'Share_Bikes', 'Share_Accessories', 'Share_Clothing', 'BikeBuyer', 'NSub']
PAIRS = [(pd.Timestamp(e), pd.Timestamp(t)) for e, t in [('2013-12-15', '2013-09-01'), ('2014-01-15', '2013-10-01'), ('2014-02-15', '2013-11-01'), ('2014-03-01', '2013-11-15')]]
def get(T): return snap[snap['T'] == T].reset_index(drop=True)

# ---------- mô hình ----------
class SK:
    def __init__(self, est, scale=False): self.est, self.scale = est, scale
    def fit(self, df):
        self.m = make_pipeline(StandardScaler(), self.est) if self.scale else self.est; self.m.fit(df[ALL].values, df.y.values); return self
    def predict(self, df): return self.m.predict_proba(df[ALL].values)[:, 1]
class GiniTree:
    def __init__(self, depth=4, leaf=400, m=50): self.m = m; self.clf = DecisionTreeClassifier(criterion='gini', max_depth=depth, min_samples_leaf=leaf, random_state=0)
    def fit(self, df):
        X, y = df[ALL].values, df.y.values; self.clf.fit(X, y); self.pi = y.mean(); leaf = self.clf.apply(X)
        n = pd.Series(leaf).value_counts(); n1 = pd.Series(leaf[y == 1]).value_counts().reindex(n.index).fillna(0)
        self.p_leaf = ((n1 + self.m * self.pi) / (n + self.m)).to_dict(); return self
    def predict(self, df): return np.array([self.p_leaf[l] for l in self.clf.apply(df[ALL].values)])
def discretize(df, qM=None):
    d = pd.DataFrame(index=df.index)
    d['R'] = pd.cut(df.Recency, [-1, 89, 179, 269, 364, 539, 10**6], labels=False); d['F'] = pd.cut(df.Frequency, [0, 1, 2, 10**6], labels=False)
    if qM is None: qM = df.Monetary.quantile([.25, .5, .75]).values
    d['M'] = np.searchsorted(qM, df.Monetary.values); d['B'] = df.BikeBuyer.values; d['N'] = pd.cut(df.NSub, [-1, 1, 2, 4, 10**6], labels=False)
    return d, qM
class NB:
    def fit(self, df): X, self.qM = discretize(df); self.clf = CategoricalNB(alpha=1, min_categories=[6, 3, 4, 2, 4]).fit(X.values, df.y.values); return self
    def predict(self, df): return self.clf.predict_proba(discretize(df, self.qM)[0].values)[:, 1]
class LR:
    def fit(self, df):
        X, self.qM = discretize(df); self.enc = OneHotEncoder(handle_unknown='ignore').fit(X.values); self.clf = LogisticRegression(C=1.0, max_iter=1000).fit(self.enc.transform(X.values), df.y.values); return self
    def predict(self, df): return self.clf.predict_proba(self.enc.transform(discretize(df, self.qM)[0].values))[:, 1]
class Majority:
    def fit(self, df): self.pi = df.y.mean(); return self
    def predict(self, df): return np.full(len(df), self.pi)
class RecencyRev:
    def fit(self, df): self.sign = 1 if roc_auc_score(df.y, df.Recency) >= 0.5 else -1; return self
    def predict(self, df): return pd.Series(self.sign * df.Recency.values).rank(pct=True).values
def mlp(seed): return SK(MLPClassifier((32, 16), max_iter=300, early_stopping=True, random_state=seed), scale=True)
MODELS = {'MLP (32,16)': lambda: mlp(0), 'Cây Gini sâu 4, lá 400': lambda: GiniTree(), 'Naive Bayes rời rạc': lambda: NB(), 'Logistic one-hot': lambda: LR(),
          'Lớp đa số': lambda: Majority(), 'Recency đảo chiều': lambda: RecencyRev(),
          'Random Forest 300': lambda: SK(RandomForestClassifier(300, min_samples_leaf=50, n_jobs=-1, random_state=0)),
          'Gradient boosting': lambda: SK(HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=300, random_state=0)),
          'kNN k=200': lambda: SK(KNeighborsClassifier(200), scale=True)}

def boot_auc_diff(y, p1, p2, n=500, seed=0):
    rng = np.random.default_rng(seed); d = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max(): continue
        d.append(roc_auc_score(y[i], p1[i]) - roc_auc_score(y[i], p2[i]))
    return np.percentile(d, [2.5, 97.5])
def Z_policy(ev, score, by_v_only=False):
    """Z theo chính sách 3.5.4: xếp theo p·v (hoặc v), lấy K = min(B/c, số khách EV>0), Z = Σ r·y·v − c·K."""
    v = G * ev.AOV.values; y = ev.y.values
    if by_v_only: order = np.argsort(-v); K = int(B_ // C_)
    else:
        order = np.argsort(-(score * v)); evi = score[order] * R_ * v[order] - C_; K = min(int(B_ // C_), int((evi > 0).sum()))
    sel = order[:K]; return R_ * (y[sel] * v[sel]).sum() - C_ * K, K

# ---------- vòng 4 fold ----------
log('# Kiểm định mô hình trên 4 fold Bảng 3.12 (dữ liệu từ CompanyX_DW)\n')
log(f'g = {G}, r = {R_}, c = {C_}, B = {B_:.0f}. Đặc trưng: {ALL}\n')
rows = []; preds_all = {}
for E, T in PAIRS:
    tr, ev = get(T), get(E); y = ev.y.values; pi = tr.y.mean(); brier_const = brier_score_loss(y, np.full(len(y), pi))
    zv, Kv = Z_policy(ev, None, by_v_only=True)
    P = {k: mk().fit(tr).predict(ev) for k, mk in MODELS.items()}; preds_all[E] = P
    for k, p in P.items():
        ci = boot_auc_diff(y, p, P['Recency đảo chiều']) if k != 'Recency đảo chiều' else (0, 0)
        z, K = Z_policy(ev, p)
        rows.append(dict(E=E.date(), T=T.date(), model=k, n=len(ev), pi_train=round(pi, 4), y_rate=round(y.mean(), 4), auc=roc_auc_score(y, p), brier=brier_score_loss(y, p), brier_const=brier_const,
                         ap1=average_precision_score(y, p), ci_lo=ci[0], ci_hi=ci[1], Z=z, K=K, Z_vonly=zv, K_vonly=Kv,
                         dk1=ci[1] >= 0, dk2=brier_score_loss(y, p) < brier_const, dk3=z > zv))
res = pd.DataFrame(rows); res.to_csv(f'{R}/folds.csv', index=False)
main = ['MLP (32,16)', 'Naive Bayes rời rạc', 'Cây Gini sâu 4, lá 400', 'Logistic one-hot', 'Recency đảo chiều', 'Lớp đa số']
log('## 1. Theo từng mốc: 3 điều kiện mục 3.4.6\n')
show = res[res.model.isin(main)][['E', 'model', 'auc', 'brier', 'brier_const', 'ci_lo', 'ci_hi', 'Z', 'K', 'Z_vonly', 'dk1', 'dk2', 'dk3']].copy()
for c in ['auc', 'brier', 'brier_const', 'ci_lo', 'ci_hi']: show[c] = show[c].round(4)
show['Z'] = show['Z'].round(0); show['Z_vonly'] = show['Z_vonly'].round(0)
log(show.to_string(index=False))
log('\n## 2. Trung bình 4 mốc (tất cả mô hình, kể cả bổ sung)\n')
agg = res.groupby('model')[['auc', 'brier', 'ap1', 'Z']].mean().round(4).sort_values('auc', ascending=False)
agg['dk1_dat'] = res.groupby('model').dk1.sum(); agg['dk2_dat'] = res.groupby('model').dk2.sum(); agg['dk3_dat'] = res.groupby('model').dk3.sum()
log(agg.to_string())
# so sánh MLP với NB theo Z từng mốc (luật hòa 3.4.6)
log('\n## 3. MLP so với Naive Bayes theo Z từng mốc (luật chọn: Z cao hơn ở nhiều mốc hơn)\n')
mz = res[res.model == 'MLP (32,16)'].set_index('E').Z; nz = res[res.model == 'Naive Bayes rời rạc'].set_index('E').Z
cmp = pd.DataFrame({'Z_MLP': mz.round(0), 'Z_NB': nz.round(0), 'MLP_thang': mz > nz}); log(cmp.to_string())
log(f'\nMLP thắng {int(cmp.MLP_thang.sum())}/4 mốc, NB thắng {int((~cmp.MLP_thang).sum())}/4 mốc. Chênh lệch Z trung bình (MLP − NB) = {(mz - nz).mean():.0f} USD ({(mz - nz).mean() / nz.mean():+.2%}).')
# ---------- ổn định seed cho MLP ----------
log('\n## 4. Ổn định MLP theo seed (AUC, Brier, Z từng mốc, seed 0..4)\n')
srows = []
for s in range(5):
    for E, T in PAIRS:
        tr, ev = get(T), get(E); p = mlp(s).fit(tr).predict(ev); z, K = Z_policy(ev, p)
        srows.append(dict(seed=s, E=E.date(), auc=roc_auc_score(ev.y, p), brier=brier_score_loss(ev.y, p), Z=z))
sd = pd.DataFrame(srows); piv = sd.pivot(index='seed', columns='E', values='auc').round(4); log('AUC:\n' + piv.to_string())
log('\nZ:\n' + sd.pivot(index='seed', columns='E', values='Z').round(0).to_string())
log(f'\nĐộ lệch chuẩn AUC theo seed (trung bình các mốc): {sd.groupby("E").auc.std().mean():.4f}; Z: {sd.groupby("E").Z.std().mean():.0f} USD')
# ---------- chấm điểm 08/07/2014 bằng mô hình học ở 01/03/2014 ----------
log('\n## 5. Chấm điểm mốc 08/07/2014 (học ở 01/03/2014)\n')
tr, sc = get(pd.Timestamp('2014-03-01')), get(pd.Timestamp('2014-07-08'))
for k in ['MLP (32,16)', 'Naive Bayes rời rạc', 'Cây Gini sâu 4, lá 400']:
    p = MODELS[k]().fit(tr).predict(sc); pct = pd.Series(p).rank(pct=True) * 100
    log(f'  {k}: n={len(sc)}, RiskScore trung vị {np.median(p):.3f}, P75 {np.percentile(p, 75):.3f}, tỷ lệ Cao (percentile>=75) {(pct >= 75).mean():.3f}, khách có v<c/r=100: {(G * sc.AOV < 100).mean():.1%}')
tree = GiniTree().fit(tr); log('\nCây đối chứng học ở 01/03/2014:\n```\n' + export_text(tree.clf, feature_names=ALL, max_depth=4) + '```')
leaf = pd.DataFrame({'leaf': tree.clf.apply(tr[ALL].values), 'y': tr.y}).groupby('leaf').y.agg(['count', 'mean']).round(3); leaf['p_m'] = [round(tree.p_leaf[l], 3) for l in leaf.index]
log(f'Số lá: {len(leaf)}\n' + leaf.to_string())
# cờ lệch TreeScore vs RiskScore > 0.3
pm = MODELS['MLP (32,16)']().fit(tr).predict(sc); pt = tree.predict(sc)
log(f'\nKhách tại 08/07/2014 có |TreeScore − RiskScore(MLP)| > 0,3: {(abs(pm - pt) > 0.3).sum()} / {len(sc)} ({(abs(pm - pt) > 0.3).mean():.1%})')
open(f'{R}/models_check.md', 'w').write('\n'.join(out))
