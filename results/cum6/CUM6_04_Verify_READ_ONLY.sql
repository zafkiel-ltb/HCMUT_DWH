USE [CompanyX_DW];
SET NOCOUNT ON;
/* CUM6_04 – Kiểm tra chỉ đọc. Mong đợi: 18360 khách có nhóm, 5 nhóm, 9 quy tắc, 6124 khuyến nghị, Z ≈ 256,502 */
SELECT COUNT(*) AS KhachCoNhom, COUNT(DISTINCT ClusterID) AS SoNhom FROM analytics.CustomerSegment WHERE SnapshotDate='2014-07-08';
SELECT s.ClusterName, COUNT(*) AS SoKhach, AVG(r.RiskScore) AS RiskScore_TB, SUM(CASE WHEN r.RiskLevel=N'Cao' THEN 1 ELSE 0 END) AS SoCao
FROM analytics.CustomerSegment s JOIN analytics.CustomerRiskScore r ON r.CustomerID=s.CustomerID AND r.ScoreDate=s.SnapshotDate GROUP BY s.ClusterName ORDER BY s.ClusterName;
SELECT COUNT(*) AS SoQuyTac, SUM(CAST(IsActive AS INT)) AS DangBat FROM analytics.CareRule;
SELECT ScenarioID, COUNT(*) AS SoKhach, SUM(ChannelCost) AS ChiPhi, SUM(ExpectedValue) AS Z FROM analytics.CareRecommendation GROUP BY ScenarioID;
-- Màn hình 2: hồ sơ một khách (ví dụ 19785)
SELECT r.CustomerID, s.ClusterName, s.ABCClass, r.RiskScore, r.RiskLevel, r.TreeScore, c.ChannelRule, c.SuggestedProducts, c.ExpectedValue
FROM analytics.CustomerRiskScore r JOIN analytics.CustomerSegment s ON s.CustomerID=r.CustomerID AND s.SnapshotDate=r.ScoreDate
LEFT JOIN analytics.CareRecommendation c ON c.CustomerID=r.CustomerID AND c.ScenarioID=N'BASE_r10_c10_B40000_20140708_NB_T20140301_v1' WHERE r.CustomerID=19785;
