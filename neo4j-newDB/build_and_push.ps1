param(
    [string]$ImageName,
    [string]$Tag = "latest"
)

if (-not $ImageName) {
    Write-Host "Usage: .\build_and_push.ps1 -ImageName <registry/imagename> [-Tag <tag>]"
    exit 1
}

Write-Host "Building image $ImageName:$Tag (build context = repo root)"
# build from repo root so Dockerfile can COPY ./neo4jdata/export/export_10_combined.cypher
docker build -t $ImageName:$Tag -f neo4j-newDB/Dockerfile .

if ($LASTEXITCODE -ne 0) { Write-Host "docker build failed"; exit $LASTEXITCODE }

Write-Host "Pushing image $ImageName:$Tag"
docker push $ImageName:$Tag
