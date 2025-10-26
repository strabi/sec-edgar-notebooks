#!/bin/bash
set -euo pipefail

log() {
  echo "[railway] $1"
}

DUMP_PATH="/imports/neo4j.dump"
DUMP_DIR="$(dirname "${DUMP_PATH}")"
DATABASE_NAME="${NEO4J_DATABASE_NAME:-neo4j}"
DATA_ROOT="/var/lib/neo4j/data/databases/${DATABASE_NAME}"

restore_dump() {
  if [ "${LOAD_NEO4J_DUMP:-1}" != "1" ]; then
    log "LOAD_NEO4J_DUMP != 1 (current: ${LOAD_NEO4J_DUMP:-unset}); skipping restore"
    return
  fi

  if [ ! -f "${DUMP_PATH}" ]; then
    log "Dump not found at ${DUMP_PATH}; skipping restore"
    return
  fi

  if [ -f "${DATA_ROOT}/neostore" ]; then
    log "Existing database detected at ${DATA_ROOT}; skipping restore"
    return
  fi

  log "Restoring dump for database ${DATABASE_NAME}"
  mkdir -p "$(dirname "${DATA_ROOT}")"
  neo4j-admin database load "${DATABASE_NAME}" --from-path="${DUMP_DIR}" --overwrite-destination=true --verbose
  chown -R neo4j:neo4j /var/lib/neo4j/data
  log "Restored dump into ${DATA_ROOT}"
}

# Attempt to restore before handing off to the stock entrypoint.
restore_dump

exec /startup/docker-entrypoint.sh "$@"
