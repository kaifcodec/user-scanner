/**
 * Cytoscape Relationship Graph Controller for User-Scanner
 * Visualizes target entities, discovered accounts, avatars, and linked connections.
 */

let cy = null;
let currentFilterType = 'ALL';
let activeTooltipEl = null;
let gradualZoomTimer = null;
let currentGraphTheme = (typeof document !== 'undefined' && document.documentElement.getAttribute('data-theme')) || 'dark';

function getGraphStyles(theme = 'dark') {
  const isLight = theme === 'light';
  return [
    // Base Node Style
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'color': isLight ? '#0f172a' : '#f1f5f9',
        'font-family': 'Inter, system-ui, sans-serif',
        'font-size': '11px',
        'font-weight': 600,
        'text-valign': 'bottom',
        'text-margin-y': 7,
        'background-color': 'data(color)',
        'shape': 'data(shape)',
        'width': 38,
        'height': 38,
        'border-width': 2.5,
        'border-color': isLight ? '#ffffff' : '#0f172a',
        'text-background-opacity': isLight ? 0.95 : 0.88,
        'text-background-color': isLight ? '#ffffff' : '#030712',
        'text-background-padding': 4,
        'text-background-shape': 'roundrectangle',
        'transition-property': 'background-color, border-color, width, height, opacity, underlay-opacity',
        'transition-duration': '0.2s'
      }
    },

    // Target Root Entity
    {
      selector: 'node[type = "THREAT_ACTOR"], node[type = "TARGET"]',
      style: {
        'width': 56,
        'height': 56,
        'border-width': 4,
        'border-color': '#f43f5e',
        'background-color': '#e11d48',
        'font-size': '12px',
        'font-weight': 800,
        'underlay-color': '#f43f5e',
        'underlay-padding': 6,
        'underlay-opacity': 0.45,
        'z-index': 100
      }
    },

    // Discovered Platform Accounts
    {
      selector: 'node[type = "SOCIAL_ACCOUNT"]',
      style: {
        'width': 38,
        'height': 38,
        'border-width': 2.5,
        'border-color': 'data(color)',
        'underlay-color': 'data(color)',
        'underlay-padding': 4,
        'underlay-opacity': 0.3,
        'z-index': 60
      }
    },

    // Profile Photo Avatar Nodes
    {
      selector: 'node[?avatar_url]',
      style: {
        'shape': 'ellipse',
        'background-image': 'data(avatar_url)',
        'background-fit': 'cover',
        'background-clip': 'node',
        'border-width': 3,
        'border-color': '#06b6d4',
        'width': 44,
        'height': 44,
        'underlay-color': '#06b6d4',
        'underlay-padding': 4,
        'underlay-opacity': 0.35,
        'z-index': 85
      }
    },

    // Email Pivot Nodes
    {
      selector: 'node[type = "EMAIL"]',
      style: {
        'width': 34,
        'height': 34,
        'shape': 'round-rectangle',
        'background-color': '#ec4899',
        'border-color': '#f472b6',
        'border-width': 2.5,
        'underlay-color': '#ec4899',
        'underlay-padding': 4,
        'underlay-opacity': 0.35,
        'z-index': 70
      }
    },

    // Autonomous Cross-Scan Pivot Nodes (--cross-scan)
    {
      selector: 'node[type = "REBRANDED_ALIAS"], node[type = "PIVOT_USER"]',
      style: {
        'width': 50,
        'height': 50,
        'border-width': 3.5,
        'border-color': '#a855f7',
        'background-color': '#7e22ce',
        'shape': 'hexagon',
        'font-size': '11px',
        'font-weight': 800,
        'underlay-color': '#a855f7',
        'underlay-padding': 5,
        'underlay-opacity': 0.4,
        'z-index': 95
      }
    },

    // Base Edge Style: Clean & uncluttered
    {
      selector: 'edge',
      style: {
        'width': 1.8,
        'line-color': isLight ? 'rgba(100, 116, 139, 0.45)' : 'rgba(148, 163, 184, 0.25)',
        'target-arrow-color': isLight ? 'rgba(100, 116, 139, 0.65)' : 'rgba(148, 163, 184, 0.4)',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 0.85,
        'curve-style': 'bezier',
        'label': '',
        'font-family': 'monospace',
        'font-size': '9px',
        'font-weight': 600,
        'color': isLight ? '#0284c7' : '#38bdf8',
        'text-rotation': 'autorotate',
        'text-margin-y': -8,
        'text-background-opacity': 0.95,
        'text-background-color': isLight ? '#ffffff' : '#020617',
        'text-background-padding': 3,
        'text-background-shape': 'roundrectangle',
        'transition-property': 'width, line-color, target-arrow-color, opacity',
        'transition-duration': '0.2s'
      }
    },

    // Pivot edges (e.g. platform -> leaked email)
    {
      selector: 'edge[relation = "EXPOSES_EMAIL"]',
      style: {
        'line-style': 'dashed',
        'line-color': isLight ? 'rgba(236, 72, 153, 0.6)' : 'rgba(236, 72, 153, 0.45)',
        'target-arrow-color': isLight ? '#ec4899' : '#f472b6',
        'width': 2.0
      }
    },

    // Autonomous Cross-Scan Pivot Edges
    {
      selector: 'edge[relation = "CROSS_PIVOT_TO"]',
      style: {
        'line-style': 'dashed',
        'line-color': isLight ? 'rgba(168, 85, 247, 0.7)' : 'rgba(168, 85, 247, 0.6)',
        'target-arrow-color': isLight ? '#9333ea' : '#a855f7',
        'target-arrow-shape': 'triangle',
        'width': 2.4
      }
    },

    // Active / Selected States
    {
      selector: 'node:selected, node.active-focus',
      style: {
        'border-width': 4.5,
        'border-color': isLight ? '#0284c7' : '#38bdf8',
        'underlay-color': isLight ? 'rgba(2, 132, 199, 0.4)' : '#06b6d4',
        'underlay-padding': 8,
        'underlay-opacity': 0.6,
        'z-index': 999
      }
    },
    {
      selector: 'edge.active-edge',
      style: {
        'width': 3.2,
        'line-color': isLight ? '#0284c7' : '#38bdf8',
        'target-arrow-color': isLight ? '#0284c7' : '#38bdf8',
        'label': 'data(relation)',
        'z-index': 998
      }
    },
    {
      selector: '.dimmed',
      style: {
        'opacity': isLight ? 0.18 : 0.12
      }
    }
  ];
}

