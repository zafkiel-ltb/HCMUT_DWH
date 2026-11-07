# -*- coding: utf-8 -*-
"""CỤM 5 – Chấm điểm mốc 08/07/2014 và SINH FILE SQL để ghi vào CompanyX_DW (không cần pyodbc).
Đầu vào: data/dataset.csv (cụm 3B), models/*.joblib (cụm 4).
Đầu ra:  results/cum5/CUM5_01_ModelRegistry.sql, CUM5_02_ModelTreeLeaf.sql, CUM5_03_CustomerRiskScore.sql,
         CUM5_04_Verify_READ_ONLY.sql, bảng/CSV cho 4.3.3–4.3.5, results/cum5/cum5_ket_qua.md
Chạy:    python python/phan_tich/cum5_cham_diem_sinh_sql.py   rồi mở 3 file SQL trong SSMS theo thứ tự 01 → 02 → 03, cuối cùng 04.
Thiết kế: RiskScore = xác suất Naive Bayes, RiskPercentile = thứ hạng phần trăm trong mốc (phá hoà theo Recency giảm dần),
          RiskLevel Cao khi RiskPercentile >= 75 (config.RISK_HIGH_PERCENTILE), TreeScore + TopFactors từ cây đối chứng."""
import os, sys, json, warnings
import pandas as pd, numpy as np, joblib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
from models_def import NB, GiniTree, SK, discretize, abc_class, pct_within_class  # định nghĩa lớp để joblib nạp được
from sklearn.metrics import roc_auc_score, brier_score_loss, average_precision_score, roc_curve
warnings.filterwarnings('ignore')
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'); D = f'{ROOT}/data'; R = f'{ROOT}/results/cum5'; M = f'{ROOT}/models'
os.makedirs(R, exist_ok=True); out = []
def log(s=''): print(s, flush=True); out.append(s)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
T0, E0 = C.SCORING_TRAIN_DATE, C.SCORING_DATE
TAG = T0.replace('-', '')
V_NB, V_TREE, V_MLP = f'NB_T{TAG}_v1', f'TREE_T{TAG}_v1', f'MLP_T{TAG}_v1'
ALL = C.FEATURES

ds = pd.read_csv(f'{D}/dataset.csv', parse_dates=['T'])
tr = ds[ds['T'] == pd.Timestamp(T0)].reset_index(drop=True); sc = ds[ds['T'] == pd.Timestamp(E0)].reset_index(drop=True)
nb = joblib.load(f'{M}/nb_T{TAG}.joblib'); tree = joblib.load(f'{M}/tree_T{TAG}.joblib'); mlp = joblib.load(f'{M}/mlp_T{TAG}.joblib')
folds = pd.read_csv(f'{ROOT}/results/cum4/bang_4_3_2a_theo_fold.csv')
def fold_mean(name, col): return float(folds[folds.mo_hinh == name][col].mean())

# ---------- 1. chấm điểm ----------
p_nb, p_tree, p_mlp = nb.predict(sc), tree.predict(sc), mlp.predict(sc)
leaf_id = tree.clf.apply(sc[ALL].values)
# Hạng ABC tại mốc chấm điểm (3.5.3, công thức 3.19) để tính phân vị TRONG TỪNG HẠNG (thiết kế 3.4.6: rủi ro tương đối so với khách cùng hạng giá trị)
abc = abc_class(sc.Monetary)
pct = pct_within_class(p_nb, abc, sc.Recency.values); level = np.where(pct >= C.RISK_HIGH_PERCENTILE, 'Cao', 'Thấp')
# luật của từng lá cây (đường đi từ gốc)
t = tree.clf.tree_
def leaf_rules():
    rules = {}
    def walk(node, conds):
        if t.feature[node] < 0: rules[node] = conds; return
        f, thr = ALL[t.feature[node]], t.threshold[node]
        walk(t.children_left[node], conds + [f'{f} <= {thr:.2f}']); walk(t.children_right[node], conds + [f'{f} > {thr:.2f}'])
    walk(0, []); return rules
