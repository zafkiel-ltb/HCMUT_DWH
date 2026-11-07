USE [CompanyX_DW];
SET NOCOUNT ON;
/* CUM5_04 – Kiểm tra sau khi ghi (chỉ đọc). Chụp 4 kết quả này cho mục 4.3.5. */
-- 1. Số dòng và tỷ lệ Cao (mong đợi: 18360 khách, Cao 4592 = 25.0%)
SELECT COUNT(*) AS SoKhach, SUM(CASE WHEN RiskLevel=N'Cao' THEN 1 ELSE 0 END) AS SoCao,
       CAST(100.0*SUM(CASE WHEN RiskLevel=N'Cao' THEN 1 ELSE 0 END)/COUNT(*) AS DECIMAL(5,1)) AS TyLeCao,
       SUM(CASE WHEN ABS(TreeScore-RiskScore)>0.3 THEN 1 ELSE 0 END) AS SoCoLech
FROM analytics.CustomerRiskScore WHERE ScoreDate='2014-07-08';
-- 2. Mỗi khách đúng một dòng và nối được với Snapshot + mô hình đang dùng (mong đợi: 18360 / 18360)
SELECT COUNT(*) AS DongNoi, COUNT(DISTINCT r.CustomerID) AS KhachNoi
FROM analytics.CustomerRiskScore r
JOIN analytics.CustomerSnapshot s ON s.CustomerID=r.CustomerID AND s.SnapshotDate=r.ScoreDate
JOIN analytics.ModelRegistry m ON m.ModelVersion=r.ModelVersion AND m.IsActive=1 AND m.ModelRole=N'SCORING';
-- 3. Ba mô hình đã đăng ký
SELECT ModelVersion, ModelRole, TrainingSnapshot, TrainBaseRate, DecisionThreshold, ROCAUC, BrierScore FROM analytics.ModelRegistry ORDER BY ModelRole;
-- 4. Khách minh hoạ cho 4.3.4 (mã 12201, 26339, 26774) kèm RFM từ Snapshot
SELECT r.CustomerID, s.RecencyDays, s.Frequency, s.Monetary, r.RiskScore, r.RiskPercentile, r.RiskLevel, r.TreeScore, r.TopFactors
FROM analytics.CustomerRiskScore r JOIN analytics.CustomerSnapshot s ON s.CustomerID=r.CustomerID AND s.SnapshotDate=r.ScoreDate
WHERE r.CustomerID IN (12201,26339,26774) ORDER BY r.RiskPercentile DESC;
-- 5. Phân bố RiskPercentile theo lá cây (cho 4.3.4)
SELECT l.LeafID, l.LeafCount, l.TreeScore, COUNT(r.CustomerID) AS KhachTaiMocChamDiem, AVG(r.RiskScore) AS RiskScore_TB
FROM analytics.ModelTreeLeaf l LEFT JOIN analytics.CustomerRiskScore r ON r.TreeModelVersion=l.ModelVersion AND r.TopFactors LIKE N'Lá '+CAST(l.LeafID AS NVARCHAR(5))+N':%'
WHERE l.ModelVersion=N'TREE_T20140301_v1' GROUP BY l.LeafID, l.LeafCount, l.TreeScore ORDER BY l.LeafID;