function applyGraphTheme(theme) {
  currentGraphTheme = theme;
  if (cy) {
    cy.style(getGraphStyles(theme)).update();
  }
}
window.applyGraphTheme = applyGraphTheme;

/**
 * Computes concentric hierarchy for clean, untangled orbits.
 */
function getConcentricLevel(node) {
  const type = (node.data('type') || '').toUpperCase();
  if (type === 'THREAT_ACTOR') return 100;
  if (type === 'SOCIAL_ACCOUNT') {
    const cat = (node.data('category') || '').toUpperCase();
    if (cat === 'DEV') return 75;
    if (cat === 'SOCIAL') return 60;
    if (cat === 'COMMUNITY') return 50;
    if (cat === 'GAMING') return 40;
    if (cat === 'FINANCE') return 35;
    return 30;
  }
  if (type === 'EMAIL') return 20;
  return 10;
}

function initGraph(containerId, elements) {
  if (cy) {
    cy.destroy();
  }

  initTooltipElement(containerId);

  const sel = document.getElementById('layout-select');
  if (sel) {
    sel.value = 'cose';
  }

  currentGraphTheme = (typeof document !== 'undefined' && document.documentElement.getAttribute('data-theme')) || 'dark';

  cy = cytoscape({
    container: document.getElementById(containerId),
    elements: elements || [],
    style: getGraphStyles(currentGraphTheme),
    minZoom: 0.35,
    maxZoom: 3.0,
    wheelSensitivity: 0.15,
    boxSelectionEnabled: false,
    layout: getLayoutConfig('cose')
  });

  window.cy = cy;

  // Node Hover - Tooltip & Highlight Neighborhood
  cy.on('mouseover', 'node', function(evt) {
    const node = evt.target;
    focusNeighborhood(node);
    showNodeTooltip(node, evt.renderedPosition);
  });

  cy.on('mouseout', 'node', function() {
    hideNodeTooltip();
  });

  // Node Click - Open Inspector Drawer
  cy.on('tap', 'node', function(evt) {
    const node = evt.target;
    focusNeighborhood(node);
    if (window.onGraphNodeSelected) {
      window.onGraphNodeSelected(node.data());
    }
  });

  // Canvas Background Click - Reset Focus
  cy.on('tap', function(evt) {
    if (evt.target === cy) {
      clearNeighborhoodFocus();
      hideNodeTooltip();
    }
  });

  return cy;
}

