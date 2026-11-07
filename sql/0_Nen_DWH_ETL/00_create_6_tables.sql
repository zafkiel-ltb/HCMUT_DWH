USE [CompanyX_DW];
SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    IF DB_NAME() <> N'CompanyX_DW'
        THROW 51001, N'Safety check failed: not in CompanyX_DW.', 1;

    BEGIN TRANSACTION;

    IF OBJECT_ID(N'dbo.DimCustomer', N'U') IS NOT NULL
       OR OBJECT_ID(N'dbo.DimDate', N'U') IS NOT NULL
       OR OBJECT_ID(N'dbo.DimProduct', N'U') IS NOT NULL
       OR OBJECT_ID(N'dbo.DimTerritory', N'U') IS NOT NULL
       OR OBJECT_ID(N'dbo.FactSalesOrder', N'U') IS NOT NULL
       OR OBJECT_ID(N'dbo.FactSalesOrderLine', N'U') IS NOT NULL
        THROW 51002, N'At least one DW table already exists. Review before re-running; nothing was dropped.', 1;

    /* 1. DIMENSIONS */
    CREATE TABLE dbo.DimCustomer (
        CustomerKey       INT IDENTITY(1,1) NOT NULL,
        CustomerID        INT NOT NULL,
        PersonID          INT NOT NULL,
        CustomerFullName  NVARCHAR(200) NULL,
        SourceTerritoryID INT NULL,
        CONSTRAINT PK_DW_DimCustomer PRIMARY KEY (CustomerKey),
        CONSTRAINT UQ_DW_DimCustomer_CustomerID UNIQUE (CustomerID)
    );

    CREATE TABLE dbo.DimDate (
        DateKey   INT NOT NULL,          -- Example: 20130630
        FullDate  DATE NOT NULL,
        [Day]     TINYINT NOT NULL,
        [Month]   TINYINT NOT NULL,
        [Quarter] TINYINT NOT NULL,
        [Year]    SMALLINT NOT NULL,
        CONSTRAINT PK_DW_DimDate PRIMARY KEY (DateKey),
        CONSTRAINT UQ_DW_DimDate_FullDate UNIQUE (FullDate),
        CONSTRAINT CK_DW_DimDate_Month CHECK ([Month] BETWEEN 1 AND 12),
        CONSTRAINT CK_DW_DimDate_Quarter CHECK ([Quarter] BETWEEN 1 AND 4),
        CONSTRAINT CK_DW_DimDate_Day CHECK ([Day] BETWEEN 1 AND 31)
    );

    CREATE TABLE dbo.DimProduct (
        ProductKey       INT IDENTITY(1,1) NOT NULL,
        ProductID        INT NOT NULL,
        ProductName      NVARCHAR(100) NOT NULL,
        SubcategoryID    INT NULL,
        SubcategoryName  NVARCHAR(100) NULL,
        CategoryID       INT NULL,
        CategoryName     NVARCHAR(100) NULL,
        CONSTRAINT PK_DW_DimProduct PRIMARY KEY (ProductKey),
        CONSTRAINT UQ_DW_DimProduct_ProductID UNIQUE (ProductID)
    );

    CREATE TABLE dbo.DimTerritory (
        TerritoryKey      INT IDENTITY(1,1) NOT NULL,
        TerritoryID       INT NOT NULL,
        TerritoryName     NVARCHAR(100) NOT NULL,
        CountryRegionCode NVARCHAR(3) NOT NULL,
        TerritoryGroup    NVARCHAR(50) NOT NULL,
        CONSTRAINT PK_DW_DimTerritory PRIMARY KEY (TerritoryKey),
        CONSTRAINT UQ_DW_DimTerritory_TerritoryID UNIQUE (TerritoryID)
    );

    /* 2. FACTS: one row per source order */
    CREATE TABLE dbo.FactSalesOrder (
        SalesOrderID INT NOT NULL,
        CustomerKey  INT NOT NULL,
        OrderDateKey INT NOT NULL,
        TerritoryKey INT NULL,             -- source TerritoryID may be NULL
        ShipDate     DATE NULL,
        DueDate      DATE NOT NULL,
        [Status]     TINYINT NOT NULL,     -- warehouse scope: shipped orders only
        SubTotal     DECIMAL(19,4) NOT NULL,
        TaxAmt       DECIMAL(19,4) NOT NULL,
        Freight      DECIMAL(19,4) NOT NULL,
        TotalDue     DECIMAL(19,4) NOT NULL,
        CONSTRAINT PK_DW_FactSalesOrder PRIMARY KEY (SalesOrderID),
        CONSTRAINT FK_DW_Order_Customer FOREIGN KEY (CustomerKey)
            REFERENCES dbo.DimCustomer(CustomerKey),
        CONSTRAINT FK_DW_Order_OrderDate FOREIGN KEY (OrderDateKey)
            REFERENCES dbo.DimDate(DateKey),
        CONSTRAINT FK_DW_Order_Territory FOREIGN KEY (TerritoryKey)
            REFERENCES dbo.DimTerritory(TerritoryKey),
        CONSTRAINT CK_DW_Order_Shipped CHECK ([Status] = 5)
    );

    /* One row per (SalesOrderID, SalesOrderDetailID), source composite PK.
       Both facts share conformed dimensions; ETL checks consistency with order header. */
    CREATE TABLE dbo.FactSalesOrderLine (
        SalesOrderID       INT NOT NULL,
        SalesOrderDetailID INT NOT NULL,
        CustomerKey        INT NOT NULL,
        OrderDateKey       INT NOT NULL,
        TerritoryKey       INT NULL,
        ProductKey         INT NOT NULL,
        OrderQty           SMALLINT NOT NULL,
        UnitPrice          DECIMAL(19,4) NOT NULL,
        UnitPriceDiscount  DECIMAL(19,4) NOT NULL,
        LineTotal          DECIMAL(19,4) NOT NULL,
        CONSTRAINT PK_DW_FactSalesOrderLine
            PRIMARY KEY (SalesOrderID, SalesOrderDetailID),
        CONSTRAINT FK_DW_Line_Customer FOREIGN KEY (CustomerKey)
            REFERENCES dbo.DimCustomer(CustomerKey),
        CONSTRAINT FK_DW_Line_OrderDate FOREIGN KEY (OrderDateKey)
            REFERENCES dbo.DimDate(DateKey),
        CONSTRAINT FK_DW_Line_Territory FOREIGN KEY (TerritoryKey)
            REFERENCES dbo.DimTerritory(TerritoryKey),
        CONSTRAINT FK_DW_Line_Product FOREIGN KEY (ProductKey)
            REFERENCES dbo.DimProduct(ProductKey),
        CONSTRAINT CK_DW_Line_Qty CHECK (OrderQty > 0),
        CONSTRAINT CK_DW_Line_Price CHECK (UnitPrice >= 0),
        CONSTRAINT CK_DW_Line_Discount
            CHECK (UnitPriceDiscount BETWEEN 0 AND 1)
    );

    COMMIT TRANSACTION;
    PRINT N'SUCCESS: created 4 dimensions, 2 facts and their PK/FK in CompanyX_DW.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;

/* 3. VERIFY RESULTS */
SELECT DB_NAME() AS CurrentDatabase,
       s.name AS SchemaName,
       t.name AS TableName
FROM sys.tables AS t
INNER JOIN sys.schemas AS s ON s.schema_id = t.schema_id
WHERE s.name = N'dbo'
  AND t.name IN (N'DimCustomer', N'DimDate', N'DimProduct', N'DimTerritory',
                 N'FactSalesOrder', N'FactSalesOrderLine')
ORDER BY t.name;

SELECT fk.name AS ForeignKeyName,
       OBJECT_NAME(fk.parent_object_id) AS FromTable,
       OBJECT_NAME(fk.referenced_object_id) AS ToTable
FROM sys.foreign_keys AS fk
WHERE OBJECT_NAME(fk.parent_object_id) IN (N'FactSalesOrder', N'FactSalesOrderLine')
ORDER BY FromTable, ForeignKeyName;
