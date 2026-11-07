USE [CompanyX_DW];
SET NOCOUNT ON; SET XACT_ABORT ON; SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON;
/* CUM5_02 – 11 lá của cây đối chứng TREE_T20140301_v1 */
BEGIN TRANSACTION;
INSERT analytics.ModelTreeLeaf(ModelVersion,LeafID,RuleText,ConditionsJSON,LeafCount,PositiveCount,TreeScore) VALUES
(N'TREE_T20140301_v1',1,N'Recency <= 275.50 AND Monetary <= 4640.88 AND BikeBuyer <= 0.50 AND Monetary <= 150.94',N'["Recency <= 275.50", "Monetary <= 4640.88", "BikeBuyer <= 0.50", "Monetary <= 150.94"]',6054,5440,0.897933),
(N'TREE_T20140301_v1',2,N'Recency <= 275.50 AND Monetary <= 4640.88 AND BikeBuyer <= 0.50 AND Monetary > 150.94',N'["Recency <= 275.50", "Monetary <= 4640.88", "BikeBuyer <= 0.50", "Monetary > 150.94"]',452,331,0.741001),
(N'TREE_T20140301_v1',3,N'Recency <= 275.50 AND Monetary <= 4640.88 AND BikeBuyer > 0.50 AND Monetary <= 1956.81',N'["Recency <= 275.50", "Monetary <= 4640.88", "BikeBuyer > 0.50", "Monetary <= 1956.81"]',1756,1747,0.990024),
(N'TREE_T20140301_v1',4,N'Recency <= 275.50 AND Monetary <= 4640.88 AND BikeBuyer > 0.50 AND Monetary > 1956.81',N'["Recency <= 275.50", "Monetary <= 4640.88", "BikeBuyer > 0.50", "Monetary > 1956.81"]',1904,1801,0.942673),
(N'TREE_T20140301_v1',5,N'Recency <= 275.50 AND Monetary > 4640.88 AND Monetary <= 4960.65',N'["Recency <= 275.50", "Monetary > 4640.88", "Monetary <= 4960.65"]',440,246,0.585679),
(N'TREE_T20140301_v1',6,N'Recency <= 275.50 AND Monetary > 4640.88 AND Monetary > 4960.65 AND Monetary <= 6587.16',N'["Recency <= 275.50", "Monetary > 4640.88", "Monetary > 4960.65", "Monetary <= 6587.16"]',901,776,0.859077),
(N'TREE_T20140301_v1',7,N'Recency <= 275.50 AND Monetary > 4640.88 AND Monetary > 4960.65 AND Monetary > 6587.16',N'["Recency <= 275.50", "Monetary > 4640.88", "Monetary > 4960.65", "Monetary > 6587.16"]',664,632,0.942553),
(N'TREE_T20140301_v1',8,N'Recency > 275.50 AND Tenure <= 744.00 AND Monetary <= 1684.87',N'["Recency > 275.50", "Tenure <= 744.00", "Monetary <= 1684.87"]',420,76,0.248899),
(N'TREE_T20140301_v1',9,N'Recency > 275.50 AND Tenure <= 744.00 AND Monetary > 1684.87 AND Monetary <= 2349.77',N'["Recency > 275.50", "Tenure <= 744.00", "Monetary > 1684.87", "Monetary <= 2349.77"]',467,175,0.417761),
(N'TREE_T20140301_v1',10,N'Recency > 275.50 AND Tenure <= 744.00 AND Monetary > 1684.87 AND Monetary > 2349.77',N'["Recency > 275.50", "Tenure <= 744.00", "Monetary > 1684.87", "Monetary > 2349.77"]',515,104,0.256606),
(N'TREE_T20140301_v1',11,N'Recency > 275.50 AND Tenure > 744.00',N'["Recency > 275.50", "Tenure > 744.00"]',594,284,0.504631);
COMMIT TRANSACTION;
SELECT LeafID, LeafCount, PositiveCount, TreeScore, RuleText FROM analytics.ModelTreeLeaf WHERE ModelVersion=N'TREE_T20140301_v1' ORDER BY LeafID;
PRINT N'CUM5_02_OK: 11 lá.';