function getLayoutConfig(name) {
  switch (name) {
    case 'concentric':
      return {
        name: 'concentric',
        concentric: getConcentricLevel,
        levelWidth: function() { return 25; },
        minNodeSpacing: 55,
        spacingFactor: 1.45,
        padding: 70,
        animate: true,
        animationDuration: 550,
        avoidOverlap: true
      };
    case 'breadthfirst':
      return {
        name: 'breadthfirst',
        directed: true,
        roots: cy ? cy.nodes('[type = "THREAT_ACTOR"]') : undefined,
        spacingFactor: 1.5,
        padding: 70,
        animate: true,
        animationDuration: 500
      };
    case 'circle':
      return {
        name: 'circle',
        padding: 70,
        spacingFactor: 1.3,
        animate: true,
        animationDuration: 500
      };
    case 'cose':
    default:
      return {
        name: 'cose',
        idealEdgeLength: 140,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 75,
        randomize: false,
        componentSpacing: 140,
        nodeRepulsion: function() { return 65000; },
        edgeElasticity: function() { return 32; },
        nestingFactor: 1.2,
        gravity: 0.25,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
        animate: true,
        animationDuration: 500
      };
  }
}

function relayoutGraph(layoutName = 'cose', onComplete) {
  if (!cy) return;
  clearNeighborhoodFocus();

  if (gradualZoomTimer) {
    clearTimeout(gradualZoomTimer);
    gradualZoomTimer = null;
  }
  cy.stop();

  const sel = document.getElementById('layout-select');
  if (sel && sel.value !== layoutName) {
    sel.value = layoutName;
  }

  const layout = cy.layout(getLayoutConfig(layoutName));
  layout.one('layoutstop', () => {
    fitGraph();
    if (typeof onComplete === 'function') onComplete();
  });
  layout.run();
}

/**
 * Focuses on a node and its direct incident edges.
 */
function focusNeighborhood(node) {
  if (!cy) return;
  cy.elements().addClass('dimmed').removeClass('active-focus active-edge');
  
  node.removeClass('dimmed').addClass('active-focus');
  
  const connectedEdges = node.connectedEdges();
  connectedEdges.removeClass('dimmed').addClass('active-edge');

  const neighbors = node.neighborhood().nodes();
  neighbors.removeClass('dimmed');
}

function clearNeighborhoodFocus() {
  if (!cy) return;
  cy.elements().removeClass('dimmed active-focus active-edge');
}

/**
 * Filter graph by Category Chip
 */
