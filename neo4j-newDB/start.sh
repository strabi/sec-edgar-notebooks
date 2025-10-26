#!/usr/bin/env bash
set -euo pipefail

# Ensure PORT exists (Railway sets it; default to 7474 if not)
: "${PORT:=7474}"

# Bind HTTP to Railway's port and let everything listen on all interfaces
export NEO4J_server_http_listen__address="0.0.0.0:${PORT}"
export NEO4J_server_default__listen__address="0.0.0.0"

# Sensible memory caps (override in Railway vars if you want)
export NEO4J_server_memory_heap_initial__size="${NEO4J_server_memory_heap_initial__size:-256m}"
export NEO4J_server_memory_heap_max__size="${NEO4J_server_memory_heap_max__size:-512m}"
export NEO4J_server_memory_pagecache_size="${NEO4J_server_memory_pagecache_size:-256m}"

# Optional: turn off usage reporting
export NEO4J_dbms_usage__report_enabled="${NEO4J_dbms_usage__report_enabled:-false}"

# Kick off your one-time import in the background
/var/lib/neo4j/scripts/auto_import.sh &

# Foreground server (PID 1)
exec /var/lib/neo4j/bin/neo4j console
