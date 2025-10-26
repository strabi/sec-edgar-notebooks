# neo4j-newDB — local test image & Railway deployment

This folder contains artifacts to run a reproducible Neo4j instance with the 10% sample preloaded.

What's included
- `Dockerfile` — builds an image based on `neo4j:latest` and includes `export_10_combined.cypher` in `/var/lib/neo4j/import/`.
- `auto_import.sh` — runs on container start and will automatically apply the cypher import once if the DB is empty.
- `import_and_start.ps1` — PowerShell helper that recreates a clean local container and runs the import (good for Windows devs).
- `build_and_push.ps1` — helper to build and push the image to a registry.

Behavior: automatic import on first boot
- This image implements an "auto import" helper that waits for Neo4j to start and runs the combined import file once. The helper:
  - reads credentials from `NEO4J_AUTH` (format `user/password`) — default `neo4j/password`.
  - waits for cypher-shell to accept connections, then checks `SHOW CONSTRAINTS` for `unique_chunk`.
  - if the constraint is not present, it runs `/var/lib/neo4j/import/export_10_combined.cypher`.

Disable automatic import
- If you prefer to run the import manually after deployment, set the environment variable `SKIP_AUTO_IMPORT=1` in the container (Railway environment variables or `docker run -e SKIP_AUTO_IMPORT=1 ...`).

Local quick start (fresh import, recommended)

```powershell
cd .\neo4j-newDB
.\import_and_start.ps1
```

This helper will remove any existing `neo4j-newdb` container, delete `./data` so Neo4j starts empty, start the container, copy the cypher file from `../neo4jdata/export/`, and run the import.

Manual import (if you disabled auto-import)

```powershell
# start container via compose
docker compose -f .\docker-compose.yml up -d
# copy the export into the container (if not baked into image)
docker cp ..\neo4jdata\export\export_10_combined.cypher neo4j-newdb:/var/lib/neo4j/import/
# run the import
docker exec neo4j-newdb /var/lib/neo4j/bin/cypher-shell -u neo4j -p <password> -f /var/lib/neo4j/import/export_10_combined.cypher
```

Railway deployment (build from repo Dockerfile)

1. Push this repository to GitHub (or ensure Railway can access the repo).
2. In Railway, create a new service and choose "Deploy from GitHub" or create a Docker service that builds from the repo.
   - Set the build context to the repository root and the Dockerfile path to `neo4j-newDB/Dockerfile` (Railway will use the repo root as build context).
3. Add environment variables in Railway service settings:
   - `NEO4J_AUTH` — e.g. `neo4j/<strong_password>` (use secrets in Railway)
   - `NEO4J_PLUGINS` — `["apoc"]`
   - `NEO4J_dbms_security_procedures_unrestricted` — `apoc.*`
   - Optional: `SKIP_AUTO_IMPORT=1` (to disable automatic import)
4. Deploy the service. By default the image will run auto-import on first boot (unless `SKIP_AUTO_IMPORT=1` is set).

Notes about Railway and long-running imports
- The auto-import script waits up to ~120s for Neo4j to become ready; for larger imports or slower hosts you may want to disable auto-import and run the cypher import with a Railway one-off command after the service is up.

Security
- Use a strong password for `NEO4J_AUTH` on Railway and avoid exposing the Bolt/HTTP ports publicly unless protected by network rules.

Want automation?
- I can add a GitHub Actions workflow that builds the image and pushes it to a registry (GitHub Container Registry / DockerHub) on push. Let me know which registry and I will add the workflow and a secrets template.
