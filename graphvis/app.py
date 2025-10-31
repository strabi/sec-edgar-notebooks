# app.py
import os
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import AuthError, ServiceUnavailable
from neo4j.graph import Node, Relationship, Path as NeoPath

# --- Config ---
NEO4J_URI = (
    os.getenv("NEO4J_BOLT_URL")
    or os.getenv("NEO4J_URI")
    or "bolt://localhost:7687"
)
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD")
NEO4J_AUTH_RAW = os.getenv("NEO4J_AUTH")
INDEX_PATH = Path("static/index.html")
INDEX_V2_PATH = Path("static/v2/index.html")
INDEX_V2_DIR = INDEX_V2_PATH.parent


def _credential_candidates() -> list[Tuple[str, str]]:
    candidates: list[Tuple[str, str]] = []
    if NEO4J_USER and NEO4J_PASS:
        candidates.append((NEO4J_USER, NEO4J_PASS))
    if NEO4J_AUTH_RAW:
        auth_user, _, auth_pass = NEO4J_AUTH_RAW.partition("/")
        if auth_user and auth_pass:
            candidates.append((auth_user, auth_pass))
    candidates.extend([
        ("neo4j", "@Newyork2025"),
        ("neo4j", "password"),
        ("neo4j", "test1234"),
    ])
    deduped: list[Tuple[str, str]] = []
    for cred in candidates:
        if cred not in deduped:
            deduped.append(cred)
    return deduped


def _create_driver() -> Driver:
    last_error: Optional[Exception] = None
    for user, password in _credential_candidates():
        try:
            drv = GraphDatabase.driver(NEO4J_URI, auth=(user, password))
            with drv.session() as session:
                session.run("RETURN 1")
            global NEO4J_USER, NEO4J_PASS
            NEO4J_USER, NEO4J_PASS = user, password
            return drv
        except AuthError as exc:
            last_error = exc
        except ServiceUnavailable as exc:
            last_error = exc
    raise RuntimeError(
        f"Failed to connect to Neo4j at {NEO4J_URI!r} with available credentials: {last_error}"
    )

# --- App / Driver ---
driver = _create_driver()
app = FastAPI(title="FNV Graph Viz")

app.mount("/v2/css", StaticFiles(directory=INDEX_V2_DIR / "css"), name="v2-css")
app.mount("/v2/js", StaticFiles(directory=INDEX_V2_DIR / "js"), name="v2-js")


@app.get("/", response_class=HTMLResponse)
def home():
    return INDEX_PATH.read_text(encoding="utf-8")


@app.get("/v2/", response_class=HTMLResponse)
def home_v2():
    return INDEX_V2_PATH.read_text(encoding="utf-8")


# ---------- Shared helpers ----------