rules = leaf_rules()
leaf_ids = sorted(rules); leaf_no = {l: i + 1 for i, l in enumerate(leaf_ids)}
tr_leaf = tree.clf.apply(tr[ALL].values)
leaf_tab = pd.DataFrame({'LeafID': [leaf_no[l] for l in leaf_ids], 'sk_leaf': leaf_ids,
                         'LeafCount': [int((tr_leaf == l).sum()) for l in leaf_ids], 'PositiveCount': [int(tr.y.values[tr_leaf == l].sum()) for l in leaf_ids],
                         'TreeScore': [round(float(tree.p_leaf[l]), 6) for l in leaf_ids], 'RuleText': [' AND '.join(rules[l]) for l in leaf_ids]})
def topfactors(l):
    r = leaf_tab[leaf_tab.sk_leaf == l].iloc[0]
    return f'Lá {r.LeafID}: {r.RuleText} | nhóm {r.LeafCount} khách, tỷ lệ không mua lại {r.PositiveCount / r.LeafCount:.1%}, TreeScore {r.TreeScore:.3f}'
score = pd.DataFrame({'CustomerID': sc.CustomerID, 'ScoreDate': E0, 'ABC': abc, 'RiskScore': np.round(p_nb, 6), 'RiskPercentile': pct, 'RiskLevel': level,
                      'TreeScore': np.round(p_tree, 6), 'LeafID': [leaf_no[l] for l in leaf_id], 'TopFactors': [topfactors(l) for l in leaf_id],
                      'MLPScore': np.round(p_mlp, 6), 'Recency': sc.Recency, 'Frequency': sc.Frequency, 'Monetary': sc.Monetary, 'AOV': sc.AOV})
score['Flag'] = (abs(score.RiskScore - score.TreeScore) > C.TREE_FLAG_GAP).astype(int)
score.to_csv(f'{R}/customer_risk_score_{TAG}.csv', index=False)
log(f'# Cụm 5 – Chấm điểm {E0} bằng mô hình học ở {T0}\n')
log(f'Khách chấm điểm: {len(score)}. RiskLevel Cao (phân vị 75 trong từng hạng ABC): {(level == "Cao").sum()} ({(level == "Cao").mean():.1%}), theo hạng: ' + str(pd.crosstab(abc, level).to_dict()) + f'. Ngưỡng RiskScore tại phân vị 75 toàn bộ: {np.percentile(p_nb, 75):.4f}. Cờ |TreeScore − RiskScore| > {C.TREE_FLAG_GAP}: {score.Flag.sum()} ({score.Flag.mean():.1%}).')

# ---------- 2. bảng cho 4.3.3: Lớp 1 ở các ngưỡng mục 3.4.6 hứa, Lớp 2 và 3 (Bảng 3.16) tại fold cuối ----------
E, T = C.FOLDS[-1]; ev = ds[ds['T'] == pd.Timestamp(E)].reset_index(drop=True); trf = ds[ds['T'] == pd.Timestamp(T)].reset_index(drop=True)
def get(d): return ds[ds['T'] == pd.Timestamp(d)].reset_index(drop=True)
def youden_thr(yy, pp): fpr, tpr, thr = roc_curve(yy, pp); return float(thr[np.argmax(tpr - fpr)])
nbf = NB().fit(trf); p = nbf.predict(ev); y = ev.y.values
youden = youden_thr(trf.y.values, nbf.predict(trf))                                  # (a) chọn trên chính mốc huấn luyện 15/11/2013
T1, T2 = '2013-08-01', '2013-11-15'                                                  # (b) ngoài mẫu: học ở T1, dự đoán T2, nhãn T2 đã đủ trước E
assert pd.Timestamp(T1) + pd.Timedelta(days=C.LABEL_LAG_DAYS) <= pd.Timestamp(T2) and pd.Timestamp(T2) + pd.Timedelta(days=C.LABEL_LAG_DAYS) <= pd.Timestamp(E)
youden_out = youden_thr(get(T2).y.values, NB().fit(get(T1)).predict(get(T2)))
abc_e = abc_class(ev.Monetary); pct_e = pct_within_class(p, abc_e, ev.Recency.values)  # (c) RiskLevel Cao: phân vị 75 trong từng hạng ABC tại E
def lop1(yhat):
    tp = int(((yhat == 1) & (y == 1)).sum()); fp = int(((yhat == 1) & (y == 0)).sum()); fn = int(((yhat == 0) & (y == 1)).sum()); tn = int(((yhat == 0) & (y == 0)).sum())
    f = lambda a, b: a / b if b else np.nan
    return {'Số khách bị cảnh báo (dự đoán y = 1)': tp + fp, 'Tỷ lệ khách bị cảnh báo': (tp + fp) / len(y), 'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn, 'Accuracy': (tp + tn) / len(y), 'Tỷ lệ lỗi': (fp + fn) / len(y),
            'Precision': f(tp, tp + fp), 'Sensitivity (recall)': f(tp, tp + fn), 'Specificity': f(tn, tn + fp), 'F1': f(2 * tp, 2 * tp + fp + fn)}
