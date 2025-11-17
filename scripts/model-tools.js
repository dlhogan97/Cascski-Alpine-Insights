// model-tools.js - Dynamic rendering and search for model tools page

(function() {
  'use strict';

  // Configuration
  const DATA_URL = 'data/model-tools.json';
  const TOOLS_LIST_ID = 'tools-list';
  const SEARCH_INPUT_ID = 'tools-search';

  let allTools = [];

  // Fetch tools data from JSON
  async function fetchTools() {
    try {
      const response = await fetch(DATA_URL);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      allTools = await response.json();
      renderTools(allTools);
    } catch (error) {
      console.warn('Could not load tools data:', error);
      // Fallback: keep the static HTML content
    }
  }

  // Render tools to the DOM
  function renderTools(tools) {
    const container = document.getElementById(TOOLS_LIST_ID);
    if (!container) return;

    // Clear existing content
    container.innerHTML = '';

    // Render each tool
    tools.forEach(tool => {
      const card = createToolCard(tool);
      container.appendChild(card);
    });
  }

  // Create a tool card element
  function createToolCard(tool) {
    const card = document.createElement('a');
    card.href = tool.url || '#';
    card.className = 'tool-card';

    card.innerHTML = `
      <div class="tool-card__icon">${tool.icon || '🔧'}</div>
      <div class="tool-card__body">
        <h3>${tool.name}</h3>
        <p>${tool.description}</p>
        <div class="tool-meta">
          <span class="btn">View</span>
          <span class="status">${tool.status || 'Available'}</span>
        </div>
      </div>
    `;

    return card;
  }

  // Filter tools based on search query
  function filterTools(query) {
    const lowerQuery = query.toLowerCase().trim();
    
    if (!lowerQuery) {
      renderTools(allTools);
      return;
    }

    const filtered = allTools.filter(tool => {
      return (
        tool.name.toLowerCase().includes(lowerQuery) ||
        tool.description.toLowerCase().includes(lowerQuery) ||
        (tool.status && tool.status.toLowerCase().includes(lowerQuery))
      );
    });

    renderTools(filtered);
  }

  // Initialize search functionality
  function initializeSearch() {
    const searchInput = document.getElementById(SEARCH_INPUT_ID);
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
      filterTools(e.target.value);
    });
  }

  // Initialize the page
  function init() {
    fetchTools();
    initializeSearch();
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
