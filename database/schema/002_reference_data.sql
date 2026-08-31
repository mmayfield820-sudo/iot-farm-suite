
-- Final reference-data snapshot exported from the live `farm` database on 2026-08-31.
-- Run after 001_schema.sql and before database/seed/001_demo_data.sql.
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` (`role_id`, `role_code`, `scope_type`) VALUES (1,'farmer','plot'),(2,'farm_admin','farm'),(3,'system_admin','system');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `permissions` WRITE;
/*!40000 ALTER TABLE `permissions` DISABLE KEYS */;
INSERT INTO `permissions` (`permission_id`, `permission_code`, `resource_type`, `action_type`) VALUES (1,'farm_view','farm','view'),(2,'farm_manage','farm','manage'),(3,'plot_view','plot','view'),(4,'plot_manage','plot','manage'),(5,'device_view','device','view'),(6,'device_manage','device','manage'),(7,'irrigation_control','irrigation','control'),(8,'threshold_view','threshold_config','view'),(9,'threshold_update','threshold_config','update'),(10,'report_view','report','view'),(11,'alert_view','alert','view'),(12,'alert_manage','alert','manage');
/*!40000 ALTER TABLE `permissions` ENABLE KEYS */;
UNLOCK TABLES;

LOCK TABLES `role_permission_rel` WRITE;
/*!40000 ALTER TABLE `role_permission_rel` DISABLE KEYS */;
INSERT INTO `role_permission_rel` (`role_id`, `permission_id`) VALUES (2,1),(3,1),(2,2),(3,2),(1,3),(2,3),(3,3),(2,4),(3,4),(1,5),(2,5),(3,5),(2,6),(3,6),(1,7),(2,7),(3,7),(1,8),(2,8),(3,8),(1,9),(2,9),(3,9),(1,10),(2,10),(3,10),(1,11),(2,11),(3,11),(2,12),(3,12);
/*!40000 ALTER TABLE `role_permission_rel` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
