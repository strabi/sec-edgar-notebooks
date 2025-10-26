FROM neo4j:latest

# Copy prepared export file into Neo4j import dir
COPY ./neo4jdata/export/export_10_combined.cypher /var/lib/neo4j/import/export_10_combined.cypher

# Add auto-import helper script
COPY ./neo4j-newDB/auto_import.sh /var/lib/neo4j/scripts/auto_import.sh
RUN chmod +x /var/lib/neo4j/scripts/auto_import.sh

# Default environment variables (can override in Railway)
ENV NEO4J_AUTH=neo4j/password
ENV NEO4J_PLUGINS='["apoc"]'
ENV NEO4J_dbms_security_procedures_unrestricted='apoc.*'
ENV NEO4J_dbms_default__listen__address=0.0.0.0

# Start Neo4j: dynamically export HTTP port for Railway, run auto-import in background
CMD ["bash","-lc","export NEO4J_server_http_listen__address=0.0.0.0:${PORT} && /var/lib/neo4j/scripts/auto_import.sh & exec /var/lib/neo4j/bin/neo4j console"]
