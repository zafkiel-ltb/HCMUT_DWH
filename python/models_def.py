# -*- coding: utf-8 -*-
"""Định nghĩa các mô hình dùng chung cho cụm 4, 5, 6 (tách riêng để joblib nạp lại được mà không chạy huấn luyện)."""
import pandas as pd, numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import CategoricalNB
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score
import config as C
ALL = C.FEATURES

class SK:
    """Bọc mô hình scikit-learn, tuỳ chọn chuẩn hoá z-score fit trên mốc huấn luyện."""
    def __init__(self, est, scale=False): self.est, self.scale = est, scale
    def fit(self, df):
        self.m = make_pipeline(StandardScaler(), self.est) if self.scale else self.est; self.m.fit(df[ALL].values, df.y.values); return self
    def predict(self, df): return self.m.predict_proba(df[ALL].values)[:, 1]

class GiniTree:
    """Cây CART Gini, xác suất lá theo m-estimate (công thức 3.3)."""
    def __init__(self, depth=4, leaf=400, m=50): self.m = m; self.clf = DecisionTreeClassifier(criterion='gini', max_depth=depth, min_samples_leaf=leaf, random_state=C.RANDOM_STATE)
    def fit(self, df):
        X, y = df[ALL].values, df.y.values; self.clf.fit(X, y); self.pi = y.mean(); leaf = self.clf.apply(X)
        n = pd.Series(leaf).value_counts(); n1 = pd.Series(leaf[y == 1]).value_counts().reindex(n.index).fillna(0)
        self.n_leaf, self.n1_leaf = n.to_dict(), n1.to_dict(); self.p_leaf = ((n1 + self.m * self.pi) / (n + self.m)).to_dict(); return self
    def predict(self, df): return np.array([self.p_leaf[l] for l in self.clf.apply(df[ALL].values)])
    def root(self):
        t = self.clf.tree_; return ALL[t.feature[0]], round(float(t.threshold[0]), 1), int(t.n_leaves)

def discretize(df, qM=None):
    """Rời rạc hoá theo Bảng 3.10. Tứ phân vị Monetary tính trên mốc huấn luyện và giữ nguyên khi áp dụng."""
    d = pd.DataFrame(index=df.index)
    d['R'] = pd.cut(df.Recency, C.RECENCY_BINS, labels=False); d['F'] = pd.cut(df.Frequency, C.FREQUENCY_BINS, labels=False)
    if qM is None: qM = df.Monetary.quantile([.25, .5, .75]).values
    d['M'] = np.searchsorted(qM, df.Monetary.values); d['B'] = df.BikeBuyer.values; d['N'] = pd.cut(df.NSub, C.NSUB_BINS, labels=False)
    return d, qM

class NB:
    """Naive Bayes rời rạc, hiệu chỉnh Laplace alpha = 1 – mô hình chấm điểm."""
    def fit(self, df): X, self.qM = discretize(df); self.clf = CategoricalNB(alpha=1, min_categories=[6, 3, 4, 2, 4]).fit(X.values, df.y.values); return self
    def predict(self, df): return self.clf.predict_proba(discretize(df, self.qM)[0].values)[:, 1]

def abc_class(monetary):
    """Hạng ABC theo công thức 3.19: xếp Monetary giảm dần, A khi tỷ trọng luỹ kế trước khách < 80%, B khi < 95%, còn lại C."""
    m = pd.Series(np.asarray(monetary, dtype=float)); s = m.sort_values(ascending=False); prev = (s.cumsum() / s.sum()).shift(fill_value=0)
    return pd.Series(np.where(prev < .8, 'A', np.where(prev < .95, 'B', 'C')), index=s.index).reindex(m.index).values

def pct_within_class(p, cls, recency):
    """RiskPercentile trong từng hạng (3.4.6): thứ hạng phần trăm của p trong hạng, đồng điểm thì Recency lớn hơn xếp sau (rủi ro hơn)."""
    p, cls, recency = np.asarray(p), np.asarray(cls), np.asarray(recency); pct = np.empty(len(p))
    for c in np.unique(cls):
        idx = np.where(cls == c)[0]; order = idx[np.lexsort((-recency[idx], p[idx]))]
        pct[order] = (np.arange(len(idx)) + 1) / len(idx) * 100
    return np.round(pct, 3)

class LR:
    def fit(self, df):
        X, self.qM = discretize(df); self.enc = OneHotEncoder(handle_unknown='ignore').fit(X.values); self.clf = LogisticRegression(C=1.0, max_iter=1000).fit(self.enc.transform(X.values), df.y.values); return self
    def predict(self, df): return self.clf.predict_proba(self.enc.transform(discretize(df, self.qM)[0].values))[:, 1]

class Majority:
    def fit(self, df): self.pi = df.y.mean(); return self
    def predict(self, df): return np.full(len(df), self.pi)

class RecencyRev:
    """Quy tắc Recency đảo chiều, chiều xếp chọn trên mốc huấn luyện, chỉ cho thứ hạng."""
    def fit(self, df): self.sign = 1 if roc_auc_score(df.y, df.Recency) >= 0.5 else -1; return self
    def predict(self, df): return pd.Series(self.sign * df.Recency.values).rank(pct=True).values
