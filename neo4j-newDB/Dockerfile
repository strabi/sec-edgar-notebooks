FROM neo4j:latest

# Copy the prepared combined export into the image so it's available in /var/lib/neo4j/import
# When building locally, run the build from the repository root so the path below exists.
COPY ./neo4jdata/export/export_10_combined.cypher /var/lib/neo4j/import/export_10_combined.cypher

# Add an auto-import helper script that runs once on container start if the DB is empty.
COPY ./neo4j-newDB/auto_import.sh /var/lib/neo4j/scripts/auto_import.sh
RUN chmod +x /var/lib/neo4j/scripts/auto_import.sh

# Default envs (can be overridden at runtime)
ENV NEO4J_AUTH=neo4j/password
ENV NEO4J_PLUGINS='["apoc"]'
ENV NEO4J_dbms_security_procedures_unrestricted='apoc.*'

# Start Neo4j but run the auto-import helper in background which will wait for the DB to be ready
# and then run the import if it hasn't been applied yet.
# The official image provides an entrypoint; we pass the CLI argument `neo4j` to start the DB.
CMD ["sh", "-c", "/var/lib/neo4j/scripts/auto_import.sh & neo4j"]