cols = {f'Youden trên mốc huấn luyện (RiskScore ≥ {youden:.3f})': lop1((p >= youden).astype(int)), f'Youden ngoài mẫu (RiskScore ≥ {youden_out:.3f})': lop1((p >= youden_out).astype(int)),
        'Phân vị 75 trong từng hạng ABC (RiskLevel Cao)': lop1((pct_e >= C.RISK_HIGH_PERCENTILE).astype(int)), 'Luôn dự đoán y = 1 (lớp đa số)': lop1(np.ones(len(y), dtype=int))}
lop1_tab = pd.DataFrame(cols); lop1_tab.index.name = 'Chỉ số'
lop1_tab.to_csv(f'{R}/bang_4_3_3a_lop1_ba_nguong.csv')
log(f'\n## Bảng 4.3.3a – Lớp 1: chỉ số phân lớp (Lecture 5, slide 69–70) của Naive Bayes tại mốc {E} ở ba ngưỡng, kèm cách luôn dự đoán lớp đa số\n'
    f'Ngưỡng ngoài mẫu: Naive Bayes học ở {T1}, dự đoán mốc {T2} (nhãn đủ trước {E}), chọn ngưỡng Youden trên dự đoán đó.\n' + lop1_tab.round(4).to_string())
K = 4000; top = np.argsort(-p)[:K]
lop = pd.DataFrame([
    ['Lớp 2 – xếp hạng và xác suất', 'ROC-AUC', roc_auc_score(y, p)], ['', 'ROC-AUC Recency đảo chiều', float(folds[(folds.mo_hinh == 'Recency đảo chiều') & (folds.E == E)].AUC.iloc[0])], ['', 'AP lớp 1', average_precision_score(y, p)], ['', 'AP lớp 0', average_precision_score(1 - y, 1 - p)],
    ['', 'Brier', brier_score_loss(y, p)], ['', 'Brier dự đoán hằng số', brier_score_loss(y, np.full(len(y), trf.y.mean()))], ['', f'Precision@K (K = {K})', y[top].mean()],
    ['Lớp 3 – giá trị quyết định', 'Z theo p·v (USD)', float(folds[(folds.mo_hinh == 'Naive Bayes rời rạc') & (folds.E == E)].Z_pv.iloc[0])], ['', 'Z chỉ theo v (USD)', float(folds[folds.E == E].Z_v.iloc[0])], ['', 'Z biết trước nhãn (USD)', float(folds[folds.E == E].Z_oracle.iloc[0])]],
    columns=['Lớp', 'Chỉ số', f'Giá trị tại mốc {E}'])
lop.to_csv(f'{R}/bang_4_3_3b_lop2_lop3.csv', index=False)
log(f'\n## Bảng 4.3.3b – Lớp 2 và Lớp 3 của Naive Bayes tại mốc {E}\n' + lop.round(4).to_string(index=False))
for old in ('bang_4_3_3_ba_lop_danh_gia.csv',):
    if os.path.exists(f'{R}/{old}'): os.remove(f'{R}/{old}')

