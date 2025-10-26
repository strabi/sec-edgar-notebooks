FROM neo4j:latest

# Seed files
COPY ./neo4jdata/export/export_10_combined.cypher /var/lib/neo4j/import/export_10_combined.cypher
COPY ./neo4j-newDB/auto_import.sh /var/lib/neo4j/scripts/auto_import.sh
COPY ./neo4j-newDB/start.sh /var/lib/neo4j/scripts/start.sh

# Normalize line endings and make executable
RUN sed -i 's/\r$//' /var/lib/neo4j/scripts/*.sh && chmod +x /var/lib/neo4j/scripts/*.sh

# Defaults (override in Railway Variables if you like)
ENV NEO4J_AUTH=neo4j/password \
    NEO4J_PLUGINS='["apoc"]' \
    NEO4J_dbms_security_procedures_unrestricted='apoc.*'

# Start via our script
CMD ["/var/lib/neo4j/scripts/start.sh"]
