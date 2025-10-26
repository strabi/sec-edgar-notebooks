ARG NEO4J_VERSION=5.23.0
FROM neo4j:${NEO4J_VERSION}

ARG NEO4J_AUTH="neo4j/neo4j"
ARG NEO4J_PLUGINS='["apoc","gds"]'
ARG NEO4J_ACCEPT_LICENSE_AGREEMENT="yes"

ENV NEO4J_AUTH="${NEO4J_AUTH}" \
    NEO4J_PLUGINS='${NEO4J_PLUGINS}' \
    NEO4J_ACCEPT_LICENSE_AGREEMENT="${NEO4J_ACCEPT_LICENSE_AGREEMENT}" \
    NEO4J_dbms_default__listen__address="0.0.0.0" \
    NEO4J_dbms_default__advertised__address="0.0.0.0" \
    NEO4J_apoc_export_file_enabled="true" \
    NEO4J_apoc_import_file_enabled="true" \
    NEO4J_apoc_import_file_use__neo4j__config="true" \
    NEO4J_dbms_ssl_policy_bolt_enabled="false"

# optional baseline config (envs still win)
COPY neo4j.conf /var/lib/neo4j/conf/neo4j.conf

# load the dump into the 'neo4j' DB at build time
COPY ../../data/neo4j.dump /var/lib/neo4j/import/neo4j.dump
RUN mkdir -p /var/lib/neo4j/data/databases && \
    chown -R neo4j:neo4j /var/lib/neo4j && \
    neo4j-admin database load neo4j --from-path=/var/lib/neo4j/import --overwrite-destination=true

EXPOSE 7474 7687