# ---------- 3. bảng cho 4.3.4: khách minh hoạ + bảng xác suất có điều kiện ----------
ex = score.sort_values('RiskPercentile', ascending=False)
ex_hi = ex[ex.Flag == 0].iloc[0]; ex_flag = ex[ex.Flag == 1].iloc[0]; ex_lo = ex[ex.Flag == 0].iloc[-1]   # cao và thống nhất, cao nhưng cây lệch, thấp và thống nhất
mh = pd.DataFrame([ex_hi, ex_flag, ex_lo])[['CustomerID', 'Recency', 'Frequency', 'Monetary', 'RiskScore', 'RiskPercentile', 'RiskLevel', 'TreeScore', 'Flag', 'TopFactors']]
mh.to_csv(f'{R}/bang_4_3_4_khach_minh_hoa.csv', index=False)
log('\n## Bảng 4.3.4a – Ba khách minh hoạ (rủi ro cao, có cờ lệch, rủi ro thấp)\n' + mh.to_string(index=False))
names = {'Recency': ['<90', '90–179', '180–269', '270–364', '365–539', '≥540'], 'Frequency': ['1', '2', '≥3'], 'Monetary': ['Q1', 'Q2', 'Q3', 'Q4'], 'BikeBuyer': ['0', '1'], 'NSub': ['1', '2', '3–4', '≥5']}
rows = []
for i, f in enumerate(['Recency', 'Frequency', 'Monetary', 'BikeBuyer', 'NSub']):
    lp = np.exp(nb.clf.feature_log_prob_[i])
    for k, nm in enumerate(names[f]): rows.append(dict(thuoc_tinh=f, khoang=nm, P_x_y0=round(lp[0][k], 4), P_x_y1=round(lp[1][k], 4), ty_so=round(lp[1][k] / lp[0][k], 3)))
cp = pd.DataFrame(rows); cp.to_csv(f'{R}/bang_4_3_4_xac_suat_co_dieu_kien_NB.csv', index=False)
log(f'\n## Bảng 4.3.4b – Xác suất có điều kiện P(x | y) của Naive Bayes học ở {T0} (tỷ số > 1 làm tăng rủi ro). Tiên nghiệm P(y=1) = {np.exp(nb.clf.class_log_prior_[1]):.4f}\n' + cp.to_string(index=False))

# ---------- 4. sinh SQL ----------
def q(s): return "N'" + str(s).replace("'", "''") + "'"
hdr = "USE [CompanyX_DW];\nSET NOCOUNT ON; SET XACT_ABORT ON; SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON;\n"
cfg_nb = json.dumps(dict(model='sklearn.naive_bayes.CategoricalNB', alpha=1, features=['Recency', 'Frequency', 'Monetary', 'BikeBuyer', 'NSub'], recency_bins=C.RECENCY_BINS, frequency_bins=C.FREQUENCY_BINS, nsub_bins=C.NSUB_BINS,
                         monetary_quartiles=[round(float(v), 4) for v in nb.qM], bikebuyer='Share_Bikes > 0.5', class_prior=[round(float(np.exp(v)), 6) for v in nb.clf.class_log_prior_],
                         youden_threshold_train=round(youden, 6), risk_high_percentile=C.RISK_HIGH_PERCENTILE, percentile_within='ABC class (80/95 on Monetary at scoring date)', tie_break='Recency desc', sklearn='1.6.1', folds=C.FOLDS), ensure_ascii=False)
