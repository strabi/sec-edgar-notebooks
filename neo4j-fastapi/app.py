import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, ConfigDict
from neo4j import GraphDatabase, basic_auth

APP_NAME = "neo4j-fastapi"
BOLT_URL = os.environ.get("NEO4J_BOLT_URL", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")
MAX_ROWS = int(os.environ.get("MAX_ROWS", "1000"))

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD environment variable is required")

app = FastAPI(title="Neo4j Cypher API", version="0.1.0")

_driver = None


@app.on_event("startup")
def startup():
    global _driver
    _driver = GraphDatabase.driver(BOLT_URL, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))


@app.on_event("shutdown")
def shutdown():
    global _driver
    if _driver is not None:
        _driver.close()


class CypherRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "query": "MATCH (n) RETURN count(n) AS total",
        }
    })

    query: str = Field(..., description="Cypher query to execute")


class CypherResponse(BaseModel):
    rows: List[Dict[str, Any]]
    count: int
    capped: bool


def neo4j_status() -> Dict[str, Any]:
    if _driver is None:
        return {"status": "degraded", "neo4j": False, "error": "Driver not initialized"}
    try:
        with _driver.session() as session:
            ok = bool(session.run("RETURN 1 AS ok").single().get("ok", 0))
        return {"status": "ok", "neo4j": ok, "error": None}
    except Exception as exc:
        return {"status": "degraded", "neo4j": False, "error": str(exc)}


def record_to_dict(rec) -> Dict[str, Any]:
    # Convert a neo4j.Record into a plain dict
    out = {}
    for key in rec.keys():
        val = rec.get(key)
        # basic serialization for nodes/relationships/paths
        try:
            if hasattr(val, "items") and "element_id" in dir(val):
                # Node or Relationship → show labels/type + properties
                if val.__class__.__name__ == "Node":
                    out[key] = {
                        "_type": "node",
                        "id": val.element_id,
                        "labels": list(val.labels),
                        "props": dict(val),
                    }
                elif val.__class__.__name__ == "Relationship":
                    out[key] = {
                        "_type": "relationship",
                        "id": val.element_id,
                        "type": val.type,
                        "props": dict(val),
                    }
                else:
                    out[key] = str(val)
            else:
                out[key] = val
        except Exception:
            out[key] = str(val)
    return out


@app.get("/", response_class=HTMLResponse)
def root():
    status = neo4j_status()
    status_label = "connected" if status["neo4j"] else "error"
    error_message = f"<p><strong>Error:</strong> {status['error']}</p>" if status["error"] else ""
    body = f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"utf-8\" />
        <title>{APP_NAME}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 2rem; }}
            .status {{ font-size: 1.1rem; }}
            .connected {{ color: #0a8754; }}
            .error {{ color: #c0392b; }}
            .card {{ max-width: 520px; border: 1px solid #ddd; padding: 1.5rem; border-radius: 8px; }}
            a {{ color: #0366d6; }}
        </style>
    </head>
    <body>
        <div class=\"card\">
            <h1>{APP_NAME}</h1>
            <p class=\"status {status_label}\">Neo4j status: <strong>{status_label}</strong></p>
            <p>Bolt URL: <code>{BOLT_URL}</code></p>
            <p>Connected as: <code>{NEO4J_USER}</code></p>
            {error_message}
            <hr />
            <p>Use the <a href=\"/docs\">Swagger UI</a> to run Cypher queries.</p>
            <p>Health check JSON is available at <a href=\"/health\">/health</a>.</p>
            <h2>Quick sample</h2>
            <pre>{'{"query":"MATCH (n) RETURN count(n) AS total"}'}</pre>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=body)


@app.get("/health")
def health():
    status = neo4j_status()
    if status["error"]:
        return {"status": status["status"], "neo4j": status["neo4j"], "error": status["error"]}
    return {"status": status["status"], "neo4j": status["neo4j"]}


@app.post("/cypher", response_model=CypherResponse, summary="Execute a Cypher query")
def run_cypher(body: CypherRequest):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")

    # Soft cap: don't stream unbounded results
    rows: List[Dict[str, Any]] = []
    try:
        with _driver.session() as s:
            result = s.run(body.query)
            for i, rec in enumerate(result):
                if i >= MAX_ROWS:
                    break
                rows.append(record_to_dict(rec))
        return {"rows": rows, "count": len(rows), "capped": len(rows) >= MAX_ROWS}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cypher error: {e}")
