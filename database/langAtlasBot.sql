-- phpMyAdmin SQL Dump
-- version 4.6.6deb5
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Creato il: Nov 09, 2020 alle 22:47
-- Versione del server: 5.7.31-0ubuntu0.18.04.1
-- Versione PHP: 7.2.24-0ubuntu0.18.04.7

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `langAtlasBot`
--

-- --------------------------------------------------------

--
-- Struttura della tabella `continent`
--

CREATE TABLE `continent` (
  `id` int(11) NOT NULL,
  `continetName` varchar(100) NOT NULL,
  `img` text NOT NULL,
  `continetName_fur` varchar(100) DEFAULT NULL,
  `continetName_en` varchar(100) DEFAULT NULL,
  `continetName_vec` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `continetName_es` varchar(100) NOT NULL,
  `continetName_cat` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `country`
--

CREATE TABLE `country` (
  `id` int(11) NOT NULL,
  `countryName` varchar(100) NOT NULL,
  `continent` int(11) NOT NULL,
  `img` text NOT NULL,
  `countryName_en` varchar(100) DEFAULT NULL,
  `countryName_fur` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `countryName_vec` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `countryName_es` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `countryName_cat` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `country_dialet`
--

CREATE TABLE `country_dialet` (
  `country` int(11) NOT NULL,
  `dialet` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `country_lang`
--

CREATE TABLE `country_lang` (
  `country` int(11) NOT NULL,
  `lang` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `customLang`
--

CREATE TABLE `customLang` (
  `codeCLang` varchar(50) NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `native` varchar(50) DEFAULT NULL,
  `flag` text,
  `addedBy` bigint(20) DEFAULT NULL,
  `visible` tinyint(1) NOT NULL DEFAULT '1',
  `name_en` varchar(50) DEFAULT NULL,
  `name_fur` varchar(50) DEFAULT NULL,
  `name_vec` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name_es` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name_cat` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `feedback`
--

CREATE TABLE `feedback` (
  `idFeed` int(11) NOT NULL,
  `chat_id` bigint(20) NOT NULL,
  `msg_id` bigint(20) NOT NULL,
  `status` varchar(50) NOT NULL,
  `risposta` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `adminMsgID` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `lang`
--

CREATE TABLE `lang` (
  `code` varchar(50) NOT NULL,
  `name` varchar(50) CHARACTER SET utf32 COLLATE utf32_unicode_ci NOT NULL,
  `flag` text,
  `visible` tinyint(1) NOT NULL DEFAULT '1',
  `name_en` varchar(50) DEFAULT NULL,
  `name_vec` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name_es` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `name_cat` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `richieste`
--

CREATE TABLE `richieste` (
  `idRichiesta` int(11) NOT NULL,
  `idChat` bigint(20) NOT NULL,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `link` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `stati` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `isoCode` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `stato` int(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Struttura della tabella `user`
--

CREATE TABLE `user` (
  `id` bigint(20) NOT NULL,
  `status` text,
  `lang` text,
  `dateReg` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `isAdmin` tinyint(1) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indici per le tabelle scaricate
--

--
-- Indici per le tabelle `continent`
--
ALTER TABLE `continent`
  ADD PRIMARY KEY (`id`);

--
-- Indici per le tabelle `country`
--
ALTER TABLE `country`
  ADD PRIMARY KEY (`id`),
  ADD KEY `continent` (`continent`);

--
-- Indici per le tabelle `country_dialet`
--
ALTER TABLE `country_dialet`
  ADD KEY `country_dialet_ibfk_1` (`country`),
  ADD KEY `country_dialet_ibfk_2` (`dialet`);

--
-- Indici per le tabelle `country_lang`
--
ALTER TABLE `country_lang`
  ADD PRIMARY KEY (`country`,`lang`),
  ADD KEY `country_lang_ibfk_2` (`lang`);

--
-- Indici per le tabelle `customLang`
--
ALTER TABLE `customLang`
  ADD PRIMARY KEY (`codeCLang`),
  ADD KEY `native` (`native`),
  ADD KEY `addedBy` (`addedBy`);

--
-- Indici per le tabelle `feedback`
--
ALTER TABLE `feedback`
  ADD PRIMARY KEY (`idFeed`);

--
-- Indici per le tabelle `lang`
--
ALTER TABLE `lang`
  ADD PRIMARY KEY (`code`);

--
-- Indici per le tabelle `richieste`
--
ALTER TABLE `richieste`
  ADD PRIMARY KEY (`idRichiesta`),
  ADD KEY `idChat` (`idChat`);

--
-- Indici per le tabelle `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT per le tabelle scaricate
--

--
-- AUTO_INCREMENT per la tabella `continent`
--
ALTER TABLE `continent`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;
--
-- AUTO_INCREMENT per la tabella `country`
--
ALTER TABLE `country`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=381;
--
-- AUTO_INCREMENT per la tabella `feedback`
--
ALTER TABLE `feedback`
  MODIFY `idFeed` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT per la tabella `richieste`
--
ALTER TABLE `richieste`
  MODIFY `idRichiesta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=54;
--
-- Limiti per le tabelle scaricate
--

--
-- Limiti per la tabella `country`
--
ALTER TABLE `country`
  ADD CONSTRAINT `country_ibfk_1` FOREIGN KEY (`continent`) REFERENCES `continent` (`id`);

--
-- Limiti per la tabella `country_dialet`
--
ALTER TABLE `country_dialet`
  ADD CONSTRAINT `country_dialet_ibfk_1` FOREIGN KEY (`country`) REFERENCES `country` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `country_dialet_ibfk_2` FOREIGN KEY (`dialet`) REFERENCES `customLang` (`codeCLang`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limiti per la tabella `country_lang`
--
ALTER TABLE `country_lang`
  ADD CONSTRAINT `country_lang_ibfk_1` FOREIGN KEY (`country`) REFERENCES `country` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `country_lang_ibfk_2` FOREIGN KEY (`lang`) REFERENCES `lang` (`code`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limiti per la tabella `customLang`
--
ALTER TABLE `customLang`
  ADD CONSTRAINT `customLang_ibfk_1` FOREIGN KEY (`native`) REFERENCES `lang` (`code`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `customLang_ibfk_2` FOREIGN KEY (`addedBy`) REFERENCES `user` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Limiti per la tabella `richieste`
--
ALTER TABLE `richieste`
  ADD CONSTRAINT `richieste_ibfk_1` FOREIGN KEY (`idChat`) REFERENCES `user` (`id`) ON DELETE NO ACTION;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
