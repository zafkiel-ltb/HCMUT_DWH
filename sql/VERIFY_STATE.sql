/* VERIFY_STATE.sql - "Vân tay" trạng thái CompanyX_DW sau cụm 0 -> 3A.
   Chạy trong SSMS/sqlcmd, database CompanyX_DW, chỉ đọc. So kết quả với cột "Mong đợi".
   Hai máy cho cùng số và cùng hash => cùng dữ liệu, cụm 3B trở đi có thể chạy trên bất kỳ máy nào. */
USE [CompanyX_DW];
SET NOCOUNT ON;
SELECT N'DimCustomer' AS Bang, COUNT(*) AS SoDong, 18484 AS MongDoi FROM dbo.DimCustomer
UNION ALL SELECT N'DimProduct', COUNT(*), 504 FROM dbo.DimProduct
UNION ALL SELECT N'DimTerritory', COUNT(*), 10 FROM dbo.DimTerritory
UNION ALL SELECT N'DimDate', COUNT(*), 1127 FROM dbo.DimDate
UNION ALL SELECT N'FactSalesOrder', COUNT(*), 27382 FROM dbo.FactSalesOrder
UNION ALL SELECT N'FactSalesOrderLine', COUNT(*), 59795 FROM dbo.FactSalesOrderLine
UNION ALL SELECT N'CustomerSnapshot', COUNT(*), 196985 FROM analytics.CustomerSnapshot
UNION ALL SELECT N'CustomerSnapshot moc', COUNT(DISTINCT SnapshotDate), 20 FROM analytics.CustomerSnapshot
UNION ALL SELECT N'RejectedRow lan chay moi nhat', COUNT(*), 81 FROM etl.RejectedRow WHERE RunID=(SELECT TOP 1 RunID FROM etl.RunLog ORDER BY StartedAt DESC)
UNION ALL SELECT N'ModelRegistry', COUNT(*), 0 FROM analytics.ModelRegistry
UNION ALL SELECT N'CustomerRiskScore', COUNT(*), 0 FROM analytics.CustomerRiskScore;

SELECT CAST(SUM(SubTotal) AS DECIMAL(19,4)) AS SubTotal_DW, CAST(29052549.9450 AS DECIMAL(19,4)) AS MongDoi_SubTotal,
       CAST(SUM(TotalDue) AS DECIMAL(19,4)) AS TotalDue_DW, CAST(32103068.4755 AS DECIMAL(19,4)) AS MongDoi_TotalDue FROM dbo.FactSalesOrder;

/* Hash toàn bộ Snapshot (thứ tự cố định). Mong đợi: 0x044F3D499F4F400FA9D20C9B63CA1FB43CFEB10B791A8D32A068B44EE2DCE52F */
SELECT HASHBYTES('SHA2_256', STRING_AGG(CONVERT(NVARCHAR(MAX), CONCAT(CustomerID,'|',SnapshotDate,'|',RecencyDays,'|',Frequency,'|',Monetary,'|',OrdersLast90Days,'|',OrdersLast180Days,'|',Tenure,'|',Share_Bikes,'|',Share_Accessories,'|',Share_Clothing,'|',NSub)), ';')
       WITHIN GROUP (ORDER BY SnapshotDate, CustomerID)) AS Snapshot_SHA256,
       0x044F3D499F4F400FA9D20C9B63CA1FB43CFEB10B791A8D32A068B44EE2DCE52F AS MongDoi
FROM analytics.CustomerSnapshot;

/* Vân tay nguồn CompanyX (để chắc hai máy dùng cùng bản sao lưu) */
SELECT (SELECT COUNT(*) FROM CompanyX.Sales.SalesOrderHeader) AS SrcOrders, 31465 AS MongDoi_Orders,
       (SELECT COUNT(*) FROM CompanyX.Sales.SalesOrderDetail) AS SrcLines, 121317 AS MongDoi_Lines,
       (SELECT COUNT(*) FROM CompanyX.Sales.Customer) AS SrcCustomers, 19820 AS MongDoi_Customers,
       (SELECT CHECKSUM_AGG(CHECKSUM(SalesOrderID, CustomerID, OrderDate, Status, TotalDue)) FROM CompanyX.Sales.SalesOrderHeader) AS SrcOrderChecksum, -1956926310 AS MongDoi_Checksum;
