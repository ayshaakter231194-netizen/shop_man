-- MySQL Database Backup
-- Generated: 20251022_160302
-- Database: shop_management
SET FOREIGN_KEY_CHECKS=0;


-- Table structure for table `auth_group`
DROP TABLE IF EXISTS `auth_group`;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `auth_group_permissions`
DROP TABLE IF EXISTS `auth_group_permissions`;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `auth_permission`
DROP TABLE IF EXISTS `auth_permission`;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=105 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `auth_permission`
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (1, 'Can add log entry', 1, 'add_logentry');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (2, 'Can change log entry', 1, 'change_logentry');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (3, 'Can delete log entry', 1, 'delete_logentry');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (4, 'Can view log entry', 1, 'view_logentry');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (5, 'Can add permission', 2, 'add_permission');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (6, 'Can change permission', 2, 'change_permission');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (7, 'Can delete permission', 2, 'delete_permission');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (8, 'Can view permission', 2, 'view_permission');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (9, 'Can add group', 3, 'add_group');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (10, 'Can change group', 3, 'change_group');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (11, 'Can delete group', 3, 'delete_group');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (12, 'Can view group', 3, 'view_group');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (13, 'Can add user', 4, 'add_user');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (14, 'Can change user', 4, 'change_user');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (15, 'Can delete user', 4, 'delete_user');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (16, 'Can view user', 4, 'view_user');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (17, 'Can add content type', 5, 'add_contenttype');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (18, 'Can change content type', 5, 'change_contenttype');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (19, 'Can delete content type', 5, 'delete_contenttype');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (20, 'Can view content type', 5, 'view_contenttype');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (21, 'Can add session', 6, 'add_session');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (22, 'Can change session', 6, 'change_session');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (23, 'Can delete session', 6, 'delete_session');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (24, 'Can view session', 6, 'view_session');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (25, 'Can add category', 7, 'add_category');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (26, 'Can change category', 7, 'change_category');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (27, 'Can delete category', 7, 'delete_category');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (28, 'Can view category', 7, 'view_category');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (29, 'Can add supplier', 8, 'add_supplier');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (30, 'Can change supplier', 8, 'change_supplier');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (31, 'Can delete supplier', 8, 'delete_supplier');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (32, 'Can view supplier', 8, 'view_supplier');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (33, 'Can add customer', 9, 'add_customer');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (34, 'Can change customer', 9, 'change_customer');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (35, 'Can delete customer', 9, 'delete_customer');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (36, 'Can view customer', 9, 'view_customer');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (37, 'Can add due payment', 10, 'add_duepayment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (38, 'Can change due payment', 10, 'change_duepayment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (39, 'Can delete due payment', 10, 'delete_duepayment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (40, 'Can view due payment', 10, 'view_duepayment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (41, 'Can add product', 11, 'add_product');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (42, 'Can change product', 11, 'change_product');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (43, 'Can delete product', 11, 'delete_product');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (44, 'Can view product', 11, 'view_product');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (45, 'Can add purchase order', 12, 'add_purchaseorder');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (46, 'Can change purchase order', 12, 'change_purchaseorder');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (47, 'Can delete purchase order', 12, 'delete_purchaseorder');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (48, 'Can view purchase order', 12, 'view_purchaseorder');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (49, 'Can add purchase order cancellation', 13, 'add_purchaseordercancellation');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (50, 'Can change purchase order cancellation', 13, 'change_purchaseordercancellation');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (51, 'Can delete purchase order cancellation', 13, 'delete_purchaseordercancellation');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (52, 'Can view purchase order cancellation', 13, 'view_purchaseordercancellation');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (53, 'Can add purchase order item', 14, 'add_purchaseorderitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (54, 'Can change purchase order item', 14, 'change_purchaseorderitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (55, 'Can delete purchase order item', 14, 'delete_purchaseorderitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (56, 'Can view purchase order item', 14, 'view_purchaseorderitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (57, 'Can add product batch', 15, 'add_productbatch');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (58, 'Can change product batch', 15, 'change_productbatch');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (59, 'Can delete product batch', 15, 'delete_productbatch');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (60, 'Can view product batch', 15, 'view_productbatch');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (61, 'Can add purchase return', 16, 'add_purchasereturn');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (62, 'Can change purchase return', 16, 'change_purchasereturn');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (63, 'Can delete purchase return', 16, 'delete_purchasereturn');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (64, 'Can view purchase return', 16, 'view_purchasereturn');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (65, 'Can add purchase return item', 17, 'add_purchasereturnitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (66, 'Can change purchase return item', 17, 'change_purchasereturnitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (67, 'Can delete purchase return item', 17, 'delete_purchasereturnitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (68, 'Can view purchase return item', 17, 'view_purchasereturnitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (69, 'Can add sale', 18, 'add_sale');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (70, 'Can change sale', 18, 'change_sale');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (71, 'Can delete sale', 18, 'delete_sale');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (72, 'Can view sale', 18, 'view_sale');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (73, 'Can add sale item', 19, 'add_saleitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (74, 'Can change sale item', 19, 'change_saleitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (75, 'Can delete sale item', 19, 'delete_saleitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (76, 'Can view sale item', 19, 'view_saleitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (77, 'Can add sale return', 20, 'add_salereturn');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (78, 'Can change sale return', 20, 'change_salereturn');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (79, 'Can delete sale return', 20, 'delete_salereturn');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (80, 'Can view sale return', 20, 'view_salereturn');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (81, 'Can add sale return item', 21, 'add_salereturnitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (82, 'Can change sale return item', 21, 'change_salereturnitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (83, 'Can delete sale return item', 21, 'delete_salereturnitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (84, 'Can view sale return item', 21, 'view_salereturnitem');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (85, 'Can add stock adjustment', 22, 'add_stockadjustment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (86, 'Can change stock adjustment', 22, 'change_stockadjustment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (87, 'Can delete stock adjustment', 22, 'delete_stockadjustment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (88, 'Can view stock adjustment', 22, 'view_stockadjustment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (89, 'Can add stock movement', 23, 'add_stockmovement');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (90, 'Can change stock movement', 23, 'change_stockmovement');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (91, 'Can delete stock movement', 23, 'delete_stockmovement');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (92, 'Can view stock movement', 23, 'view_stockmovement');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (93, 'Can add supplier bill', 24, 'add_supplierbill');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (94, 'Can change supplier bill', 24, 'change_supplierbill');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (95, 'Can delete supplier bill', 24, 'delete_supplierbill');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (96, 'Can view supplier bill', 24, 'view_supplierbill');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (97, 'Can add payment', 25, 'add_payment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (98, 'Can change payment', 25, 'change_payment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (99, 'Can delete payment', 25, 'delete_payment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (100, 'Can view payment', 25, 'view_payment');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (101, 'Can add user profile', 26, 'add_userprofile');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (102, 'Can change user profile', 26, 'change_userprofile');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (103, 'Can delete user profile', 26, 'delete_userprofile');
INSERT INTO `auth_permission` (`id`, `name`, `content_type_id`, `codename`) VALUES (104, 'Can view user profile', 26, 'view_userprofile');

-- Table structure for table `auth_user`
DROP TABLE IF EXISTS `auth_user`;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `auth_user`
INSERT INTO `auth_user` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`) VALUES (1, 'pbkdf2_sha256$1000000$Io4OQ6Gd8YiivyWfN486kY$1Y22j7+xdDhcovoud6f3SnYGF4yKBYPF/6rxqi+4soA=', '2025-10-22 07:06:16.513809', 1, 'shuvo', '', '', 's@huvo.com', 1, 1, '2025-10-22 07:00:08.107096');

-- Table structure for table `auth_user_groups`
DROP TABLE IF EXISTS `auth_user_groups`;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `auth_user_user_permissions`
DROP TABLE IF EXISTS `auth_user_user_permissions`;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `core_category`
DROP TABLE IF EXISTS `core_category`;
CREATE TABLE `core_category` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_category`
INSERT INTO `core_category` (`id`, `name`, `description`, `created_at`) VALUES (1, 'Tissue', '', '2025-10-22 07:07:27.789811');
INSERT INTO `core_category` (`id`, `name`, `description`, `created_at`) VALUES (2, 'Biscuit', '', '2025-10-22 07:43:15.105493');

-- Table structure for table `core_customer`
DROP TABLE IF EXISTS `core_customer`;
CREATE TABLE `core_customer` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(254) DEFAULT NULL,
  `address` longtext,
  `total_due` decimal(10,2) NOT NULL,
  `credit_limit` decimal(10,2) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `phone` (`phone`),
  KEY `core_custom_phone_cf7ec3_idx` (`phone`),
  KEY `core_custom_name_b5e864_idx` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_customer`
INSERT INTO `core_customer` (`id`, `name`, `phone`, `email`, `address`, `total_due`, `credit_limit`, `is_active`, `created_at`, `updated_at`) VALUES (1, 'zakaria', '01644334516', NULL, NULL, '0.00', '10000.00', 1, '2025-10-22 07:12:07.738905', '2025-10-22 07:12:07.738921');
INSERT INTO `core_customer` (`id`, `name`, `phone`, `email`, `address`, `total_due`, `credit_limit`, `is_active`, `created_at`, `updated_at`) VALUES (2, 'SHUVO', '01790009817', NULL, NULL, '0.00', '10000.00', 1, '2025-10-22 07:12:48.198504', '2025-10-22 07:12:48.198527');

-- Table structure for table `core_duepayment`
DROP TABLE IF EXISTS `core_duepayment`;
CREATE TABLE `core_duepayment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `payment_date` datetime(6) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_method` varchar(20) NOT NULL,
  `reference_number` varchar(100) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `allocated_details` json DEFAULT NULL,
  `customer_id` bigint NOT NULL,
  `received_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_duepayment_customer_id_e915b3d2_fk_core_customer_id` (`customer_id`),
  KEY `core_duepayment_received_by_id_d48e9530_fk_auth_user_id` (`received_by_id`),
  CONSTRAINT `core_duepayment_customer_id_e915b3d2_fk_core_customer_id` FOREIGN KEY (`customer_id`) REFERENCES `core_customer` (`id`),
  CONSTRAINT `core_duepayment_received_by_id_d48e9530_fk_auth_user_id` FOREIGN KEY (`received_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `core_payment`
DROP TABLE IF EXISTS `core_payment`;
CREATE TABLE `core_payment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `payment_date` date NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_method` varchar(20) NOT NULL,
  `reference_number` varchar(100) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `received_by_id` int NOT NULL,
  `bill_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_payment_received_by_id_9c5f8200_fk_auth_user_id` (`received_by_id`),
  KEY `core_payment_bill_id_0893fd82_fk_core_supplierbill_id` (`bill_id`),
  CONSTRAINT `core_payment_bill_id_0893fd82_fk_core_supplierbill_id` FOREIGN KEY (`bill_id`) REFERENCES `core_supplierbill` (`id`),
  CONSTRAINT `core_payment_received_by_id_9c5f8200_fk_auth_user_id` FOREIGN KEY (`received_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_payment`
INSERT INTO `core_payment` (`id`, `payment_date`, `amount`, `payment_method`, `reference_number`, `notes`, `created_at`, `received_by_id`, `bill_id`) VALUES (1, '2025-10-22', '750.00', 'cash', '', '', '2025-10-22 07:20:42.721338', 1, 1);

-- Table structure for table `core_product`
DROP TABLE IF EXISTS `core_product`;
CREATE TABLE `core_product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `sku` varchar(50) NOT NULL,
  `barcode` varchar(100) DEFAULT NULL,
  `description` longtext NOT NULL,
  `cost_price` decimal(10,2) NOT NULL,
  `selling_price` decimal(10,2) NOT NULL,
  `current_stock` int NOT NULL,
  `min_stock_level` int NOT NULL,
  `has_expiry` tinyint(1) NOT NULL,
  `expiry_warning_days` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `category_id` bigint NOT NULL,
  `supplier_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`),
  UNIQUE KEY `barcode` (`barcode`),
  KEY `core_produc_barcode_5cc7aa_idx` (`barcode`),
  KEY `core_produc_sku_a1eae6_idx` (`sku`),
  KEY `core_produc_supplie_c9aba1_idx` (`supplier_id`),
  KEY `core_product_category_id_b9d8ff9f_fk_core_category_id` (`category_id`),
  CONSTRAINT `core_product_category_id_b9d8ff9f_fk_core_category_id` FOREIGN KEY (`category_id`) REFERENCES `core_category` (`id`),
  CONSTRAINT `core_product_supplier_id_493af3ba_fk_core_supplier_id` FOREIGN KEY (`supplier_id`) REFERENCES `core_supplier` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_product`
INSERT INTO `core_product` (`id`, `name`, `sku`, `barcode`, `description`, `cost_price`, `selling_price`, `current_stock`, `min_stock_level`, `has_expiry`, `expiry_warning_days`, `created_at`, `updated_at`, `category_id`, `supplier_id`) VALUES (1, 'Tissue', '8941193041116', '8941193041116', '', '50.00', '65.00', 14, 10, 0, 30, '2025-10-22 07:09:14.955301', '2025-10-22 07:19:28.033766', 1, 1);
INSERT INTO `core_product` (`id`, `name`, `sku`, `barcode`, `description`, `cost_price`, `selling_price`, `current_stock`, `min_stock_level`, `has_expiry`, `expiry_warning_days`, `created_at`, `updated_at`, `category_id`, `supplier_id`) VALUES (2, 'Kaju Delight', '8941168005976', '8941168005976', '', '15.00', '20.00', 15, 10, 1, 30, '2025-10-22 08:05:17.789822', '2025-10-22 09:21:56.377937', 2, 2);

-- Table structure for table `core_productbatch`
DROP TABLE IF EXISTS `core_productbatch`;
CREATE TABLE `core_productbatch` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `batch_number` varchar(100) NOT NULL,
  `manufacture_date` date DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `quantity` int NOT NULL,
  `current_quantity` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `product_id` bigint NOT NULL,
  `purchase_order_item_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `core_productbatch_product_id_batch_number_3611ce94_uniq` (`product_id`,`batch_number`),
  KEY `core_productbatch_purchase_order_item__dc222bb0_fk_core_purc` (`purchase_order_item_id`),
  CONSTRAINT `core_productbatch_product_id_244f2835_fk_core_product_id` FOREIGN KEY (`product_id`) REFERENCES `core_product` (`id`),
  CONSTRAINT `core_productbatch_purchase_order_item__dc222bb0_fk_core_purc` FOREIGN KEY (`purchase_order_item_id`) REFERENCES `core_purchaseorderitem` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_productbatch`
INSERT INTO `core_productbatch` (`id`, `batch_number`, `manufacture_date`, `expiry_date`, `quantity`, `current_quantity`, `created_at`, `product_id`, `purchase_order_item_id`) VALUES (1, 'BATCH-1-22102501', '2025-10-22', NULL, 15, 15, '2025-10-22 07:10:31.415519', 1, 1);
INSERT INTO `core_productbatch` (`id`, `batch_number`, `manufacture_date`, `expiry_date`, `quantity`, `current_quantity`, `created_at`, `product_id`, `purchase_order_item_id`) VALUES (2, 'BATCH-2-79074221025', '2025-10-22', '2026-01-22', 15, 15, '2025-10-22 09:21:56.374776', 2, 2);

-- Table structure for table `core_purchaseorder`
DROP TABLE IF EXISTS `core_purchaseorder`;
CREATE TABLE `core_purchaseorder` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `po_number` varchar(50) NOT NULL,
  `order_date` datetime(6) NOT NULL,
  `expected_date` datetime(6) NOT NULL,
  `status` varchar(20) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `supplier_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `po_number` (`po_number`),
  KEY `core_purchaseorder_created_by_id_e567dc99_fk_auth_user_id` (`created_by_id`),
  KEY `core_purchaseorder_supplier_id_0242d2c5_fk_core_supplier_id` (`supplier_id`),
  CONSTRAINT `core_purchaseorder_created_by_id_e567dc99_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_purchaseorder_supplier_id_0242d2c5_fk_core_supplier_id` FOREIGN KEY (`supplier_id`) REFERENCES `core_supplier` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_purchaseorder`
INSERT INTO `core_purchaseorder` (`id`, `po_number`, `order_date`, `expected_date`, `status`, `total_amount`, `created_at`, `created_by_id`, `supplier_id`) VALUES (1, '31edf672-c9f2-4165-bff8-ec936d597ac9', '2025-10-22 07:10:02.791460', '2025-10-24 00:00:00', 'completed', '750.00', '2025-10-22 07:10:02.797212', 1, 1);
INSERT INTO `core_purchaseorder` (`id`, `po_number`, `order_date`, `expected_date`, `status`, `total_amount`, `created_at`, `created_by_id`, `supplier_id`) VALUES (2, '79074cc1-285b-4b29-ab17-d5fb63148476', '2025-10-22 09:21:30.939624', '2025-10-31 00:00:00', 'completed', '225.00', '2025-10-22 09:21:30.947624', 1, 2);

-- Table structure for table `core_purchaseordercancellation`
DROP TABLE IF EXISTS `core_purchaseordercancellation`;
CREATE TABLE `core_purchaseordercancellation` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `reason` longtext NOT NULL,
  `cancelled_at` datetime(6) NOT NULL,
  `cancelled_by_id` int NOT NULL,
  `purchase_order_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_purchaseorderca_cancelled_by_id_4dab93ca_fk_auth_user` (`cancelled_by_id`),
  KEY `core_purchaseorderca_purchase_order_id_939fb2da_fk_core_purc` (`purchase_order_id`),
  CONSTRAINT `core_purchaseorderca_cancelled_by_id_4dab93ca_fk_auth_user` FOREIGN KEY (`cancelled_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_purchaseorderca_purchase_order_id_939fb2da_fk_core_purc` FOREIGN KEY (`purchase_order_id`) REFERENCES `core_purchaseorder` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `core_purchaseorderitem`
DROP TABLE IF EXISTS `core_purchaseorderitem`;
CREATE TABLE `core_purchaseorderitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int NOT NULL,
  `unit_cost` decimal(10,2) NOT NULL,
  `total_cost` decimal(10,2) NOT NULL,
  `batch_number` varchar(100) NOT NULL,
  `expiry_date` date DEFAULT NULL,
  `product_id` bigint NOT NULL,
  `purchase_order_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_purchaseorderitem_product_id_e4cc27f0_fk_core_product_id` (`product_id`),
  KEY `core_purchaseorderit_purchase_order_id_ec9433f4_fk_core_purc` (`purchase_order_id`),
  CONSTRAINT `core_purchaseorderit_purchase_order_id_ec9433f4_fk_core_purc` FOREIGN KEY (`purchase_order_id`) REFERENCES `core_purchaseorder` (`id`),
  CONSTRAINT `core_purchaseorderitem_product_id_e4cc27f0_fk_core_product_id` FOREIGN KEY (`product_id`) REFERENCES `core_product` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_purchaseorderitem`
INSERT INTO `core_purchaseorderitem` (`id`, `quantity`, `unit_cost`, `total_cost`, `batch_number`, `expiry_date`, `product_id`, `purchase_order_id`) VALUES (1, 15, '50.00', '750.00', '', NULL, 1, 1);
INSERT INTO `core_purchaseorderitem` (`id`, `quantity`, `unit_cost`, `total_cost`, `batch_number`, `expiry_date`, `product_id`, `purchase_order_id`) VALUES (2, 15, '15.00', '225.00', '', NULL, 2, 2);

-- Table structure for table `core_purchasereturn`
DROP TABLE IF EXISTS `core_purchasereturn`;
CREATE TABLE `core_purchasereturn` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `return_number` varchar(50) NOT NULL,
  `return_date` datetime(6) NOT NULL,
  `reason` varchar(20) NOT NULL,
  `description` longtext NOT NULL,
  `return_amount` decimal(10,2) NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `purchase_order_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `return_number` (`return_number`),
  KEY `core_purchasereturn_created_by_id_4d36f1df_fk_auth_user_id` (`created_by_id`),
  KEY `core_purchasereturn_purchase_order_id_145be185_fk_core_purc` (`purchase_order_id`),
  CONSTRAINT `core_purchasereturn_created_by_id_4d36f1df_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_purchasereturn_purchase_order_id_145be185_fk_core_purc` FOREIGN KEY (`purchase_order_id`) REFERENCES `core_purchaseorder` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `core_purchasereturnitem`
DROP TABLE IF EXISTS `core_purchasereturnitem`;
CREATE TABLE `core_purchasereturnitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int NOT NULL,
  `unit_cost` decimal(10,2) NOT NULL,
  `total_cost` decimal(10,2) NOT NULL,
  `reason` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `batch_id` bigint DEFAULT NULL,
  `purchase_order_item_id` bigint NOT NULL,
  `purchase_return_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_purchasereturni_batch_id_56282041_fk_core_prod` (`batch_id`),
  KEY `core_purchasereturni_purchase_order_item__1300e4df_fk_core_purc` (`purchase_order_item_id`),
  KEY `core_purchasereturni_purchase_return_id_9a26c3af_fk_core_purc` (`purchase_return_id`),
  CONSTRAINT `core_purchasereturni_batch_id_56282041_fk_core_prod` FOREIGN KEY (`batch_id`) REFERENCES `core_productbatch` (`id`),
  CONSTRAINT `core_purchasereturni_purchase_order_item__1300e4df_fk_core_purc` FOREIGN KEY (`purchase_order_item_id`) REFERENCES `core_purchaseorderitem` (`id`),
  CONSTRAINT `core_purchasereturni_purchase_return_id_9a26c3af_fk_core_purc` FOREIGN KEY (`purchase_return_id`) REFERENCES `core_purchasereturn` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `core_sale`
DROP TABLE IF EXISTS `core_sale`;
CREATE TABLE `core_sale` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `invoice_number` varchar(50) NOT NULL,
  `customer_name` varchar(200) NOT NULL,
  `customer_phone` varchar(20) NOT NULL,
  `sale_date` datetime(6) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `tax_amount` decimal(10,2) NOT NULL,
  `discount_amount` decimal(10,2) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `paid_amount` decimal(10,2) NOT NULL,
  `change_amount` decimal(10,2) NOT NULL,
  `returned_amount` decimal(10,2) NOT NULL,
  `payment_status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `tax_percentage` decimal(5,2) NOT NULL,
  `discount_percentage` decimal(5,2) NOT NULL,
  `customer_id` bigint DEFAULT NULL,
  `sold_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `invoice_number` (`invoice_number`),
  KEY `core_sale_customer_id_2acb5b23_fk_core_customer_id` (`customer_id`),
  KEY `core_sale_sold_by_id_93088dbc_fk_auth_user_id` (`sold_by_id`),
  CONSTRAINT `core_sale_customer_id_2acb5b23_fk_core_customer_id` FOREIGN KEY (`customer_id`) REFERENCES `core_customer` (`id`),
  CONSTRAINT `core_sale_sold_by_id_93088dbc_fk_auth_user_id` FOREIGN KEY (`sold_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_sale`
INSERT INTO `core_sale` (`id`, `invoice_number`, `customer_name`, `customer_phone`, `sale_date`, `subtotal`, `tax_amount`, `discount_amount`, `total_amount`, `paid_amount`, `change_amount`, `returned_amount`, `payment_status`, `created_at`, `tax_percentage`, `discount_percentage`, `customer_id`, `sold_by_id`) VALUES (1, 'eb87caa7-e77f-4d8f-bd9c-efba5fca2062', 'zakaria', '01644334516', '2025-10-22 07:12:07.737488', '65.00', '0.00', '0.00', '65.00', '65.00', '0.00', '0.00', 'paid', '2025-10-22 07:12:07.739689', '0.00', '0.00', 1, 1);
INSERT INTO `core_sale` (`id`, `invoice_number`, `customer_name`, `customer_phone`, `sale_date`, `subtotal`, `tax_amount`, `discount_amount`, `total_amount`, `paid_amount`, `change_amount`, `returned_amount`, `payment_status`, `created_at`, `tax_percentage`, `discount_percentage`, `customer_id`, `sold_by_id`) VALUES (2, 'df3834af-5e28-446c-8edb-48578fbd98f1', 'SHUVO', '01790009817', '2025-10-22 07:12:48.195604', '65.00', '0.00', '0.00', '65.00', '65.00', '0.00', '65.00', 'paid', '2025-10-22 07:12:48.199488', '0.00', '0.00', 2, 1);

-- Table structure for table `core_saleitem`
DROP TABLE IF EXISTS `core_saleitem`;
CREATE TABLE `core_saleitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `total_price` decimal(10,2) NOT NULL,
  `batch_id` bigint DEFAULT NULL,
  `product_id` bigint NOT NULL,
  `sale_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_saleitem_batch_id_6438f07f_fk_core_productbatch_id` (`batch_id`),
  KEY `core_saleitem_product_id_2972cee0_fk_core_product_id` (`product_id`),
  KEY `core_saleitem_sale_id_ac8b60ae_fk_core_sale_id` (`sale_id`),
  CONSTRAINT `core_saleitem_batch_id_6438f07f_fk_core_productbatch_id` FOREIGN KEY (`batch_id`) REFERENCES `core_productbatch` (`id`),
  CONSTRAINT `core_saleitem_product_id_2972cee0_fk_core_product_id` FOREIGN KEY (`product_id`) REFERENCES `core_product` (`id`),
  CONSTRAINT `core_saleitem_sale_id_ac8b60ae_fk_core_sale_id` FOREIGN KEY (`sale_id`) REFERENCES `core_sale` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_saleitem`
INSERT INTO `core_saleitem` (`id`, `quantity`, `unit_price`, `total_price`, `batch_id`, `product_id`, `sale_id`) VALUES (1, 1, '65.00', '65.00', NULL, 1, 1);
INSERT INTO `core_saleitem` (`id`, `quantity`, `unit_price`, `total_price`, `batch_id`, `product_id`, `sale_id`) VALUES (2, 1, '65.00', '65.00', NULL, 1, 2);

-- Table structure for table `core_salereturn`
DROP TABLE IF EXISTS `core_salereturn`;
CREATE TABLE `core_salereturn` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `return_number` varchar(20) NOT NULL,
  `return_date` datetime(6) NOT NULL,
  `reason` varchar(20) NOT NULL,
  `return_type` varchar(10) NOT NULL,
  `refund_amount` decimal(10,2) NOT NULL,
  `balance_amount` decimal(10,2) NOT NULL,
  `exchange_quantity` int unsigned NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(10) NOT NULL,
  `processed_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `exchange_product_id` bigint DEFAULT NULL,
  `processed_by_id` int DEFAULT NULL,
  `sale_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `return_number` (`return_number`),
  KEY `core_salereturn_created_by_id_ed5c0847_fk_auth_user_id` (`created_by_id`),
  KEY `core_salereturn_exchange_product_id_37e55d8a_fk_core_product_id` (`exchange_product_id`),
  KEY `core_salereturn_processed_by_id_f610d15d_fk_auth_user_id` (`processed_by_id`),
  KEY `core_salereturn_sale_id_8e308520_fk_core_sale_id` (`sale_id`),
  CONSTRAINT `core_salereturn_created_by_id_ed5c0847_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_salereturn_exchange_product_id_37e55d8a_fk_core_product_id` FOREIGN KEY (`exchange_product_id`) REFERENCES `core_product` (`id`),
  CONSTRAINT `core_salereturn_processed_by_id_f610d15d_fk_auth_user_id` FOREIGN KEY (`processed_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_salereturn_sale_id_8e308520_fk_core_sale_id` FOREIGN KEY (`sale_id`) REFERENCES `core_sale` (`id`),
  CONSTRAINT `core_salereturn_chk_1` CHECK ((`exchange_quantity` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_salereturn`
INSERT INTO `core_salereturn` (`id`, `return_number`, `return_date`, `reason`, `return_type`, `refund_amount`, `balance_amount`, `exchange_quantity`, `description`, `status`, `processed_at`, `created_at`, `updated_at`, `created_by_id`, `exchange_product_id`, `processed_by_id`, `sale_id`) VALUES (1, 'SR202510220001', '2025-10-22 07:14:12.408573', 'defective', 'money', '65.00', '0.00', 0, '', 'completed', '2025-10-22 07:19:28.040921', '2025-10-22 07:14:12.424175', '2025-10-22 07:19:28.040999', 1, NULL, 1, 2);

-- Table structure for table `core_salereturnitem`
DROP TABLE IF EXISTS `core_salereturnitem`;
CREATE TABLE `core_salereturnitem` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `quantity` int NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `total_price` decimal(10,2) NOT NULL,
  `reason` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `batch_id` bigint DEFAULT NULL,
  `sale_item_id` bigint NOT NULL,
  `sale_return_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_salereturnitem_batch_id_f420f2e7_fk_core_productbatch_id` (`batch_id`),
  KEY `core_salereturnitem_sale_item_id_1f72d4a8_fk_core_saleitem_id` (`sale_item_id`),
  KEY `core_salereturnitem_sale_return_id_f00a0503_fk_core_sale` (`sale_return_id`),
  CONSTRAINT `core_salereturnitem_batch_id_f420f2e7_fk_core_productbatch_id` FOREIGN KEY (`batch_id`) REFERENCES `core_productbatch` (`id`),
  CONSTRAINT `core_salereturnitem_sale_item_id_1f72d4a8_fk_core_saleitem_id` FOREIGN KEY (`sale_item_id`) REFERENCES `core_saleitem` (`id`),
  CONSTRAINT `core_salereturnitem_sale_return_id_f00a0503_fk_core_sale` FOREIGN KEY (`sale_return_id`) REFERENCES `core_salereturn` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_salereturnitem`
INSERT INTO `core_salereturnitem` (`id`, `quantity`, `unit_price`, `total_price`, `reason`, `notes`, `batch_id`, `sale_item_id`, `sale_return_id`) VALUES (1, 1, '65.00', '65.00', 'defective', '', NULL, 2, 1);

-- Table structure for table `core_stockadjustment`
DROP TABLE IF EXISTS `core_stockadjustment`;
CREATE TABLE `core_stockadjustment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `adjustment_type` varchar(20) NOT NULL,
  `quantity` int NOT NULL,
  `reason` longtext NOT NULL,
  `adjusted_at` datetime(6) NOT NULL,
  `adjusted_by_id` int NOT NULL,
  `batch_id` bigint DEFAULT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_stockadjustment_adjusted_by_id_c68139be_fk_auth_user_id` (`adjusted_by_id`),
  KEY `core_stockadjustment_batch_id_c463bda5_fk_core_productbatch_id` (`batch_id`),
  KEY `core_stockadjustment_product_id_ad3ed755_fk_core_product_id` (`product_id`),
  CONSTRAINT `core_stockadjustment_adjusted_by_id_c68139be_fk_auth_user_id` FOREIGN KEY (`adjusted_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_stockadjustment_batch_id_c463bda5_fk_core_productbatch_id` FOREIGN KEY (`batch_id`) REFERENCES `core_productbatch` (`id`),
  CONSTRAINT `core_stockadjustment_product_id_ad3ed755_fk_core_product_id` FOREIGN KEY (`product_id`) REFERENCES `core_product` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for table `core_stockmovement`
DROP TABLE IF EXISTS `core_stockmovement`;
CREATE TABLE `core_stockmovement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `movement_type` varchar(20) NOT NULL,
  `quantity` int NOT NULL,
  `batch_number` varchar(100) NOT NULL,
  `reference_number` varchar(100) NOT NULL,
  `notes` longtext NOT NULL,
  `movement_date` datetime(6) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `core_stockmovement_product_id_bd647177_fk_core_product_id` (`product_id`),
  CONSTRAINT `core_stockmovement_product_id_bd647177_fk_core_product_id` FOREIGN KEY (`product_id`) REFERENCES `core_product` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_stockmovement`
INSERT INTO `core_stockmovement` (`id`, `movement_type`, `quantity`, `batch_number`, `reference_number`, `notes`, `movement_date`, `created_at`, `product_id`) VALUES (1, 'return_in', 1, '', 'SR202510220001', 'Sale return completed - SR202510220001', '2025-10-22 07:19:28.039661', '2025-10-22 07:19:28.040051', 1);

-- Table structure for table `core_supplier`
DROP TABLE IF EXISTS `core_supplier`;
CREATE TABLE `core_supplier` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `contact_person` varchar(100) NOT NULL,
  `email` varchar(254) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `address` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_supplier`
INSERT INTO `core_supplier` (`id`, `name`, `contact_person`, `email`, `phone`, `address`, `created_at`) VALUES (1, 'Bashundhara', 'Zakaria', 'sss@ahil.com', '01708480317', '77', '2025-10-22 07:08:30.102829');
INSERT INTO `core_supplier` (`id`, `name`, `contact_person`, `email`, `phone`, `address`, `created_at`) VALUES (2, 'Ifad Multi Products Ltd.', 'shuvo', 's@u.vo', '289237878', 'hhh', '2025-10-22 07:42:47.489684');

-- Table structure for table `core_supplierbill`
DROP TABLE IF EXISTS `core_supplierbill`;
CREATE TABLE `core_supplierbill` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bill_number` varchar(50) NOT NULL,
  `bill_date` datetime(6) NOT NULL,
  `due_date` datetime(6) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `paid_amount` decimal(10,2) NOT NULL,
  `due_amount` decimal(10,2) NOT NULL,
  `status` varchar(20) NOT NULL,
  `notes` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `purchase_order_id` bigint NOT NULL,
  `supplier_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bill_number` (`bill_number`),
  UNIQUE KEY `purchase_order_id` (`purchase_order_id`),
  KEY `core_supplierbill_created_by_id_36eaffa5_fk_auth_user_id` (`created_by_id`),
  KEY `core_supplierbill_supplier_id_a5a2c12a_fk_core_supplier_id` (`supplier_id`),
  CONSTRAINT `core_supplierbill_created_by_id_36eaffa5_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `core_supplierbill_purchase_order_id_15e96e6a_fk_core_purc` FOREIGN KEY (`purchase_order_id`) REFERENCES `core_purchaseorder` (`id`),
  CONSTRAINT `core_supplierbill_supplier_id_a5a2c12a_fk_core_supplier_id` FOREIGN KEY (`supplier_id`) REFERENCES `core_supplier` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_supplierbill`
INSERT INTO `core_supplierbill` (`id`, `bill_number`, `bill_date`, `due_date`, `total_amount`, `paid_amount`, `due_amount`, `status`, `notes`, `created_at`, `created_by_id`, `purchase_order_id`, `supplier_id`) VALUES (1, '219ae54c-8344-4d13-8ae0-41033a39757e', '2025-10-22 07:10:31.422879', '2025-11-23 00:00:00', '750.00', '750.00', '0.00', 'paid', '', '2025-10-22 07:10:31.423986', 1, 1, 1);
INSERT INTO `core_supplierbill` (`id`, `bill_number`, `bill_date`, `due_date`, `total_amount`, `paid_amount`, `due_amount`, `status`, `notes`, `created_at`, `created_by_id`, `purchase_order_id`, `supplier_id`) VALUES (2, '4d2f844c-60fd-46d3-be46-4419c2903352', '2025-10-22 09:21:56.388650', '2025-11-30 00:00:00', '225.00', '0.00', '225.00', 'pending', '', '2025-10-22 09:21:56.389900', 1, 2, 2);

-- Table structure for table `core_userprofile`
DROP TABLE IF EXISTS `core_userprofile`;
CREATE TABLE `core_userprofile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role` varchar(20) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `address` longtext,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `core_userprofile_user_id_5141ad90_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `core_userprofile`
INSERT INTO `core_userprofile` (`id`, `role`, `phone`, `address`, `created_at`, `updated_at`, `user_id`) VALUES (1, 'admin', NULL, '', '2025-10-22 07:06:07.301375', '2025-10-22 07:06:07.301393', 1);

-- Table structure for table `django_admin_log`
DROP TABLE IF EXISTS `django_admin_log`;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `django_admin_log`
INSERT INTO `django_admin_log` (`id`, `action_time`, `object_id`, `object_repr`, `action_flag`, `change_message`, `content_type_id`, `user_id`) VALUES (1, '2025-10-22 07:06:07.302441', '1', 'shuvo - admin', 1, '[{"added": {}}]', 26, 1);
INSERT INTO `django_admin_log` (`id`, `action_time`, `object_id`, `object_repr`, `action_flag`, `change_message`, `content_type_id`, `user_id`) VALUES (2, '2025-10-22 07:07:27.790732', '1', 'Tissue', 1, '[{"added": {}}]', 7, 1);
INSERT INTO `django_admin_log` (`id`, `action_time`, `object_id`, `object_repr`, `action_flag`, `change_message`, `content_type_id`, `user_id`) VALUES (3, '2025-10-22 07:08:30.104100', '1', 'Bashundhara', 1, '[{"added": {}}]', 8, 1);

-- Table structure for table `django_content_type`
DROP TABLE IF EXISTS `django_content_type`;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `django_content_type`
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (1, 'admin', 'logentry');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (3, 'auth', 'group');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (2, 'auth', 'permission');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (4, 'auth', 'user');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (5, 'contenttypes', 'contenttype');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (7, 'core', 'category');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (9, 'core', 'customer');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (10, 'core', 'duepayment');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (25, 'core', 'payment');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (11, 'core', 'product');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (15, 'core', 'productbatch');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (12, 'core', 'purchaseorder');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (13, 'core', 'purchaseordercancellation');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (14, 'core', 'purchaseorderitem');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (16, 'core', 'purchasereturn');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (17, 'core', 'purchasereturnitem');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (18, 'core', 'sale');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (19, 'core', 'saleitem');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (20, 'core', 'salereturn');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (21, 'core', 'salereturnitem');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (22, 'core', 'stockadjustment');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (23, 'core', 'stockmovement');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (8, 'core', 'supplier');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (24, 'core', 'supplierbill');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (26, 'core', 'userprofile');
INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES (6, 'sessions', 'session');

-- Table structure for table `django_migrations`
DROP TABLE IF EXISTS `django_migrations`;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dumping data for table `django_migrations`
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (1, 'contenttypes', '0001_initial', '2025-10-22 06:59:24.348513');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (2, 'auth', '0001_initial', '2025-10-22 06:59:25.427870');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (3, 'admin', '0001_initial', '2025-10-22 06:59:25.657120');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (4, 'admin', '0002_logentry_remove_auto_add', '2025-10-22 06:59:25.671040');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (5, 'admin', '0003_logentry_add_action_flag_choices', '2025-10-22 06:59:25.681792');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (6, 'contenttypes', '0002_remove_content_type_name', '2025-10-22 06:59:25.838766');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (7, 'auth', '0002_alter_permission_name_max_length', '2025-10-22 06:59:25.951488');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (8, 'auth', '0003_alter_user_email_max_length', '2025-10-22 06:59:25.989177');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (9, 'auth', '0004_alter_user_username_opts', '2025-10-22 06:59:25.998822');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (10, 'auth', '0005_alter_user_last_login_null', '2025-10-22 06:59:26.096698');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (11, 'auth', '0006_require_contenttypes_0002', '2025-10-22 06:59:26.102596');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (12, 'auth', '0007_alter_validators_add_error_messages', '2025-10-22 06:59:26.112711');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (13, 'auth', '0008_alter_user_username_max_length', '2025-10-22 06:59:26.227916');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (14, 'auth', '0009_alter_user_last_name_max_length', '2025-10-22 06:59:26.348012');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (15, 'auth', '0010_alter_group_name_max_length', '2025-10-22 06:59:26.373622');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (16, 'auth', '0011_update_proxy_permissions', '2025-10-22 06:59:26.387148');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (17, 'auth', '0012_alter_user_first_name_max_length', '2025-10-22 06:59:26.484202');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (18, 'core', '0001_initial', '2025-10-22 06:59:31.679233');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (19, 'sessions', '0001_initial', '2025-10-22 06:59:31.745900');

-- Table structure for table `django_session`
DROP TABLE IF EXISTS `django_session`;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS=1;