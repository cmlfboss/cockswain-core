-- l7_evolution_v1 - 新增三張表

CREATE TABLE IF NOT EXISTS l7_evolution_log (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_at DATETIME NOT NULL,
  category VARCHAR(50) NOT NULL,       -- daily_summary / observation / adjustment / reflection
  title VARCHAR(255) NOT NULL,
  summary TEXT NOT NULL,
  details JSON NULL,
  PRIMARY KEY (id),
  KEY idx_created_at (created_at),
  KEY idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS l7_system_status (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_at DATETIME NOT NULL,
  overall_health VARCHAR(32) NOT NULL,  -- good / warning / critical
  l1_status VARCHAR(32) DEFAULT NULL,
  l2_status VARCHAR(32) DEFAULT NULL,
  l3_status VARCHAR(32) DEFAULT NULL,
  l4_status VARCHAR(32) DEFAULT NULL,
  l5_status VARCHAR(32) DEFAULT NULL,
  l6_status VARCHAR(32) DEFAULT NULL,
  l7_status VARCHAR(32) DEFAULT NULL,
  metrics JSON NULL,                    -- CPU / Mem / 服務狀態 等
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS l7_suggested_tasks (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  created_at DATETIME NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  priority TINYINT UNSIGNED NOT NULL DEFAULT 3, -- 1~5
  status ENUM('suggested','approved','rejected','in_progress','done') NOT NULL DEFAULT 'suggested',
  source VARCHAR(64) NOT NULL,                  -- 'l7_evolution'
  meta JSON NULL,
  PRIMARY KEY (id),
  KEY idx_created_at (created_at),
  KEY idx_status (status),
  KEY idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
