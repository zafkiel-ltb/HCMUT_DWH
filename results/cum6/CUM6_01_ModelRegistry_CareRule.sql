USE [CompanyX_DW];
SET NOCOUNT ON; SET XACT_ABORT ON; SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON;
/* CUM6_01 – Đăng ký mô hình phân cụm K-means (ModelRole CLUSTERING) + 9 quy tắc chăm sóc (Bảng 3.30). Cần đã chạy Cluster1b. */
IF OBJECT_ID(N'analytics.CareRule') IS NULL THROW 56001, N'Chưa chạy sql/4_Cum1b_Schema_DSS_DE_XUAT.sql.', 1;
IF EXISTS (SELECT 1 FROM analytics.ModelRegistry WHERE ModelVersion=N'KMEANS_E20140708_v1') THROW 56002, N'K-means đã đăng ký. Xoá bằng RESET_DSS.sql nếu muốn ghi lại.', 1;
BEGIN TRANSACTION;
INSERT analytics.ModelRegistry(ModelVersion,ModelRole,ModelType,TrainingSnapshot,FeatureList,ConfigurationJSON,EffectiveFrom,IsActive)
VALUES (N'KMEANS_E20140708_v1',N'CLUSTERING',N'K-means k = 5 trên (R, ln(1+F), ln(1+M)) z-score','2014-07-08',N'Recency,Frequency,Monetary',N'{"features": ["Recency", "ln1p_Frequency", "ln1p_Monetary"], "mean": [198.584423, 0.870323, 5.890745], "std": [148.533643, 0.26049, 2.155937], "centers": [[-0.043537, -0.680165, -1.007369], [-0.117677, 1.101661, 1.166836], [-0.008574, -0.680165, 0.59872], [-0.534446, 1.337539, -0.50371], [4.481094, -0.680165, 0.979911]], "cluster_to_name": {"1": "N1", "3": "N4", "4": "N3", "2": "N2", "0": "N5"}, "k": 5, "n_init": 20, "random_state": 42, "hopkins": 0.0038, "silhouette": 0.466, "ari_seeds": [1.0, 1.0, 1.0], "ari_ward": 0.9952}','2014-07-08',1);
INSERT analytics.CareRule(RuleCode,RuleVersion,RuleType,ConditionText,ActionText,Rationale,ChannelCost,ChannelSuccess,IsActive,EffectiveFrom,UpdatedBy) VALUES
(N'R1',1,N'Loại trừ',N'Khách đã được liên hệ trong 90 ngày trước (nhật ký CRM)',N'Không đưa vào danh sách mới',N'Chính sách đề xuất, chưa có dữ liệu CRM',NULL,NULL,0,'2014-07-08',N'Nhóm TA_DSS'),
(N'R2',1,N'Loại trừ',N'p·r·v − c ≤ 0',N'Không đưa vào danh sách chăm sóc cá nhân',N'Mục 3.5.2',NULL,NULL,1,'2014-07-08',N'Nhóm TA_DSS'),
(N'R3',1,N'Hình thức liên hệ',N'Nhóm N1 và RiskLevel = Cao',N'Liên hệ cá nhân kèm ưu đãi',N'N1 giá trị cao, mua nhiều lần',25.0,0.15,1,'2014-07-08',N'Nhóm TA_DSS'),
(N'R4',1,N'Hình thức liên hệ',N'Nhóm N3',N'Nội dung mời quay lại kèm ưu đãi',N'N3 mua một lần, đã lâu không quay lại',15.0,0.12,1,'2014-07-08',N'Nhóm TA_DSS'),
(N'R5',1,N'Hình thức liên hệ',N'Các trường hợp còn lại',N'Email cá nhân hóa gửi tự động',N'Chi phí liên hệ thấp',3.0,0.05,1,'2014-07-08',N'Nhóm TA_DSS'),
(N'R6',1,N'Sản phẩm gợi ý',N'Đã mua Touring Bikes, chưa mua Helmets',N'Gợi ý Helmets',N'Bảng 3.29',NULL,NULL,1,'2014-07-08',N'Nhóm TA_DSS'),
(N'R7',1,N'Sản phẩm gợi ý',N'Đã mua Mountain Bikes, chưa mua Fenders',N'Gợi ý Fenders',N'Bảng 3.29',NULL,NULL,1,'2014-07-08',N'Nhóm TA_DSS'),
(N'R8',1,N'Sản phẩm gợi ý',N'Đã mua Gloves chưa mua Helmets, hoặc đã mua Hydration Packs chưa mua Bottles and Cages',N'Gợi ý sản phẩm vế phải',N'Bảng 3.29',NULL,NULL,1,'2014-07-08',N'Nhóm TA_DSS'),
(N'R9',1,N'Giám sát mô hình',N'Đã đủ nhãn 90 ngày sau chiến dịch',N'So ROC-AUC với Recency trên nhóm đối chứng, cảnh báo nếu không hơn',N'Mục 3.4.7',NULL,NULL,0,'2014-07-08',N'Nhóm TA_DSS');
COMMIT TRANSACTION;
SELECT RuleCode, RuleType, ChannelCost, ChannelSuccess, IsActive, LEFT(ConditionText,60) AS DieuKien FROM analytics.CareRule ORDER BY RuleCode;
PRINT N'CUM6_01_OK: K-means đăng ký, 9 quy tắc (R1, R9 tạm tắt vì chưa có dữ liệu CRM).';
