# GraphRAG Viz v2 Preview

This directory hosts a lightweight "v2" UI so you can compare the original Three.js graph viz ("v1") with the small animation-loop improvement applied in v2.

## Run locally

1. From the repository root, install project dependencies (skip if already done):
   ```powershell
   pip install -e .
   ```
2. Start the FastAPI app that serves both versions:
   ```powershell
   cd graphvis
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```
3. Open your browser to `http://localhost:8000/` to load v1. Use the banner link to jump to `http://localhost:8000/v2/` and the return link to go back to v1.

The app expects a reachable Neo4j instance (see `graphvis/README.md` for connection details). Both front-ends share the same API endpoints, so no extra build steps are required.
