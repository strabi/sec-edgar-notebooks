#!/bin/sh
set -e

# auto_import.sh
# Waits for Neo4j to start and runs the combined cypher import once if constraints are not present.

LOG_PREFIX="[auto-import]"
echo "$LOG_PREFIX helper starting"

# Allow skipping automatic import via env var
if [ "$SKIP_AUTO_IMPORT" = "1" ]; then
  echo "$LOG_PREFIX SKIP_AUTO_IMPORT=1 set; skipping automatic import"
  exit 0
fi

# Parse NEO4J_AUTH which is expected in the form user/password
if [ -z "$NEO4J_AUTH" ]; then
  echo "$LOG_PREFIX NEO4J_AUTH not set, defaulting to neo4j/password"
  NEO4J_AUTH="neo4j/password"
fi

USER=$(echo "$NEO4J_AUTH" | cut -d'/' -f1)
PASS=$(echo "$NEO4J_AUTH" | cut -d'/' -f2-)

CYPHER_FILE=${CYPHER_IMPORT_FILE:-/var/lib/neo4j/import/export_10_combined.cypher}
echo "$LOG_PREFIX using cypher file at $CYPHER_FILE"

wait_for_neo4j() {
  echo "$LOG_PREFIX waiting for cypher-shell to accept connections..."
  max=120
  i=0
  until echo "RETURN 1" | /var/lib/neo4j/bin/cypher-shell -u "$USER" -p "$PASS" 2>/dev/null >/dev/null; do
    i=$((i+1))
    if [ $i -ge $max ]; then
      echo "$LOG_PREFIX timeout waiting for Neo4j"
      return 1
    fi
    sleep 1
  done
  echo "$LOG_PREFIX cypher-shell is available"
}

# If the DB already contains the uniqueness constraint, assume import ran
import_needed() {
  # Show constraints and search for a known constraint name
  if /var/lib/neo4j/bin/cypher-shell -u "$USER" -p "$PASS" "SHOW CONSTRAINTS" 2>/dev/null | grep -q "unique_chunk"; then
    echo "$LOG_PREFIX detected existing constraints; skipping import"
    return 1
  fi
  return 0
}

if wait_for_neo4j; then
  if import_needed; then
    if [ -f "$CYPHER_FILE" ]; then
      echo "$LOG_PREFIX running import from $CYPHER_FILE"
      /var/lib/neo4j/bin/cypher-shell -u "$USER" -p "$PASS" -f "$CYPHER_FILE" || {
        echo "$LOG_PREFIX import failed"
        exit 1
      }
      echo "$LOG_PREFIX import completed"
    else
      echo "$LOG_PREFIX no cypher file found at $CYPHER_FILE; skipping"
    fi
  fi
else
  echo "$LOG_PREFIX neo4j did not become ready; skipping import"
fi

exit 0
