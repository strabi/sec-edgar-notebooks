# Railway deployment checklist — neo4j-newdb (build from repo Dockerfile)

This short checklist walks through deploying the `neo4j-newdb` service on Railway by building the Dockerfile in `neo4j-newDB/Dockerfile` from this repository.

Before you start
- Ensure the repository is pushed to GitHub and Railway has access (OAuth or via repository invite).
- Make sure you have a strong password to set in `NEO4J_AUTH` (avoid `neo4j/password` in production).

1) Create a new Railway project and connect the GitHub repo
- Login to https://railway.app
- Click "New Project" -> "Deploy from GitHub"
- Select the repository `strabi/sec-edgar-notebooks` (or your fork)

Screenshot tip: Railway will show a list of repos; pick the one that contains this repo root. If prompted for permissions, allow Railway to read your repo.

2) Configure the service to use the Dockerfile
- Railway will detect build options. Choose "Dockerfile" or "Docker" service.
- Set the Dockerfile path to: `neo4j-newDB/Dockerfile`
- Leave build context as the repository root (default).

Screenshot tip: In the build settings pane, set the Dockerfile path exactly as above. If Railway lets you preview the Dockerfile, confirm it includes `auto_import.sh` and `export_10_combined.cypher` paths.

3) Set environment variables (use Railway secrets)
- In the Environment / Variables section add:
  - `NEO4J_AUTH` = `neo4j/<strong_password>` (replace `<strong_password>`)
  - `NEO4J_PLUGINS` = `["apoc"]`
  - `NEO4J_dbms_security_procedures_unrestricted` = `apoc.*`
  - Optional (to disable auto-import): `SKIP_AUTO_IMPORT` = `1`

Screenshot tip: Use the Railway UI to mark sensitive values as secret; don't commit them to Git.

4) Deploy and watch logs
- Click Deploy. The build will use the repo root as context and the specified Dockerfile path.
- Open the service logs as it boots. Look for lines from the helper script:
  - `[auto-import] helper starting`
  - `[auto-import] cypher-shell is available`
  - `[auto-import] running import from /var/lib/neo4j/import/export_10_combined.cypher`
  - `[auto-import] import completed`

Screenshot tip: Use the Logs tab in Railway to tail logs in real time. If you don't see `[auto-import]`, expand earlier logs or increase the log buffer.

5) Troubleshooting
- Import timed out / not running: The helper waits up to ~120s for the DB to accept cypher-shell connections. If your host is slower, set `SKIP_AUTO_IMPORT=1` and run the import manually using Railway's "Run" command:
  `/var/lib/neo4j/bin/cypher-shell -u neo4j -p <password> -f /var/lib/neo4j/import/export_10_combined.cypher`
- Constraint/duplicate errors: If the import fails due to duplicate constraints or existing data, redeploy with a fresh data volume or set `SKIP_AUTO_IMPORT=1` and run a manual wipe before import (not recommended in production):
  `MATCH (n) DETACH DELETE n; DROP CONSTRAINT unique_chunk IF EXISTS;` then run the import.
- Logs: Check both startup logs (build logs) and the runtime container logs. Build errors means Railway failed to include files in the build context — ensure the export file exists at `neo4jdata/export/export_10_combined.cypher` at repo root when Railway builds.

6) Networking & security
- Railway exposes services via public URLs by default. Protect Neo4j ports or restrict access using Railway private networking if you need to limit access.

7) Alternative: Build & push image externally
- If you prefer to build an image yourself and push to a registry, use `neo4j-newDB/build_and_push.ps1` locally, then in Railway create a Docker service that pulls that image instead of building from the repo.

If you want, I can also:
- Add a GitHub Actions workflow to build and push the image to GHCR on push to a branch.
- Prepare a Railway-run script that executes the import manually via Railway's CLI.
