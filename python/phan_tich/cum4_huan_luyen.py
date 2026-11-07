"""CỤM 4 – Huấn luyện và so sánh mô hình (Bảng 3.14, 3.15) trên 4 fold Bảng 3.12, ba điều kiện mục 3.4.6.
Đầu vào: data/dataset.csv (từ cum3b). Đầu ra: results/cum4/*.csv|png|md, models/*.joblib (mô hình học ở mốc 01/03/2014).
Chạy:    python python/phan_tich/cum4_huan_luyen.py
Mô hình chấm điểm: Naive Bayes (3.4.5). Cây Gini: mô hình đối chứng. MLP, LR, lớp đa số, Recency đảo chiều: so sánh.
RF, gradient boosting, kNN: bổ sung ngoài nội dung môn học."""
import os, sys, json, time, warnings
import pandas as pd, numpy as np, joblib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
from sklearn.neural_network import MLPClassifier
from sklearn.tree import export_text
from sklearn.naive_bayes import CategoricalNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, brier_score_loss, average_precision_score, roc_curve, precision_recall_curve, confusion_matrix
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); D = f'{ROOT}/data'; R = f'{ROOT}/results/cum4'; M = f'{ROOT}/models'
os.makedirs(R, exist_ok=True); os.makedirs(M, exist_ok=True)
out = []
def log(s=''): print(s, flush=True); out.append(s)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)

ds = pd.read_csv(f'{D}/dataset.csv', parse_dates=['T'])
G = C.GROSS_MARGIN; R_, C_, B_ = C.BASE_SCENARIO['r'], C.BASE_SCENARIO['c'], C.BASE_SCENARIO['B']
ALL = C.FEATURES
def get(T): return ds[ds['T'] == pd.Timestamp(T)].reset_index(drop=True)

# ---------- mô hình (định nghĩa dùng chung ở models_def.py) ----------
from models_def import SK, GiniTree, discretize, NB, LR, Majority, RecencyRev
def mlp(seed=C.RANDOM_STATE, arch=(32, 16)): return SK(MLPClassifier(arch, max_iter=300, early_stopping=True, random_state=seed), scale=True)
ROLE = {'Naive Bayes rời rạc': 'Mô hình chấm điểm', 'Cây Gini sâu 4, lá 400': 'Mô hình đối chứng', 'MLP (32,16)': 'So sánh', 'Logistic one-hot': 'So sánh', 'Lớp đa số': 'Mốc so sánh', 'Recency đảo chiều': 'Mốc so sánh',
        'Random Forest 300': 'Bổ sung ngoài nội dung môn học', 'Gradient boosting': 'Bổ sung ngoài nội dung môn học', 'kNN k=200': 'Bổ sung ngoài nội dung môn học'}
MODELS = {'Naive Bayes rời rạc': lambda: NB(), 'Cây Gini sâu 4, lá 400': lambda: GiniTree(), 'MLP (32,16)': lambda: mlp(), 'Logistic one-hot': lambda: LR(), 'Lớp đa số': lambda: Majority(), 'Recency đảo chiều': lambda: RecencyRev(),
          'Random Forest 300': lambda: SK(RandomForestClassifier(300, min_samples_leaf=50, n_jobs=-1, random_state=C.RANDOM_STATE)),
          'Gradient boosting': lambda: SK(HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=300, random_state=C.RANDOM_STATE)),
          'kNN k=200': lambda: SK(KNeighborsClassifier(200), scale=True)}

def boot_auc_diff(y, p1, p2, n=500, seed=C.RANDOM_STATE):
    rng = np.random.default_rng(seed); d = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max(): continue
        d.append(roc_auc_score(y[i], p1[i]) - roc_auc_score(y[i], p2[i]))
    return np.percentile(d, [2.5, 97.5])