function filterGraphByType(category) {
  currentFilterType = category;
  if (!cy) return;

  clearNeighborhoodFocus();

  if (category === 'ALL') {
    cy.elements().removeClass('dimmed active-focus active-edge');
    showCanvasStatus("");
    fitGraph();
    return;
  }

  const matches = cy.nodes().filter(n => {
    const type = (n.data('type') || '').toUpperCase();
    const cat = (n.data('category') || '').toUpperCase();
    if (category === 'ACTOR') return type === 'THREAT_ACTOR';
    if (category === 'DEV') return cat === 'DEV';
    if (category === 'SOCIAL') return cat === 'SOCIAL';
    if (category === 'COMMUNITY') return cat === 'COMMUNITY';
    if (category === 'GAMING') return cat === 'GAMING';
    if (category === 'FINANCE') return cat === 'FINANCE';
    if (category === 'PIVOTS') return type === 'EMAIL' || (n.data('id') || '').startsWith('piv_');
    return false;
  });

  if (matches.length === 0) {
    cy.elements().removeClass('dimmed');
    showCanvasStatus(`No ${category} entities in this scan. Showing all nodes.`);
    
    document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
    document.querySelector('.filter-chip[data-category="ALL"]')?.classList.add("active");
    fitGraph();
    return;
  }

  cy.elements().addClass('dimmed').removeClass('active-focus active-edge');
  matches.removeClass('dimmed').addClass('active-focus');
  
  matches.connectedEdges().forEach(e => {
    if (!e.source().hasClass('dimmed') && !e.target().hasClass('dimmed')) {
      e.removeClass('dimmed').addClass('active-edge');
    }
  });

  showCanvasStatus(`Isolated ${matches.length} ${category} ${matches.length === 1 ? 'entity' : 'entities'}`);
  fitGraph(matches);
}

function showCanvasStatus(msg) {
  const banner = document.getElementById('canvas-status-banner');
  if (!banner) return;
  if (!msg) {
    banner.classList.remove('visible');
    return;
  }
  banner.innerText = msg;
  banner.classList.add('visible');
  clearTimeout(banner._timer);
  banner._timer = setTimeout(() => {
    banner.classList.remove('visible');
  }, 3500);
}

/**
 * Entity Search Box Filter
 */
function searchNodeInGraph(query) {
  if (!cy) return;
  const q = (query || "").trim().toLowerCase();
  clearNeighborhoodFocus();

  if (!q) {
    if (currentFilterType !== 'ALL') {
      filterGraphByType(currentFilterType);
    }
    return;
  }

  const matches = cy.nodes().filter(n => {
    const label = (n.data('label') || '').toLowerCase();
    const type = (n.data('type') || '').toLowerCase();
    const id = (n.data('id') || '').toLowerCase();
    const meta = JSON.stringify(n.data('metadata') || {}).toLowerCase();
    return label.includes(q) || type.includes(q) || id.includes(q) || meta.includes(q);
  });

  if (matches.length > 0) {
    cy.elements().addClass('dimmed');
    matches.removeClass('dimmed').addClass('active-focus');
    matches.connectedEdges().removeClass('dimmed').addClass('active-edge');

    cy.animate({
      center: { eles: matches[0] },
      zoom: Math.min(Math.max(cy.zoom(), 1.2), 2.2),
      duration: 350
    });

    if (window.onGraphNodeSelected) {
      window.onGraphNodeSelected(matches[0].data());
    }
  }
}

/**
 * Zoom & Navigation Helpers
 */
function zoomIn() {
  if (!cy) return;
  const next = Math.min(cy.zoom() * 1.3, 3.0);
  cy.animate({
    zoom: { level: next, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } },
    duration: 200
  });
}

function zoomOut() {
  if (!cy) return;
  const next = Math.max(cy.zoom() * 0.75, 0.35);
  cy.animate({
    zoom: { level: next, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } },
    duration: 200
  });
}

