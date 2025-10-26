# Deploying Neo4j to Railway

This directory contains the Docker assets that Railway can use to deploy the full SEC EDGAR knowledge graph. The image loads the `neo4j.dump` file from `data/sample/neo4j.dump` the first time the container starts, then hands control back to the stock Neo4j entrypoint.

## Build Context Layout

- `Dockerfile` – builds from `neo4j:5.23.0`, copies the dump and the helper script, and swaps the entrypoint.
- `restore-and-run.sh` – restores the dump exactly once (or whenever the on-disk database is missing) and then executes `/startup/docker-entrypoint.sh` with the original arguments.

## Required Railway Settings

1. **Repository**: Connect your Railway service to this repository and point the build to `railway/Dockerfile`.
2. **Variables**: Set the same environment variables you use locally, for example:
   - `NEO4J_AUTH=neo4j/<your-password>`
   - `NEO4J_dbms_default__advertised__address=0.0.0.0`
   - `NEO4J_apoc_export_file_enabled=true`
   - `NEO4J_apoc_import_file_enabled=true`
   - `NEO4J_apoc_import_file_use__neo4j__config=true`
   - Optional: `NEO4J_DATABASE_NAME=neo4j` (only change this if you renamed the database)
   - Optionally `LOAD_NEO4J_DUMP=1` (defaults to 1).
3. **Ports**: Expose Railway ports 7474 (HTTP) and 7687 (Bolt).

## First Boot Behaviour

On the first start (or whenever `/var/lib/neo4j/data/databases/neo4j/neostore` is missing), the script runs:

```bash
neo4j-admin database load neo4j --from=/imports/neo4j.dump --overwrite-destination --verbose
```

Subsequent restarts detect the populated database and skip the restore. To force a reload, delete the database directory in the Railway persistent volume or set `LOAD_NEO4J_DUMP=1` and clear the volume.

Logs include a `[railway]` prefix so you can confirm whether a restore happened (`Restoring dump...` vs `Existing database detected...`).
