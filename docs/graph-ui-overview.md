# Graph Visualization UI Overview

This document summarizes the user interface implemented in [`graphvis/static/index.html`](../graphvis/static/index.html).

## Page Layout
- The page occupies the entire viewport with a dark background, placing a full-screen `<div id="scene">` behind floating overlay panels for interaction and information.

## Control Panel (Top Right)
- A mode selector toggles between **Filings**, **Holdings**, and **Sections**, which determines the dataset that is requested and how focus options are populated.
- A **Focus** dropdown filters the graph to a specific entity type (e.g., company, form, manager) and is paired with a text field for entering the identifier or name used in the query.
- Additional buttons and toggles configure graph behavior: node sizing by metric versus degree, link force strength, manual reload, camera auto-spin, and a button to fetch a textual summary for the active view.

## Legend (Top Left)
- A fixed legend explains the color-coding applied to node labels such as Manager, Company, Form, Chunk, and RailwayMarker, matching the palette used in the force-graph renderer.

## Summary Panel (Bottom Right)
- The "Impact Summary" drawer is hidden by default and opens when the **Explain** button retrieves narrative text from `/summary`; it includes a Close button and renders the response as preformatted content.

## Details Panel (Bottom Left)
- Hovering or clicking a node populates the **Details** drawer with the node’s label, name, and property key-value pairs; closing it or clicking the background hides the panel.

## Graph Rendering & Interactions
- The UI uses `ForceGraph3D` (built on Three.js) with orbit controls, node labels, directional particle effects on links, and camera repositioning on node clicks.
- Node colors derive from their labels, and node sizes scale logarithmically based on the currently selected metric.
- An optional auto-spin animation rotates the camera when enabled via the **Auto-Spin** button.

## Data Loading & API Hooks
- The `load()` function composes a `/graph` request according to the current controls (mode, focus type, focus value) and feeds the response into the renderer.
- Adjusting link strength updates the underlying d3 force immediately, while the control initialization on page load ensures the graph renders using default mode and focus settings.