def _focus_clauses(mode: str, focusType: Optional[str], focus: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    if not focusType or not focus:
        return "", {}

    params: Dict[str, Any] = {"focus": focus, "focusLower": focus.lower()}
    try:
        params["focusInt"] = int(focus.replace(",", ""))
    except ValueError:
        params["focusInt"] = None

    if mode == "filings":
        if focusType == "company":
            clause = (
                "WHERE toLower(coalesce(company.companyName, company.names[0], '')) CONTAINS $focusLower "
                "OR company.cusip6 = $focus "
                "OR toString(company.cik) = $focus"
            )
        elif focusType == "form":
            clause = "WHERE form.formId = $focus"
        elif focusType == "cusip":
            clause = "WHERE company.cusip6 = $focus"
        else:
            clause = ""

    elif mode == "holdings":
        if focusType == "manager":
            clause = (
                "WHERE toLower(coalesce(manager.managerName, '')) CONTAINS $focusLower "
                "OR toString(manager.managerCik) = $focus"
            )
        elif focusType == "company":
            clause = (
                "WHERE toLower(coalesce(company.companyName, company.names[0], '')) CONTAINS $focusLower "
                "OR company.cusip6 = $focus"
            )
        elif focusType == "cusip":
            clause = "WHERE company.cusip6 = $focus"
        else:
            clause = ""

    else:  # sections
        if focusType == "form":
            clause = "WHERE form.formId = $focus"
        elif focusType == "company":
            clause = (
                "WHERE toLower(coalesce(company.companyName, company.names[0], '')) CONTAINS $focusLower "
                "OR company.cusip6 = $focus"
            )
        elif focusType == "item":
            clause = "WHERE sectionRel.item = $focus"
        elif focusType == "chunk":
            clause = "WHERE section.chunkId = $focus"
        else:
            clause = ""

    return clause, params


def build_query(mode: str, focusType: Optional[str], focus: Optional[str], limit: int) -> Tuple[str, Dict[str, Any]]:
    where_clause, focus_params = _focus_clauses(mode, focusType, focus)
    params: Dict[str, Any] = {"limit": limit, **focus_params}

    if mode == "holdings":
        cypher = f"""
        MATCH (manager:Manager)-[owns:OWNS_STOCK_IN]->(company:Company)
        {where_clause}
        OPTIONAL MATCH (company)-[filed:FILED]->(form:Form)
        RETURN manager, owns, company, form, filed
        ORDER BY owns.value DESC, company.name
        LIMIT $limit
        """
    elif mode == "sections":
        cypher = f"""
        MATCH (form:Form)-[sectionRel:SECTION]->(section:Chunk)
        OPTIONAL MATCH (company:Company)-[filed:FILED]->(form)
        WITH form, sectionRel, section, company, filed
        {where_clause}
        OPTIONAL MATCH (section)-[nextRel:NEXT]->(nextChunk:Chunk)
        OPTIONAL MATCH (section)<-[prevRel:NEXT]-(prevChunk:Chunk)
        RETURN form, company, filed, sectionRel, section, nextRel, nextChunk, prevRel, prevChunk
        LIMIT $limit
        """
    else:  # filings
        cypher = f"""
        MATCH (company:Company)-[filed:FILED]->(form:Form)
        {where_clause}
        OPTIONAL MATCH (company)<-[owns:OWNS_STOCK_IN]-(manager:Manager)
        OPTIONAL MATCH (form)-[sectionRel:SECTION]->(section:Chunk)
        OPTIONAL MATCH (section)-[nextRel:NEXT]->(nextChunk:Chunk)
        RETURN company, filed, form, manager, owns, sectionRel, section, nextRel, nextChunk
        LIMIT $limit
        """

    return cypher, params


def to_graph(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    nodes: list[Dict[str, Any]] = []
    links: list[Dict[str, Any]] = []
    seen_nodes: set[Any] = set()
    seen_links: set[Tuple[Any, Any, str]] = set()

    def sanitize_props(data: Dict[str, Any]) -> Dict[str, Any]:
        props = {
            k: v for k, v in data.items() if k not in {"textEmbedding", "summaryEmbeddings"}
        }
        text_val = props.get("text")
        if isinstance(text_val, str) and len(text_val) > 600:
            props["text"] = text_val[:600] + "…"
        return props

    def node_name(node_label: str, props: Dict[str, Any]) -> str:
        name_val = props.get("name") or props.get("companyName") or props.get("managerName")
        if name_val:
            return str(name_val)
        if node_label == "Form" and props.get("formId"):
            return str(props["formId"])
        if node_label == "Company" and props.get("cusip6"):
            label_name = name_val or props.get("names") or "Company"
            if isinstance(label_name, list) and label_name:
                label_name = label_name[0]
            return f"{label_name} ({props['cusip6']})"
        if node_label == "Manager":
            cik_val = props.get("cik") or props.get("managerCik")
            return f"{name_val or 'Manager'} ({cik_val})" if cik_val else str(name_val or "Manager")
        if node_label == "Chunk":
            text = props.get("text") or props.get("chunkId") or "Chunk"
            return str(text)[:80] + ("…" if isinstance(text, str) and len(text) > 80 else "")
        if props.get("chunkId"):
            return str(props["chunkId"])
        return f"{node_label}"

    def add_node(node: Node) -> None:
        if not isinstance(node, Node):
            return
        if node.id in seen_nodes:
            return
        seen_nodes.add(node.id)
        label = next(iter(node.labels)) if node.labels else "Node"
        props = sanitize_props(dict(node.items()))
        metric = (
            props.get("value")
            or props.get("shares")
            or props.get("amount")
            or (len(props.get("text", "")) if props.get("text") else 1)
        )
        nodes.append(
            {
                "id": node.id,
                "label": label,
                "name": node_name(label, props),
                "metric": metric,
                "props": props,
            }
        )

    def add_relationship(rel: Relationship) -> None:
        if not isinstance(rel, Relationship):
            return
        start = getattr(rel, "start_node", None)
        end = getattr(rel, "end_node", None)
        if (start is None or end is None) and hasattr(rel, "nodes"):
            rel_nodes = rel.nodes
            if rel_nodes and len(rel_nodes) == 2:
                start, end = rel_nodes
        if start is None or end is None:
            return
        add_node(start)
        add_node(end)
        key = (start.id, end.id, rel.type)
        if key in seen_links:
            return
        seen_links.add(key)
        links.append(
            {
                "source": start.id,
                "target": end.id,
                "type": rel.type,
                "props": dict(rel.items()),
            }
        )

    def handle(value: Any) -> None:
        if isinstance(value, Node):
            add_node(value)
        elif isinstance(value, Relationship):
            add_relationship(value)
        elif isinstance(value, NeoPath):
            for path_node in value.nodes:
                add_node(path_node)
            for path_rel in value.relationships:
                add_relationship(path_rel)
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
            for item in value:
                handle(item)

    for record in records:
        for value in record.values():
            handle(value)

    return {"nodes": nodes, "links": links}


def summarize_graph(mode: str, focusType: Optional[str], focus: Optional[str], graph: Dict[str, Any]) -> str:
    # Basic stats
    labels = [n["label"] for n in graph["nodes"]]
    counts = Counter(labels)
    by_label_names = defaultdict(list)
    for n in graph["nodes"]:
        name = str(n.get("name", ""))
        if name:
            by_label_names[n["label"]].append(name)

    # relationship flavors
    link_types = Counter(l["type"] for l in graph["links"])
    # top apps and endpoints by degree (proxy for impact)
    deg = Counter()
    for l in graph["links"]:
        deg[l["source"]] += 1
        deg[l["target"]] += 1
    id_to = {n["id"]: n for n in graph["nodes"]}
    top_nodes = [id_to[i]["name"] for i, _ in deg.most_common(5) if i in id_to]
    top_managers = [
        id_to[i]["name"]
        for i, _ in deg.most_common()
        if i in id_to and id_to[i]["label"] == "Manager"
    ][:3]
    top_companies = [
        id_to[i]["name"]
        for i, _ in deg.most_common()
        if i in id_to and id_to[i]["label"] == "Company"
    ][:3]
    top_forms = [
        id_to[i]["name"]
        for i, _ in deg.most_common()
        if i in id_to and id_to[i]["label"] == "Form"
    ][:3]
    top_chunks = [
        id_to[i]["name"]
        for i, _ in deg.most_common()
        if i in id_to and id_to[i]["label"] == "Chunk"
    ][:3]

    # compose a short narrative
    focus_str = ""
    if focusType and focus:
        focus_str = f" Focus: {focusType} = “{focus}”."

    parts = []
    parts.append(f"{mode.capitalize()} view with {len(graph['nodes'])} nodes / {len(graph['links'])} links.{focus_str}")

    # label counts
    if counts:
        label_bits = ", ".join(f"{k}:{v}" for k, v in counts.most_common())
        parts.append(f" Node mix → {label_bits}.")

    # link types
    if link_types:
        link_bits = ", ".join(f"{k}:{v}" for k, v in link_types.most_common())
        parts.append(f" Relations → {link_bits}.")

    # impact highlights
    if mode == "holdings" and top_managers:
        parts.append(f" Top managers: {', '.join(top_managers)}.")
    if mode in {"filings", "holdings"} and top_companies:
        parts.append(f" Key companies: {', '.join(top_companies)}.")
    if mode == "filings" and top_forms:
        parts.append(f" Active filings: {', '.join(top_forms)}.")
    if mode == "sections" and top_chunks:
        parts.append(f" Dense chunks: {', '.join(top_chunks)}.")
    if top_nodes:
        parts.append(f" Overall hubs: {', '.join(top_nodes)}.")

    # gentle callout based on mode
    if mode == "filings":
        parts.append(" Suggestion: review company narratives alongside filing sections for emerging risks.")
    elif mode == "holdings":
        parts.append(" Suggestion: compare position sizes across managers to spot concentration or consensus trades.")
    elif mode == "sections":
        parts.append(" Suggestion: follow NEXT chains to capture surrounding context before quoting a chunk.")

    return " ".join(parts)


# ---------- Endpoints ----------

@app.get("/graph")
def graph(
    mode: str = Query("filings", pattern="^(filings|holdings|sections)$"),
    limit: int = Query(800, ge=1, le=5000),
    focusType: Optional[str] = Query(None),
    focus: Optional[str] = Query(None),
):
    cypher, params = build_query(mode, focusType, focus, limit)
    with driver.session() as s:
        recs = s.run(cypher, **params)
        return JSONResponse(to_graph(recs))


@app.get("/summary", response_class=PlainTextResponse)
def summary(
    mode: str = Query("filings", pattern="^(filings|holdings|sections)$"),
    limit: int = Query(800, ge=1, le=5000),
    focusType: Optional[str] = Query(None),
    focus: Optional[str] = Query(None),
):
    """
    Returns a concise, human-readable impact explanation for the current subgraph.
    """
    cypher, params = build_query(mode, focusType, focus, limit)
    with driver.session() as s:
        recs = s.run(cypher, **params)
        g = to_graph(recs)
    return summarize_graph(mode, focusType, focus, g)