cfg_tree = json.dumps(dict(model='sklearn.tree.DecisionTreeClassifier', criterion='gini', max_depth=4, min_samples_leaf=400, m_estimate=50, random_state=C.RANDOM_STATE, n_leaves=len(leaf_ids), features=ALL), ensure_ascii=False)
cfg_mlp = json.dumps(dict(model='sklearn.neural_network.MLPClassifier', hidden_layer_sizes=[32, 16], activation='relu', solver='adam', max_iter=300, early_stopping=True, random_state=C.RANDOM_STATE, scaler='StandardScaler fit on train', features=ALL, note='mô hình so sánh, không dùng để chấm điểm'), ensure_ascii=False)
p75 = float(np.percentile(p_nb, 75))
reg = hdr + f"""/* CUM5_01 – Đăng ký 3 mô hình học ở mốc {T0}. Chạy MỘT lần. Nếu đã có thì xoá bằng RESET_SCORES.sql trước. */
IF EXISTS (SELECT 1 FROM analytics.ModelRegistry WHERE ModelVersion IN ({q(V_NB)},{q(V_TREE)},{q(V_MLP)}))
    THROW 55001, N'ModelVersion đã tồn tại. Chạy sql/RESET_SCORES.sql nếu muốn ghi lại.', 1;
BEGIN TRANSACTION;
INSERT analytics.ModelRegistry(ModelVersion,ModelRole,ModelType,TrainingSnapshot,FeatureList,ConfigurationJSON,ArtifactPath,ScalerPath,TrainBaseRate,DecisionThreshold,ROCAUC,BrierScore,EffectiveFrom,IsActive) VALUES
({q(V_NB)},N'SCORING',N'Naive Bayes (CategoricalNB, Bảng 3.10)','{T0}',{q('Recency,Frequency,Monetary,BikeBuyer,NSub (rời rạc)')},{q(cfg_nb)},{q(f'models/nb_T{TAG}.joblib')},{q(f'models/chuan_hoa_T{TAG}.json')},{tr.y.mean():.6f},{p75:.6f},{fold_mean('Naive Bayes rời rạc', 'AUC'):.6f},{fold_mean('Naive Bayes rời rạc', 'Brier'):.6f},'{E0}',1),
({q(V_TREE)},N'TREE',N'Cây quyết định Gini (CART) sâu 4, 400 khách/lá, m = 50','{T0}',{q(','.join(ALL))},{q(cfg_tree)},{q(f'models/tree_T{TAG}.joblib')},NULL,{tr.y.mean():.6f},NULL,{fold_mean('Cây Gini sâu 4, lá 400', 'AUC'):.6f},{fold_mean('Cây Gini sâu 4, lá 400', 'Brier'):.6f},'{E0}',1),
({q(V_MLP)},N'COMPARISON',N'Mạng nơ-ron MLP (32,16)','{T0}',{q(','.join(ALL))},{q(cfg_mlp)},{q(f'models/mlp_T{TAG}.joblib')},{q(f'models/chuan_hoa_T{TAG}.json')},{tr.y.mean():.6f},NULL,{fold_mean('MLP (32,16)', 'AUC'):.6f},{fold_mean('MLP (32,16)', 'Brier'):.6f},'{E0}',1);
COMMIT TRANSACTION;
SELECT ModelVersion, ModelRole, ModelType, TrainingSnapshot, TrainBaseRate, DecisionThreshold, ROCAUC, BrierScore, IsActive FROM analytics.ModelRegistry ORDER BY ModelRole;
PRINT N'CUM5_01_OK: 3 mô hình đã đăng ký.';
"""
open(f'{R}/CUM5_01_ModelRegistry.sql', 'w', encoding='utf-8-sig').write(reg)
leaf_sql = hdr + f"/* CUM5_02 – {len(leaf_ids)} lá của cây đối chứng {V_TREE} */\nBEGIN TRANSACTION;\nINSERT analytics.ModelTreeLeaf(ModelVersion,LeafID,RuleText,ConditionsJSON,LeafCount,PositiveCount,TreeScore) VALUES\n" + ',\n'.join(
    f"({q(V_TREE)},{r.LeafID},{q(r.RuleText)},{q(json.dumps(rules[r.sk_leaf], ensure_ascii=False))},{r.LeafCount},{r.PositiveCount},{r.TreeScore:.6f})" for _, r in leaf_tab.iterrows()) + \
    f";\nCOMMIT TRANSACTION;\nSELECT LeafID, LeafCount, PositiveCount, TreeScore, RuleText FROM analytics.ModelTreeLeaf WHERE ModelVersion={q(V_TREE)} ORDER BY LeafID;\nPRINT N'CUM5_02_OK: {len(leaf_ids)} lá.';\n"
