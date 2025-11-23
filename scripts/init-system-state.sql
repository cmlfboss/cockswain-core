CREATE DATABASE IF NOT EXISTS cockswain
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cockswain;

CREATE TABLE IF NOT EXISTS system_state (
  id INT AUTO_INCREMENT PRIMARY KEY,
  timestamp DATETIME NOT NULL,
  cpu_temp VARCHAR(16),
  disk_usage VARCHAR(16),
  warn TINYINT(1) DEFAULT 0,
  source VARCHAR(50) DEFAULT 'observer',
  note VARCHAR(255)
);
