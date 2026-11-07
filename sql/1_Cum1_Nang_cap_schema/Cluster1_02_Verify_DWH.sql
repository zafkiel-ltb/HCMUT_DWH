/* Read-only schema and row-count verification. Run AFTER Cluster1_01_Upgrade_DWH.sql */
USE [CompanyX_DW];
GO
SET NOCOUNT ON;

/* 1. Required columns: all results should be FOUND. */
;WITH RequiredColumns AS (
    SELECT N'etl.RejectedRow' AS TableName, N'IsInScope' AS ColumnName
    UNION ALL SELECT N'analytics.CustomerSnapshot', N'Tenure'
    UNION ALL SELECT N'analytics.CustomerSnapshot', N'Share_Bikes'
    UNION ALL SELECT N'analytics.CustomerSnapshot', N'Share_Accessories'
    UNION ALL SELECT N'analytics.CustomerSnapshot', N'Share_Clothing'
    UNION ALL SELECT N'analytics.CustomerSnapshot', N'NSub'
    UNION ALL SELECT N'analytics.ModelRegistry', N'ModelVersion'
    UNION ALL SELECT N'analytics.ModelRegistry', N'ModelRole'
    UNION ALL SELECT N'analytics.ModelRegistry', N'ModelType'
    UNION ALL SELECT N'analytics.ModelRegistry', N'TrainingSnapshot'
    UNION ALL SELECT N'analytics.ModelRegistry', N'ConfigurationJSON'
    UNION ALL SELECT N'analytics.ModelRegistry', N'IsActive'
    UNION ALL SELECT N'analytics.ModelTreeLeaf', N'ModelVersion'
    UNION ALL SELECT N'analytics.ModelTreeLeaf', N'LeafID'
    UNION ALL SELECT N'analytics.ModelTreeLeaf', N'TreeScore'
    UNION ALL SELECT N'analytics.CustomerRiskScore', N'CustomerID'
    UNION ALL SELECT N'analytics.CustomerRiskScore', N'ScoreDate'
    UNION ALL SELECT N'analytics.CustomerRiskScore', N'ModelVersion'
    UNION ALL SELECT N'analytics.CustomerRiskScore', N'RiskScore'
    UNION ALL SELECT N'analytics.CustomerRiskScore', N'RiskPercentile'
    UNION ALL SELECT N'analytics.CustomerRiskScore', N'RiskLevel'
    UNION ALL SELECT N'analytics.CustomerRiskScore', N'TreeScore'
    UNION ALL SELECT N'analytics.CustomerRiskScore', N'TopFactors'
)
SELECT TableName, ColumnName,
       CASE WHEN COL_LENGTH(TableName, ColumnName) IS NULL THEN N'MISSING' ELSE N'FOUND' END AS Result
FROM RequiredColumns
ORDER BY TableName, ColumnName;

/* 2. Expected 6 DW table names unchanged + 2 new analytics tables. */
SELECT s.name AS SchemaName, t.name AS TableName
FROM sys.tables AS t
JOIN sys.schemas AS s ON s.schema_id = t.schema_id
WHERE (s.name = N'dbo' AND t.name IN
       (N'DimCustomer', N'DimDate', N'DimProduct', N'DimTerritory',
        N'FactSalesOrder', N'FactSalesOrderLine'))
   OR (s.name = N'analytics' AND t.name IN
       (N'CustomerSnapshot', N'ModelRegistry', N'ModelTreeLeaf', N'CustomerRiskScore'))
   OR (s.name = N'etl' AND t.name = N'RejectedRow')
ORDER BY SchemaName, TableName;

/* 3. Count original 6 fact/dim FKs; should still be 7. */
SELECT COUNT(*) AS Original_DW_ForeignKeys_Expected7
FROM sys.foreign_keys
WHERE parent_object_id IN (
    OBJECT_ID(N'dbo.FactSalesOrder'), OBJECT_ID(N'dbo.FactSalesOrderLine'));

/* 4. Existing snapshots preserved; feature NULLs are expected until Cluster 3. */
SELECT SnapshotDate, COUNT(*) AS Customers,
       SUM(CASE WHEN Tenure IS NULL THEN 1 ELSE 0 END) AS Tenure_NotYetComputed,
       SUM(CASE WHEN NSub IS NULL THEN 1 ELSE 0 END) AS NSub_NotYetComputed
FROM analytics.CustomerSnapshot
GROUP BY SnapshotDate ORDER BY SnapshotDate;

/* 5. Registry/scores should be EMPTY until Cluster 4/5. */
SELECT (SELECT COUNT(*) FROM analytics.ModelRegistry) AS ModelRegistryRows,
       (SELECT COUNT(*) FROM analytics.CustomerRiskScore) AS CustomerRiskScoreRows,
       (SELECT COUNT(*) FROM analytics.ModelTreeLeaf) AS ModelTreeLeafRows,
       (SELECT COUNT(*) FROM etl.RejectedRow WHERE IsInScope IS NULL) AS OldRejectRows_Unclassified;
GO