function fitGraph(targetEles) {
  if (!cy) return;
  const eles = targetEles || cy.elements();
  if (!eles || eles.length === 0) {
    cy.animate({ fit: { eles: cy.elements(), padding: 70 }, duration: 300 });
    return;
  }
  if (eles.length === 1) {
    cy.animate({
      center: { eles: eles[0] },
      zoom: 1.45,
      duration: 350,
      easing: 'ease-out-cubic'
    });
    return;
  }
  cy.animate({
    fit: { eles: eles, padding: 70 },
    duration: 350
  });
}

function resetGraphView() {
  if (!cy) return;
  clearNeighborhoodFocus();

  document.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
  document.querySelector('.filter-chip[data-category="ALL"]')?.classList.add("active");
  currentFilterType = 'ALL';

  const search = document.querySelector(".canvas-search-input");
  if (search) {
    search.value = "";
  }

  cy.elements().removeClass('dimmed active-focus active-edge');

  relayoutGraph('cose', () => {
    showCanvasStatus("Canvas reset to Force-Directed layout");
  });
}

/**
 * Real-Time Streaming Hit Sprouter
 * Adds a new OSINT pivot node and edge on-the-fly with smooth golden-angle orbital spring animation.
 */
function addStreamingNode(hit) {
  if (!cy || !hit || !hit.node) return;

  const nodeId = hit.node.data.id;
  const existingNode = cy.$id(nodeId);
  if (existingNode.length > 0) {
    existingNode.addClass('active-focus');
    existingNode.animate({
      style: {
        'border-width': 4.5,
        'border-color': hit.target_type === 'email' ? '#f472b6' : '#a855f7'
      },
      duration: 350
    });
    setTimeout(() => existingNode.removeClass('active-focus'), 1800);
    return;
  }

  let actorPos = { x: cy.width() / 2, y: cy.height() / 2 };
  if (hit.actor_node_id) {
    const actorEl = cy.$id(hit.actor_node_id);
    if (actorEl.length > 0) {
      actorPos = actorEl.position();
    }
  }

  const nodeDef = {
    group: 'nodes',
    data: hit.node.data,
    position: {
      x: actorPos.x + (Math.random() - 0.5) * 24,
      y: actorPos.y + (Math.random() - 0.5) * 24
    }
  };

  const elementsToAdd = [nodeDef];
  if (hit.edge && hit.edge.data) {
    elementsToAdd.push({
      group: 'edges',
      data: hit.edge.data
    });
  }

  const added = cy.add(elementsToAdd);
  const newNode = added.filter('node');

  // Distribute new nodes using sunflower phyllotaxis (137.5 deg)
  const hitIndex = hit.hit_index || cy.nodes().length;
  const radius = Math.min(180 + Math.floor(hitIndex / 6) * 35, 360);
  const angle = (hitIndex * 137.508) * (Math.PI / 180);
  const targetX = actorPos.x + Math.cos(angle) * radius;
  const targetY = actorPos.y + Math.sin(angle) * radius;

  newNode.animate({
    position: { x: targetX, y: targetY },
    duration: 520,
    easing: 'ease-out-cubic'
  });

  newNode.addClass('active-focus');
  setTimeout(() => {
    newNode.removeClass('active-focus');
  }, 1400);

  const platformName = hit.platform || 'Platform';
  const targetNote = hit.target ? ` for ${hit.target.includes('@') ? '' : '@'}${hit.target}` : '';
  showCanvasStatus(`Found ${platformName} account${targetNote}`);

  scheduleGradualZoomOut();
}

/**
 * Gradually adjusts zoom as new nodes enter the graph.
 */
function scheduleGradualZoomOut() {
  if (gradualZoomTimer) clearTimeout(gradualZoomTimer);
  gradualZoomTimer = setTimeout(() => {
    gradualZoomTimer = null;
    if (!cy) return;

    const nodes = cy.nodes();
    const count = nodes.length;

    if (count <= 1) {
      const targetNode = nodes[0];
      cy.animate({
        center: { eles: targetNode },
        zoom: 1.45,
        duration: 350,
        easing: 'ease-out-cubic'
      });
      return;
    }

    const dynamicPadding = Math.min(65 + Math.floor(count * 2.5), 115);
    cy.animate({
      fit: {
        eles: cy.elements(),
        padding: dynamicPadding
      },
      duration: 480,
      easing: 'ease-out-cubic'
    });
  }, 130);
}

