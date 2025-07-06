/*
 Navicat Premium Data Transfer

 Source Server         : xm
 Source Server Type    : MySQL
 Source Server Version : 80404 (8.4.4)
 Source Host           : localhost:3306
 Source Schema         : cs

 Target Server Type    : MySQL
 Target Server Version : 80404 (8.4.4)
 File Encoding         : 65001

 Date: 14/04/2025 12:48:40
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for api_keys
-- ----------------------------
DROP TABLE IF EXISTS `api_keys`;
CREATE TABLE `api_keys`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `api_key` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_used` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `api_key`(`api_key` ASC) USING BTREE,
  INDEX `user_id`(`user_id` ASC) USING BTREE,
  CONSTRAINT `api_keys_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 73 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for conversations
-- ----------------------------
DROP TABLE IF EXISTS `conversations`;
CREATE TABLE `conversations`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NULL DEFAULT NULL,
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_user_time`(`user_id` ASC, `created_at` ASC) USING BTREE,
  CONSTRAINT `conversations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 799 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for messages
-- ----------------------------
DROP TABLE IF EXISTS `messages`;
CREATE TABLE `messages`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `conversation_id` int NULL DEFAULT NULL,
  `role` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_conversation_time`(`conversation_id` ASC, `timestamp` ASC) USING BTREE,
  INDEX `idx_conv_time`(`conversation_id` ASC, `timestamp` ASC) USING BTREE,
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`conversation_id`) REFERENCES `conversations` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4667 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Table structure for questions
-- ----------------------------
DROP TABLE IF EXISTS `questions`;
CREATE TABLE `questions`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `user_id` int NOT NULL,
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `conversation_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_conversation_id`(`conversation_id` ASC) USING BTREE,
  INDEX `idx_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for reference_files
-- ----------------------------
DROP TABLE IF EXISTS `reference_files`;
CREATE TABLE `reference_files`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `question_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `file_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `file_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `file_type` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `similarity` float NULL DEFAULT NULL,
  `source` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `question_id`(`question_id` ASC) USING BTREE,
  CONSTRAINT `reference_files_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 166 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for user_documents
-- ----------------------------
DROP TABLE IF EXISTS `user_documents`;
CREATE TABLE `user_documents`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `file_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `file_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `file_size` int NOT NULL,
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `user_id`(`user_id` ASC) USING BTREE,
  CONSTRAINT `user_documents_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password_hash` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 22 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Function structure for f_jysl
-- ----------------------------
DROP FUNCTION IF EXISTS `f_jysl`;
delimiter ;;
CREATE FUNCTION `f_jysl`(rname varchar(15))
 RETURNS int
  DETERMINISTIC
begin
			declare rnum int;
			select reader.Num into rnum from reader where Readername=rname;
			if rnum is null THEN
			set rnum =0;
			end if;
					return rnum;
end
;;
delimiter ;

-- ----------------------------
-- Function structure for f_sjzt
-- ----------------------------
DROP FUNCTION IF EXISTS `f_sjzt`;
delimiter ;;
CREATE FUNCTION `f_sjzt`(bname varchar(50),bpublisher varchar(30))
 RETURNS varchar(50) CHARSET utf8mb4
  DETERMINISTIC
begin
			declare bstatus varchar(50);
			select Bookstatus into bstatus from bookinfo where Bookname=bname and Publisher=bpublisher;
	if bstatus is null THEN
			set bstatus ='该书籍不存在';
	end if;
			return bstatus;
end
;;
delimiter ;

-- ----------------------------
-- Procedure structure for p_cfind
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_cfind`;
delimiter ;;
CREATE PROCEDURE `p_cfind`(in bm varchar(20))
BEGIN
			declare bid VARCHAR(30);
			declare bname VARCHAR(30);
			declare rid VARCHAR(10);
			declare rname char(20);
			declare jtime datetime;
			declare htime datetime;
			declare done int DEFAULT false;
			DECLARE my_cursor CURSOR for
			select bookinfo.Bookid,bookinfo.Bookname,reader.Readerid,reader.Readername,booklended.Lendtime,booklended.Backtime FROM bookinfo LEFT JOIN booklended on bookinfo.Bookid=booklended.Bookid LEFT JOIN reader on
			booklended.Readerid=reader.Readerid where reader.Dept=bm;
			declare continue handler for not found SET done = TRUE;
			OPEN my_cursor;
			myLoop:LOOP
			FETCH my_cursor INTO bid,bname,rid,rname,jtime,htime;
			if done THEN
							LEAVE myLoop;
			end if;
			insert into brl_bak VALUES(bid,bname,rid,rname,jtime,htime,NOW());
			END LOOP myLoop;
			CLOSE my_cursor;
END
;;
delimiter ;

-- ----------------------------
-- Procedure structure for p_intsp
-- ----------------------------
DROP PROCEDURE IF EXISTS `p_intsp`;
delimiter ;;
CREATE PROCEDURE `p_intsp`(in uspbh char(20),in uspmc char(30),in usslb char(20),in ujg float,in usl int,out v_msg varchar(50))
begin 
     
	   declare done int default false;
		  declare continue handler for 1062 set done=true;
			 insert into spxx values(uspbh,uspmc,usslb,ujg,usl);
		 if done THEN
		      set v_msg='插入失败';
					insert into splog values(uspbh,uspmc,now(),'insert');			
		 end if;
		
end
;;
delimiter ;

-- ----------------------------
-- Procedure structure for P_yg
-- ----------------------------
DROP PROCEDURE IF EXISTS `P_yg`;
delimiter ;;
CREATE PROCEDURE `P_yg`(in bmmc1 varchar(50))
begin
select ygbh,name,zw from ygxx INNER JOIN bmxx on bmxx.bmbh=ygxx.ssbmbh where bmmc=bmmc1;
end
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
