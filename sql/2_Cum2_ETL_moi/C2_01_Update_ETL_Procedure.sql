/* ===============================================================================
   COMPANYX / CLUSTER 2 -- UPDATE EXISTING ETL ONLY
   Prerequisite: Cluster 1 completed; dbo dimensions and facts already exist.
   Execute in SSMS before running C2_02_Run_ETL_ONLY.py.
   Data source CompanyX is READ-ONLY. No procedure is executed by this script.
   Key accounting convention:
      StepLog.ExcludedRows: ALL out-of-scope rows, even if also audited as invalid.
      StepLog.RejectedRows: ONLY in-scope rejected rows (mutually exclusive).
      etl.RejectedRow logs BOTH scopes with IsInScope=0/1.
   This prevents double-counting in Source = Loaded + Excluded + Rejected.
   =============================================================================== */
USE [CompanyX_DW];
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;
IF DB_NAME() <> N'CompanyX_DW' THROW 55201, N'Wrong target: CompanyX_DW required.', 1;
IF DB_ID(N'CompanyX') IS NULL THROW 55202, N'Missing source CompanyX.', 1;
IF COL_LENGTH(N'etl.RejectedRow', N'IsInScope') IS NULL
   THROW 55203, N'Cluster 1 missing: etl.RejectedRow.IsInScope.', 1;
IF OBJECT_ID(N'dbo.FactSalesOrder', N'U') IS NULL OR OBJECT_ID(N'dbo.FactSalesOrderLine', N'U') IS NULL
   THROW 55204, N'DW Fact tables missing.', 1;
GO
/* Two staging attributes needed for the precise UnitPrice anomaly rule.
   SpecialOfferID=1 is the usual no-promotion offer in CompanyX/AdventureWorks.
   We verify the source semantics in a separate diagnostic before ETL. */
IF COL_LENGTH(N'stg.ProductRaw', N'ListPrice') IS NULL
    ALTER TABLE stg.ProductRaw ADD ListPrice DECIMAL(19,4) NULL;
IF COL_LENGTH(N'stg.OrderLineRaw', N'SpecialOfferID') IS NULL
    ALTER TABLE stg.OrderLineRaw ADD SpecialOfferID INT NULL;
