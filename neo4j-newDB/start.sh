#!/usr/bin/env bash
set -euo pipefail

# Ensure PORT exists (Railway sets it; default to 7474 if not)
: "${PORT:=7474}"

# Bind HTTP to Railway's port and let everything listen on all interfaces
# NOTE: Neo4j translates `.` in config keys to double underscores when reading
# from environment variables (e.g. `server.http.listen_address` →
# `NEO4J_server_http__listen__address`). We previously missed the double
# underscore between `http` and `listen`, which meant Neo4j interpreted the
# value as part of the next environment variable during parsing and failed to
# start (showing an address like `"0.0.0.0"NEO4J_server_memory_heap_initial__size=256m:7474`).
# Setting the correctly named variable ensures the HTTP connector binds
# properly on Railway's assigned port.
export NEO4J_server_http__listen__address="0.0.0.0:${PORT}"
export NEO4J_server_default__listen__address="0.0.0.0"

# Sensible memory caps (override in Railway vars if you want).
# Neo4j 5.x expects underscores in config keys to be doubled when
# translated to environment variables. Support both the correct names and
# the older single-underscore spellings we previously used so existing
# Railway variables continue to work.
initial_heap_size="${NEO4J_server_memory_heap__initial__size:-${NEO4J_server_memory_heap_initial__size:-256m}}"
max_heap_size="${NEO4J_server_memory_heap__max__size:-${NEO4J_server_memory_heap_max__size:-512m}}"
pagecache_size="${NEO4J_server_memory_pagecache__size:-${NEO4J_server_memory_pagecache_size:-256m}}"

export NEO4J_server_memory_heap__initial__size="$initial_heap_size"
export NEO4J_server_memory_heap__max__size="$max_heap_size"
export NEO4J_server_memory_pagecache__size="$pagecache_size"

# Avoid leaking the legacy env vars into the process; Neo4j treats unknown
# NEO4J_* vars as configuration and will warn/fail if the key is invalid.
unset NEO4J_server_memory_heap_initial__size 2>/dev/null || true
unset NEO4J_server_memory_heap_max__size 2>/dev/null || true
unset NEO4J_server_memory_pagecache_size 2>/dev/null || true
unset NEO4J_server_http_listen__address 2>/dev/null || true

# Optional: turn off usage reporting
export NEO4J_dbms_usage__report_enabled="${NEO4J_dbms_usage__report_enabled:-false}"

# Kick off your one-time import in the background
/var/lib/neo4j/scripts/auto_import.sh &

# Foreground server (PID 1)
exec /var/lib/neo4j/bin/neo4j console