/**
 * Export High-Resolution PNG Snapshot
 */
function exportGraphImage() {
  if (!cy) return;
  const pngBlob = cy.png({
    full: true,
    scale: 2.5,
    bg: '#020611',
    maxWidth: 3840,
    maxHeight: 2160
  });
  
  const link = document.createElement('a');
  link.href = pngBlob;
  link.download = `user_scanner_graph.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Floating Glassmorphic Hover Tooltip
 */
function initTooltipElement(containerId) {
  let tip = document.getElementById('cy-hud-tooltip');
  if (!tip) {
    tip = document.createElement('div');
    tip.id = 'cy-hud-tooltip';
    tip.className = 'cy-hud-tooltip';
    const container = document.getElementById(containerId);
    if (container) container.appendChild(tip);
  }
  activeTooltipEl = tip;
}

function showNodeTooltip(node, pos) {
  if (!activeTooltipEl) return;
  const data = node.data();
  const avatar = data.avatar_url || (data.metadata ? data.metadata.avatar_url : null);
  const isTarget = data.type === 'TARGET' || data.type === 'THREAT_ACTOR';
  const statusLabel = isTarget ? 'Target Entity' : (data.type === 'EMAIL' ? 'Discovered Email' : 'Verified Account');
  const pivotRating = data.metadata && data.metadata.confidence ? data.metadata.confidence : null;

  let metaSnip = '';
  if (data.metadata) {
    if (data.metadata.url) metaSnip += `<div><strong>URL:</strong> <span style="color:#38bdf8">${escapeHtml(data.metadata.url)}</span></div>`;
    if (data.metadata.email) metaSnip += `<div><strong>Email:</strong> <span style="color:#10b981">${escapeHtml(data.metadata.email)}</span></div>`;
    if (data.metadata.bio) metaSnip += `<div style="color:#cbd5e1;font-style:italic;margin-top:4px;">"${escapeHtml(data.metadata.bio.substring(0, 85))}..."</div>`;
  }

  activeTooltipEl.innerHTML = `
    <div class="tip-header" style="display:flex;align-items:center;gap:10px;">
      ${avatar ? `<img src="${avatar}" style="width:36px;height:36px;border-radius:50%;border:2px solid #06b6d4;object-fit:cover;" onerror="this.style.display='none'">` : ''}
      <div style="flex:1;overflow:hidden;">
        <div class="tip-label" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(data.label)}</div>
        <span class="tip-badge">${escapeHtml(data.category || data.type)}</span>
      </div>
    </div>
    <div class="tip-body">
      <div class="tip-conf">
        <span>Status</span>
        <span style="color:#10b981;font-weight:700">${statusLabel}</span>
      </div>
      ${pivotRating ? `
      <div class="tip-conf">
        <span>Pivot Rating</span>
        <span style="color:#06b6d4;font-weight:700">${escapeHtml(pivotRating)}</span>
      </div>
      ` : ''}
      ${metaSnip ? `<div class="tip-meta">${metaSnip}</div>` : ''}
    </div>
  `;

  const pad = 15;
  activeTooltipEl.style.left = `${Math.min(pos.x + pad, cy.width() - 260)}px`;
  activeTooltipEl.style.top = `${Math.min(pos.y + pad, cy.height() - 170)}px`;
  activeTooltipEl.classList.add('visible');
}

function hideNodeTooltip() {
  if (activeTooltipEl) {
    activeTooltipEl.classList.remove('visible');
  }
}

function escapeHtml(str) {
  if (typeof str !== "string") return String(str ?? "");
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
