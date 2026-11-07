/* =====================================================================================
   ĐỀ XUẤT CLUSTER 1b - BỔ SUNG SCHEMA CHO CỤM 5-6 (theo đúng Chương 3, chưa có trong Cluster1_01)
   Chạy MỘT LẦN trong SSMS, database CompanyX_DW, sau Cluster1_01 và sau C3_02 (Snapshot đã có).
   Chỉ THÊM cột/bảng, không sửa, không xoá dữ liệu hiện có. Có thể chạy lại (idempotent).
   Căn cứ Chương 3:
     - 3.5.2 / Bảng 3.21: g "tính từ giá vốn và doanh thu các đơn trước mốc" -> kho cần giá vốn theo dòng đơn.
     - 3.5.3: analytics.CustomerSegment (hạng ABC + nhóm K-means tại mỗi mốc chấm điểm).
     - 3.5.5: analytics.CareRule (kho quy tắc theo phiên bản), analytics.CareRecommendation (khuyến nghị đã tạo).
   ===================================================================================== */
USE [CompanyX_DW];
SET NOCOUNT ON; SET XACT_ABORT ON; SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON;
IF DB_NAME() <> N'CompanyX_DW' THROW 51901, N'Phải chạy trong CompanyX_DW.', 1;
IF OBJECT_ID(N'analytics.CustomerSnapshot',N'U') IS NULL THROW 51902, N'Chạy Cluster1_01 và C3 trước.', 1;
BEGIN TRANSACTION;

/* 1. Giá vốn đơn vị theo dòng đơn (lấy từ ProductCostHistory tại ngày đặt, thiếu thì lấy Product.StandardCost) */
IF COL_LENGTH(N'dbo.FactSalesOrderLine', N'UnitCost') IS NULL
    ALTER TABLE dbo.FactSalesOrderLine ADD UnitCost DECIMAL(19,4) NULL;
IF COL_LENGTH(N'dbo.DimProduct', N'StandardCost') IS NULL
    ALTER TABLE dbo.DimProduct ADD StandardCost DECIMAL(19,4) NULL;
COMMIT TRANSACTION;   -- cột phải tồn tại trước khi UPDATE ở batch sau
GO
SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON; SET XACT_ABORT ON;
BEGIN TRANSACTION;
UPDATE l SET l.UnitCost = ISNULL(h.StandardCost, p.StandardCost)
FROM dbo.FactSalesOrderLine l
JOIN dbo.DimProduct dp ON dp.ProductKey = l.ProductKey
JOIN dbo.DimDate d ON d.DateKey = l.OrderDateKey
JOIN CompanyX.Production.Product p ON p.ProductID = dp.ProductID
LEFT JOIN CompanyX.Production.ProductCostHistory h ON h.ProductID = p.ProductID
     AND d.FullDate >= CAST(h.StartDate AS DATE) AND (h.EndDate IS NULL OR d.FullDate < CAST(h.EndDate AS DATE))
WHERE l.UnitCost IS NULL;
UPDATE dp SET dp.StandardCost = p.StandardCost
FROM dbo.DimProduct dp JOIN CompanyX.Production.Product p ON p.ProductID = dp.ProductID WHERE dp.StandardCost IS NULL;
IF EXISTS (SELECT 1 FROM dbo.FactSalesOrderLine WHERE UnitCost IS NULL) THROW 51903, N'Còn dòng chưa có UnitCost.', 1;

/* 2. analytics.CustomerSegment - hạng ABC và nhóm tại mỗi mốc chấm điểm (3.5.3) */
IF OBJECT_ID(N'analytics.CustomerSegment',N'U') IS NULL
CREATE TABLE analytics.CustomerSegment (
    CustomerID        INT          NOT NULL,
    SnapshotDate      DATE         NOT NULL,
    ClusterModelVersion NVARCHAR(80) NOT NULL,          -- ModelRegistry.ModelRole = CLUSTERING
    ABCClass          NCHAR(1)     NOT NULL,            -- A / B / C theo (3.19), ngưỡng 80% / 95%
    CumShare          DECIMAL(9,6) NOT NULL,            -- S(k-1) của khách
    ClusterID         TINYINT      NOT NULL,            -- 1..5 (N1..N5)
    ClusterName       NVARCHAR(40) NULL,                -- tên nhóm theo hồ sơ R-F-M (Bảng 3.24)
    DistanceToCenter  DECIMAL(12,6) NULL,
    CreatedAt         DATETIME2(0) NOT NULL CONSTRAINT DF_CustomerSegment_CreatedAt DEFAULT SYSDATETIME(),
    CONSTRAINT PK_Analytics_CustomerSegment PRIMARY KEY (CustomerID, SnapshotDate, ClusterModelVersion),
    CONSTRAINT FK_Analytics_Segment_Snapshot FOREIGN KEY (CustomerID, SnapshotDate) REFERENCES analytics.CustomerSnapshot(CustomerID, SnapshotDate),
    CONSTRAINT FK_Analytics_Segment_Model FOREIGN KEY (ClusterModelVersion) REFERENCES analytics.ModelRegistry(ModelVersion),
    CONSTRAINT CK_Analytics_Segment_ABC CHECK (ABCClass IN (N'A', N'B', N'C')),
    CONSTRAINT CK_Analytics_Segment_Cluster CHECK (ClusterID BETWEEN 1 AND 9)
);

