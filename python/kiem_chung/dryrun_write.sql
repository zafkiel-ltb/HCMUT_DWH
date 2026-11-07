/* Chuẩn hoá bước 3: thử ghi giả lập vào ModelRegistry -> ModelTreeLeaf -> CustomerRiskScore với dữ liệu kích thước thật,
   rồi ROLLBACK. Kiểm tra kiểu dữ liệu, độ dài, CHECK, FK, chỉ mục duy nhất. Không để lại dòng nào. */
USE [CompanyX_DW];
SET NOCOUNT ON; SET XACT_ABORT OFF; SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON;
DECLARE @msg NVARCHAR(4000);
BEGIN TRANSACTION;
BEGIN TRY
  /* 1. ModelRegistry: 3 vai trò, JSON cấu hình dài, FeatureList */
  INSERT analytics.ModelRegistry(ModelVersion,ModelRole,ModelType,TrainingSnapshot,FeatureList,ConfigurationJSON,ArtifactPath,ScalerPath,TrainBaseRate,DecisionThreshold,ROCAUC,BrierScore,EffectiveFrom,IsActive)
  VALUES (N'mlp_32_16_T20140301_v1',N'SCORING',N'MLPClassifier (32,16) relu adam',  '2014-03-01',
          N'Recency,Frequency,Monetary,Orders90,Orders180,Tenure,Share_Bikes,Share_Accessories,Share_Clothing,BikeBuyer,NSub',
          REPLICATE(N'{"hidden_layer_sizes":[32,16],"activation":"relu","solver":"adam","max_iter":300,"early_stopping":true,"random_state":0,"scaler":"StandardScaler","note":"', 50) + N'"}',
          N'models/mlp_32_16_T20140301_v1.joblib', N'models/scaler_T20140301_v1.joblib', 0.819700, 0.812345, 0.751234, 0.128456, '2014-07-08', 1),
         (N'tree_gini_d4_l400_T20140301_v1',N'TREE',N'DecisionTreeClassifier gini depth4 leaf400 m50','2014-03-01',N'(như trên)',N'{"max_depth":4,"min_samples_leaf":400,"m":50}',NULL,NULL,0.819700,NULL,0.680000,0.140000,'2014-07-08',1),
         (N'nb_cat_T20140301_v1',N'COMPARISON',N'CategoricalNB alpha1 (Bảng 3.10)','2014-03-01',N'R,F,M,BikeBuyer,NSub rời rạc',N'{"alpha":1}',NULL,NULL,0.819700,NULL,0.720000,0.125000,'2014-07-08',1);
  PRINT N'OK 1: ModelRegistry 3 dòng (SCORING/TREE/COMPARISON cùng IsActive=1)';

  /* 2. ModelTreeLeaf: 12 lá với RuleText dài */
  ;WITH n AS (SELECT TOP (12) ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS i FROM sys.objects)
  INSERT analytics.ModelTreeLeaf(ModelVersion,LeafID,RuleText,ConditionsJSON,LeafCount,PositiveCount,TreeScore)
  SELECT N'tree_gini_d4_l400_T20140301_v1', i, REPLICATE(N'Recency > 269.5 AND Frequency <= 1.5 AND Share_Bikes > 0.5 AND Tenure <= 400.5; ', 20),
         N'[{"f":"Recency","op":">","v":269.5},{"f":"Frequency","op":"<=","v":1.5}]', 400 + i * 100, 300 + i * 50, CAST((300.0 + i * 50) / (400 + i * 100) AS DECIMAL(9,6)) FROM n;
  PRINT N'OK 2: ModelTreeLeaf 12 lá';

  /* 3. CustomerRiskScore: toàn bộ khách mốc 08/07/2014, percentile và RiskLevel đúng CHECK, TopFactors dài */
  ;WITH s AS (
    SELECT CustomerID, SnapshotDate, CAST(ABS(CHECKSUM(NEWID())) % 1000000 / 1000000.0 AS DECIMAL(9,6)) AS p FROM analytics.CustomerSnapshot WHERE SnapshotDate='2014-07-08'),
  r AS (SELECT *, CAST(PERCENT_RANK() OVER (ORDER BY p) * 100 AS DECIMAL(6,3)) AS pct FROM s)
  INSERT analytics.CustomerRiskScore(CustomerID,ScoreDate,ModelVersion,RiskScore,RiskPercentile,RiskLevel,TreeScore,TreeModelVersion,TopFactors)
  SELECT CustomerID, SnapshotDate, N'mlp_32_16_T20140301_v1', p, pct, CASE WHEN pct >= 75 THEN N'Cao' ELSE N'Thấp' END,
         CAST(p * 0.9 AS DECIMAL(9,6)), N'tree_gini_d4_l400_T20140301_v1',
         N'Lá 7: Recency > 269.5 AND Frequency <= 1.5 AND Share_Bikes > 0.5 | nl=1.240, nl1=1.082, TreeScore=0,861 | ' + REPLICATE(N'giải thích thêm ', 30)
  FROM r;
  SELECT @msg = N'OK 3: CustomerRiskScore ' + CONVERT(NVARCHAR(20), @@ROWCOUNT) + N' dòng'; PRINT @msg;
  SELECT RiskLevel, COUNT(*) n, MIN(RiskPercentile) minp, MAX(RiskPercentile) maxp FROM analytics.CustomerRiskScore GROUP BY RiskLevel;

  /* 4. Phải LỖI: hai mô hình SCORING cùng IsActive=1 (UX_ModelRegistry_ActiveRole) */
  BEGIN TRY
    INSERT analytics.ModelRegistry(ModelVersion,ModelRole,ModelType,IsActive) VALUES (N'mlp_v2_active_too',N'SCORING',N'x',1);
    PRINT N'FAIL 4: cho phép 2 SCORING active cùng lúc';
  END TRY BEGIN CATCH PRINT N'OK 4: chặn 2 SCORING active (' + ERROR_MESSAGE() + N')'; END CATCH
  /* 5. Phải LỖI: RiskLevel sai so với percentile */
  BEGIN TRY
    INSERT analytics.CustomerRiskScore(CustomerID,ScoreDate,ModelVersion,RiskScore,RiskPercentile,RiskLevel) VALUES (11000,'2014-07-09',N'mlp_32_16_T20140301_v1',0.5,80,N'Thấp');
    PRINT N'FAIL 5: cho phép RiskLevel sai';
  END TRY BEGIN CATCH PRINT N'OK 5: chặn RiskLevel sai (' + ERROR_MESSAGE() + N')'; END CATCH
  /* 6. Phải LỖI: ModelVersion chưa đăng ký */
  BEGIN TRY
    INSERT analytics.CustomerRiskScore(CustomerID,ScoreDate,ModelVersion,RiskScore,RiskPercentile,RiskLevel) VALUES (11000,'2014-07-09',N'chua_dang_ky',0.5,80,N'Cao');
    PRINT N'FAIL 6: cho phép ModelVersion chưa đăng ký';
  END TRY BEGIN CATCH PRINT N'OK 6: chặn ModelVersion chưa đăng ký'; END CATCH
  /* 7. C3_01 sẽ từ chối rebuild khi có điểm: kiểm tra điều kiện nó dùng */
  SELECT COUNT(*) AS ExistingRiskScores_seen_by_C3 FROM analytics.CustomerRiskScore;
  /* 8. Truy vấn DSS màn hình 1: nối điểm với snapshot, một dòng mỗi khách */
  SELECT COUNT(*) AS rows_join, COUNT(DISTINCT r.CustomerID) AS customers
  FROM analytics.CustomerRiskScore r JOIN analytics.CustomerSnapshot s ON s.CustomerID=r.CustomerID AND s.SnapshotDate=r.ScoreDate
  JOIN analytics.ModelRegistry m ON m.ModelVersion=r.ModelVersion AND m.IsActive=1 AND m.ModelRole=N'SCORING';
END TRY
BEGIN CATCH
  PRINT N'LỖI NGOÀI DỰ KIẾN: ' + ERROR_MESSAGE();
END CATCH
ROLLBACK TRANSACTION;
SELECT (SELECT COUNT(*) FROM analytics.ModelRegistry) AS reg_after, (SELECT COUNT(*) FROM analytics.ModelTreeLeaf) AS leaf_after, (SELECT COUNT(*) FROM analytics.CustomerRiskScore) AS score_after;
