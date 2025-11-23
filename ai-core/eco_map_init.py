#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化生態地圖資料表（無 SSL 版）
"""
import mysql.connector
from pathlib import Path

def load_env_pw():
    env_file = Path("/srv/cockswain-core/.env")
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("MYSQL_PASSWORD="):
                return line.split("=", 1)[1].strip()
    return None

def main():
    pw = load_env_pw()
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="cockswain_core",
        password=pw,
        database="cockswain",
        ssl_disabled=True   # ← 關鍵：不要用 SSL
    )
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS eco_nodes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        node_name VARCHAR(128) NOT NULL,
        node_type VARCHAR(64) DEFAULT 'mother',
        ip_addr VARCHAR(64),
        status VARCHAR(32) DEFAULT 'active',
        meta JSON NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS eco_agents (
        id INT AUTO_INCREMENT PRIMARY KEY,
        agent_name VARCHAR(128) NOT NULL,
        role VARCHAR(64),
        bind_node INT,
        status VARCHAR(32) DEFAULT 'active',
        meta JSON NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bind_node) REFERENCES eco_nodes(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS eco_services (
        id INT AUTO_INCREMENT PRIMARY KEY,
        service_name VARCHAR(128) NOT NULL,
        endpoint VARCHAR(255),
        bind_agent INT,
        status VARCHAR(32) DEFAULT 'active',
        meta JSON NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bind_agent) REFERENCES eco_agents(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("eco_map tables created/verified.")

if __name__ == "__main__":
    main()
