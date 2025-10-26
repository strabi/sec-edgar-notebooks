Neo4j Docker quickstart for sec-edgar-notebooks

This folder contains instructions to run the Neo4j database used by the project using Docker Compose.

Prerequisites
- Docker and Docker Compose (Docker Desktop on Windows)
- (Optional) OpenAI API key if you want to run the knowledge-graph construction that uses embeddings

Quick run (PowerShell)

# start with default credentials (neo4j/password)
$env:NEO4J_AUTH = "neo4j/password"
docker compose up -d

Check the Browser
Open: http://localhost:7474/browser/
Login with the credentials from `NEO4J_AUTH` (defaults to `neo4j/password`).

Restore the sample DB (one-time)
If you want to load the provided `data/sample/neo4j.dump` into the mounted `neo4jdata` folder, run the following (PowerShell):

# stop any running container
docker compose down

# load dump into the host `neo4jdata` directory (overwrites any existing db)
docker run --rm -v ${PWD}:/work -w /work -v ${PWD}/data/sample:/backups -v ${PWD}/neo4jdata:/var/lib/neo4j/data neo4j:latest bash -c "cat /backups/neo4j.dump | neo4j-admin database load --from-stdin neo4j --overwrite-destination=true --verbose"

# start the service
docker compose up -d

Persistence and .gitignore
- The repo includes a `neo4jdata/` directory which is used for persistent DB files. Do NOT commit that directory to version control.

Environment variables
- NEO4J_AUTH: authentication token in the form `user/password`. Default in the examples: `neo4j/password`.
- OPENAI_API_KEY: if you want to run `kg-construction.cypher` or the notebooks that call the OpenAI API for embeddings.

How to run the KG construction script
- Open `notebooks/kg-construction/kg-construction.cypher` in the Neo4j Browser.
- Set the `:params` block at the top with your OpenAI key and then run the script in the Browser (or run the statements with `cypher-shell`).

Commit guidance
- Add `docker-compose.yml` and this README to the repo, but ensure `neo4jdata/` is in `.gitignore` so you don't commit DB files.

If you want, I can add a `Makefile` or PowerShell helper scripts to automate the restore and start steps.