open(f'{R}/CUM5_02_ModelTreeLeaf.sql', 'w', encoding='utf-8-sig').write(leaf_sql)
chunks = []
for i in range(0, len(score), 500):
    part = score.iloc[i:i + 500]
    chunks.append("INSERT analytics.CustomerRiskScore(CustomerID,ScoreDate,ModelVersion,RiskScore,RiskPercentile,RiskLevel,TreeScore,TreeModelVersion,TopFactors) VALUES\n" + ',\n'.join(
        f"({r.CustomerID},'{E0}',{q(V_NB)},{r.RiskScore:.6f},{r.RiskPercentile:.3f},{q(r.RiskLevel)},{r.TreeScore:.6f},{q(V_TREE)},{q(r.TopFactors)})" for r in part.itertuples()) + ';')
crs = hdr + f"""/* CUM5_03 – Ghi {len(score)} điểm rủi ro tại mốc {E0}. Sau bước này C3_01/C3_02 sẽ từ chối tính lại Snapshot (đúng thiết kế). */
IF EXISTS (SELECT 1 FROM analytics.CustomerRiskScore WHERE ScoreDate='{E0}' AND ModelVersion={q(V_NB)})
    THROW 55002, N'Đã có điểm cho mốc này. Chạy sql/RESET_SCORES.sql nếu muốn ghi lại.', 1;
BEGIN TRANSACTION;
""" + '\n'.join(chunks) + f"""
IF (SELECT COUNT(*) FROM analytics.CustomerRiskScore WHERE ScoreDate='{E0}' AND ModelVersion={q(V_NB)}) <> {len(score)}
    THROW 55003, N'Số dòng ghi không khớp.', 1;
COMMIT TRANSACTION;
SELECT RiskLevel, COUNT(*) AS SoKhach, CAST(100.0*COUNT(*)/SUM(COUNT(*)) OVER () AS DECIMAL(5,1)) AS TyLe, MIN(RiskScore) AS RiskScore_Min, MAX(RiskScore) AS RiskScore_Max
FROM analytics.CustomerRiskScore WHERE ScoreDate='{E0}' GROUP BY RiskLevel;
PRINT N'CUM5_03_OK: {len(score)} khách đã có điểm.';
"""
open(f'{R}/CUM5_03_CustomerRiskScore.sql', 'w', encoding='utf-8-sig').write(crs)
ver = f"""USE [CompanyX_DW];
SET NOCOUNT ON;
/* CUM5_04 – Kiểm tra sau khi ghi (chỉ đọc). Chụp 4 kết quả này cho mục 4.3.5. */
-- 1. Số dòng và tỷ lệ Cao (mong đợi: {len(score)} khách, Cao {(level == 'Cao').sum()} = {(level == 'Cao').mean() * 100:.1f}%)
SELECT COUNT(*) AS SoKhach, SUM(CASE WHEN RiskLevel=N'Cao' THEN 1 ELSE 0 END) AS SoCao,
       CAST(100.0*SUM(CASE WHEN RiskLevel=N'Cao' THEN 1 ELSE 0 END)/COUNT(*) AS DECIMAL(5,1)) AS TyLeCao,
       SUM(CASE WHEN ABS(TreeScore-RiskScore)>{C.TREE_FLAG_GAP} THEN 1 ELSE 0 END) AS SoCoLech
FROM analytics.CustomerRiskScore WHERE ScoreDate='{E0}';
-- 2. Mỗi khách đúng một dòng và nối được với Snapshot + mô hình đang dùng (mong đợi: {len(score)} / {len(score)})
SELECT COUNT(*) AS DongNoi, COUNT(DISTINCT r.CustomerID) AS KhachNoi
FROM analytics.CustomerRiskScore r
JOIN analytics.CustomerSnapshot s ON s.CustomerID=r.CustomerID AND s.SnapshotDate=r.ScoreDate
JOIN analytics.ModelRegistry m ON m.ModelVersion=r.ModelVersion AND m.IsActive=1 AND m.ModelRole=N'SCORING';
-- 3. Ba mô hình đã đăng ký
SELECT ModelVersion, ModelRole, TrainingSnapshot, TrainBaseRate, DecisionThreshold, ROCAUC, BrierScore FROM analytics.ModelRegistry ORDER BY ModelRole;
-- 4. Khách minh hoạ cho 4.3.4 (mã {int(ex_hi.CustomerID)}, {int(ex_flag.CustomerID)}, {int(ex_lo.CustomerID)}) kèm RFM từ Snapshot
SELECT r.CustomerID, s.RecencyDays, s.Frequency, s.Monetary, r.RiskScore, r.RiskPercentile, r.RiskLevel, r.TreeScore, r.TopFactors
FROM analytics.CustomerRiskScore r JOIN analytics.CustomerSnapshot s ON s.CustomerID=r.CustomerID AND s.SnapshotDate=r.ScoreDate
WHERE r.CustomerID IN ({int(ex_hi.CustomerID)},{int(ex_flag.CustomerID)},{int(ex_lo.CustomerID)}) ORDER BY r.RiskPercentile DESC;
-- 5. Phân bố RiskPercentile theo lá cây (cho 4.3.4)
SELECT l.LeafID, l.LeafCount, l.TreeScore, COUNT(r.CustomerID) AS KhachTaiMocChamDiem, AVG(r.RiskScore) AS RiskScore_TB
FROM analytics.ModelTreeLeaf l LEFT JOIN analytics.CustomerRiskScore r ON r.TreeModelVersion=l.ModelVersion AND r.TopFactors LIKE N'Lá '+CAST(l.LeafID AS NVARCHAR(5))+N':%'
WHERE l.ModelVersion={q(V_TREE)} GROUP BY l.LeafID, l.LeafCount, l.TreeScore ORDER BY l.LeafID;
"""
open(f'{R}/CUM5_04_Verify_READ_ONLY.sql', 'w', encoding='utf-8-sig').write(ver)
log(f'\nĐã sinh 4 file SQL trong results/cum5/. Mong đợi sau khi chạy: {len(score)} khách, Cao {(level == "Cao").sum()} ({(level == "Cao").mean():.1%}), cờ lệch {score.Flag.sum()}.')

