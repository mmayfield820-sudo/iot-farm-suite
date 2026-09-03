#!/usr/bin/env bash
set -euo pipefail

export MYSQL_PWD="${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_DATABASE="${MYSQL_DATABASE:-farm}"
MYSQL_USER="${MYSQL_USER:-farm}"

mysql_exec() {
  mysql --protocol=TCP --host="$MYSQL_HOST" --user="$MYSQL_USER" --database="$MYSQL_DATABASE" "$@"
}

for attempt in $(seq 1 60); do
  if mysql_exec --execute="SELECT 1" >/dev/null 2>&1; then
    break
  fi
  if [ "$attempt" = "60" ]; then
    echo "Database did not become ready in time" >&2
    exit 1
  fi
  sleep 2
done

# 001/002 与演示数据由 MySQL 首次创建数据卷时初始化；这里记录基线，
# 后续只按文件名顺序执行增量迁移，保证每次自动部署都可安全重复运行。
mysql_exec <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
  version VARCHAR(255) NOT NULL,
  applied_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
INSERT IGNORE INTO schema_migrations (version)
VALUES ('001_schema.sql'), ('002_reference_data.sql'), ('seed/001_demo_data.sql');
SQL

find /migrations/schema -maxdepth 1 -type f -name '[0-9][0-9][0-9]_*.sql' -print \
  | sort \
  | while IFS= read -r migration; do
      version="$(basename "$migration")"
      case "$version" in
        001_schema.sql|002_reference_data.sql) continue ;;
      esac

      applied="$(mysql_exec --batch --skip-column-names \
        --execute="SELECT COUNT(*) FROM schema_migrations WHERE version = '${version}'")"
      if [ "$applied" = "0" ]; then
        echo "Applying database migration: $version"
        mysql_exec < "$migration"
        mysql_exec --execute="INSERT INTO schema_migrations (version) VALUES ('${version}')"
      else
        echo "Skipping applied database migration: $version"
      fi
    done
