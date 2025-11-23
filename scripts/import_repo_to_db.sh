#!/usr/bin/env bash
set -e
REPO_ROOT="/srv/cockswain-core/data/repo"
ENV_FILE="/srv/cockswain-core/.env"
LOG_FILE="/srv/cockswain-core/logs/import_repo_to_db.log"
mkdir -p "$(dirname "$LOG_FILE")"
# default
MYSQL_HOST="localhost"
MYSQL_USER="root"
MYSQL_PASSWORD=""
MYSQL_DATABASE="cockswain"
# load from .env
if [ -f "$ENV_FILE" ]; then
  while IFS='=' read -r k v; do
    case "$k" in
      MYSQL_HOST) MYSQL_HOST="$v" ;;
      MYSQL_USER) MYSQL_USER="$v" ;;
      MYSQL_PASSWORD) MYSQL_PASSWORD="$v" ;;
      MYSQL_DATABASE) MYSQL_DATABASE="$v" ;;
    esac
  done < <(grep -v '^#' "$ENV_FILE" | grep '=')
fi

log() { echo "[$(date '+%F %T')] $*" >> "$LOG_FILE"; }

log "=== start import ==="

mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \\\`$MYSQL_DATABASE\\\`;" 2>>"$LOG_FILE"

mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" <<'SQL' 2>>"$LOG_FILE"
CREATE TABLE IF NOT EXISTS records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trace_id VARCHAR(255),
  topic VARCHAR(255),
  title TEXT,
  description TEXT,
  tags JSON,
  meta JSON,
  content JSON,
  received_at DATETIME NULL,
  inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
SQL
find "$REPO_ROOT" -type f -name '*.json' | while read -r file; do
  trace_id=$(jq -r '.meta.trace_id // empty' "$file")
  topic=$(jq -r '.meta.topic // empty' "$file")
  title=$(jq -r '.summary.title // empty' "$file")
  description=$(jq -r '.summary.description // empty' "$file")
  tags=$(jq -c '.tags // []' "$file")
  meta=$(jq -c '.meta // {}' "$file")
  content=$(jq -c '.content // {}' "$file")
  received_at=$(jq -r '.meta.received_at // empty' "$file")

  [ -z "$trace_id" ] && log "skip $file (no trace_id)" && continue

  esc() { printf "%s" "$1" | sed "s/'/''/g"; }
  title_esc=$(esc "$title")
  description_esc=$(esc "$description")
  tags_esc=$(esc "$tags")
  meta_esc=$(esc "$meta")
  content_esc=$(esc "$content")

  [ -n "$received_at" ] && received_sql="'$received_at'" || received_sql="NULL"

  mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
    -e "INSERT INTO records (trace_id,topic,title,description,tags,meta,content,received_at)
        VALUES (
          '$trace_id',
          '$topic',
          '$title_esc',
          '$description_esc',
          '$tags_esc',
          '$meta_esc',
          '$content_esc',
          $received_sql
        );" 2>>"$LOG_FILE" \
    && log "imported $file" \
    || log "failed $file"
done

log "=== done import ==="
MYSQL_DATABASE="cockswain"

# load from .env if exists
if [ -f "$ENV_FILE" ]; then
  while IFS="=" read -r k v; do
    case "$k" in
      MYSQL_HOST) MYSQL_HOST="$v" ;;
      MYSQL_USER) MYSQL_USER="$v" ;;
      MYSQL_PASSWORD) MYSQL_PASSWORD="$v" ;;
      MYSQL_DATABASE) MYSQL_DATABASE="$v" ;;
    esac
  done < <(grep -v "^#" "$ENV_FILE" | grep "=")
fi

log() { echo "[$(date "+%F %T")] $*" >> "$LOG_FILE"; }

log "=== start import ==="

mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \\\`$MYSQL_DATABASE\\\`;" 2>>"$LOG_FILE"

mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" << "SQL" 2>>"$LOG_FILE"
CREATE TABLE IF NOT EXISTS records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trace_id VARCHAR(255),
  topic VARCHAR(255),
  title TEXT,
  description TEXT,
  tags JSON,
  meta JSON,
  content JSON,
  received_at DATETIME NULL,
  inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
SQL
