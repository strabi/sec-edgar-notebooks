# Neo4j FastAPI (tiny)

Run Cypher over HTTP. Swagger UI lives at `/docs`.

## Local run

```bash
cd neo4j-fastapi
cp .env.example .env
# edit .env with your Railway Bolt proxy (bolt://host:port) and password

python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8088
```

Open http://localhost:8088/docs

## Docker

```bash
docker build -t neo4j-fastapi:dev neo4j-fastapi
```

```bash
docker run --rm -p 8088:8088 \
  -e NEO4J_BOLT_URL=bolt://<proxy-host>:<public-port> \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=<password> \
  neo4j-fastapi:dev
```

## Example request

```bash
curl -s http://localhost:8088/cypher \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n) RETURN count(n) AS total"}' | jq .
```

Note: This is a dev-only endpoint that executes arbitrary Cypher. Protect or restrict it before exposing publicly.

Swagger tip: open `http://localhost:8088/docs`, pick `POST /cypher`, click `Try it out`, and execute the default `{ "query": "MATCH (n) RETURN count(n) AS total" }` request for a quick connectivity check.

## Handy sample queries

- Total nodes: `{"query":"MATCH (n) RETURN count(n) AS total"}`
- Total relationships: `{"query":"MATCH ()-[r]->() RETURN count(r) AS total"}`
- Top labels: `{"query":"CALL db.labels() YIELD label WITH label ORDER BY label RETURN label LIMIT 10"}`
- Sample nodes per label: `{"query":"MATCH (n:YourLabel) RETURN n LIMIT 5"}`
- Schema visualization: `{"query":"CALL db.schema.visualization()"}`