/* 3. analytics.CareRule - kho quy tắc theo phiên bản (3.5.5, Bảng 3.30) */
IF OBJECT_ID(N'analytics.CareRule',N'U') IS NULL
CREATE TABLE analytics.CareRule (
    RuleCode       NVARCHAR(10)  NOT NULL,              -- R1..R9
    RuleVersion    INT           NOT NULL,
    RuleType       NVARCHAR(40)  NOT NULL,              -- Loại trừ / Hình thức liên hệ / Sản phẩm gợi ý / Giám sát mô hình
    ConditionText  NVARCHAR(1000) NOT NULL,             -- IF
    ActionText     NVARCHAR(1000) NOT NULL,             -- THEN
    Rationale      NVARCHAR(1000) NULL,                 -- căn cứ
    ChannelCost    DECIMAL(9,2)  NULL,                  -- c_k (Bảng 3.26a), chỉ với quy tắc hình thức liên hệ
    ChannelSuccess DECIMAL(5,4)  NULL,                  -- r_k
    IsActive       BIT           NOT NULL CONSTRAINT DF_CareRule_IsActive DEFAULT 1,
    EffectiveFrom  DATE          NOT NULL,
    EffectiveTo    DATE          NULL,
    UpdatedBy      NVARCHAR(100) NULL,
    UpdatedAt      DATETIME2(0)  NOT NULL CONSTRAINT DF_CareRule_UpdatedAt DEFAULT SYSDATETIME(),
    CONSTRAINT PK_Analytics_CareRule PRIMARY KEY (RuleCode, RuleVersion),
    CONSTRAINT CK_Analytics_CareRule_Succ CHECK (ChannelSuccess IS NULL OR (ChannelSuccess >= 0 AND ChannelSuccess <= 1))
);

/* 4. analytics.CareRecommendation - khuyến nghị đã tạo cho một kịch bản (3.5.4, 3.5.5, màn hình 3-4) */
IF OBJECT_ID(N'analytics.CareRecommendation',N'U') IS NULL
CREATE TABLE analytics.CareRecommendation (
    RecommendationID BIGINT IDENTITY(1,1) NOT NULL,
    ScenarioID       NVARCHAR(80)  NOT NULL,            -- mã kịch bản (B, r, c, ngày chấm điểm, phiên bản mô hình)
    CustomerID       INT           NOT NULL,
    ScoreDate        DATE          NOT NULL,
    ModelVersion     NVARCHAR(80)  NOT NULL,
    RiskScore        DECIMAL(9,6)  NOT NULL,            -- p_i tại thời điểm tạo
    CustomerValue    DECIMAL(19,4) NOT NULL,            -- v_i = g * AOV_i
    ExpectedValue    DECIMAL(19,4) NOT NULL,            -- p_i * r_k * v_i - c_k
    ChannelRule      NVARCHAR(10)  NULL,                -- R3 / R4 / R5
    ChannelCost      DECIMAL(9,2)  NULL,
    ProductRules     NVARCHAR(200) NULL,                -- ví dụ 'R6,R8'
    SuggestedProducts NVARCHAR(400) NULL,
    Explanation      NVARCHAR(MAX) NULL,                -- quy tắc kích hoạt + TopFactors
    IsSelected       BIT           NOT NULL CONSTRAINT DF_CareRec_IsSelected DEFAULT 1,
    ManualOverride   NVARCHAR(400) NULL,                -- lý do thêm/bớt thủ công
    CreatedBy        NVARCHAR(100) NULL,
    CreatedAt        DATETIME2(0)  NOT NULL CONSTRAINT DF_CareRec_CreatedAt DEFAULT SYSDATETIME(),
    CONSTRAINT PK_Analytics_CareRecommendation PRIMARY KEY (RecommendationID),
    CONSTRAINT UQ_Analytics_CareRec UNIQUE (ScenarioID, CustomerID),
    CONSTRAINT FK_Analytics_CareRec_Score FOREIGN KEY (CustomerID, ScoreDate, ModelVersion) REFERENCES analytics.CustomerRiskScore(CustomerID, ScoreDate, ModelVersion)
);
COMMIT TRANSACTION;

/* 5. Kiểm tra */
SELECT N'UnitCost null' AS Check_, COUNT(*) AS N FROM dbo.FactSalesOrderLine WHERE UnitCost IS NULL
UNION ALL SELECT N'g toan kho (1 - COGS/Revenue)', CAST(ROUND(1 - SUM(UnitCost*OrderQty)/SUM(LineTotal), 4) * 10000 AS INT) FROM dbo.FactSalesOrderLine   -- mong đợi 4115 (= 0,4115)
UNION ALL SELECT N'Bang CustomerSegment', CASE WHEN OBJECT_ID(N'analytics.CustomerSegment') IS NULL THEN 0 ELSE 1 END
UNION ALL SELECT N'Bang CareRule', CASE WHEN OBJECT_ID(N'analytics.CareRule') IS NULL THEN 0 ELSE 1 END
UNION ALL SELECT N'Bang CareRecommendation', CASE WHEN OBJECT_ID(N'analytics.CareRecommendation') IS NULL THEN 0 ELSE 1 END;
PRINT N'CLUSTER_1B_OK: UnitCost/StandardCost + 3 bảng analytics cho cụm 5-6.';
GO
