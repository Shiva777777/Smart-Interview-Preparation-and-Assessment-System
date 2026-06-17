-- =====================================================================
-- Database Schema for AI-Powered Smart Interview Preparation and Assessment System
-- Target Database: MySQL 8.x / 5.7
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `interview_prep` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `interview_prep`;

-- ---------------------------------------------------------------------
-- Table: accounts_userprofile
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `accounts_userprofile` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `career_goal` VARCHAR(100) DEFAULT NULL,
    `domain_preference` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: resume_analyzer_resumeanalysis
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `resume_analyzer_resumeanalysis` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `resume_file` VARCHAR(100) NOT NULL,
    `name` VARCHAR(100) DEFAULT NULL,
    `email` VARCHAR(100) DEFAULT NULL,
    `phone` VARCHAR(30) DEFAULT NULL,
    `education` TEXT DEFAULT NULL,
    `experience` TEXT DEFAULT NULL,
    `skills` TEXT DEFAULT NULL,
    `extracted_text` LONGTEXT DEFAULT NULL,
    `analysed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_resume_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: quiz_question
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `quiz_question` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `text` TEXT NOT NULL,
    `option_a` VARCHAR(255) NOT NULL,
    `option_b` VARCHAR(255) NOT NULL,
    `option_c` VARCHAR(255) NOT NULL,
    `option_d` VARCHAR(255) NOT NULL,
    `correct_option` VARCHAR(5) NOT NULL,
    `explanation` TEXT NOT NULL,
    `domain` VARCHAR(50) NOT NULL,
    `difficulty` VARCHAR(20) NOT NULL,
    `follow_up_question` TEXT DEFAULT NULL,
    `follow_up_explanation` TEXT DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: quiz_quizattempt
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `quiz_quizattempt` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `domain` VARCHAR(50) NOT NULL,
    `difficulty` VARCHAR(20) NOT NULL,
    `score` INT NOT NULL,
    `completed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `tab_switches` INT NOT NULL DEFAULT 0,
    `window_minimizes` INT NOT NULL DEFAULT 0,
    `focus_lost` INT NOT NULL DEFAULT 0,
    CONSTRAINT `fk_quizattempt_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: quiz_useranswer
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `quiz_useranswer` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `attempt_id` BIGINT NOT NULL,
    `question_id` BIGINT NOT NULL,
    `selected_option` VARCHAR(5) DEFAULT NULL,
    `is_correct` TINYINT(1) NOT NULL,
    CONSTRAINT `fk_useranswer_attempt` FOREIGN KEY (`attempt_id`) REFERENCES `quiz_quizattempt` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_useranswer_question` FOREIGN KEY (`question_id`) REFERENCES `quiz_question` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: coding_codingquestion
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `coding_codingquestion` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(100) NOT NULL,
    `description` TEXT NOT NULL,
    `input_format` TEXT NOT NULL,
    `output_format` TEXT NOT NULL,
    `sample_input` TEXT NOT NULL,
    `sample_output` TEXT NOT NULL,
    `difficulty` VARCHAR(10) NOT NULL,
    `test_cases` JSON NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: coding_codingattempt
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `coding_codingattempt` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `question_id` BIGINT NOT NULL,
    `code` TEXT NOT NULL,
    `language` VARCHAR(20) NOT NULL DEFAULT 'Python',
    `status` VARCHAR(30) NOT NULL,
    `marks` INT NOT NULL,
    `attempted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_codingattempt_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_codingattempt_question` FOREIGN KEY (`question_id`) REFERENCES `coding_codingquestion` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: hr_interview_hrquestion
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `hr_interview_hrquestion` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `text` TEXT NOT NULL,
    `key_phrases` TEXT NOT NULL,
    `explanation` TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: hr_interview_hrattempt
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `hr_interview_hrattempt` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `question_id` BIGINT NOT NULL,
    `user_answer` TEXT NOT NULL,
    `feedback` TEXT NOT NULL,
    `score` INT NOT NULL,
    `attempted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_hrattempt_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_hrattempt_question` FOREIGN KEY (`question_id`) REFERENCES `hr_interview_hrquestion` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: roadmap_roadmapprogress
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `roadmap_roadmapprogress` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `goal` VARCHAR(50) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_roadmap_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Table: roadmap_milestone
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `roadmap_milestone` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `roadmap_id` BIGINT NOT NULL,
    `month` INT NOT NULL,
    `topic` VARCHAR(100) NOT NULL,
    `description` TEXT NOT NULL,
    `completed` TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT `fk_milestone_roadmap` FOREIGN KEY (`roadmap_id`) REFERENCES `roadmap_roadmapprogress` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create indexes for performance optimization
CREATE INDEX `idx_quiz_question_domain` ON `quiz_question` (`domain`);
CREATE INDEX `idx_coding_question_diff` ON `coding_codingquestion` (`difficulty`);
CREATE INDEX `idx_milestone_completed` ON `roadmap_milestone` (`completed`);
