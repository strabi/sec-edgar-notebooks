#!/usr/bin/env pwsh
Write-Host "=== neo4j-newDB: fresh import helper ==="

# Run this script from the neo4j-newDB folder. It will:
# - remove any existing neo4j-newdb container
# - delete ./data so Neo4j starts empty
# - start the container using docker compose
# - copy the combined export from ../neo4jdata/export into the container
# - wait for the HTTP endpoint to become available and run the import

# Stop & remove container if present
Write-Host "Stopping/removing existing container (if any)..."
docker rm -f neo4j-newdb 2>$null | Out-Null

# Remove existing database files so we get a clean import
if (Test-Path "./data") {
    Write-Host "Removing existing data directory ./data"
    Remove-Item -Recurse -Force ./data
}

Write-Host "Starting neo4j-newdb via docker compose..."
docker compose -f ./docker-compose.yml up -d

Write-Host "Waiting for Neo4j HTTP to become available on http://localhost:7475 ..."
$max=60
for ($i=0; $i -lt $max; $i++) {
    try {
        $r = Invoke-WebRequest -Uri http://localhost:7475 -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { Write-Host "Neo4j HTTP available"; break }
    } catch { Start-Sleep -Seconds 1 }
}

if ($i -ge $max-1) { Write-Host "Warning: Neo4j did not become healthy in time. Check container logs." }

Write-Host "Copying export_10_combined.cypher into container import folder..."
docker cp ../neo4jdata/export/export_10_combined.cypher neo4j-newdb:/var/lib/neo4j/import/

Write-Host "Running import (cypher-shell)..."
docker exec neo4j-newdb /var/lib/neo4j/bin/cypher-shell -u neo4j -p password -f /var/lib/neo4j/import/export_10_combined.cypher

Write-Host "Verifying counts..."
docker exec neo4j-newdb /var/lib/neo4j/bin/cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n) AS nodes"
docker exec neo4j-newdb /var/lib/neo4j/bin/cypher-shell -u neo4j -p password "MATCH ()-[r]->() RETURN count(r) AS rels"

Write-Host "Done."
