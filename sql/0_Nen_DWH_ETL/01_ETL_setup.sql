/* COMPANYX - ETL 4.2.2 | Run ONCE in SSMS, database: CompanyX_DW.
   Requires the existing 4 Dim + 2 Fact tables created in 4.2.1.
   Source CompanyX is READ-ONLY in this script. Does not drop any DW Fact/Dim.
   Model: Python orchestrates SQL stored procedures on the same SQL Server instance.
*/
USE [CompanyX_DW];
GO
IF DB_ID(N'CompanyX') IS NULL OR DB_ID(N'CompanyX_DW') IS NULL
    THROW 52001, 'CompanyX and CompanyX_DW must both exist on this instance.', 1;
IF OBJECT_ID(N'dbo.FactSalesOrderLine', N'U') IS NULL OR OBJECT_ID(N'dbo.FactSalesOrder', N'U') IS NULL
    THROW 52002, 'Run the 4.2.1 six-table DDL before this ETL setup.', 1;
GO
IF SCHEMA_ID(N'stg') IS NULL EXEC(N'CREATE SCHEMA stg');
IF SCHEMA_ID(N'etl') IS NULL EXEC(N'CREATE SCHEMA etl');
IF SCHEMA_ID(N'analytics') IS NULL EXEC(N'CREATE SCHEMA analytics');
GO
IF OBJECT_ID(N'etl.RunLog',N'U') IS NULL
CREATE TABLE etl.RunLog (
    RunID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
    StartedAt DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
    FinishedAt DATETIME2(0) NULL,
    [Status] NVARCHAR(20) NOT NULL,
    ErrorMessage NVARCHAR(4000) NULL
);
IF OBJECT_ID(N'etl.StepLog',N'U') IS NULL
CREATE TABLE etl.StepLog (
    RunID UNIQUEIDENTIFIER NOT NULL,
    StepNo INT NOT NULL,
    StepName NVARCHAR(80) NOT NULL,
    SourceRows INT NOT NULL,
    LoadedRows INT NOT NULL,
    ExcludedRows INT NOT NULL DEFAULT 0,
    RejectedRows INT NOT NULL DEFAULT 0,
    CONSTRAINT PK_ETL_StepLog PRIMARY KEY (RunID,StepNo),
    CONSTRAINT FK_ETL_StepLog_Run FOREIGN KEY (RunID) REFERENCES etl.RunLog(RunID)
);
IF OBJECT_ID(N'etl.RejectedRow',N'U') IS NULL
CREATE TABLE etl.RejectedRow (
    RejectID BIGINT IDENTITY(1,1) PRIMARY KEY,
    RunID UNIQUEIDENTIFIER NOT NULL,
    EntityType NVARCHAR(30) NOT NULL,
    SourceKey NVARCHAR(100) NOT NULL,
    RejectReason NVARCHAR(200) NOT NULL
);
GO
IF OBJECT_ID(N'stg.CustomerRaw',N'U') IS NULL
CREATE TABLE stg.CustomerRaw (
 CustomerID INT NOT NULL PRIMARY KEY, PersonID INT NULL, StoreID INT NULL,
 TerritoryID INT NULL, CustomerFullName NVARCHAR(200) NULL
);
IF OBJECT_ID(N'stg.ProductRaw',N'U') IS NULL
CREATE TABLE stg.ProductRaw (
 ProductID INT NOT NULL PRIMARY KEY, ProductName NVARCHAR(100) NULL,
 SubcategoryID INT NULL, SubcategoryName NVARCHAR(100) NULL,
 CategoryID INT NULL, CategoryName NVARCHAR(100) NULL
);
IF OBJECT_ID(N'stg.TerritoryRaw',N'U') IS NULL
CREATE TABLE stg.TerritoryRaw (
 TerritoryID INT NOT NULL PRIMARY KEY, TerritoryName NVARCHAR(100) NULL,
 CountryRegionCode NVARCHAR(3) NULL, TerritoryGroup NVARCHAR(50) NULL
);
IF OBJECT_ID(N'stg.OrderRaw',N'U') IS NULL
CREATE TABLE stg.OrderRaw (
 SalesOrderID INT NOT NULL PRIMARY KEY, CustomerID INT NOT NULL,
 OrderDate DATETIME NOT NULL, DueDate DATETIME NOT NULL, ShipDate DATETIME NULL,
 [Status] TINYINT NOT NULL, TerritoryID INT NULL,
 SubTotal DECIMAL(19,4) NOT NULL, TaxAmt DECIMAL(19,4) NOT NULL,
 Freight DECIMAL(19,4) NOT NULL, TotalDue DECIMAL(19,4) NOT NULL
);
IF OBJECT_ID(N'stg.OrderLineRaw',N'U') IS NULL
CREATE TABLE stg.OrderLineRaw (
 SalesOrderID INT NOT NULL, SalesOrderDetailID INT NOT NULL, ProductID INT NOT NULL,
 OrderQty SMALLINT NULL, UnitPrice DECIMAL(19,4) NULL,
 UnitPriceDiscount DECIMAL(19,4) NOT NULL, LineTotal DECIMAL(19,4) NOT NULL,
 CONSTRAINT PK_stg_OrderLineRaw PRIMARY KEY(SalesOrderID,SalesOrderDetailID)
);
GO
/* Use a validated snapshot time to avoid ML using future transaction data. */
IF OBJECT_ID(N'analytics.CustomerSnapshot', N'U') IS NULL
CREATE TABLE analytics.CustomerSnapshot (
 CustomerID INT NOT NULL,
 SnapshotDate DATE NOT NULL,
 CustomerKey INT NOT NULL,
 RecencyDays INT NOT NULL,
 Frequency INT NOT NULL,
 Monetary DECIMAL(19,4) NOT NULL,
 OrdersLast90Days INT NOT NULL,
 OrdersLast180Days INT NOT NULL,
 CONSTRAINT PK_Analytics_CustomerSnapshot PRIMARY KEY(CustomerID,SnapshotDate),
 CONSTRAINT FK_Analytics_SnapshotCustomer FOREIGN KEY(CustomerKey)
      REFERENCES dbo.DimCustomer(CustomerKey)
);
GO
CREATE OR ALTER PROCEDURE etl.usp_FullLoad @RunID UNIQUEIDENTIFIER
AS
BEGIN
 SET NOCOUNT ON;
 SET XACT_ABORT ON;
 IF DB_NAME() <> N'CompanyX_DW' THROW 52003,'Wrong target database',1;
 IF NOT EXISTS (SELECT 1 FROM etl.RunLog WHERE RunID=@RunID)
  INSERT etl.RunLog(RunID,[Status]) VALUES(@RunID,N'RUNNING');
 BEGIN TRY
  BEGIN TRANSACTION;
  /* EXTRACT: whole relevant source tables, before filtering; source is not modified */
  TRUNCATE TABLE stg.OrderLineRaw;
  TRUNCATE TABLE stg.OrderRaw;
  TRUNCATE TABLE stg.CustomerRaw;
  TRUNCATE TABLE stg.ProductRaw;
  TRUNCATE TABLE stg.TerritoryRaw;

  INSERT stg.CustomerRaw(CustomerID,PersonID,StoreID,TerritoryID,CustomerFullName)
  SELECT c.CustomerID,c.PersonID,c.StoreID,c.TerritoryID,
         NULLIF(CONCAT_WS(N' ',p.FirstName,p.MiddleName,p.LastName),N'')
  FROM CompanyX.Sales.Customer AS c
  LEFT JOIN CompanyX.Person.Person AS p ON p.BusinessEntityID=c.PersonID;

  INSERT stg.ProductRaw(ProductID,ProductName,SubcategoryID,SubcategoryName,CategoryID,CategoryName)
  SELECT p.ProductID,p.[Name],sc.ProductSubcategoryID,sc.[Name],cat.ProductCategoryID,cat.[Name]
  FROM CompanyX.Production.Product AS p
  LEFT JOIN CompanyX.Production.ProductSubcategory sc
       ON p.ProductSubcategoryID=sc.ProductSubcategoryID
  LEFT JOIN CompanyX.Production.ProductCategory cat
       ON sc.ProductCategoryID=cat.ProductCategoryID;

  INSERT stg.TerritoryRaw(TerritoryID,TerritoryName,CountryRegionCode,TerritoryGroup)
  SELECT TerritoryID,[Name],CountryRegionCode,[Group]
  FROM CompanyX.Sales.SalesTerritory;

  INSERT stg.OrderRaw(SalesOrderID,CustomerID,OrderDate,DueDate,ShipDate,[Status],TerritoryID,
                      SubTotal,TaxAmt,Freight,TotalDue)
  SELECT SalesOrderID,CustomerID,OrderDate,DueDate,ShipDate,[Status],TerritoryID,
         SubTotal,TaxAmt,Freight,TotalDue
  FROM CompanyX.Sales.SalesOrderHeader;

  INSERT stg.OrderLineRaw(SalesOrderID,SalesOrderDetailID,ProductID,OrderQty,UnitPrice,
                           UnitPriceDiscount,LineTotal)
  SELECT SalesOrderID,SalesOrderDetailID,ProductID,OrderQty,UnitPrice,
         UnitPriceDiscount,LineTotal
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

  /* TRANSFORM & LOAD DIMENSIONS: preserve surrogate keys across repeat executions */
  UPDATE d SET d.PersonID=s.PersonID, d.CustomerFullName=s.CustomerFullName,
               d.SourceTerritoryID=s.TerritoryID
  FROM dbo.DimCustomer d JOIN stg.CustomerRaw s ON s.CustomerID=d.CustomerID
  WHERE s.PersonID IS NOT NULL AND s.StoreID IS NULL;
  INSERT dbo.DimCustomer(CustomerID,PersonID,CustomerFullName,SourceTerritoryID)
  SELECT s.CustomerID,s.PersonID,s.CustomerFullName,s.TerritoryID
  FROM stg.CustomerRaw s
  WHERE s.PersonID IS NOT NULL AND s.StoreID IS NULL
    AND NOT EXISTS (SELECT 1 FROM dbo.DimCustomer d WHERE d.CustomerID=s.CustomerID);

  UPDATE d SET d.ProductName=s.ProductName,d.SubcategoryID=s.SubcategoryID,
               d.SubcategoryName=s.SubcategoryName,d.CategoryID=s.CategoryID,
               d.CategoryName=s.CategoryName
  FROM dbo.DimProduct d JOIN stg.ProductRaw s ON d.ProductID=s.ProductID;
  INSERT dbo.DimProduct(ProductID,ProductName,SubcategoryID,SubcategoryName,CategoryID,CategoryName)
  SELECT s.ProductID,s.ProductName,s.SubcategoryID,s.SubcategoryName,s.CategoryID,s.CategoryName
  FROM stg.ProductRaw s
  WHERE NOT EXISTS (SELECT 1 FROM dbo.DimProduct d WHERE d.ProductID=s.ProductID);

  UPDATE d SET d.TerritoryName=s.TerritoryName,
               d.CountryRegionCode=s.CountryRegionCode,d.TerritoryGroup=s.TerritoryGroup
  FROM dbo.DimTerritory d JOIN stg.TerritoryRaw s ON d.TerritoryID=s.TerritoryID;
  INSERT dbo.DimTerritory(TerritoryID,TerritoryName,CountryRegionCode,TerritoryGroup)
  SELECT s.TerritoryID,s.TerritoryName,s.CountryRegionCode,s.TerritoryGroup
  FROM stg.TerritoryRaw s
  WHERE NOT EXISTS (SELECT 1 FROM dbo.DimTerritory d WHERE d.TerritoryID=s.TerritoryID);

  /* A complete calendar over order dates; for the fixed sample, ~3 years. */
  DECLARE @FirstDate DATE=(SELECT MIN(CAST(OrderDate AS DATE)) FROM stg.OrderRaw);
  DECLARE @LastDate DATE=(SELECT MAX(CAST(OrderDate AS DATE)) FROM stg.OrderRaw);
  ;WITH Dates AS (
      SELECT @FirstDate AS d
      UNION ALL SELECT DATEADD(DAY,1,d) FROM Dates WHERE d < @LastDate
  )
  INSERT dbo.DimDate(DateKey,FullDate,[Day],[Month],[Quarter],[Year])
  SELECT CONVERT(INT,CONVERT(CHAR(8),v.d,112)),v.d,DAY(v.d),MONTH(v.d),
         DATEPART(QUARTER,v.d),YEAR(v.d)
  FROM Dates v
  WHERE NOT EXISTS(SELECT 1 FROM dbo.DimDate dd WHERE dd.FullDate=v.d)
  OPTION(MAXRECURSION 0);

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

  /* VALIDATE shipped individual orders; excluded = outside business scope, rejected = invalid within scope. */
  INSERT etl.RejectedRow(RunID,EntityType,SourceKey,RejectReason)
  SELECT @RunID,N'Order',CONVERT(NVARCHAR(100),o.SalesOrderID),
   CASE
      WHEN o.ShipDate IS NULL THEN N'Shipped order has NULL ShipDate'
      WHEN CAST(o.ShipDate AS DATE) < CAST(o.OrderDate AS DATE) THEN N'ShipDate before OrderDate'
      WHEN o.DueDate < o.OrderDate THEN N'DueDate before OrderDate'
      WHEN o.SubTotal < 0 OR o.TaxAmt < 0 OR o.Freight < 0 OR o.TotalDue < 0 THEN N'Negative order amount'
      WHEN ABS(o.TotalDue - (o.SubTotal+o.TaxAmt+o.Freight)) > 0.01 THEN N'TotalDue reconciliation failed'
      WHEN dc.CustomerKey IS NULL THEN N'Customer dimension missing'
      WHEN dt.DateKey IS NULL THEN N'Order date dimension missing'
      WHEN o.TerritoryID IS NOT NULL AND ter.TerritoryKey IS NULL THEN N'Territory dimension missing'
   END
  FROM stg.OrderRaw o
  JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
  LEFT JOIN dbo.DimCustomer dc ON dc.CustomerID=o.CustomerID
  LEFT JOIN dbo.DimDate dt ON dt.FullDate=CAST(o.OrderDate AS DATE)
  LEFT JOIN dbo.DimTerritory ter ON ter.TerritoryID=o.TerritoryID
  WHERE c.PersonID IS NOT NULL AND c.StoreID IS NULL AND o.[Status]=5
  AND (o.ShipDate IS NULL OR CAST(o.ShipDate AS DATE)<CAST(o.OrderDate AS DATE)
       OR o.DueDate<o.OrderDate OR o.SubTotal<0 OR o.TaxAmt<0 OR o.Freight<0
       OR o.TotalDue<0 OR ABS(o.TotalDue-(o.SubTotal+o.TaxAmt+o.Freight))>0.01
       OR dc.CustomerKey IS NULL OR dt.DateKey IS NULL
       OR (o.TerritoryID IS NOT NULL AND ter.TerritoryKey IS NULL));

  /* FULL REFRESH facts: identities of dimensions remain stable, repeat runs do not duplicate facts. */
  DELETE FROM dbo.FactSalesOrderLine;
  DELETE FROM dbo.FactSalesOrder;
  INSERT dbo.FactSalesOrder(SalesOrderID,CustomerKey,OrderDateKey,TerritoryKey,
                                 ShipDate,DueDate,[Status],SubTotal,TaxAmt,Freight,TotalDue)
  SELECT o.SalesOrderID,dc.CustomerKey,dt.DateKey,ter.TerritoryKey,
         CAST(o.ShipDate AS DATE),CAST(o.DueDate AS DATE),o.[Status],
         o.SubTotal,o.TaxAmt,o.Freight,o.TotalDue
  FROM stg.OrderRaw o
  JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
  JOIN dbo.DimCustomer dc ON dc.CustomerID=o.CustomerID
  JOIN dbo.DimDate dt ON dt.FullDate=CAST(o.OrderDate AS DATE)
  LEFT JOIN dbo.DimTerritory ter ON ter.TerritoryID=o.TerritoryID
  WHERE c.PersonID IS NOT NULL AND c.StoreID IS NULL AND o.[Status]=5
    AND NOT EXISTS (
       SELECT 1 FROM etl.RejectedRow r WHERE r.RunID=@RunID AND r.EntityType=N'Order'
         AND r.SourceKey=CONVERT(NVARCHAR(100),o.SalesOrderID)
    );

  /* Check lines from fact orders (already valid), quarantine lines with invalid product/values. */
  INSERT etl.RejectedRow(RunID,EntityType,SourceKey,RejectReason)
  SELECT @RunID,N'OrderLine',CONCAT(CONVERT(NVARCHAR(20),ol.SalesOrderID),N':',CONVERT(NVARCHAR(20),ol.SalesOrderDetailID)),
    CASE WHEN dp.ProductKey IS NULL THEN N'Product dimension missing'
         WHEN ol.OrderQty IS NULL OR ol.OrderQty<=0 THEN N'Invalid quantity'
         WHEN ol.UnitPrice IS NULL OR ol.UnitPrice<0 THEN N'Invalid unit price'
         WHEN ol.UnitPriceDiscount<0 OR ol.UnitPriceDiscount>1 THEN N'Invalid discount'
         WHEN ABS(ol.LineTotal - ol.UnitPrice*(1-ol.UnitPriceDiscount)*ol.OrderQty)>0.01 THEN N'LineTotal reconciliation failed'
    END
  FROM stg.OrderLineRaw ol
  JOIN dbo.FactSalesOrder f ON f.SalesOrderID=ol.SalesOrderID
  LEFT JOIN dbo.DimProduct dp ON dp.ProductID=ol.ProductID
  WHERE dp.ProductKey IS NULL OR ol.OrderQty IS NULL OR ol.OrderQty<=0
        OR ol.UnitPrice IS NULL OR ol.UnitPrice<0
        OR ol.UnitPriceDiscount<0 OR ol.UnitPriceDiscount>1
        OR ABS(ol.LineTotal - ol.UnitPrice*(1-ol.UnitPriceDiscount)*ol.OrderQty)>0.01;

  INSERT dbo.FactSalesOrderLine(
       SalesOrderID,SalesOrderDetailID,CustomerKey,OrderDateKey,TerritoryKey,
       ProductKey,OrderQty,UnitPrice,UnitPriceDiscount,LineTotal)
  SELECT ol.SalesOrderID,ol.SalesOrderDetailID,f.CustomerKey,f.OrderDateKey,
         f.TerritoryKey,dp.ProductKey,ol.OrderQty,ol.UnitPrice,ol.UnitPriceDiscount,ol.LineTotal
  FROM stg.OrderLineRaw ol
  JOIN dbo.FactSalesOrder f ON f.SalesOrderID=ol.SalesOrderID
  JOIN dbo.DimProduct dp ON dp.ProductID=ol.ProductID
  WHERE NOT EXISTS (
    SELECT 1 FROM etl.RejectedRow r WHERE r.RunID=@RunID AND r.EntityType=N'OrderLine'
      AND r.SourceKey=CONCAT(CONVERT(NVARCHAR(20),ol.SalesOrderID),N':',CONVERT(NVARCHAR(20),ol.SalesOrderDetailID))
  );

  /* Child lines of rejected in-scope orders must also be counted as rejected;
     otherwise source-read = excluded + rejected + loaded will fail. */
  INSERT etl.RejectedRow(RunID,EntityType,SourceKey,RejectReason)
  SELECT @RunID,N'OrderLine',
         CONCAT(CONVERT(NVARCHAR(20),ol.SalesOrderID),N':',CONVERT(NVARCHAR(20),ol.SalesOrderDetailID)),
         N'Parent shipped order rejected in validation'
  FROM stg.OrderLineRaw ol
  JOIN etl.RejectedRow r ON r.RunID=@RunID AND r.EntityType=N'Order'
       AND r.SourceKey=CONVERT(NVARCHAR(100),ol.SalesOrderID);

  DECLARE @ExcludedOrders INT=(
   SELECT COUNT(*) FROM stg.OrderRaw o LEFT JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
   WHERE NOT(o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL)
  );
  DECLARE @RejectedOrders INT=(SELECT COUNT(*) FROM etl.RejectedRow
                                 WHERE RunID=@RunID AND EntityType=N'Order');
  DECLARE @RejectedLines INT=(SELECT COUNT(*) FROM etl.RejectedRow
                                 WHERE RunID=@RunID AND EntityType=N'OrderLine');
  DECLARE @ExcludedLines INT=(
   SELECT COUNT(*) FROM stg.OrderLineRaw ol
   WHERE NOT EXISTS (
       SELECT 1 FROM stg.OrderRaw o
       JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
       WHERE o.SalesOrderID=ol.SalesOrderID AND o.[Status]=5
         AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
   )
  );
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows,ExcludedRows,RejectedRows)
  SELECT @RunID,10,N'Load.FactSalesOrder',(SELECT COUNT(*) FROM stg.OrderRaw),
   (SELECT COUNT(*) FROM dbo.FactSalesOrder),@ExcludedOrders,@RejectedOrders;
  INSERT etl.StepLog(RunID,StepNo,StepName,SourceRows,LoadedRows,ExcludedRows,RejectedRows)
  SELECT @RunID,11,N'Load.FactSalesOrderLine',(SELECT COUNT(*) FROM stg.OrderLineRaw),
   (SELECT COUNT(*) FROM dbo.FactSalesOrderLine),@ExcludedLines,@RejectedLines;

  /* Stop on count mismatches instead of claiming success; in-source invalid lines are quarantined. */
  IF (SELECT COUNT(*) FROM dbo.FactSalesOrder) + @ExcludedOrders + @RejectedOrders
    <> (SELECT COUNT(*) FROM stg.OrderRaw)
    THROW 52004,N'Order count reconciliation failed',1;
  IF (SELECT COUNT(*) FROM dbo.FactSalesOrderLine) + @ExcludedLines + @RejectedLines
    <> (SELECT COUNT(*) FROM stg.OrderLineRaw)
    THROW 52005,N'Order line count reconciliation failed',1;

  COMMIT TRANSACTION;
  UPDATE etl.RunLog SET FinishedAt=SYSDATETIME(),[Status]=N'SUCCESS' WHERE RunID=@RunID;
 END TRY
 BEGIN CATCH
  IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
  UPDATE etl.RunLog SET FinishedAt=SYSDATETIME(),[Status]=N'FAILED',
      ErrorMessage=ERROR_MESSAGE() WHERE RunID=@RunID;
  THROW;
 END CATCH
END;
GO
PRINT 'SETUP_OK: staging, ETL audit and procedures are ready; no source data modified.';
GO