# ---------- 5. tự kiểm (dừng nếu sai) và tóm tắt số cho hướng dẫn (python/tao_huong_dan.py đọc file này) ----------
assert len(score) == score.CustomerID.nunique() == len(sc), 'Mỗi khách phải đúng một dòng'
assert ((score.RiskPercentile >= C.RISK_HIGH_PERCENTILE) == (score.RiskLevel == 'Cao')).all(), 'RiskLevel phải khớp RiskPercentile (ràng buộc CHECK trong kho)'
for cls in ('A', 'B', 'C'):
    msk = abc == cls; share = (level[msk] == 'Cao').mean()
    assert abs(share - (100 - C.RISK_HIGH_PERCENTILE) / 100) <= 2 / msk.sum(), f'Hạng {cls}: tỷ lệ Cao {share:.4f} lệch 25%'
assert ex_hi.Flag == 0 and ex_flag.Flag == 1 and ex_lo.Flag == 0 and ex_hi.RiskLevel == 'Cao' and ex_lo.RiskLevel == 'Thấp', 'Ba khách minh hoạ không đúng vai trò'
assert len(leaf_tab) == len(set(leaf_tab.LeafID)) and leaf_tab.LeafCount.sum() == len(tr), 'Lá cây phải phủ đủ khách mốc huấn luyện'
lv = pd.crosstab(abc, level)
cao_min = score[score.RiskLevel == 'Cao'].groupby('ABC').RiskScore.agg(['min', 'median'])
leaf_flag = score.groupby('LeafID').agg(n=('Flag', 'size'), co=('Flag', 'sum'), risk_tb=('RiskScore', 'mean'), tree=('TreeScore', 'first')).sort_values('co', ascending=False)
def kh(r):
    lf = leaf_tab[leaf_tab.LeafID == score.loc[score.CustomerID == r.CustomerID, 'LeafID'].iloc[0]].iloc[0]
    return dict(id=int(r.CustomerID), recency=int(r.Recency), frequency=int(r.Frequency), monetary=round(float(r.Monetary), 2), risk=round(float(r.RiskScore), 3), pct=round(float(r.RiskPercentile), 3),
                level=r.RiskLevel, tree=round(float(r.TreeScore), 3), flag=int(r.Flag), la=int(lf.LeafID), la_ty_le=round(lf.PositiveCount / lf.LeafCount, 3), la_khach=int(lf.LeafCount),
                abc=score.loc[score.CustomerID == r.CustomerID, 'ABC'].iloc[0])
