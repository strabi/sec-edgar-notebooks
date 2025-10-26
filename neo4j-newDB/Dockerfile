FROM neo4j:latest

# Seed files
COPY ./neo4jdata/export/export_10_combined.cypher /var/lib/neo4j/import/export_10_combined.cypher
COPY ./neo4j-newDB/auto_import.sh /var/lib/neo4j/scripts/auto_import.sh
RUN chmod +x /var/lib/neo4j/scripts/auto_import.sh

# Defaults (override in Railway Variables if you like)
ENV NEO4J_AUTH=neo4j/password
ENV NEO4J_PLUGINS='["apoc"]'
ENV NEO4J_dbms_security_procedures_unrestricted='apoc.*'
ENV NEO4J_dbms_default__listen__address=0.0.0.0

# Ephemeral persistence for a running deployment
VOLUME ["/data"]

# Start: set HTTP to Railway $PORT, run auto-import in background, then foreground server
CMD ["bash","-lc","export NEO4J_server_http_listen__address=0.0.0.0:${PORT} && /var/lib/neo4j/scripts/auto_import.sh & exec /var/lib/neo4j/bin/neo4j console"]