GO
CREATE OR ALTER PROCEDURE etl.usp_FullLoad @RunID UNIQUEIDENTIFIER
AS
BEGIN
 SET NOCOUNT ON;
 SET XACT_ABORT ON;
 IF DB_NAME() <> N'CompanyX_DW' THROW 55205, N'Wrong target.', 1;
 IF NOT EXISTS (SELECT 1 FROM etl.RunLog WHERE RunID=@RunID)
   INSERT etl.RunLog(RunID,[Status]) VALUES(@RunID,N'RUNNING');
 BEGIN TRY
  BEGIN TRANSACTION;

  /* EXTRACT: full staging, no customer/Status filtering. */
  TRUNCATE TABLE stg.OrderLineRaw;
  TRUNCATE TABLE stg.OrderRaw;
  TRUNCATE TABLE stg.CustomerRaw;
  TRUNCATE TABLE stg.ProductRaw;
  TRUNCATE TABLE stg.TerritoryRaw;

  INSERT stg.CustomerRaw(CustomerID,PersonID,StoreID,TerritoryID,CustomerFullName)
  SELECT c.CustomerID,c.PersonID,c.StoreID,c.TerritoryID,
         NULLIF(CONCAT_WS(N' ',p.FirstName,p.MiddleName,p.LastName),N'')
  FROM CompanyX.Sales.Customer c
  LEFT JOIN CompanyX.Person.Person p ON p.BusinessEntityID=c.PersonID;

  INSERT stg.ProductRaw(ProductID,ProductName,SubcategoryID,SubcategoryName,
                             CategoryID,CategoryName,ListPrice)
  SELECT p.ProductID,p.[Name],sc.ProductSubcategoryID,sc.[Name],
         cat.ProductCategoryID,cat.[Name],p.ListPrice
  FROM CompanyX.Production.Product p
  LEFT JOIN CompanyX.Production.ProductSubcategory sc
    ON p.ProductSubcategoryID=sc.ProductSubcategoryID
  LEFT JOIN CompanyX.Production.ProductCategory cat
    ON sc.ProductCategoryID=cat.ProductCategoryID;

  INSERT stg.TerritoryRaw(TerritoryID,TerritoryName,CountryRegionCode,TerritoryGroup)
  SELECT TerritoryID,[Name],CountryRegionCode,[Group]
  FROM CompanyX.Sales.SalesTerritory;

  INSERT stg.OrderRaw(SalesOrderID,CustomerID,OrderDate,DueDate,ShipDate,[Status],
                           TerritoryID,SubTotal,TaxAmt,Freight,TotalDue)
  SELECT SalesOrderID,CustomerID,OrderDate,DueDate,ShipDate,[Status],
         TerritoryID,SubTotal,TaxAmt,Freight,TotalDue
  FROM CompanyX.Sales.SalesOrderHeader;

  INSERT stg.OrderLineRaw(SalesOrderID,SalesOrderDetailID,ProductID,OrderQty,
                               UnitPrice,UnitPriceDiscount,LineTotal,SpecialOfferID)
  SELECT SalesOrderID,SalesOrderDetailID,ProductID,OrderQty,
         UnitPrice,UnitPriceDiscount,LineTotal,SpecialOfferID
  FROM CompanyX.Sales.SalesOrderDetail;

  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows)
  SELECT @RunID,1,N'Extract.Customer',COUNT(*),COUNT(*) FROM stg.CustomerRaw;
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows)
  SELECT @RunID,2,N'Extract.Product',COUNT(*),COUNT(*) FROM stg.ProductRaw;
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows)
  SELECT @RunID,3,N'Extract.Territory',COUNT(*),COUNT(*) FROM stg.TerritoryRaw;
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows)
  SELECT @RunID,4,N'Extract.Order',COUNT(*),COUNT(*) FROM stg.OrderRaw;
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows)
  SELECT @RunID,5,N'Extract.OrderLine',COUNT(*),COUNT(*) FROM stg.OrderLineRaw;

  /* SCD Type 1 dimensions. Same four dimensions, no schema changes. */
  UPDATE d SET d.PersonID=s.PersonID, d.CustomerFullName=s.CustomerFullName,
               d.SourceTerritoryID=s.TerritoryID
  FROM dbo.DimCustomer d JOIN stg.CustomerRaw s ON s.CustomerID=d.CustomerID
  WHERE s.PersonID IS NOT NULL AND s.StoreID IS NULL;
  INSERT dbo.DimCustomer(CustomerID,PersonID,CustomerFullName,SourceTerritoryID)
  SELECT s.CustomerID,s.PersonID,s.CustomerFullName,s.TerritoryID
  FROM stg.CustomerRaw s
  WHERE s.PersonID IS NOT NULL AND s.StoreID IS NULL
    AND NOT EXISTS(SELECT 1 FROM dbo.DimCustomer d WHERE d.CustomerID=s.CustomerID);

  UPDATE d SET d.ProductName=s.ProductName,d.SubcategoryID=s.SubcategoryID,
               d.SubcategoryName=s.SubcategoryName,d.CategoryID=s.CategoryID,
               d.CategoryName=s.CategoryName
  FROM dbo.DimProduct d JOIN stg.ProductRaw s ON d.ProductID=s.ProductID;
  INSERT dbo.DimProduct(ProductID,ProductName,SubcategoryID,SubcategoryName,CategoryID,CategoryName)
  SELECT s.ProductID,s.ProductName,s.SubcategoryID,s.SubcategoryName,s.CategoryID,s.CategoryName
  FROM stg.ProductRaw s
  WHERE NOT EXISTS(SELECT 1 FROM dbo.DimProduct d WHERE d.ProductID=s.ProductID);

  UPDATE d SET d.TerritoryName=s.TerritoryName,
               d.CountryRegionCode=s.CountryRegionCode,d.TerritoryGroup=s.TerritoryGroup
  FROM dbo.DimTerritory d JOIN stg.TerritoryRaw s ON d.TerritoryID=s.TerritoryID;
  INSERT dbo.DimTerritory(TerritoryID,TerritoryName,CountryRegionCode,TerritoryGroup)
  SELECT s.TerritoryID,s.TerritoryName,s.CountryRegionCode,s.TerritoryGroup
  FROM stg.TerritoryRaw s
  WHERE NOT EXISTS(SELECT 1 FROM dbo.DimTerritory d WHERE d.TerritoryID=s.TerritoryID);

  DECLARE @FirstDate DATE=(SELECT MIN(CONVERT(DATE,OrderDate)) FROM stg.OrderRaw);
  DECLARE @LastDate DATE=(SELECT MAX(CONVERT(DATE,OrderDate)) FROM stg.OrderRaw);
  ;WITH Dates AS (
      SELECT @FirstDate AS d
      UNION ALL SELECT DATEADD(DAY,1,d) FROM Dates WHERE d<@LastDate
  )
  INSERT dbo.DimDate(DateKey,FullDate,[Day],[Month],[Quarter],[Year])
  SELECT CONVERT(INT,CONVERT(CHAR(8),v.d,112)),v.d,DAY(v.d),MONTH(v.d),
         DATEPART(QUARTER,v.d),YEAR(v.d)
  FROM Dates v
  WHERE NOT EXISTS (SELECT 1 FROM dbo.DimDate d WHERE d.FullDate=v.d)
  OPTION (MAXRECURSION 0);

  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows,ExcludedRows)
  SELECT @RunID,6,N'Load.DimCustomer',COUNT(*),
      (SELECT COUNT(*) FROM dbo.DimCustomer),
      SUM(CASE WHEN PersonID IS NOT NULL AND StoreID IS NULL THEN 0 ELSE 1 END)
  FROM stg.CustomerRaw;
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows)
  SELECT @RunID,7,N'Load.DimProduct',COUNT(*),(SELECT COUNT(*) FROM dbo.DimProduct)
  FROM stg.ProductRaw;
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows)
  SELECT @RunID,8,N'Load.DimTerritory',COUNT(*),(SELECT COUNT(*) FROM dbo.DimTerritory)
  FROM stg.TerritoryRaw;
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows)
  SELECT @RunID,9,N'Load.DimDate',COUNT(*),COUNT(*) FROM dbo.DimDate;

  /* A. VALIDATE ALL STAGED ORDERS, INCLUDING OUT-OF-SCOPE ORDERS.
     ShipDate IS NULL is invalid ONLY for Status=5, as unshipped orders may
     legitimately lack ShipDate. Missing dimension = defect only for scope=1.
     Business validity checks are applied globally before the scope filter.
  */
  ;WITH Inspected AS (
    SELECT o.SalesOrderID,
       CAST(CASE WHEN o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
            THEN 1 ELSE 0 END AS BIT) AS IsInScope,
       CASE
         WHEN EXISTS (SELECT 1 FROM stg.OrderLineRaw l
                       WHERE l.SalesOrderID=o.SalesOrderID) AND o.SubTotal<=0
           THEN N'Nonpositive SubTotal with order lines'
         WHEN o.[Status]=5 AND o.ShipDate IS NULL THEN N'Shipped order has NULL ShipDate'
         WHEN o.ShipDate IS NOT NULL AND CONVERT(DATE,o.ShipDate)<CONVERT(DATE,o.OrderDate)
           THEN N'ShipDate before OrderDate'
         WHEN o.DueDate<o.OrderDate THEN N'DueDate before OrderDate'
         WHEN o.SubTotal<0 OR o.TaxAmt<0 OR o.Freight<0 OR o.TotalDue<0
           THEN N'Negative order amount'
         WHEN ABS(o.TotalDue-(o.SubTotal+o.TaxAmt+o.Freight))>0.01
           THEN N'TotalDue reconciliation failed'
         WHEN o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
              AND dc.CustomerKey IS NULL THEN N'Customer dimension missing'
         WHEN o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
              AND dd.DateKey IS NULL THEN N'Order date dimension missing'
         WHEN o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
              AND o.TerritoryID IS NOT NULL AND ter.TerritoryKey IS NULL
           THEN N'Territory dimension missing'
       END AS Reason
    FROM stg.OrderRaw o
    LEFT JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
    LEFT JOIN dbo.DimCustomer dc ON dc.CustomerID=o.CustomerID
    LEFT JOIN dbo.DimDate dd ON dd.FullDate=CONVERT(DATE,o.OrderDate)
    LEFT JOIN dbo.DimTerritory ter ON ter.TerritoryID=o.TerritoryID
  )
  INSERT etl.RejectedRow(RunID,EntityType,SourceKey,RejectReason,IsInScope)
  SELECT @RunID,N'Order',CONVERT(NVARCHAR(100),SalesOrderID),Reason,IsInScope
  FROM Inspected WHERE Reason IS NOT NULL;

  /* B. VALIDATE ALL STAGED LINES, INCLUDING OUT-OF-SCOPE LINES.
     SpecialOfferID = 1 means standard/no-discount offer in the provided
     CompanyX schema. Do not classify promotional zero-price lines by this rule.
     Check the source offer label in C2_00_Preflight.sql before approving.
  */
  ;WITH Inspected AS (
    SELECT l.SalesOrderID,l.SalesOrderDetailID,
       CAST(CASE WHEN o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
            THEN 1 ELSE 0 END AS BIT) AS IsInScope,
       CASE
         WHEN pr.ProductID IS NULL THEN N'Product missing from source'
         WHEN l.OrderQty IS NULL OR l.OrderQty<=0 THEN N'Invalid quantity'
         WHEN l.UnitPrice IS NULL OR l.UnitPrice<0 THEN N'Invalid unit price'
         WHEN l.UnitPrice=0 AND pr.ListPrice>0 AND ISNULL(l.SpecialOfferID,1)=1
           THEN N'Zero UnitPrice; positive ListPrice; no promotion'
         WHEN l.UnitPriceDiscount NOT BETWEEN 0 AND 1 THEN N'Invalid discount'
         WHEN ABS(l.LineTotal - l.UnitPrice*(1-l.UnitPriceDiscount)*l.OrderQty)>0.01
           THEN N'LineTotal reconciliation failed'
         WHEN o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
              AND dp.ProductKey IS NULL THEN N'Product dimension missing'
       END AS Reason
    FROM stg.OrderLineRaw l
    LEFT JOIN stg.OrderRaw o ON o.SalesOrderID=l.SalesOrderID
    LEFT JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
    LEFT JOIN stg.ProductRaw pr ON pr.ProductID=l.ProductID
    LEFT JOIN dbo.DimProduct dp ON dp.ProductID=l.ProductID
  )
  INSERT etl.RejectedRow(RunID,EntityType,SourceKey,RejectReason,IsInScope)
  SELECT @RunID,N'OrderLine',
      CONCAT(CONVERT(NVARCHAR(20),SalesOrderID),N':',CONVERT(NVARCHAR(20),SalesOrderDetailID)),
      Reason,IsInScope
  FROM Inspected WHERE Reason IS NOT NULL;

  /* C. If an in-scope line is invalid, its parent order must not be loaded:
     otherwise Sum(LineTotal) <> SubTotal of its loaded header. */
  INSERT etl.RejectedRow(RunID,EntityType,SourceKey,RejectReason,IsInScope)
  SELECT @RunID,N'Order',CONVERT(NVARCHAR(100),o.SalesOrderID),
         N'An in-scope order line failed validation',CAST(1 AS BIT)
  FROM stg.OrderRaw o
  JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
  WHERE o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
    AND EXISTS (SELECT 1 FROM etl.RejectedRow r
      WHERE r.RunID=@RunID AND r.EntityType=N'OrderLine'
        AND r.IsInScope=1 AND r.SourceKey LIKE CONVERT(NVARCHAR(30),o.SalesOrderID)+N':%')
    AND NOT EXISTS (SELECT 1 FROM etl.RejectedRow r
      WHERE r.RunID=@RunID AND r.EntityType=N'Order'
        AND r.SourceKey=CONVERT(NVARCHAR(100),o.SalesOrderID));

  /* D. All children of rejected in-scope orders are rejected for accounting;
     do NOT write duplicate RejectedRow records for already-invalid lines. */
  INSERT etl.RejectedRow(RunID,EntityType,SourceKey,RejectReason,IsInScope)
  SELECT @RunID,N'OrderLine',
      CONCAT(CONVERT(NVARCHAR(20),l.SalesOrderID),N':',CONVERT(NVARCHAR(20),l.SalesOrderDetailID)),
      N'Parent in-scope order rejected',CAST(1 AS BIT)
  FROM stg.OrderLineRaw l
  JOIN etl.RejectedRow r ON r.RunID=@RunID AND r.EntityType=N'Order'
    AND r.IsInScope=1 AND r.SourceKey=CONVERT(NVARCHAR(100),l.SalesOrderID)
  WHERE NOT EXISTS (SELECT 1 FROM etl.RejectedRow oldr
    WHERE oldr.RunID=@RunID AND oldr.EntityType=N'OrderLine'
      AND oldr.SourceKey=CONCAT(CONVERT(NVARCHAR(20),l.SalesOrderID),N':',CONVERT(NVARCHAR(20),l.SalesOrderDetailID)));

  /* E. LOAD: only in-scope records not rejected. */
  DELETE FROM dbo.FactSalesOrderLine;
  DELETE FROM dbo.FactSalesOrder;
  INSERT dbo.FactSalesOrder(SalesOrderID,CustomerKey,OrderDateKey,TerritoryKey,
                                  ShipDate,DueDate,[Status],SubTotal,TaxAmt,Freight,TotalDue)
  SELECT o.SalesOrderID,dc.CustomerKey,dd.DateKey,ter.TerritoryKey,
         CONVERT(DATE,o.ShipDate),CONVERT(DATE,o.DueDate),o.[Status],
         o.SubTotal,o.TaxAmt,o.Freight,o.TotalDue
  FROM stg.OrderRaw o
  JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
  JOIN dbo.DimCustomer dc ON dc.CustomerID=o.CustomerID
  JOIN dbo.DimDate dd ON dd.FullDate=CONVERT(DATE,o.OrderDate)
  LEFT JOIN dbo.DimTerritory ter ON ter.TerritoryID=o.TerritoryID
  WHERE o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
    AND NOT EXISTS(SELECT 1 FROM etl.RejectedRow r
       WHERE r.RunID=@RunID AND r.EntityType=N'Order'
         AND r.SourceKey=CONVERT(NVARCHAR(100),o.SalesOrderID));

  INSERT dbo.FactSalesOrderLine(SalesOrderID,SalesOrderDetailID,CustomerKey,OrderDateKey,
                                    TerritoryKey,ProductKey,OrderQty,UnitPrice,
                                    UnitPriceDiscount,LineTotal)
  SELECT l.SalesOrderID,l.SalesOrderDetailID,f.CustomerKey,f.OrderDateKey,
         f.TerritoryKey,dp.ProductKey,l.OrderQty,l.UnitPrice,l.UnitPriceDiscount,l.LineTotal
  FROM stg.OrderLineRaw l
  JOIN dbo.FactSalesOrder f ON f.SalesOrderID=l.SalesOrderID
  JOIN dbo.DimProduct dp ON dp.ProductID=l.ProductID
  WHERE NOT EXISTS(SELECT 1 FROM etl.RejectedRow r
       WHERE r.RunID=@RunID AND r.EntityType=N'OrderLine'
         AND r.SourceKey=CONCAT(CONVERT(NVARCHAR(20),l.SalesOrderID),N':',CONVERT(NVARCHAR(20),l.SalesOrderDetailID)));

  /* F. Nonoverlapping accounting, while still logging out-of-scope anomalies. */
  DECLARE @ExcludedOrders INT=(
      SELECT COUNT(*) FROM stg.OrderRaw o
      LEFT JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
      WHERE NOT(o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL));
  DECLARE @RejectedOrders INT=(
      SELECT COUNT(*) FROM etl.RejectedRow
      WHERE RunID=@RunID AND EntityType=N'Order' AND IsInScope=1);
  DECLARE @ExcludedLines INT=(
      SELECT COUNT(*) FROM stg.OrderLineRaw l
      LEFT JOIN stg.OrderRaw o ON o.SalesOrderID=l.SalesOrderID
      LEFT JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
      WHERE NOT(o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL));
  DECLARE @RejectedLines INT=(
      SELECT COUNT(*) FROM etl.RejectedRow
      WHERE RunID=@RunID AND EntityType=N'OrderLine' AND IsInScope=1);

  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows,ExcludedRows,RejectedRows)
  SELECT @RunID,10,N'Load.FactSalesOrder',(SELECT COUNT(*) FROM stg.OrderRaw),
         (SELECT COUNT(*) FROM dbo.FactSalesOrder),@ExcludedOrders,@RejectedOrders;
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows,ExcludedRows,RejectedRows)
  SELECT @RunID,11,N'Load.FactSalesOrderLine',(SELECT COUNT(*) FROM stg.OrderLineRaw),
         (SELECT COUNT(*) FROM dbo.FactSalesOrderLine),@ExcludedLines,@RejectedLines;

  IF (SELECT COUNT(*) FROM stg.OrderRaw)<>
     ((SELECT COUNT(*) FROM dbo.FactSalesOrder)+@ExcludedOrders+@RejectedOrders)
     THROW 55206,N'Order reconciliation failed (scope/rejection overlap?).',1;
  IF (SELECT COUNT(*) FROM stg.OrderLineRaw)<>
     ((SELECT COUNT(*) FROM dbo.FactSalesOrderLine)+@ExcludedLines+@RejectedLines)
     THROW 55207,N'Line reconciliation failed (scope/rejection overlap?).',1;

  /* No in-scope header should remain without all its valid order lines. */
  IF EXISTS (
      SELECT 1 FROM dbo.FactSalesOrder f
      LEFT JOIN (SELECT SalesOrderID, SUM(CAST(LineTotal AS DECIMAL(38,4))) SumLines
                 FROM dbo.FactSalesOrderLine GROUP BY SalesOrderID) l
         ON l.SalesOrderID=f.SalesOrderID
      WHERE l.SalesOrderID IS NULL OR ABS(f.SubTotal-l.SumLines)>0.01
  ) THROW 55208,N'Fact financial consistency failed after quarantine.',1;

  COMMIT TRANSACTION;
  UPDATE etl.RunLog SET FinishedAt=SYSDATETIME(),[Status]=N'SUCCESS',ErrorMessage=NULL
  WHERE RunID=@RunID;
 END TRY
 BEGIN CATCH
  IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
  UPDATE etl.RunLog SET FinishedAt=SYSDATETIME(),[Status]=N'FAILED',
         ErrorMessage=ERROR_MESSAGE() WHERE RunID=@RunID;
  THROW;
 END CATCH
END;
GO
PRINT N'CLUSTER2_PROCEDURE_UPDATED; data NOT reloaded. Next: C2_02_Run_ETL_ONLY.py';
GO