L1 = {k: {m: (round(float(v), 4) if isinstance(v, float) else int(v)) for m, v in d.items()} for k, d in cols.items()}
tom = dict(n=int(len(score)), cao=int((level == 'Cao').sum()), cao_pct=round(float((level == 'Cao').mean()), 4), cao_hang={c: int(lv.loc[c, 'Cao']) for c in 'ABC'}, thap_hang={c: int(lv.loc[c, 'Thấp']) for c in 'ABC'},
           cao_min={c: round(float(cao_min.loc[c, 'min']), 3) for c in 'ABC'}, cao_median={c: round(float(cao_min.loc[c, 'median']), 3) for c in 'ABC'}, p75_toan_bo=round(p75, 4),
           co=int(score.Flag.sum()), co_pct=round(float(score.Flag.mean()), 4), la_nhieu_co=dict(la=int(leaf_flag.index[0]), co=int(leaf_flag.co.iloc[0]), n=int(leaf_flag.n.iloc[0]), risk_tb=round(float(leaf_flag.risk_tb.iloc[0]), 2), tree=round(float(leaf_flag.tree.iloc[0]), 2)),
           E=E, T=T, T1=T1, T2=T2, youden=round(youden, 3), youden_out=round(youden_out, 3), lop1=L1, lop1_cot=list(cols.keys()),
           lop2=dict(auc=round(float(lop.iloc[0, 2]), 4), auc_rec=round(float(lop.iloc[1, 2]), 4), ap1=round(float(lop.iloc[2, 2]), 4), ap0=round(float(lop.iloc[3, 2]), 4), brier=round(float(lop.iloc[4, 2]), 4), brier_hs=round(float(lop.iloc[5, 2]), 4), p_at_k=round(float(lop.iloc[6, 2]), 4)),
           lop3=dict(z_pv=round(float(lop.iloc[7, 2])), z_v=round(float(lop.iloc[8, 2])), z_oracle=round(float(lop.iloc[9, 2]))),
           reg=dict(nb_auc4=round(fold_mean('Naive Bayes rời rạc', 'AUC'), 4), nb_brier4=round(fold_mean('Naive Bayes rời rạc', 'Brier'), 4), mlp_auc4=round(fold_mean('MLP (32,16)', 'AUC'), 4), tree_auc4=round(fold_mean('Cây Gini sâu 4, lá 400', 'AUC'), 4)),
           la=dict(so=int(len(leaf_tab)), min=int(leaf_tab.LeafCount.min()), max=int(leaf_tab.LeafCount.max())), prior=round(float(np.exp(nb.clf.class_log_prior_[1])), 4),
           khach=dict(cao=kh(ex_hi), lech=kh(ex_flag), thap=kh(ex_lo)), ty_so={f'{r.thuoc_tinh} {r.khoang}': r.ty_so for r in cp.itertuples()},
           thap_cao=dict(thap=int((level == 'Thấp').sum())))
json.dump(tom, open(f'{R}/tom_tat.json', 'w'), ensure_ascii=False, indent=1)
log('\nTự kiểm: đạt (mỗi khách một dòng, RiskLevel khớp phân vị, mỗi hạng ABC 25% Cao, ba khách minh hoạ đúng vai trò, lá cây phủ đủ khách).')
open(f'{R}/cum5_ket_qua.md', 'w').write('\n'.join(out))
