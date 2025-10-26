#!/usr/bin/env bash
set -e

# Resolve Railway's dynamic port and export cleanly
export NEO4J_server_http_listen__address="0.0.0.0:${PORT}"

# Optional: limit memory if needed
export NEO4J_server_memory_heap_initial__size=256m
export NEO4J_server_memory_heap_max__size=512m
export NEO4J_server_memory_pagecache_size=256m

# Disable telemetry if desired
export NEO4J_dbms_usage__report_enabled=false

# Run import helper in background, then start Neo4j in foreground
/var/lib/neo4j/scripts/auto_import.sh &
exec /var/lib/neo4j/bin/neo4j console
