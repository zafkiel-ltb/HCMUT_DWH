/* ============================================================================
   COMPANYX_DW / CLUSTER 1: SCHEMA UPGRADE ONLY
   SSMS, SQL Server 2025. Execute after backing up CompanyX_DW.

   Does NOT touch OLTP CompanyX, six Dim/Fact tables, rows in Fact tables,
   stored procedures, snapshot content, or ETL logs.
   Designed to be rerunnable. All changes in one transaction.

   Owner of subsequent population:
     IsInScope                  -> Cluster 2 (revised ETL)
     Tenure, Share_*, NSub      -> Cluster 3 (revised snapshot builder)
     ModelRegistry, RiskScore   -> Clusters 4/5 (model training and scoring)
   ============================================================================ */
USE [CompanyX_DW];
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    IF DB_NAME() <> N'CompanyX_DW'
        THROW 54101, N'Safety stop: select CompanyX_DW.', 1;
    IF OBJECT_ID(N'etl.RejectedRow', N'U') IS NULL
        THROW 54102, N'Missing etl.RejectedRow. First run the EXISTING 01_ETL_setup.sql.', 1;
    IF OBJECT_ID(N'analytics.CustomerSnapshot', N'U') IS NULL
        THROW 54103, N'Missing analytics.CustomerSnapshot. First run the EXISTING 01_ETL_setup.sql.', 1;
    IF OBJECT_ID(N'dbo.DimCustomer', N'U') IS NULL
        THROW 54104, N'Missing dbo.DimCustomer.', 1;

    BEGIN TRANSACTION;

    /* A. New flag on existing reject log. NULL = legacy row not yet classified.
       1 = within study scope; 0 = outside study scope.
       A NEW ETL run in Cluster 2 must populate this explicitly. */
    IF COL_LENGTH(N'etl.RejectedRow', N'IsInScope') IS NULL
        ALTER TABLE etl.RejectedRow ADD IsInScope BIT NULL;

    /* B. Snapshot feature schema only. Existing rows remain, new values NULL.
       Do not set DEFAULT 0: NULL correctly means not computed yet. */
    IF COL_LENGTH(N'analytics.CustomerSnapshot', N'Tenure') IS NULL
        ALTER TABLE analytics.CustomerSnapshot ADD Tenure INT NULL;
    IF COL_LENGTH(N'analytics.CustomerSnapshot', N'Share_Bikes') IS NULL
        ALTER TABLE analytics.CustomerSnapshot ADD Share_Bikes DECIMAL(9,6) NULL;
    IF COL_LENGTH(N'analytics.CustomerSnapshot', N'Share_Accessories') IS NULL
        ALTER TABLE analytics.CustomerSnapshot ADD Share_Accessories DECIMAL(9,6) NULL;
    IF COL_LENGTH(N'analytics.CustomerSnapshot', N'Share_Clothing') IS NULL
        ALTER TABLE analytics.CustomerSnapshot ADD Share_Clothing DECIMAL(9,6) NULL;
    IF COL_LENGTH(N'analytics.CustomerSnapshot', N'NSub') IS NULL
        ALTER TABLE analytics.CustomerSnapshot ADD NSub INT NULL;

    /* C. Model management table. ConfigurationJSON may contain network layers,
       random seed, Gini/tree settings, m-estimate, threshold and scaler settings.
       ArtifactPath points to files stored outside SQL Server. */
    IF OBJECT_ID(N'analytics.ModelRegistry', N'U') IS NULL
    BEGIN
        CREATE TABLE analytics.ModelRegistry (
            ModelVersion      NVARCHAR(80) NOT NULL,
            ModelRole         NVARCHAR(20) NOT NULL,  -- SCORING / TREE / CLUSTERING / COMPARISON
            ModelType         NVARCHAR(60) NOT NULL,  -- MLP / CART / NB / LR / ...
            TrainingSnapshot  DATE NULL,
            FeatureList       NVARCHAR(MAX) NULL,
            ConfigurationJSON NVARCHAR(MAX) NULL,
            ArtifactPath      NVARCHAR(500) NULL,
            ScalerPath        NVARCHAR(500) NULL,
            TrainBaseRate     DECIMAL(9,6) NULL,
            DecisionThreshold DECIMAL(9,6) NULL,
            ROCAUC            DECIMAL(9,6) NULL,
            BrierScore        DECIMAL(9,6) NULL,
            EffectiveFrom     DATE NULL,
            IsActive          BIT NOT NULL CONSTRAINT DF_ModelRegistry_IsActive DEFAULT (0),
            CreatedAt         DATETIME2(0) NOT NULL CONSTRAINT DF_ModelRegistry_CreatedAt DEFAULT SYSDATETIME(),
            CONSTRAINT PK_Analytics_ModelRegistry PRIMARY KEY (ModelVersion),
            CONSTRAINT CK_ModelRegistry_Role CHECK (ModelRole IN
                (N'SCORING', N'TREE', N'CLUSTERING', N'COMPARISON')),
            CONSTRAINT CK_ModelRegistry_BaseRate CHECK (TrainBaseRate BETWEEN 0 AND 1),
            CONSTRAINT CK_ModelRegistry_Threshold CHECK (DecisionThreshold BETWEEN 0 AND 1),
            CONSTRAINT CK_ModelRegistry_AUC CHECK (ROCAUC BETWEEN 0 AND 1),
            CONSTRAINT CK_ModelRegistry_Brier CHECK (BrierScore BETWEEN 0 AND 1)
        );
    END;

    /* At most one ACTIVE version per role. Supports separate scoring/tree models. */
    IF OBJECT_ID(N'analytics.ModelRegistry', N'U') IS NOT NULL
       AND NOT EXISTS (
           SELECT 1 FROM sys.indexes
           WHERE object_id = OBJECT_ID(N'analytics.ModelRegistry')
             AND name = N'UX_ModelRegistry_ActiveRole'
       )
        CREATE UNIQUE INDEX UX_ModelRegistry_ActiveRole
        ON analytics.ModelRegistry(ModelRole)
        WHERE IsActive = 1;

    /* C2. Decision-tree leaf rule table required by the model base (Table 3.18).
       Cluster 4/5 will populate one row per trained tree leaf. */
    IF OBJECT_ID(N'analytics.ModelTreeLeaf', N'U') IS NULL
    BEGIN
        CREATE TABLE analytics.ModelTreeLeaf (
            ModelVersion   NVARCHAR(80) NOT NULL,
            LeafID         INT NOT NULL,
            RuleText       NVARCHAR(2000) NOT NULL,
            ConditionsJSON NVARCHAR(MAX) NULL,
            LeafCount      INT NOT NULL,
            PositiveCount  INT NOT NULL,
            TreeScore      DECIMAL(9,6) NOT NULL,
            CONSTRAINT PK_Analytics_ModelTreeLeaf PRIMARY KEY (ModelVersion, LeafID),
            CONSTRAINT FK_Analytics_ModelTreeLeaf_Registry
                FOREIGN KEY (ModelVersion) REFERENCES analytics.ModelRegistry(ModelVersion),
            CONSTRAINT CK_Analytics_ModelTreeLeaf_Counts
                CHECK (LeafCount >= 0 AND PositiveCount >= 0 AND PositiveCount <= LeafCount),
            CONSTRAINT CK_Analytics_ModelTreeLeaf_Score
                CHECK (TreeScore BETWEEN 0 AND 1)
        );
    END;

    /* D. Scores. 1 customer x 1 date x 1 model version.
       ScoreDate is NOT FK to DimDate: 2014-07-08 scoring date falls after
       the existing DimDate order-date calendar ends on 2014-06-30.
       TreeScore and TreeModelVersion are useful optional traceability fields.
       No FK to CustomerSnapshot, since snapshots are currently rebuilt via DELETE.
    */
    IF OBJECT_ID(N'analytics.CustomerRiskScore', N'U') IS NULL
    BEGIN
        CREATE TABLE analytics.CustomerRiskScore (
            CustomerID        INT NOT NULL,
            ScoreDate         DATE NOT NULL,
            ModelVersion      NVARCHAR(80) NOT NULL,
            RiskScore         DECIMAL(9,6) NOT NULL,
            RiskPercentile    DECIMAL(6,3) NOT NULL,
            RiskLevel         NVARCHAR(10) NOT NULL,
            TreeScore         DECIMAL(9,6) NULL,
            TreeModelVersion  NVARCHAR(80) NULL,
            TopFactors        NVARCHAR(MAX) NULL,
            ScoredAt          DATETIME2(0) NOT NULL
                CONSTRAINT DF_CustomerRiskScore_ScoredAt DEFAULT SYSDATETIME(),
            CONSTRAINT PK_Analytics_CustomerRiskScore
                PRIMARY KEY (CustomerID, ScoreDate, ModelVersion),
            CONSTRAINT FK_Analytics_RiskScore_Customer
                FOREIGN KEY (CustomerID) REFERENCES dbo.DimCustomer(CustomerID),
            CONSTRAINT FK_Analytics_RiskScore_Model
                FOREIGN KEY (ModelVersion) REFERENCES analytics.ModelRegistry(ModelVersion),
            CONSTRAINT FK_Analytics_RiskScore_TreeModel
                FOREIGN KEY (TreeModelVersion) REFERENCES analytics.ModelRegistry(ModelVersion),
            CONSTRAINT CK_Analytics_RiskScore_Range CHECK (RiskScore BETWEEN 0 AND 1),
            CONSTRAINT CK_Analytics_RiskPercentile_Range CHECK (RiskPercentile BETWEEN 0 AND 100),
            CONSTRAINT CK_Analytics_TreeScore_Range CHECK (TreeScore BETWEEN 0 AND 1),
            CONSTRAINT CK_Analytics_RiskLevel CHECK (
                (RiskPercentile >= 75 AND RiskLevel = N'Cao') OR
                (RiskPercentile < 75 AND RiskLevel = N'Thấp')
            )
        );
    END;

    IF OBJECT_ID(N'analytics.CustomerRiskScore', N'U') IS NOT NULL
       AND NOT EXISTS (
           SELECT 1 FROM sys.indexes
           WHERE object_id = OBJECT_ID(N'analytics.CustomerRiskScore')
             AND name = N'IX_CustomerRiskScore_DateModelRisk'
       )
        CREATE INDEX IX_CustomerRiskScore_DateModelRisk
          ON analytics.CustomerRiskScore(ScoreDate, ModelVersion, RiskScore DESC);

    COMMIT TRANSACTION;
    PRINT N'CLUSTER_1_SCHEMA_OK. No existing snapshot/Fact data has been rewritten.';
    PRINT N'NEXT: Cluster 2 updates ETL/rejection logic; Cluster 3 fills the feature columns.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