def Z_policy(ev, score, by='pv'):
    """Z theo chính sách 3.5.4 (Bảng 3.17): xếp theo p·v (hoặc v, p), K = min(B/c, số khách EV > 0), Z = Σ r·y·v − c·K."""
    v = G * ev.AOV.values; y = ev.y.values
    if by == 'v': order = np.argsort(-v); K = int(B_ // C_)
    elif by == 'p': order = np.argsort(-score); evi = score[order] * R_ * v[order] - C_; K = min(int(B_ // C_), int((evi > 0).sum()))
    elif by == 'oracle': order = np.lexsort((-v, -y)); K = min(int(B_ // C_), int(y.sum()))
    else: order = np.argsort(-(score * v)); evi = score[order] * R_ * v[order] - C_; K = min(int(B_ // C_), int((evi > 0).sum()))
    sel = order[:K]; return R_ * (y[sel] * v[sel]).sum() - C_ * K, K
def youden(y, p):
    fpr, tpr, thr = roc_curve(y, p); return thr[np.argmax(tpr - fpr)]

t0 = time.time()
log('# Cụm 4 – Huấn luyện và so sánh mô hình\n')
log(f'Cấu hình: đặc trưng {ALL}, fold {C.FOLDS}, g = {G}, kịch bản cơ sở r = {R_}, c = {C_}, B = {B_:.0f}, random_state = {C.RANDOM_STATE}')
log('Naive Bayes: CategoricalNB alpha = 1 trên 5 thuộc tính rời rạc Bảng 3.10. Cây: gini, depth 4, min_samples_leaf 400, m = 50. MLP: (32,16) relu adam, early_stopping, z-score fit trên mốc huấn luyện.\n')

# ---------- 1. vòng 4 fold ----------
rows = []; preds = {}; roots = []
for E, T in C.FOLDS:
    tr, ev = get(T), get(E); y = ev.y.values; pi = tr.y.mean(); bc = brier_score_loss(y, np.full(len(y), pi))
    zv, Kv = Z_policy(ev, None, 'v'); zo, Ko = Z_policy(ev, None, 'oracle')
    P = {k: mk().fit(tr).predict(ev) for k, mk in MODELS.items()}; preds[E] = (ev, P)
    tree = GiniTree().fit(tr); roots.append((T, E) + tree.root())
    for k, p in P.items():
        ci = boot_auc_diff(y, p, P['Recency đảo chiều']) if k != 'Recency đảo chiều' else (0.0, 0.0)
        z, K = Z_policy(ev, p); zp, Kp = Z_policy(ev, p, 'p')
        rows.append(dict(vai_tro=ROLE[k], mo_hinh=k, E=E, T=T, n=len(ev), pi_train=round(pi, 4), y_rate=round(y.mean(), 4), AUC=roc_auc_score(y, p), Brier=brier_score_loss(y, p), Brier_hang_so=bc,
                         AP=average_precision_score(y, p), CI_lo=ci[0], CI_hi=ci[1], Z_pv=z, K=K, Z_p=zp, Z_v=zv, Z_oracle=zo, DK1=ci[1] >= 0, DK2=brier_score_loss(y, p) < bc, DK3=z > zv))
res = pd.DataFrame(rows); res.to_csv(f'{R}/bang_4_3_2a_theo_fold.csv', index=False)
log('## 1. Kết quả theo từng fold (Bảng 4.3.2a)\n' + res[['mo_hinh', 'E', 'AUC', 'Brier', 'Brier_hang_so', 'CI_lo', 'CI_hi', 'Z_pv', 'Z_v', 'DK1', 'DK2', 'DK3']].round(4).to_string(index=False))

agg = res.groupby(['vai_tro', 'mo_hinh'], sort=False).agg(AUC=('AUC', 'mean'), Brier=('Brier', 'mean'), AP=('AP', 'mean'), Z_pv=('Z_pv', 'mean'), DK1=('DK1', 'sum'), DK2=('DK2', 'sum'), DK3=('DK3', 'sum')).reset_index()
agg['Z_v'] = res.Z_v.mean(); agg['Z_oracle'] = res.Z_oracle.mean()
agg = agg.sort_values('AUC', ascending=False).round(4); agg.to_csv(f'{R}/bang_4_3_2b_trung_binh.csv', index=False)
log('\n## 2. Trung bình 4 fold và số fold đạt từng điều kiện (Bảng 4.3.2b)\n' + agg.to_string(index=False))
nb = res[res.mo_hinh == 'Naive Bayes rời rạc'].set_index('E'); ml = res[res.mo_hinh == 'MLP (32,16)'].set_index('E')
cmp = pd.DataFrame({'Z_NB': nb.Z_pv.round(0), 'Z_MLP': ml.Z_pv.round(0), 'NB_cao_hon': nb.Z_pv > ml.Z_pv}); cmp.to_csv(f'{R}/bang_4_3_2c_nb_vs_mlp.csv')
log('\n## 3. Luật hòa 3.4.6: Z theo mốc, Naive Bayes so với MLP\n' + cmp.to_string() + f'\nNB cao hơn ở {int(cmp.NB_cao_hon.sum())}/4 mốc, chênh trung bình {(nb.Z_pv - ml.Z_pv).mean():.0f} USD ({(nb.Z_pv - ml.Z_pv).mean() / ml.Z_pv.mean():+.2%}).')

# ---------- 2. cấu hình so sánh Bảng 3.15: cây và MLP ----------
log('\n## 4. So sánh cấu hình (Bảng 3.15), trung bình 4 fold')
def run_cfg(make, mode='latest'):
    a, b, z = [], [], []
    for E, T in C.FOLDS:
        ev = get(E); tr = get(T) if mode == 'latest' else get(C.FOLDS[0][1]) if mode == 'first' else ds[(ds.label_complete == 1) & (ds['T'] <= pd.Timestamp(T))].reset_index(drop=True)
        p = make().fit(tr).predict(ev); a.append(roc_auc_score(ev.y, p)); b.append(brier_score_loss(ev.y, p)); z.append(Z_policy(ev, p)[0])
    return np.mean(a), np.mean(b), np.mean(z)
cfg_rows = []
for name, mk, mode in [('NB, học mốc gần nhất (thiết kế)', NB, 'latest'), ('NB, học một lần ở mốc đầu', NB, 'first'), ('NB, gộp mọi mốc đủ nhãn', NB, 'pooled'),
                       ('Cây sâu 3', lambda: GiniTree(depth=3), 'latest'), ('Cây sâu 4 (thiết kế)', GiniTree, 'latest'), ('Cây sâu 5', lambda: GiniTree(depth=5), 'latest'), ('Cây sâu 6', lambda: GiniTree(depth=6), 'latest'),
                       ('Cây lá 200', lambda: GiniTree(leaf=200), 'latest'), ('Cây lá 800', lambda: GiniTree(leaf=800), 'latest'), ('Cây m = 0', lambda: GiniTree(m=0), 'latest'), ('Cây m = 200', lambda: GiniTree(m=200), 'latest'),
                       ('MLP (16,)', lambda: mlp(arch=(16,)), 'latest'), ('MLP (32,16)', mlp, 'latest'), ('MLP (64,32)', lambda: mlp(arch=(64, 32)), 'latest')]:
    a, b, z = run_cfg(mk, mode); cfg_rows.append(dict(cau_hinh=name, AUC=round(a, 4), Brier=round(b, 4), Z=round(z)))
    log(f'  {name:36s} AUC={a:.4f} Brier={b:.4f} Z={z:,.0f}')
pd.DataFrame(cfg_rows).to_csv(f'{R}/bang_4_3_2d_cau_hinh.csv', index=False)
log('\nGốc cây và số lá qua các mốc (T, E, thuộc tính gốc, ngưỡng, số lá):'); [log('  ' + str(r)) for r in roots]
srows = []
for s in range(3):
    for E, T in C.FOLDS:
        p = mlp(seed=s).fit(get(T)).predict(get(E)); srows.append(dict(seed=s, E=E, AUC=roc_auc_score(get(E).y, p), Z=Z_policy(get(E), p)[0]))
sd = pd.DataFrame(srows); sd.to_csv(f'{R}/bang_4_3_2e_mlp_seed.csv', index=False)
log('\nMLP theo 3 hạt giống (AUC):\n' + sd.pivot(index='seed', columns='E', values='AUC').round(4).to_string() + f'\nĐộ lệch chuẩn AUC theo seed, trung bình các mốc: {sd.groupby("E").AUC.std().mean():.4f}')

# ---------- 3. mô hình cuối: học ở 01/03/2014, lưu, chấm 08/07/2014 ----------
tr, sc = get(C.SCORING_TRAIN_DATE), get(C.SCORING_DATE)
nb_final = NB().fit(tr); tree_final = GiniTree().fit(tr); mlp_final = mlp().fit(tr)
joblib.dump(nb_final, f'{M}/nb_T{C.SCORING_TRAIN_DATE.replace("-", "")}.joblib'); joblib.dump(tree_final, f'{M}/tree_T{C.SCORING_TRAIN_DATE.replace("-", "")}.joblib'); joblib.dump(mlp_final, f'{M}/mlp_T{C.SCORING_TRAIN_DATE.replace("-", "")}.joblib')
p_nb, p_tree, p_mlp = nb_final.predict(sc), tree_final.predict(sc), mlp_final.predict(sc)
thr = youden(tr.y.values, nb_final.predict(tr))
log(f'\n## 5. Mô hình cuối học ở {C.SCORING_TRAIN_DATE} (π = {tr.y.mean():.4f}), chấm điểm {C.SCORING_DATE} (n = {len(sc)})')
log(f'  Ngưỡng Youden của NB trên mốc huấn luyện: {thr:.4f}. RiskScore NB: trung vị {np.median(p_nb):.3f}, P25 {np.percentile(p_nb, 25):.3f}, P75 {np.percentile(p_nb, 75):.3f}')
log(f'  Khách |TreeScore − RiskScore| > {C.TREE_FLAG_GAP}: {(abs(p_nb - p_tree) > C.TREE_FLAG_GAP).sum()} ({(abs(p_nb - p_tree) > C.TREE_FLAG_GAP).mean():.1%})')
log('\nCây đối chứng (luật IF-THEN):\n```\n' + export_text(tree_final.clf, feature_names=ALL, max_depth=4) + '```')
leaf = pd.DataFrame({'leaf': tree_final.clf.apply(tr[ALL].values), 'y': tr.y}).groupby('leaf').y.agg(['count', 'mean']).round(3); leaf['TreeScore_m50'] = [round(tree_final.p_leaf[l], 3) for l in leaf.index]
leaf.to_csv(f'{R}/bang_4_3_2f_la_cay.csv'); log('Lá cây (số khách, tỷ lệ y = 1 thô, TreeScore sau m-estimate):\n' + leaf.to_string())
# bảng xác suất có điều kiện của NB (để trình bày và lưu ModelRegistry)
nbtab = {name: np.exp(nb_final.clf.feature_log_prob_[i]).round(4).tolist() for i, name in enumerate(['Recency', 'Frequency', 'Monetary', 'BikeBuyer', 'NSub'])}
json.dump(dict(class_prior=np.exp(nb_final.clf.class_log_prior_).round(4).tolist(), monetary_quartiles=[float(v) for v in nb_final.qM], cond_prob=nbtab), open(f'{R}/nb_bang_xac_suat.json', 'w'), indent=1)
log('Đã lưu bảng xác suất có điều kiện NB: results/cum4/nb_bang_xac_suat.json')

# ---------- 4. hình: ROC, PR, ma trận nhầm lẫn ở fold cuối, phân bố điểm ----------
E, T = C.FOLDS[-1]; ev, P = preds[E]; y = ev.y.values
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6), dpi=150)
for k in ['Naive Bayes rời rạc', 'MLP (32,16)', 'Cây Gini sâu 4, lá 400', 'Recency đảo chiều', 'Logistic one-hot']:
    fpr, tpr, _ = roc_curve(y, P[k]); ax[0].plot(fpr, tpr, label=f'{k} (AUC {roc_auc_score(y, P[k]):.3f})')
    pr, rc, _ = precision_recall_curve(y, P[k]); ax[1].plot(rc, pr, label=f'{k} (AP {average_precision_score(y, P[k]):.3f})')
ax[0].plot([0, 1], [0, 1], 'k--', lw=0.8); ax[0].set_xlabel('Tỷ lệ dương tính giả'); ax[0].set_ylabel('Tỷ lệ dương tính thật'); ax[0].set_title(f'ROC tại mốc {E}'); ax[0].legend(fontsize=7)
ax[1].axhline(y.mean(), color='k', ls='--', lw=0.8); ax[1].set_xlabel('Recall'); ax[1].set_ylabel('Precision'); ax[1].set_title(f'Precision–Recall tại mốc {E}'); ax[1].legend(fontsize=7)
plt.tight_layout(); plt.savefig(f'{R}/hinh_4_3_2_roc_pr.png', facecolor='white'); plt.close()
thr_nb = youden(get(T).y.values, NB().fit(get(T)).predict(get(T))); cm = confusion_matrix(y, (P['Naive Bayes rời rạc'] >= thr_nb).astype(int), labels=[1, 0])
fig, ax = plt.subplots(figsize=(4.2, 3.8), dpi=150); ax.imshow(cm, cmap='Blues')
for i in range(2):
    for j in range(2): ax.text(j, i, f'{cm[i, j]:,}', ha='center', va='center', fontsize=12, color='white' if cm[i, j] > cm.max() / 2 else 'black')
ax.set_xticks([0, 1]); ax.set_yticks([0, 1]); ax.set_xticklabels(['Dự đoán y = 1', 'Dự đoán y = 0']); ax.set_yticklabels(['Thật y = 1', 'Thật y = 0']); ax.set_title(f'Naive Bayes, ngưỡng Youden {thr_nb:.3f}, mốc {E}', fontsize=9)
plt.tight_layout(); plt.savefig(f'{R}/hinh_4_3_2_ma_tran_nham_lan.png', facecolor='white'); plt.close()
tn, fp, fn, tp = cm[1, 1], cm[1, 0], cm[0, 1], cm[0, 0]
log(f'\nMa trận nhầm lẫn NB tại {E} (ngưỡng Youden {thr_nb:.3f} chọn trên mốc huấn luyện): TP {tp}, FP {fp}, FN {fn}, TN {tn}, accuracy {(tp + tn) / len(y):.3f}, sensitivity {tp / (tp + fn):.3f}, specificity {tn / (tn + fp):.3f}, precision {tp / (tp + fp):.3f}')
fig, ax = plt.subplots(figsize=(7, 3.8), dpi=150)
ax.hist(p_nb, bins=40, alpha=0.7, label='Naive Bayes'); ax.hist(p_mlp, bins=40, alpha=0.5, label='MLP (so sánh)'); ax.axvline(np.percentile(p_nb, 75), color='r', ls='--', label='P75 của NB (ngưỡng RiskLevel Cao)')
ax.set_xlabel('RiskScore tại 08/07/2014'); ax.set_ylabel('Số khách'); ax.legend(fontsize=8); plt.tight_layout(); plt.savefig(f'{R}/hinh_4_3_2_phan_bo_diem.png', facecolor='white'); plt.close()
log(f'\nThời gian chạy: {time.time() - t0:.0f} giây. Hình: hinh_4_3_2_roc_pr.png, hinh_4_3_2_ma_tran_nham_lan.png, hinh_4_3_2_phan_bo_diem.png')
open(f'{R}/cum4_ket_qua.md', 'w').write('\n'.join(out))
