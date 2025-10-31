async function bootstrap() {
  const [three, graphModule] = await Promise.all([
    import('https://unpkg.com/three@0.160.0/build/three.module.js?module'),
    import('https://unpkg.com/3d-force-graph@1.41.5/dist/3d-force-graph.min.js?module')
  ]);

  // Expose THREE for legacy expectations inside 3d-force-graph
  globalThis.THREE = three;
  const ForceGraph3D = graphModule.default || graphModule;

  const sceneEl = document.getElementById('scene');
  if (!sceneEl) {
    console.warn('Scene element not found; aborting graph initialization.');
    return;
  }

  const modeSel = document.getElementById('mode');
  const focusSel = document.getElementById('focusType');
  const focusInp = document.getElementById('focus');
  const sizeMetricSel = document.getElementById('sizeMetric');
  const linkStrengthInput = document.getElementById('linkStrength');
  const reloadBtn = document.getElementById('reload');
  const spinBtn = document.getElementById('spin');
  const explainBtn = document.getElementById('explain');
  const summaryEl = document.getElementById('summary');
  const summaryContent = document.getElementById('summaryContent');
  const summaryClose = document.getElementById('summaryClose');
  const detailsEl = document.getElementById('details');
  const detailsContent = document.getElementById('detailsContent');
  const detailsClose = document.getElementById('detailsClose');
  const statusEl = document.getElementById('graphStatus');
  const controlsForm = document.getElementById('controls-form');

  const colorByLabel = (label) => ({
    Manager: '#34d399',
    Company: '#60a5fa',
    Form: '#fbbf24',
    Chunk: '#a78bfa',
    KnowledgeGraph: '#f472b6',
    RailwayMarker: '#fb7185'
  })[label] || '#9ca3af';

  const focusConfig = {
    filings: {
      placeholder: 'Apple',
      options: [
        { value: 'company', label: 'company (name / CUSIP6)' },
        { value: 'form', label: 'form id' },
        { value: 'cusip', label: 'CUSIP6' }
      ]
    },
    holdings: {
      placeholder: 'BlackRock',
      options: [
        { value: 'manager', label: 'manager (name / CIK)' },
        { value: 'company', label: 'company (name / CUSIP6)' },
        { value: 'cusip', label: 'CUSIP6' }
      ]
    },
    sections: {
      placeholder: '0000107140-23-000092-item1a-chunk0000',
      options: [
        { value: 'form', label: 'form id' },
        { value: 'company', label: 'company (name / CUSIP6)' },
        { value: 'item', label: 'section item (e.g., item1a)' },
        { value: 'chunk', label: 'chunk id' }
      ]
    }
  };

  const Graph = ForceGraph3D({ controlType: 'orbit' })(sceneEl)
    .nodeLabel((node) => `${node.label}: ${node.name}`)
    .nodeAutoColorBy('label')
    .linkOpacity(0.35)
    .linkDirectionalParticles(2)
    .linkDirectionalParticleWidth(1.2);

  let currentGraph = null;
  let spinning = false;
  let animationLoopStarted = false;
  let detailLocked = false;

  Graph.onNodeClick((node) => {
    if (!node) {
      return;
    }
    detailLocked = true;
    const dist = 80;
    const { x, y, z } = node;
    Graph.cameraPosition({ x: x + dist, y: y + dist, z: z + dist }, node, 2000);
    showDetails(node);
  });

  Graph.onBackgroundClick(() => {
    detailLocked = false;
    showDetails(null);
  });

  Graph.onNodeHover((node) => {
    if (detailLocked) {
      return;
    }
    if (node) {
      showDetails(node);
    } else {
      showDetails(null);
    }
  });

  function setStatus(message) {
    if (statusEl) {
      statusEl.textContent = message || '';
    }
  }

  function setLoading(isLoading) {
    reloadBtn.disabled = isLoading;
    reloadBtn.setAttribute('aria-busy', String(isLoading));
    if (isLoading) {
      setStatus('Loading graph data…');
    }
  }

  function togglePanel(panel, show, focusTarget) {
    panel.hidden = !show;
    panel.classList.toggle('is-hidden', !show);
    if (show && focusTarget) {
      focusTarget.focus();
    }
    if (!show && panel.contains(document.activeElement)) {
      controlsForm.querySelector('button, input, select')?.focus();
    }
  }

  function setFocusOptions() {
    const mode = modeSel.value;
    const config = focusConfig[mode] || focusConfig.filings;
    focusSel.innerHTML = '';
    focusSel.append(new Option('(none)', ''));
    config.options.forEach(({ value, label }) => {
      focusSel.append(new Option(label, value));
    });
    focusInp.placeholder = config.placeholder;
  }

  function showDetails(node) {
    if (!node) {
      togglePanel(detailsEl, false);
      detailsContent.innerHTML = '';
      return;
    }
    const props = node.props || {};
    const rows = Object.entries(props)
      .map(([key, value]) => `<div class="panel__prop"><b>${key}</b>: ${String(value)}</div>`)
      .join('');
    detailsContent.innerHTML = `
      <div class="panel__meta">
        <span class="panel__meta-label">${node.label}</span>
        <div class="panel__meta-value">${node.name}</div>
      </div>
      <div class="panel__separator" role="presentation"></div>
      <div>${rows || '<span class="panel__empty">No properties</span>'}</div>
    `;
    togglePanel(detailsEl, true, detailsClose);
  }

  function render(graph) {
    if (!graph || !Array.isArray(graph.nodes)) {
      return;
    }
    currentGraph = graph;
    const degrees = {};
    graph.links?.forEach((link) => {
      degrees[link.source] = (degrees[link.source] || 0) + 1;
      degrees[link.target] = (degrees[link.target] || 0) + 1;
    });
    const metricMode = sizeMetricSel.value;
    graph.nodes.forEach((node) => {
      const metric = metricMode === 'degree' ? (degrees[node.id] || 1) : (node.metric || 1);
      node.color = colorByLabel(node.label);
      node.val = 2 + Math.log2(1 + metric);
    });
    Graph.graphData(graph)
      .nodeColor((node) => node.color)
      .d3Force('link')
      .strength(Number(linkStrengthInput.value));
    startAnimationLoop();
    setStatus(`Loaded ${graph.nodes.length} nodes and ${graph.links?.length || 0} links.`);
  }

  function startAnimationLoop() {
    if (animationLoopStarted) {
      return;
    }
    animationLoopStarted = true;
    (function animate() {
      if (spinning) {
        const camera = Graph.camera();
        camera.position.x += 0.1;
        camera.lookAt(Graph.scene().position);
      }
      requestAnimationFrame(animate);
    })();
  }

  async function loadGraph() {
    setLoading(true);
    detailLocked = false;
    showDetails(null);
    try {
      const mode = modeSel.value;
      const focusType = focusSel.value;
      const focusValue = focusInp.value.trim();
      const url = new URL('/graph', window.location.origin);
      url.searchParams.set('mode', mode);
      url.searchParams.set('limit', '1000');
      if (focusType) {
        url.searchParams.set('focusType', focusType);
        if (focusValue) {
          url.searchParams.set('focus', focusValue);
        }
      }
      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error(`Graph request failed (${response.status})`);
      }
      const graph = await response.json();
      render(graph);
    } catch (error) {
      console.error(error);
      setStatus('Unable to load graph data.');
      summaryContent.textContent = 'Unable to load graph data. Please try again.';
      togglePanel(summaryEl, true, summaryClose);
    } finally {
      setLoading(false);
    }
  }

  async function explainSelection() {
    try {
      setStatus('Generating summary…');
      const mode = modeSel.value;
      const focusType = focusSel.value;
      const focusValue = focusInp.value.trim();
      const url = new URL('/summary', window.location.origin);
      url.searchParams.set('mode', mode);
      url.searchParams.set('limit', '1000');
      if (focusType) {
        url.searchParams.set('focusType', focusType);
        if (focusValue) {
          url.searchParams.set('focus', focusValue);
        }
      }
      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error(`Summary request failed (${response.status})`);
      }
      const text = await response.text();
      summaryContent.textContent = text || '(no summary)';
      togglePanel(summaryEl, true, summaryClose);
      setStatus('Summary ready.');
    } catch (error) {
      console.error(error);
      summaryContent.textContent = 'Unable to generate summary right now.';
      togglePanel(summaryEl, true, summaryClose);
      setStatus('Summary request failed.');
    }
  }

  setFocusOptions();
  loadGraph();

  controlsForm.addEventListener('submit', (event) => {
    event.preventDefault();
    loadGraph();
  });

  modeSel.addEventListener('change', () => {
    setFocusOptions();
    loadGraph();
  });

  focusSel.addEventListener('change', () => {
    focusInp.focus();
  });

  sizeMetricSel.addEventListener('change', () => {
    if (currentGraph) {
      render(currentGraph);
    }
  });

  linkStrengthInput.addEventListener('input', () => {
    Graph.d3Force('link').strength(Number(linkStrengthInput.value));
  });

  spinBtn.addEventListener('click', () => {
    spinning = !spinning;
    spinBtn.setAttribute('aria-pressed', String(spinning));
    spinBtn.textContent = spinning ? 'Stop Auto-Spin' : 'Start Auto-Spin';
  });

  explainBtn.addEventListener('click', () => {
    explainSelection();
  });

  summaryClose.addEventListener('click', () => {
    togglePanel(summaryEl, false);
  });

  detailsClose.addEventListener('click', () => {
    detailLocked = false;
    togglePanel(detailsEl, false);
  });
}

bootstrap().catch((error) => {
  console.error('Failed to initialise graph viz', error);
  const statusEl = document.getElementById('graphStatus');
  if (statusEl) {
    statusEl.textContent = 'Unable to initialise graph viz.';
  }
});
