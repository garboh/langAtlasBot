-- ============================================================
--  Telegram Linguistic Atlas Bot — database schema
--  Compatible with: database.py (context-manager version)
--  Charset: utf8mb4 throughout
--  Run: mysql -u root -p < database.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS `langAtlasBot`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `langAtlasBot`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
--  user
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `user` (
  `id`      BIGINT       NOT NULL,
  `status`  VARCHAR(255) DEFAULT 'new_user',
  `lang`    VARCHAR(10)  DEFAULT 'en',
  `dateReg` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `isAdmin` TINYINT(1)   NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
--  continent  (note: column name "continetName" kept as-is — typo in original)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `continent` (
  `id`              INT          NOT NULL AUTO_INCREMENT,
  `continetName`    VARCHAR(100) NOT NULL,
  `continetName_en` VARCHAR(100) DEFAULT NULL,
  `continetName_fur`VARCHAR(100) DEFAULT NULL,
  `continetName_vec`VARCHAR(100) DEFAULT NULL,
  `continetName_es` VARCHAR(100) NOT NULL,
  `continetName_cat`VARCHAR(100) NOT NULL,
  `img`             TEXT         NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
--  country
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `country` (
  `id`             INT          NOT NULL AUTO_INCREMENT,
  `countryName`    VARCHAR(100) NOT NULL,
  `countryName_en` VARCHAR(100) DEFAULT NULL,
  `countryName_fur`VARCHAR(100) DEFAULT NULL,
  `countryName_vec`VARCHAR(100) DEFAULT NULL,
  `countryName_es` VARCHAR(100) NOT NULL,
  `countryName_cat`VARCHAR(100) NOT NULL,
  `continent`      INT          NOT NULL,
  `img`            TEXT         NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_country_continent` (`continent`),
  CONSTRAINT `fk_country_continent` FOREIGN KEY (`continent`) REFERENCES `continent` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
--  lang  (standard Telegram language codes)
--  name = Italian name (used by LANG_COL["it"])
--  name_fur is NULL in source dump — add translations manually
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `lang` (
  `code`     VARCHAR(50)  NOT NULL,
  `name`     VARCHAR(50)  NOT NULL COMMENT 'Italian name',
  `name_en`  VARCHAR(50)  DEFAULT NULL,
  `name_fur` VARCHAR(50)  DEFAULT NULL,
  `name_vec` VARCHAR(50)  DEFAULT NULL,
  `name_es`  VARCHAR(50)  DEFAULT NULL,
  `name_cat` VARCHAR(50)  DEFAULT NULL,
  `flag`     TEXT         DEFAULT NULL,
  `visible`  TINYINT(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
--  customLang  (minority / non-standard languages)
--  renamed from "dialet" in original dump; PK renamed to codeCLang
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `customLang` (
  `codeCLang` VARCHAR(50)  NOT NULL,
  `name`      VARCHAR(50)  DEFAULT NULL COMMENT 'Italian name',
  `name_en`   VARCHAR(50)  DEFAULT NULL,
  `name_fur`  VARCHAR(50)  DEFAULT NULL,
  `name_vec`  VARCHAR(50)  DEFAULT NULL,
  `name_es`   VARCHAR(50)  DEFAULT NULL,
  `name_cat`  VARCHAR(50)  DEFAULT NULL,
  `flag`      TEXT         DEFAULT NULL,
  `visible`   TINYINT(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (`codeCLang`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
--  country_lang  (country ↔ standard language mapping)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `country_lang` (
  `country` INT         NOT NULL,
  `lang`    VARCHAR(50) NOT NULL,
  PRIMARY KEY (`country`, `lang`),
  KEY `fk_cl_lang` (`lang`),
  CONSTRAINT `fk_cl_country` FOREIGN KEY (`country`) REFERENCES `country` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_cl_lang`    FOREIGN KEY (`lang`)    REFERENCES `lang` (`code`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ------------------------------------------------------------
--  richieste  (language inclusion requests)
--  Column names aligned with database.py: user_id, nameLang, linkLang
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `richieste` (
  `idRichiesta` INT          NOT NULL AUTO_INCREMENT,
  `user_id`     BIGINT       NOT NULL,
  `nameLang`    VARCHAR(100) NOT NULL,
  `linkLang`    VARCHAR(255) DEFAULT NULL,
  `stato`       TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '0=pending, 1=review, 2=approved, 3=rejected',
  PRIMARY KEY (`idRichiesta`),
  KEY `fk_richieste_user` (`user_id`),
  CONSTRAINT `fk_richieste_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
--  feedback  (not present in original dump — added for bot support)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `feedback` (
  `idFeed`         INT          NOT NULL AUTO_INCREMENT,
  `user_id`        BIGINT       NOT NULL,
  `text`           TEXT         NOT NULL,
  `status`         VARCHAR(50)  NOT NULL DEFAULT 'toBeAnswered' COMMENT 'toBeAnswered | answering | answered',
  `admin_msg_id`   BIGINT       DEFAULT NULL COMMENT 'message_id of the admin group notification',
  `user_full_name` VARCHAR(255) DEFAULT NULL,
  `user_username`  VARCHAR(100) DEFAULT NULL,
  `created`        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idFeed`),
  KEY `fk_feedback_user` (`user_id`),
  CONSTRAINT `fk_feedback_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Migration for existing deployments (safe to run multiple times):
-- ALTER TABLE `feedback`
--   ADD COLUMN IF NOT EXISTS `admin_msg_id`   BIGINT       DEFAULT NULL AFTER `status`,
--   ADD COLUMN IF NOT EXISTS `user_full_name` VARCHAR(255) DEFAULT NULL AFTER `admin_msg_id`,
--   ADD COLUMN IF NOT EXISTS `user_username`  VARCHAR(100) DEFAULT NULL AFTER `user_full_name`;

SET FOREIGN_KEY_CHECKS = 1;
