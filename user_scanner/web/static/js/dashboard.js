/**
 * User-Scanner Web Application Controller
 * Coordinates real-time scan streaming, interactive relationship graph,
 * module discovery, and investigation exports.
 */

let activeCaseId = null;
let currentCaseData = null;
let currentScanTarget = "";
let isScanning = false;
let isTheaterMode = false;
let isLeftCollapsed = false;
let isRightCollapsed = false;
let activeScanAbortController = null;

// Scan state
let scanType = "username";
let userTargetMode = "single";
let emailTargetMode = "single";

// Catalog and module selection state
let userModuleCatalog = [];
let emailModuleCatalog = [];

// Dynamically extract module counts and rounded baseline floors from body dataset
const bodyDataset = (typeof document !== "undefined" && document.body) ? document.body.dataset : {};
let userTotalModules = parseInt(bodyDataset.userMods, 10) || 532;
let emailTotalModules = parseInt(bodyDataset.emailMods, 10) || 188;
let userBaseFloor = parseInt(bodyDataset.userBase, 10) || (Math.floor(userTotalModules / 5) * 5);
let emailBaseFloor = parseInt(bodyDataset.emailBase, 10) || (Math.floor(emailTotalModules / 5) * 5);
let totalCoverageFloor = parseInt(bodyDataset.totalBase, 10) || (userBaseFloor + emailBaseFloor);

function updateGlobalCoverageCounter() {
  userBaseFloor = Math.floor(userTotalModules / 5) * 5;
  emailBaseFloor = Math.floor(emailTotalModules / 5) * 5;
  totalCoverageFloor = userBaseFloor + emailBaseFloor;
  const covEl = document.getElementById("coverage-total-count");
  if (covEl) {
    covEl.innerText = `${totalCoverageFloor}+ Supported Sites`;
  }
}

let userSelectedCategories = new Set(["ALL"]);
let emailSelectedCategories = new Set(["ALL"]);
let userSelectedModules = [];
let emailSelectedModules = [];

let validatedProxies = [];
let hudsonResults = [];

let telemetry = {
  queued: userBaseFloor,
  checked: 0,
  verified: 0,
  pivots: 0,
  hudson: 0,
  categories: { DEV: 0, SOCIAL: 0, COMMUNITY: 0, GAMING: 0, FINANCE: 0, MUSIC: 0, TECH: 0, ADULT: 0 }
};

let currentTheme = (typeof document !== 'undefined' && document.documentElement.getAttribute("data-theme")) || "dark";

// Theme handling
function initTheme() {
  currentTheme = (typeof document !== 'undefined' && document.documentElement.getAttribute("data-theme")) || "dark";
  updateThemeUI(currentTheme);
  const btn = document.getElementById("theme-toggle-btn");
  if (btn) {
    btn.addEventListener("click", toggleTheme);
  }
}

function updateThemeUI(theme) {
  const btn = document.getElementById("theme-toggle-btn");
  if (btn) {
    btn.title = theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode";
    btn.setAttribute("aria-label", btn.title);
  }
}

function toggleTheme() {
  currentTheme = currentTheme === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", currentTheme);
  try {
    localStorage.setItem("us-theme", currentTheme);
  } catch (e) {
    console.warn("Could not persist theme preference:", e);
  }
  updateThemeUI(currentTheme);
  if (typeof window.applyGraphTheme === "function") {
    window.applyGraphTheme(currentTheme);
  }
}

// Application initialization
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  setupPrimaryScanTabs();
  setupSubtabs();
  setupMasterAdvancedToggle();
  setupAccordion();
  setupModuleSearch();
  setupProxyValidator();
  setupCanvasControls();
  setupInspectorTabs();
  setupScanForm();
  setupExportControls();
  setupProgressDock();
  setupSponsorToast();

  // Pre-load catalogs for responsive tab switching
  fetchModuleCatalog(false);
  fetchModuleCatalog(true);

  // Check prefill target from query string
  const initialUserInput = document.getElementById("scan-user-target");
  if (initialUserInput && initialUserInput.value.trim().length > 0) {
    const rawVal = initialUserInput.value.trim();
    if (rawVal.includes("@")) {
      switchPrimaryScanTab("email");
      const emailInput = document.getElementById("scan-email-target");
      if (emailInput) emailInput.value = rawVal;
      initialUserInput.value = "";
    }
    setTimeout(() => {
      executeLiveScan();
    }, 250);
  }
});

// Primary mode navigation (Username vs Email)
function setupPrimaryScanTabs() {
  const tabUser = document.getElementById("tab-btn-user-scan");
  const tabEmail = document.getElementById("tab-btn-email-scan");

  if (tabUser) {
    tabUser.addEventListener("click", () => switchPrimaryScanTab("username"));
  }
  if (tabEmail) {
    tabEmail.addEventListener("click", () => switchPrimaryScanTab("email"));
  }
}

function switchPrimaryScanTab(type) {
  scanType = type;
  const tabUser = document.getElementById("tab-btn-user-scan");
  const tabEmail = document.getElementById("tab-btn-email-scan");
  const secUser = document.getElementById("section-user-scan");
  const secEmail = document.getElementById("section-email-scan");
  const btnSubmitText = document.getElementById("btn-run-scan-text");
  const queuedEl = document.getElementById("stat-vectors-queued");

  if (type === "email") {
    tabEmail?.classList.add("active");
    tabUser?.classList.remove("active");
    if (secEmail) {
      secEmail.style.display = "block";
      secEmail.classList.add("active");
    }
    if (secUser) {
      secUser.style.display = "none";
      secUser.classList.remove("active");
    }
    if (btnSubmitText) {
      btnSubmitText.innerText = "Scan Email";
    }
    if (queuedEl) {
      queuedEl.innerText = `${emailBaseFloor}+`;
    }
    if (emailModuleCatalog.length === 0) {
      fetchModuleCatalog(true);
    }
  } else {
    tabUser?.classList.add("active");
    tabEmail?.classList.remove("active");
    if (secUser) {
      secUser.style.display = "block";
      secUser.classList.add("active");
    }
    if (secEmail) {
      secEmail.style.display = "none";
      secEmail.classList.remove("active");
    }
    if (btnSubmitText) {
      btnSubmitText.innerText = "Scan Username";
    }
    if (queuedEl) {
      queuedEl.innerText = `${userBaseFloor}+`;
    }
    if (userModuleCatalog.length === 0) {
      fetchModuleCatalog(false);
    }
  }
}

// Single vs Bulk input subtabs
function setupSubtabs() {
  // Username subtabs
  const uSubSingle = document.getElementById("user-subtab-single");
  const uSubBulk = document.getElementById("user-subtab-bulk");
  const uBoxSingle = document.getElementById("user-single-target-box");
  const uBoxBulk = document.getElementById("user-bulk-target-box");
  const uBulkInput = document.getElementById("scan-user-bulk-targets");
  const uBulkFile = document.getElementById("file-user-bulk-targets");
  const uBulkCount = document.getElementById("user-bulk-count-label");
  const uPermInput = document.getElementById("scan-user-permutations");
  const uPermCount = document.getElementById("user-perm-count-label");

  if (uSubSingle && uSubBulk) {
    uSubSingle.addEventListener("click", () => {
      uSubSingle.classList.add("active");
      uSubBulk.classList.remove("active");
      if (uBoxSingle) uBoxSingle.style.display = "block";
      if (uBoxBulk) uBoxBulk.style.display = "none";
      userTargetMode = "single";
    });
    uSubBulk.addEventListener("click", () => {
      uSubBulk.classList.add("active");
      uSubSingle.classList.remove("active");
      if (uBoxSingle) uBoxSingle.style.display = "none";
      if (uBoxBulk) uBoxBulk.style.display = "block";
      userTargetMode = "bulk";
    });
  }

  if (uBulkInput && uBulkCount) {
    uBulkInput.addEventListener("input", () => {
      const lines = uBulkInput.value.split("\n").map(l => l.trim()).filter(l => l && !l.startsWith("#"));
      uBulkCount.innerText = `${lines.length} username${lines.length === 1 ? '' : 's'}`;
    });
  }

  if (uBulkFile && uBulkInput) {
    uBulkFile.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (event) => {
        uBulkInput.value = event.target.result;
        uBulkInput.dispatchEvent(new Event("input"));
      };
      reader.readAsText(file);
    });
  }

  if (uPermInput && uPermCount) {
    uPermInput.addEventListener("input", () => {
      const v = parseInt(uPermInput.value, 10) || 1;
      uPermCount.innerText = `${v} target${v > 1 ? 's' : ''}`;
    });
  }

  // Email subtabs
  const eSubSingle = document.getElementById("email-subtab-single");
  const eSubBulk = document.getElementById("email-subtab-bulk");
  const eBoxSingle = document.getElementById("email-single-target-box");
  const eBoxBulk = document.getElementById("email-bulk-target-box");
  const eBulkInput = document.getElementById("scan-email-bulk-targets");
  const eBulkFile = document.getElementById("file-email-bulk-targets");
  const eBulkCount = document.getElementById("email-bulk-count-label");

  if (eSubSingle && eSubBulk) {
    eSubSingle.addEventListener("click", () => {
      eSubSingle.classList.add("active");
      eSubBulk.classList.remove("active");
      if (eBoxSingle) eBoxSingle.style.display = "block";
      if (eBoxBulk) eBoxBulk.style.display = "none";
      emailTargetMode = "single";
    });
    eSubBulk.addEventListener("click", () => {
      eSubBulk.classList.add("active");
      eSubSingle.classList.remove("active");
      if (eBoxSingle) eBoxSingle.style.display = "none";
      if (eBoxBulk) eBoxBulk.style.display = "block";
      emailTargetMode = "bulk";
    });
  }

  if (eBulkInput && eBulkCount) {
    eBulkInput.addEventListener("input", () => {
      const lines = eBulkInput.value.split("\n").map(l => l.trim()).filter(l => l && !l.startsWith("#"));
      eBulkCount.innerText = `${lines.length} email${lines.length === 1 ? '' : 's'}`;
    });
  }

  if (eBulkFile && eBulkInput) {
    eBulkFile.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (event) => {
        eBulkInput.value = event.target.result;
        eBulkInput.dispatchEvent(new Event("input"));
      };
      reader.readAsText(file);
    });
  }
}

// Collapsible advanced options accordion
function setupAccordion() {
  const toggleBtn = document.getElementById("adv-accordion-toggle");
  const content = document.getElementById("adv-accordion-content");
  if (toggleBtn && content) {
    toggleBtn.addEventListener("click", () => {
      const isOpen = content.style.display !== "none";
      content.style.display = isOpen ? "none" : "block";
      toggleBtn.classList.toggle("open", !isOpen);
    });
  }
}

// Master toggle for advanced overrides
function setupMasterAdvancedToggle() {
  const masterToggle = document.getElementById("cfg-master-advanced-toggle");
  const advGroup = document.getElementById("adv-controls-group");
  const statusText = document.getElementById("master-toggle-status-text");

  if (!masterToggle || !advGroup) return;

  function syncMasterState() {
    const isEnabled = masterToggle.checked;
    if (isEnabled) {
      advGroup.classList.remove("adv-controls-dimmed");
      advGroup.classList.add("adv-controls-active");
      if (statusText) {
        statusText.innerHTML = `<span style="color: var(--emerald); font-weight: 600;">Active:</span> Custom parameters applied.`;
      }
    } else {
      advGroup.classList.add("adv-controls-dimmed");
      advGroup.classList.remove("adv-controls-active");
      if (statusText) {
        statusText.innerHTML = `Default mode: safe scan (skips notification triggers, excludes adult platforms, optimal concurrency).`;
      }
    }
  }

  advGroup.addEventListener("change", () => {
    if (!masterToggle.checked) {
      masterToggle.checked = true;
      syncMasterState();
    }
  });

  advGroup.addEventListener("input", () => {
    if (!masterToggle.checked) {
      masterToggle.checked = true;
      syncMasterState();
    }
  });

  masterToggle.addEventListener("change", syncMasterState);
  syncMasterState();
}

// Dynamic catalog fetching and category rendering
async function fetchModuleCatalog(isEmail = false) {
  try {
    const res = await fetch(`/api/modules?is_email=${isEmail ? 'true' : 'false'}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;

    const catalog = [];
    if (data.categories) {
      for (const [catName, mods] of Object.entries(data.categories)) {
        for (const m of mods) {
          catalog.push({
            name: m.name,
            stem: m.stem,
            category: catName,
            is_loud: m.is_loud,
            is_nsfw: m.is_nsfw
          });
        }
      }
    }

    if (isEmail) {
      emailModuleCatalog = catalog;
      emailTotalModules = data.total_modules || catalog.length;
      updateGlobalCoverageCounter();
      renderDynamicCategoryChips("email", data.categories, emailTotalModules);
      if (scanType === "email" && emailSelectedCategories.has("ALL") && emailSelectedModules.length === 0) {
        const queuedEl = document.getElementById("stat-vectors-queued");
        if (queuedEl) queuedEl.innerText = `${emailBaseFloor}+`;
      }
    } else {
      userModuleCatalog = catalog;
      userTotalModules = data.total_modules || catalog.length;
      updateGlobalCoverageCounter();
      renderDynamicCategoryChips("username", data.categories, userTotalModules);
      if (scanType === "username" && userSelectedCategories.has("ALL") && userSelectedModules.length === 0) {
        const queuedEl = document.getElementById("stat-vectors-queued");
        if (queuedEl) queuedEl.innerText = `${userBaseFloor}+`;
      }
    }
  } catch (err) {
    console.warn(`Could not load module catalog (is_email=${isEmail}):`, err);
  }
}

function syncScopeUI(type) {
  const isEmail = (type === "email");
  const modules = isEmail ? emailSelectedModules : userSelectedModules;
  const badge = document.getElementById(isEmail ? "email-modules-badge" : "user-modules-badge");
  const clearBtn = document.getElementById(isEmail ? "email-clear-modules-btn" : "user-clear-modules-btn");
  const catStatusNote = document.getElementById(isEmail ? "email-cat-status-note" : "user-cat-status-note");
  const catChipsGroup = document.getElementById(isEmail ? "email-category-chips-group" : "user-category-chips-group");
  const queuedEl = document.getElementById("stat-vectors-queued");

  if (modules.length > 0) {
    if (badge) {
      badge.innerText = `${modules.length} Selected`;
      badge.style.display = "inline-flex";
    }
    if (clearBtn) clearBtn.style.display = "inline";
    if (catStatusNote) {
      catStatusNote.innerText = `(Bypassed by ${modules.length} module${modules.length > 1 ? 's' : ''})`;
      catStatusNote.style.display = "inline";
    }
    if (catChipsGroup) {
      catChipsGroup.style.opacity = "0.45";
      catChipsGroup.querySelectorAll(".filter-chip").forEach(c => c.classList.remove("active"));
    }
    const selectedSet = isEmail ? emailSelectedCategories : userSelectedCategories;
    selectedSet.clear();

    if ((isEmail && scanType === "email") || (!isEmail && scanType === "username")) {
      if (queuedEl) queuedEl.innerText = `${modules.length}`;
    }
  } else {
    if (badge) badge.style.display = "none";
    if (clearBtn) clearBtn.style.display = "none";
    if (catStatusNote) catStatusNote.style.display = "none";
    if (catChipsGroup) {
      catChipsGroup.style.opacity = "1";
      const selectedSet = isEmail ? emailSelectedCategories : userSelectedCategories;
      if (selectedSet.size === 0) {
        selectedSet.add("ALL");
      }
      catChipsGroup.querySelectorAll(".filter-chip").forEach(c => {
        const cCat = c.getAttribute("data-cat");
        if (selectedSet.has(cCat)) {
          c.classList.add("active");
        } else {
          c.classList.remove("active");
        }
      });
    }

    if ((isEmail && scanType === "email") || (!isEmail && scanType === "username")) {
      const selectedSet = isEmail ? emailSelectedCategories : userSelectedCategories;
      let count = isEmail ? emailTotalModules : userTotalModules;
      if (!selectedSet.has("ALL") && selectedSet.size > 0) {
        const catalog = isEmail ? emailModuleCatalog : userModuleCatalog;
        const lowerCats = Array.from(selectedSet).map(s => s.toLowerCase());
        count = catalog.filter(m => lowerCats.includes((m.category || "").toLowerCase())).length;
        if (queuedEl) queuedEl.innerText = `${count}`;
      } else {
        const base = isEmail ? emailBaseFloor : userBaseFloor;
        if (queuedEl) queuedEl.innerText = `${base}+`;
      }
    }
  }
}

function renderDynamicCategoryChips(type, categoriesMap, totalCount) {
  const isEmail = (type === "email");
  const containerId = isEmail ? "email-category-chips-group" : "user-category-chips-group";
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = "";

  const allBtn = document.createElement("button");
  allBtn.type = "button";
  allBtn.className = "filter-chip active";
  allBtn.setAttribute("data-cat", "ALL");
  allBtn.innerHTML = `ALL <span class="category-chip-count">${totalCount}</span>`;
  container.appendChild(allBtn);

  const sortedCategories = Object.keys(categoriesMap || {}).sort((a, b) => a.localeCompare(b));
  for (const catName of sortedCategories) {
    const mods = categoriesMap[catName];
    const catBtn = document.createElement("button");
    catBtn.type = "button";
    catBtn.className = "filter-chip";
    catBtn.setAttribute("data-cat", catName);
    catBtn.innerHTML = `${escapeHtml(catName.toUpperCase())} <span class="category-chip-count">${mods.length}</span>`;
    container.appendChild(catBtn);
  }

  container.addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    const cat = chip.getAttribute("data-cat");
    if (!cat) return;

    // Mutually exclusive: selecting a category CLEARS specific module selection
    if (isEmail) {
      emailSelectedModules = [];
    } else {
      userSelectedModules = [];
    }
    const tagsContainer = document.getElementById(isEmail ? "email-selected-modules" : "user-selected-modules");
    if (tagsContainer) tagsContainer.innerHTML = "";

    const selectedSet = isEmail ? emailSelectedCategories : userSelectedCategories;
    const allChips = container.querySelectorAll(".filter-chip");

    if (cat === "ALL") {
      selectedSet.clear();
      selectedSet.add("ALL");
      allChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
    } else {
      selectedSet.delete("ALL");
      allChips.forEach(c => {
        if (c.getAttribute("data-cat") === "ALL") c.classList.remove("active");
      });

      if (selectedSet.has(cat)) {
        selectedSet.delete(cat);
        chip.classList.remove("active");
      } else {
        selectedSet.add(cat);
        chip.classList.add("active");
      }

      if (selectedSet.size === 0) {
        selectedSet.add("ALL");
        allChips.forEach(c => {
          if (c.getAttribute("data-cat") === "ALL") c.classList.add("active");
        });
      }
    }

    syncScopeUI(type);
  });
}

// Module search and tag selection
function setupModuleSearch() {
  setupModuleSearchSection("username");
  setupModuleSearchSection("email");
}

function setupModuleSearchSection(type) {
  const isEmail = (type === "email");
  const input = document.getElementById(isEmail ? "email-module-search-input" : "user-module-search-input");
  const suggestions = document.getElementById(isEmail ? "email-module-suggestions" : "user-module-suggestions");
  const tagsContainer = document.getElementById(isEmail ? "email-selected-modules" : "user-selected-modules");
  const clearBtn = document.getElementById(isEmail ? "email-clear-modules-btn" : "user-clear-modules-btn");

  function getSelectedList() {
    return isEmail ? emailSelectedModules : userSelectedModules;
  }
  function setSelectedList(newList) {
    if (isEmail) {
      emailSelectedModules = newList;
    } else {
      userSelectedModules = newList;
    }
  }
  function getCatalog() {
    return isEmail ? emailModuleCatalog : userModuleCatalog;
  }

  function renderTags() {
    if (!tagsContainer) return;
    tagsContainer.innerHTML = "";
    const list = getSelectedList();
    list.forEach(mod => {
      const tag = document.createElement("div");
      tag.className = "module-tag";
      tag.innerHTML = `<span>${escapeHtml(mod)}</span><span class="module-tag-del" data-mod="${escapeHtml(mod)}">&times;</span>`;
      tagsContainer.appendChild(tag);
    });
    syncScopeUI(type);
  }

  function addModuleQuery(query) {
    if (!query) return;
    const parts = query.split(/[\s,]+/).filter(Boolean);
    const list = getSelectedList();
    const catalog = getCatalog();

    parts.forEach(p => {
      const clean = p.trim().toLowerCase().replace(/^@/, "").replace(/\.py$/, "");
      if (!clean) return;
      const cleanStem = clean.includes(".") ? clean.split(".")[0] : clean;
      const matched = catalog.find(m => m.stem.toLowerCase() === cleanStem || m.name.toLowerCase() === cleanStem);
      const stemToAdd = matched ? matched.stem : cleanStem;
      if (!list.includes(stemToAdd)) {
        list.push(stemToAdd);
      }
    });

    setSelectedList(list);
    renderTags();
  }

  tagsContainer?.addEventListener("click", (e) => {
    if (e.target.classList.contains("module-tag-del")) {
      const modToRemove = e.target.getAttribute("data-mod");
      const current = getSelectedList().filter(m => m !== modToRemove);
      setSelectedList(current);
      renderTags();
    }
  });

  clearBtn?.addEventListener("click", () => {
    setSelectedList([]);
    renderTags();
  });

  if (input) {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const q = input.value.trim();
        if (q) {
          addModuleQuery(q);
          input.value = "";
          if (suggestions) suggestions.style.display = "none";
        }
      }
    });

    if (suggestions) {
      input.addEventListener("input", () => {
        const q = input.value.trim().toLowerCase();
        if (!q) {
          suggestions.style.display = "none";
          return;
        }

        const catalog = getCatalog();
        const selected = getSelectedList();
        const matches = catalog.filter(m =>
          (m.name.toLowerCase().includes(q) || m.stem.toLowerCase().includes(q)) &&
          !selected.includes(m.stem)
        ).slice(0, 15);

        if (matches.length === 0) {
          suggestions.innerHTML = `<div class="module-item" style="color: var(--text-muted); cursor: default;">No matching modules</div>`;
        } else {
          suggestions.innerHTML = matches.map(m => `
            <div class="module-item" data-stem="${escapeHtml(m.stem)}">
              <span>
                ${escapeHtml(m.name)} <span style="color: var(--text-muted); font-size: 0.65rem;">(${escapeHtml(m.stem)})</span>
                ${m.is_loud ? '<span style="color: var(--rose); font-size: 0.6rem; margin-left: 4px;">[LOUD]</span>' : ''}
              </span>
              <span class="module-item-cat">${escapeHtml(m.category)}</span>
            </div>
          `).join("");
        }
        suggestions.style.display = "block";
      });

      suggestions.addEventListener("click", (e) => {
        const item = e.target.closest(".module-item");
        if (item && item.hasAttribute("data-stem")) {
          const stem = item.getAttribute("data-stem");
          addModuleQuery(stem);
          input.value = "";
          suggestions.style.display = "none";
        }
      });

      document.addEventListener("click", (e) => {
        if (!input.contains(e.target) && !suggestions.contains(e.target)) {
          suggestions.style.display = "none";
        }
      });
    }
  }
}

// Proxy validator
function setupProxyValidator() {
  const btn = document.getElementById("btn-validate-proxies");
  const textarea = document.getElementById("cfg-proxies");
  const badge = document.getElementById("proxy-validate-badge");

  if (!btn || !textarea || !badge) return;

  btn.addEventListener("click", async () => {
    const raw = textarea.value.trim();
    if (!raw) {
      badge.style.display = "inline-block";
      badge.className = "proxy-status-pill proxy-pill-error";
      badge.innerText = "No Proxies Entered";
      setTimeout(() => { badge.style.display = "none"; }, 3000);
      return;
    }

    btn.disabled = true;
    btn.innerHTML = `<span class="status-beacon" style="background: var(--emerald);"></span> Testing...`;

    try {
      const res = await fetch("/api/proxies/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ proxies: raw, timeout: 6 })
      });
      const data = await res.json();
      badge.style.display = "inline-block";
      if (data.status === "success") {
        validatedProxies = data.working_proxies || [];
        if (data.working_count > 0) {
          badge.className = "proxy-status-pill proxy-pill-success";
          badge.innerText = `${data.working_count}/${data.total_tested} Active`;
        } else {
          badge.className = "proxy-status-pill proxy-pill-error";
          badge.innerText = `0/${data.total_tested} Working`;
        }
      } else {
        badge.className = "proxy-status-pill proxy-pill-error";
        badge.innerText = "Validation Failed";
      }
    } catch (err) {
      badge.style.display = "inline-block";
      badge.className = "proxy-status-pill proxy-pill-error";
      badge.innerText = "Error";
    } finally {
      btn.disabled = false;
      btn.innerHTML = `
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
        <span>Validate Proxies</span>
      `;
    }
  });
}

// Right inspector and analysis tabs
function setupInspectorTabs() {
  const tabBtns = document.querySelectorAll(".tab-pill");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-body").forEach(tc => tc.classList.remove("active"));
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      let targetContent = document.getElementById(targetId);
      // Support backward compatibility for tab-analytics vs tab-stylometry
      if (!targetContent && targetId === "tab-analytics") {
        targetContent = document.getElementById("tab-stylometry");
      } else if (!targetContent && targetId === "tab-stylometry") {
        targetContent = document.getElementById("tab-analytics");
      }
      if (targetContent) targetContent.classList.add("active");
    });
  });
}

// Interactive canvas toolbar
function setupCanvasControls() {
  const canvasChips = document.querySelectorAll(".canvas-top-bar .filter-chip");
  canvasChips.forEach(chip => {
    chip.addEventListener("click", () => {
      canvasChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      const cat = chip.getAttribute("data-category");
      if (typeof filterGraphByType === "function") {
        filterGraphByType(cat);
      }
    });
  });

  document.getElementById("btn-zoom-in")?.addEventListener("click", () => zoomIn());
  document.getElementById("btn-zoom-out")?.addEventListener("click", () => zoomOut());
  document.getElementById("btn-fit-graph")?.addEventListener("click", () => fitGraph());
  document.getElementById("btn-reset-layout")?.addEventListener("click", () => resetGraphView());
  document.getElementById("btn-export-png")?.addEventListener("click", () => exportGraphImage());
  document.getElementById("btn-theater-mode")?.addEventListener("click", toggleTheaterMode);

  document.getElementById("toggle-left-btn")?.addEventListener("click", toggleLeftSidebar);
  document.getElementById("toggle-right-btn")?.addEventListener("click", toggleRightSidebar);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isTheaterMode) {
      toggleTheaterMode();
    }
  });

  const searchInput = document.getElementById("canvas-search");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchNodeInGraph(e.target.value);
    });
  }

  const layoutSelect = document.getElementById("layout-select");
  if (layoutSelect) {
    layoutSelect.value = "concentric";
    layoutSelect.addEventListener("change", (e) => {
      relayoutGraph(e.target.value);
    });
  }

  window.onGraphNodeSelected = (nodeData) => {
    displayNodeDetails(nodeData);
    if (isRightCollapsed) {
      toggleRightSidebar();
    }
    document.querySelector('.tab-pill[data-tab="tab-inspector"]')?.click();
  };
}

function updateLayoutGrid() {
  const grid = document.querySelector(".dashboard-grid");
  const leftBtn = document.getElementById("toggle-left-btn");
  const rightBtn = document.getElementById("toggle-right-btn");
  const theaterBtn = document.getElementById("btn-theater-mode");

  isTheaterMode = isLeftCollapsed && isRightCollapsed;

  if (grid) {
    grid.classList.toggle("left-collapsed", isLeftCollapsed);
    grid.classList.toggle("right-collapsed", isRightCollapsed);
    grid.classList.toggle("theater-mode", isTheaterMode);
  }

  if (theaterBtn) {
    theaterBtn.classList.toggle("active", isTheaterMode);
    theaterBtn.title = isTheaterMode ? "Exit Full Screen" : "Full Screen View";
  }

  if (leftBtn) {
    leftBtn.title = isLeftCollapsed ? "Expand Panel" : "Collapse Panel";
    leftBtn.innerHTML = isLeftCollapsed
      ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>'
      : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>';
  }

  if (rightBtn) {
    rightBtn.title = isRightCollapsed ? "Expand Panel" : "Collapse Panel";
    rightBtn.innerHTML = isRightCollapsed
      ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>'
      : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>';
  }

  setTimeout(() => {
    if (typeof fitGraph === "function") fitGraph();
  }, 320);
}

function toggleTheaterMode() {
  if (isTheaterMode) {
    isLeftCollapsed = false;
    isRightCollapsed = false;
  } else {
    isLeftCollapsed = true;
    isRightCollapsed = true;
  }
  updateLayoutGrid();
}

function toggleLeftSidebar() {
  isLeftCollapsed = !isLeftCollapsed;
  updateLayoutGrid();
}

function toggleRightSidebar() {
  isRightCollapsed = !isRightCollapsed;
  updateLayoutGrid();
}

// Export button lock and validation controls
function setupExportControls() {
  const exportButtons = [
    document.getElementById("btn-pdf-export"),
    document.getElementById("btn-csv-export"),
    document.getElementById("btn-json-export")
  ];

  exportButtons.forEach(btn => {
    if (!btn) return;
    btn.addEventListener("click", (e) => {
      if (btn.classList.contains("is-locked") || isScanning || !activeCaseId) {
        e.preventDefault();
        e.stopPropagation();
        flashExportLockedWarning();
      }
    });
  });

  // Lock exports by default on initial page load
  lockExports("Scan required to export findings", false);
}

function lockExports(reason = "Scan in progress", isScanningMode = true) {
  const exportButtons = [
    document.getElementById("btn-pdf-export"),
    document.getElementById("btn-csv-export"),
    document.getElementById("btn-json-export")
  ];

  exportButtons.forEach(btn => {
    if (!btn) return;
    btn.classList.add("is-locked");
    btn.classList.remove("is-unlocked");
    btn.setAttribute("aria-disabled", "true");
    btn.removeAttribute("target");
    btn.setAttribute("href", "javascript:void(0)");
    const ind = btn.querySelector(".btn-lock-indicator");
    if (ind) {
      ind.innerText = isScanningMode ? "🔒 Scanning..." : "🔒 Locked";
    }
  });

  const statusCard = document.getElementById("export-status-card");
  const badge = document.getElementById("export-status-badge");
  const title = document.getElementById("export-status-title");
  const desc = document.getElementById("export-status-desc");

  if (statusCard) {
    statusCard.classList.remove("is-ready");
    if (isScanningMode) {
      statusCard.classList.remove("is-locked");
      statusCard.classList.add("is-scanning");
    } else {
      statusCard.classList.remove("is-scanning");
      statusCard.classList.add("is-locked");
    }
  }

  if (badge) {
    badge.innerText = isScanningMode ? "SCANNING" : "LOCKED";
    badge.className = isScanningMode ? "badge-pill export-badge-scanning" : "badge-pill export-badge-locked";
  }

  if (title) {
    title.innerText = isScanningMode ? "Scan In Progress" : "Scan Required";
  }

  if (desc) {
    desc.innerText = isScanningMode
      ? "Exports are locked while scan is actively running to prevent incomplete downloads. Scan progress is displayed in the live execution dock."
      : "Exports are locked until a scan has run. Run a username or email scan to unlock PDF reports, CSV audits, and JSON findings.";
  }
}

function unlockExports(caseId, totalHits, totalModules) {
  if (!caseId) return;

  const pdfBtn = document.getElementById("btn-pdf-export");
  const csvBtn = document.getElementById("btn-csv-export");
  const jsonBtn = document.getElementById("btn-json-export");

  [pdfBtn, csvBtn, jsonBtn].forEach(btn => {
    if (!btn) return;
    btn.classList.remove("is-locked");
    btn.classList.add("is-unlocked");
    btn.removeAttribute("aria-disabled");
    btn.setAttribute("target", "_blank");
    btn.setAttribute("rel", "noopener noreferrer");
    const ind = btn.querySelector(".btn-lock-indicator");
    if (ind) {
      ind.innerText = "✓ Ready";
    }
  });

  if (pdfBtn) pdfBtn.setAttribute("href", `/api/export/pdf/${caseId}`);
  if (csvBtn) csvBtn.setAttribute("href", `/api/export/csv/${caseId}`);
  if (jsonBtn) jsonBtn.setAttribute("href", `/api/export/json/${caseId}`);

  const statusCard = document.getElementById("export-status-card");
  const badge = document.getElementById("export-status-badge");
  const title = document.getElementById("export-status-title");
  const desc = document.getElementById("export-status-desc");

  if (statusCard) {
    statusCard.classList.remove("is-locked", "is-scanning");
    statusCard.classList.add("is-ready");
  }

  if (badge) {
    badge.innerText = "READY";
    badge.className = "badge-pill export-badge-ready";
  }

  if (title) {
    const count = totalHits !== undefined ? totalHits : telemetry.verified;
    title.innerText = `Reports Unlocked (${count} finding${count === 1 ? '' : 's'})`;
  }

  if (desc) {
    const checks = totalModules || telemetry.checked || "completed";
    desc.innerText = `Session data verified across ${checks} checks. Click any format below to download your investigative artifact.`;
  }
}

function flashExportLockedWarning() {
  const card = document.getElementById("export-status-card");
  if (card) {
    card.style.borderColor = "var(--rose)";
    card.style.transform = "scale(1.02)";
    setTimeout(() => {
      card.style.borderColor = "";
      card.style.transform = "";
    }, 400);
  }

  const msg = isScanning
    ? "Exports are locked while a scan is running. Please wait for completion or click Stop."
    : "No completed scan data to export. Please run a target scan first.";

  if (typeof showCanvasStatus === "function") {
    showCanvasStatus(`[Warning] ${msg}`);
  }
}

// Real-time scan progress dock controls
function setupProgressDock() {
  const btnStop = document.getElementById("btn-dock-stop");
  const btnExport = document.getElementById("btn-dock-export");
  const btnClose = document.getElementById("btn-dock-close");

  if (btnStop) {
    btnStop.addEventListener("click", () => {
      if (isScanning && activeScanAbortController) {
        activeScanAbortController.abort();
        stopProgressDock("Scan stopped by operator");
        if (typeof showCanvasStatus === "function") {
          showCanvasStatus("Scan stopped by operator. Preserving partial findings.");
        }
      }
    });
  }

  if (btnExport) {
    btnExport.addEventListener("click", () => {
      const exportTabPill = document.querySelector('.tab-pill[data-tab="tab-exports"]');
      if (exportTabPill) {
        exportTabPill.click();
        const exportSection = document.getElementById("tab-exports");
        if (exportSection) {
          exportSection.scrollIntoView({ behavior: "smooth" });
        }
      }
    });
  }

  if (btnClose) {
    btnClose.addEventListener("click", () => {
      const dock = document.getElementById("scan-progress-dock");
      if (dock) dock.style.display = "none";
    });
  }
}

function showProgressDock(targetLabel, totalExpected) {
  const dock = document.getElementById("scan-progress-dock");
  if (!dock) return;

  dock.style.display = "flex";
  dock.classList.remove("is-complete", "is-stopped");
  dock.classList.add("is-active");

  const beacon = document.getElementById("dock-radar-beacon");
  if (beacon) {
    beacon.className = "dock-beacon beacon-pulse";
  }

  const statusLabel = document.getElementById("dock-status-text");
  if (statusLabel) {
    statusLabel.innerText = "SCANNING DIGITAL VECTORS...";
  }

  const targetBadge = document.getElementById("dock-target-badge");
  if (targetBadge) {
    const clean = targetLabel.replace(/^@/, "");
    targetBadge.innerText = clean.includes("@") ? clean : `@${clean}`;
  }

  const countsText = document.getElementById("dock-counts-text");
  if (countsText) {
    countsText.innerText = `0 / ${totalExpected} checks`;
  }

  const remainingText = document.getElementById("dock-remaining-text");
  if (remainingText) {
    remainingText.innerText = `${totalExpected} scans left`;
  }

  const percentText = document.getElementById("dock-percent-text");
  if (percentText) {
    percentText.innerText = "0.0%";
  }

  const progressFill = document.getElementById("dock-progress-fill");
  if (progressFill) {
    progressFill.style.width = "0%";
    progressFill.style.background = "linear-gradient(90deg, #06b6d4, #10b981)";
  }

  const btnStop = document.getElementById("btn-dock-stop");
  if (btnStop) btnStop.style.display = "inline-flex";

  const btnExport = document.getElementById("btn-dock-export");
  if (btnExport) btnExport.style.display = "none";

  const btnSponsor = document.getElementById("btn-dock-sponsor");
  if (btnSponsor) btnSponsor.style.display = "none";

  const btnClose = document.getElementById("btn-dock-close");
  if (btnClose) btnClose.style.display = "none";

  // Also show telemetry card progress bar
  const telContainer = document.getElementById("telemetry-progress-container");
  if (telContainer) telContainer.style.display = "block";
  const telPct = document.getElementById("telemetry-progress-percent");
  if (telPct) telPct.innerText = `0.0% (${totalExpected} left)`;
  const telFill = document.getElementById("telemetry-progress-fill");
  if (telFill) telFill.style.width = "0%";
}

function updateProgressDock(payload) {
  const dock = document.getElementById("scan-progress-dock");
  if (!dock || dock.style.display === "none") return;

  if (payload.target) {
    const targetBadge = document.getElementById("dock-target-badge");
    if (targetBadge) {
      const clean = payload.target.replace(/^@/, "");
      targetBadge.innerText = clean.includes("@") ? clean : `@${clean}`;
    }
  }

  const checked = payload.checked || 0;
  const total = payload.total || 0;
  const remaining = payload.remaining !== undefined ? payload.remaining : Math.max(0, total - checked);
  const pctVal = typeof payload.percent === "number" ? payload.percent : (total > 0 ? (checked / total * 100) : 0);
  const pctStr = `${pctVal.toFixed(1)}%`;

  const countsText = document.getElementById("dock-counts-text");
  if (countsText) {
    countsText.innerText = `${checked} / ${total} checks`;
  }

  const remainingText = document.getElementById("dock-remaining-text");
  if (remainingText) {
    remainingText.innerText = `${remaining} scans left`;
  }

  const percentText = document.getElementById("dock-percent-text");
  if (percentText) {
    percentText.innerText = pctStr;
  }

  const progressFill = document.getElementById("dock-progress-fill");
  if (progressFill) {
    progressFill.style.width = `${Math.min(100, Math.max(0, pctVal))}%`;
  }

  // Live Telemetry progress card
  const telPct = document.getElementById("telemetry-progress-percent");
  if (telPct) telPct.innerText = `${pctStr} (${remaining} left)`;
  const telFill = document.getElementById("telemetry-progress-fill");
  if (telFill) telFill.style.width = `${Math.min(100, Math.max(0, pctVal))}%`;
}

function completeProgressDock(payload) {
  const dock = document.getElementById("scan-progress-dock");
  if (!dock) return;

  dock.classList.remove("is-active", "is-stopped");
  dock.classList.add("is-complete");

  const beacon = document.getElementById("dock-radar-beacon");
  if (beacon) {
    beacon.className = "dock-beacon beacon-complete";
  }

  const statusLabel = document.getElementById("dock-status-text");
  if (statusLabel) {
    const hits = payload.total_hits !== undefined ? payload.total_hits : telemetry.verified;
    statusLabel.innerText = `SCAN COMPLETED (${hits} VERIFIED)`;
  }

  const totalChecks = payload.total_checked || telemetry.checked;
  const countsText = document.getElementById("dock-counts-text");
  if (countsText) {
    countsText.innerText = `${totalChecks} / ${totalChecks} checks`;
  }

  const remainingText = document.getElementById("dock-remaining-text");
  if (remainingText) {
    remainingText.innerText = "0 scans left";
  }

  const percentText = document.getElementById("dock-percent-text");
  if (percentText) {
    percentText.innerText = "100.0%";
  }

  const progressFill = document.getElementById("dock-progress-fill");
  if (progressFill) {
    progressFill.style.width = "100%";
    progressFill.style.background = "linear-gradient(90deg, #10b981, #06b6d4)";
  }

  const btnStop = document.getElementById("btn-dock-stop");
  if (btnStop) btnStop.style.display = "none";

  const btnExport = document.getElementById("btn-dock-export");
  if (btnExport) btnExport.style.display = "inline-flex";

  const btnSponsor = document.getElementById("btn-dock-sponsor");
  if (btnSponsor) btnSponsor.style.display = "inline-flex";

  const btnClose = document.getElementById("btn-dock-close");
  if (btnClose) btnClose.style.display = "inline-flex";

  // Telemetry Card
  const telPct = document.getElementById("telemetry-progress-percent");
  if (telPct) telPct.innerText = "100.0% (0 left)";
  const telFill = document.getElementById("telemetry-progress-fill");
  if (telFill) telFill.style.width = "100%";
}

function stopProgressDock(reason = "Scan stopped by operator") {
  const dock = document.getElementById("scan-progress-dock");
  if (!dock) return;

  dock.classList.remove("is-active", "is-complete");
  dock.classList.add("is-stopped");

  const beacon = document.getElementById("dock-radar-beacon");
  if (beacon) {
    beacon.className = "dock-beacon beacon-stopped";
  }

  const statusLabel = document.getElementById("dock-status-text");
  if (statusLabel) {
    statusLabel.innerText = reason.toUpperCase();
  }

  const btnStop = document.getElementById("btn-dock-stop");
  if (btnStop) btnStop.style.display = "none";

  const btnExport = document.getElementById("btn-dock-export");
  if (btnExport) btnExport.style.display = "inline-flex";

  const btnSponsor = document.getElementById("btn-dock-sponsor");
  if (btnSponsor) btnSponsor.style.display = "inline-flex";

  const btnClose = document.getElementById("btn-dock-close");
  if (btnClose) btnClose.style.display = "inline-flex";

  // Telemetry Card
  const telPct = document.getElementById("telemetry-progress-percent");
  if (telPct) telPct.innerText = `STOPPED (${telemetry.checked} checks complete)`;
}

// Scan-complete sponsor alert toast controls
function setupSponsorToast() {
  const toast = document.getElementById("scan-complete-sponsor-toast");
  const closeBtn = document.getElementById("btn-close-sponsor-toast");
  const dismissBtn = document.getElementById("btn-toast-dismiss");
  const sponsorBtn = document.getElementById("btn-toast-sponsor");

  const hideToast = () => {
    if (toast) {
      toast.classList.remove("is-visible");
      setTimeout(() => {
        toast.style.display = "none";
      }, 300);
    }
  };

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      try {
        sessionStorage.setItem("us_sponsor_toast_dismissed", "true");
      } catch (e) {
        // ignore
      }
      hideToast();
    });
  }

  if (dismissBtn) {
    dismissBtn.addEventListener("click", () => {
      try {
        sessionStorage.setItem("us_sponsor_toast_dismissed", "true");
      } catch (e) {
        // ignore
      }
      hideToast();
    });
  }

  if (sponsorBtn) {
    sponsorBtn.addEventListener("click", () => {
      hideToast();
    });
  }
}

function showSponsorToast(hits = 0, totalChecked = 0) {
  try {
    if (sessionStorage.getItem("us_sponsor_toast_dismissed") === "true") {
      return;
    }
  } catch (e) {
    // ignore
  }

  const toast = document.getElementById("scan-complete-sponsor-toast");
  if (!toast) return;

  const titleEl = document.getElementById("sponsor-toast-title");
  const descEl = document.getElementById("sponsor-toast-desc");

  if (titleEl) {
    if (hits > 0) {
      titleEl.innerText = `Scan Complete — ${hits} Verified Account${hits === 1 ? "" : "s"} Found`;
    } else {
      titleEl.innerText = `Scan Complete — ${totalChecked || "Multiple"} Sites Checked`;
    }
  }

  if (descEl) {
    const totalCount = (Math.floor(userTotalModules / 5) * 5) + (Math.floor(emailTotalModules / 5) * 5);
    descEl.innerText = `user-scanner actively maintains ${totalCount}+ detection modules with regular community updates. If this scan assisted your investigation, please consider sponsoring development.`;
  }

  toast.style.display = "flex";
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      toast.classList.add("is-visible");
    });
  });
}

// Scan execution
function setupScanForm() {
  const form = document.getElementById("scan-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await executeLiveScan();
    });
  }
}

async function executeLiveScan() {
  if (isScanning) {
    console.warn("Scan already active. Ignoring duplicate invocation.");
    return;
  }

  const btn = document.getElementById("btn-run-scan");
  let targets = [];
  let stopPermutations = 1;
  let categoriesParam = "ALL";
  let modulesParam = [];

  const isEmail = (scanType === "email");

  if (isEmail) {
    if (emailTargetMode === "single") {
      const emailInput = document.getElementById("scan-email-target");
      const val = (emailInput?.value || "").trim();
      if (!val) {
        emailInput?.focus();
        return;
      }
      targets = [val];
    } else {
      const bulkInput = document.getElementById("scan-email-bulk-targets");
      const raw = (bulkInput?.value || "").trim();
      targets = raw.split("\n").map(l => l.trim()).filter(l => l && !l.startsWith("#"));
      if (targets.length === 0) {
        bulkInput?.focus();
        return;
      }
    }
    stopPermutations = 1;

    // Check if user left unsubmitted text in email module search input
    const emailModuleInput = document.getElementById("email-module-search-input");
    if (emailModuleInput && emailModuleInput.value.trim()) {
      const parts = emailModuleInput.value.trim().split(/[\s,]+/).filter(Boolean);
      parts.forEach(p => {
        const clean = p.trim().toLowerCase().replace(/^@/, "").replace(/\.py$/, "");
        const cleanStem = clean.includes(".") ? clean.split(".")[0] : clean;
        const matched = emailModuleCatalog.find(m => m.stem.toLowerCase() === cleanStem || m.name.toLowerCase() === cleanStem);
        const stemToAdd = matched ? matched.stem : cleanStem;
        if (!emailSelectedModules.includes(stemToAdd)) {
          emailSelectedModules.push(stemToAdd);
        }
      });
      emailModuleInput.value = "";
      syncScopeUI("email");
    }

    modulesParam = [...emailSelectedModules];
    categoriesParam = (modulesParam.length > 0)
      ? "ALL"
      : (emailSelectedCategories.has("ALL") ? "ALL" : Array.from(emailSelectedCategories).join(","));
  } else {
    if (userTargetMode === "single") {
      const userInput = document.getElementById("scan-user-target");
      const val = (userInput?.value || "").trim().replace(/^@/, "");
      if (!val) {
        userInput?.focus();
        return;
      }
      targets = [val];
    } else {
      const bulkInput = document.getElementById("scan-user-bulk-targets");
      const raw = (bulkInput?.value || "").trim();
      targets = raw.split("\n").map(l => l.trim().replace(/^@/, "")).filter(l => l && !l.startsWith("#"));
      if (targets.length === 0) {
        bulkInput?.focus();
        return;
      }
    }
    stopPermutations = parseInt(document.getElementById("scan-user-permutations")?.value || "1", 10);

    // Check if user left unsubmitted text in user module search input
    const userModuleInput = document.getElementById("user-module-search-input");
    if (userModuleInput && userModuleInput.value.trim()) {
      const parts = userModuleInput.value.trim().split(/[\s,]+/).filter(Boolean);
      parts.forEach(p => {
        const clean = p.trim().toLowerCase().replace(/^@/, "").replace(/\.py$/, "");
        const cleanStem = clean.includes(".") ? clean.split(".")[0] : clean;
        const matched = userModuleCatalog.find(m => m.stem.toLowerCase() === cleanStem || m.name.toLowerCase() === cleanStem);
        const stemToAdd = matched ? matched.stem : cleanStem;
        if (!userSelectedModules.includes(stemToAdd)) {
          userSelectedModules.push(stemToAdd);
        }
      });
      userModuleInput.value = "";
      syncScopeUI("username");
    }

    modulesParam = [...userSelectedModules];
    categoriesParam = (modulesParam.length > 0)
      ? "ALL"
      : (userSelectedCategories.has("ALL") ? "ALL" : Array.from(userSelectedCategories).join(","));
  }

  let expectedChecksPerTarget = 0;
  if (modulesParam.length > 0) {
    expectedChecksPerTarget = modulesParam.length;
  } else if (categoriesParam && categoriesParam !== "ALL") {
    const activeCats = categoriesParam.split(",").map(c => c.trim().toLowerCase());
    const catalog = isEmail ? emailModuleCatalog : userModuleCatalog;
    expectedChecksPerTarget = catalog.filter(m => activeCats.includes((m.category || "").toLowerCase())).length;
    if (expectedChecksPerTarget === 0) {
      expectedChecksPerTarget = isEmail ? emailTotalModules : userTotalModules;
    }
  } else {
    expectedChecksPerTarget = isEmail ? emailTotalModules : userTotalModules;
  }

  isScanning = true;
  currentScanTarget = targets[0];
  activeScanAbortController = new AbortController();

  btn.innerHTML = `<span class="status-beacon" style="background: #06b6d4;"></span> SCANNING TARGET...`;
  btn.disabled = true;

  telemetry = {
    queued: expectedChecksPerTarget * targets.length,
    checked: 0,
    verified: 0,
    pivots: 0,
    hudson: 0,
    categories: { DEV: 0, SOCIAL: 0, COMMUNITY: 0, GAMING: 0, FINANCE: 0, MUSIC: 0, TECH: 0, ADULT: 0 }
  };
  updateTelemetryUI();

  lockExports("Scan in progress...", true);
  showProgressDock(targets[0], telemetry.queued);

  const stateBadge = document.getElementById("scan-state-badge");
  if (stateBadge) {
    stateBadge.innerText = "SCANNING";
    stateBadge.style.color = "var(--cyan)";
  }

  const statHudson = document.getElementById("stat-hudson-count");
  if (statHudson) statHudson.innerText = "0";

  const targetLabel = targets.length > 1 ? `${targets.length} Targets` : (targets[0].includes("@") ? targets[0] : `@${targets[0]}`);
  const hudActor = document.getElementById("hud-actor");
  if (hudActor) hudActor.innerText = targetLabel;
  const hudVerified = document.getElementById("hud-ip");
  if (hudVerified) hudVerified.innerText = "0 Verified";
  const hudStatus = document.getElementById("hud-geo");
  if (hudStatus) hudStatus.innerText = "Scanning...";
  const hudProgress = document.getElementById("hud-conf");
  if (hudProgress) hudProgress.innerText = `0 / ${telemetry.queued || 0}`;
  const scanDateEl = document.getElementById("hud-scan-date");
  if (scanDateEl) {
    scanDateEl.innerText = new Date().toISOString().split("T")[0];
  }

  if (typeof clearNeighborhoodFocus === "function") clearNeighborhoodFocus();
  if (typeof showCanvasStatus === "function") {
    showCanvasStatus(`Initiating scan across platforms for ${targets.length} target${targets.length > 1 ? 's' : ''}...`);
  }

  const allowLoud = document.getElementById("cfg-allow-loud")?.checked || false;
  const noNsfw = document.getElementById("cfg-no-nsfw")?.checked || false;
  const showAll = document.getElementById("cfg-show-all")?.checked || false;
  const concurrency = parseInt(document.getElementById("cfg-concurrency")?.value || "0", 10);
  const timeout = parseFloat(document.getElementById("cfg-timeout")?.value || "10");
  const delay = parseFloat(document.getElementById("cfg-delay")?.value || "0");
  const proxiesRaw = document.getElementById("cfg-proxies")?.value || "";
  const proxiesList = proxiesRaw ? proxiesRaw.split("\n").map(p => p.trim()).filter(Boolean) : [];
  const crossScan = document.getElementById("cfg-cross-scan")?.checked || false;
  const crossDepth = parseInt(document.getElementById("cfg-cross-depth")?.value || "1", 10);
  const crossSweep = parseInt(document.getElementById("cfg-cross-sweep")?.value || "3", 10);
  const crossLinks = document.getElementById("cfg-cross-links")?.value || "all";
  const crossEmails = document.getElementById("cfg-cross-emails")?.value || "verified";
  const hudsonScan = document.getElementById("cfg-hudson-scan")?.checked || false;

  const requestPayload = {
    targets: targets,
    scan_type: scanType,
    categories: categoriesParam,
    modules: modulesParam,
    stop_permutations: stopPermutations,
    allow_loud: allowLoud,
    no_nsfw: noNsfw,
    show_all: showAll,
    concurrency: concurrency,
    timeout: timeout,
    delay: delay,
    proxies: proxiesList,
    cross_scan: crossScan,
    cross_depth: crossDepth,
    cross_sweep: crossSweep,
    cross_links: crossLinks,
    cross_emails: crossEmails,
    hudson_scan: hudsonScan
  };

  try {
    const res = await fetch("/api/scan/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload),
      signal: activeScanAbortController.signal
    });

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;

        try {
          const payload = JSON.parse(trimmed.slice(6));

          if (payload.event === "init") {
            activeCaseId = payload.case_id;

            const totalChecks = payload.total_checks || payload.total_modules;
            if (totalChecks) {
              telemetry.queued = totalChecks;
              const qEl = document.getElementById("stat-vectors-queued");
              if (qEl) {
                if (totalChecks >= 500) {
                  qEl.innerText = `${Math.floor(totalChecks / 5) * 5}+`;
                } else {
                  qEl.innerText = `${totalChecks}`;
                }
              }
              const hudP = document.getElementById("hud-conf");
              if (hudP) hudP.innerText = `0 / ${totalChecks}`;
              updateProgressDock({ target: currentScanTarget, checked: 0, total: totalChecks, remaining: totalChecks, percent: 0 });
            }

            if (payload.initial_elements && typeof initGraph === "function") {
              initGraph("cy", payload.initial_elements);
            }

            if (payload.initial_elements && payload.initial_elements.length > 0) {
              displayNodeDetails(payload.initial_elements[0].data);
            }

            if (typeof showCanvasStatus === "function") {
              showCanvasStatus(`Connected. Scanning targets...`);
            }
          } else if (payload.event === "error") {
            console.error("Scan engine error:", payload.message);
            stopProgressDock(`Error: ${payload.message}`);
            if (typeof showCanvasStatus === "function") {
              showCanvasStatus(`Error: ${payload.message}`);
            }
            if (stateBadge) {
              stateBadge.innerText = "ERROR";
              stateBadge.style.color = "var(--rose)";
            }
          } else if (payload.event === "progress") {
            telemetry.checked = payload.checked || telemetry.checked;
            const checksEl = document.getElementById("stat-completed-checks");
            if (checksEl) checksEl.innerText = String(telemetry.checked);
            updateProgressDock(payload);
          } else if (payload.event === "hit") {
            if (typeof addStreamingNode === "function") {
              addStreamingNode(payload);
            }

            const cat = (payload.category || (payload.node?.data?.category) || "GENERAL").toUpperCase();
            if (payload.node?.data?.type === "EMAIL" || cat === "PIVOTS") {
              telemetry.pivots++;
            } else {
              telemetry.verified++;
              if (telemetry.categories[cat] !== undefined) {
                telemetry.categories[cat]++;
              }
            }

            updateTelemetryUI();
          } else if (payload.event === "cross_round") {
            if (typeof addStreamingNode === "function") {
              addStreamingNode(payload);
            }
            telemetry.pivots++;
            if (payload.total_modules) {
              telemetry.queued = payload.total_modules;
              const qEl = document.getElementById("stat-vectors-queued");
              if (qEl) {
                if (payload.total_modules >= 500) {
                  qEl.innerText = `${Math.floor(payload.total_modules / 5) * 5}+`;
                } else {
                  qEl.innerText = `${payload.total_modules}`;
                }
              }
            }
            updateTelemetryUI();
            const targetLabel = payload.target.includes("@") ? payload.target : `@${payload.target}`;
            const hudGeo = document.getElementById("hud-geo");
            if (hudGeo) hudGeo.innerText = `Cross-Scan: ${targetLabel}`;
            const remainingChecks = Math.max(0, telemetry.queued - telemetry.checked);
            const currentPct = telemetry.queued > 0 ? (telemetry.checked / telemetry.queued * 100) : 0;
            updateProgressDock({
              target: payload.target,
              checked: telemetry.checked,
              total: telemetry.queued,
              remaining: remainingChecks,
              percent: currentPct
            });
            const dockStatus = document.getElementById("dock-status-text");
            if (dockStatus) dockStatus.innerText = `CROSS-SCAN HOP: ${targetLabel}`;
            if (typeof showCanvasStatus === "function") {
              showCanvasStatus(`[Cross-Scan Round ${payload.round}] Scanning target: ${targetLabel}`);
            }
          } else if (payload.event === "hudson") {
            renderHudsonCard(payload);
            if (payload.infected && typeof showCanvasStatus === "function") {
              showCanvasStatus(`[Hudson Rock] ${payload.total_infections} compromised credential records found for @${payload.target}`);
            }
          } else if (payload.event === "complete") {
            currentCaseData = payload.full_case;
            activeCaseId = payload.case_id;

            if (stateBadge) {
              stateBadge.innerText = "COMPLETE";
              stateBadge.style.color = "var(--emerald)";
            }

            const hudStatus = document.getElementById("hud-geo");
            if (hudStatus) hudStatus.innerText = `Complete (${payload.elapsed_seconds || 0}s)`;
            const hudProgress = document.getElementById("hud-conf");
            if (hudProgress) hudProgress.innerText = `${payload.total_checked || 0} Checked`;

            completeProgressDock(payload);
            unlockExports(payload.case_id, payload.total_hits, payload.total_checked);

            setTimeout(() => {
              showSponsorToast(payload.total_hits !== undefined ? payload.total_hits : telemetry.verified, payload.total_checked !== undefined ? payload.total_checked : telemetry.checked);
            }, 600);

            if (typeof relayoutGraph === "function") {
              setTimeout(() => {
                relayoutGraph("cose");
              }, 300);
            }

            renderAnalyticsSummary(payload.full_case);

            if (typeof showCanvasStatus === "function") {
              showCanvasStatus(`Scan completed: ${payload.total_hits || telemetry.verified} verified accounts found.`);
            }
          }
        } catch (e) {
          console.warn("Could not parse SSE payload:", e, line);
        }
      }
    }
  } catch (err) {
    if (err.name === "AbortError") {
      console.info("Scan operation aborted by operator.");
      stopProgressDock("Scan stopped by operator");
      if (activeCaseId) {
        unlockExports(activeCaseId, telemetry.verified, telemetry.checked);
      }
      if (typeof showCanvasStatus === "function") {
        showCanvasStatus("Scan stopped by operator. Partial results preserved.");
      }
    } else {
      console.error("Scan error:", err);
      stopProgressDock(`Scan error: ${err.message || err}`);
      if (activeCaseId) {
        unlockExports(activeCaseId, telemetry.verified, telemetry.checked);
      }
      if (typeof showCanvasStatus === "function") {
        showCanvasStatus(`Scan error: ${err.message || err}`);
      }
    }
  } finally {
    isScanning = false;
    activeScanAbortController = null;
    const btnText = isEmail ? "Scan Email" : "Scan Username";
    btn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="2" x2="12" y2="6"></line>
        <line x1="12" y1="18" x2="12" y2="22"></line>
        <line x1="2" y1="12" x2="6" y2="12"></line>
        <line x1="18" y1="12" x2="22" y2="12"></line>
      </svg>
      <span id="btn-run-scan-text">${btnText}</span>
    `;
    btn.disabled = false;
  }
}

// Hudson Rock compromised device card rendering
function renderHudsonCard(data) {
  const container = document.getElementById("hudson-results-container");
  const badgeStatus = document.getElementById("hudson-badge-status");
  const statHudson = document.getElementById("stat-hudson-count");
  if (!container) return;

  if (container.querySelector(".stealer-card") === null) {
    container.innerHTML = "";
  }

  if (!data.infected || !data.stealers || data.stealers.length === 0) {
    if (badgeStatus) {
      badgeStatus.innerText = "CLEAN";
      badgeStatus.style.background = "rgba(16, 185, 129, 0.2)";
      badgeStatus.style.color = "var(--emerald)";
    }
    const cleanBox = document.createElement("div");
    cleanBox.style.cssText = "background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 6px; padding: 12px; text-align: center; margin-bottom: 8px;";
    cleanBox.innerHTML = `
      <div style="color: var(--emerald); font-weight: 700; font-size: 0.78rem; margin-bottom: 2px;">NO INFECTIONS FOUND</div>
      <div style="color: var(--text-secondary); font-size: 0.68rem;">Target @${escapeHtml(data.target)} has no known infostealer malware logs.</div>
    `;
    container.appendChild(cleanBox);
    return;
  }

  if (badgeStatus) {
    badgeStatus.innerText = `${data.total_infections} INFECTIONS`;
    badgeStatus.style.background = "rgba(244, 63, 94, 0.2)";
    badgeStatus.style.color = "var(--rose)";
  }

  if (statHudson) {
    const cur = parseInt(statHudson.innerText || "0", 10);
    statHudson.innerText = String(cur + data.total_infections);
  }

  data.stealers.forEach(s => {
    const card = document.createElement("div");
    card.className = "stealer-card";
    const dateComp = s.date_compromised ? s.date_compromised.split("T")[0] : "Unknown";
    card.innerHTML = `
      <div class="stealer-header">
        <span class="stealer-computer-name">${escapeHtml(s.computer_name || 'Infected System')}</span>
        <span class="stealer-badge">${escapeHtml(s.stealer_family || 'Infostealer')}</span>
      </div>
      <div class="stealer-meta-grid">
        <div class="stealer-meta-item">OS: <strong>${escapeHtml(s.operating_system || 'Windows')}</strong></div>
        <div class="stealer-meta-item">Compromised: <strong>${escapeHtml(dateComp)}</strong></div>
        <div class="stealer-meta-item">IP: <strong>${escapeHtml(s.ip || 'Redacted')}</strong></div>
        <div class="stealer-meta-item">Credentials: <strong>${escapeHtml(String(s.total_passwords || 0))} Stolen</strong></div>
      </div>
      ${s.corporate_emails && s.corporate_emails.length > 0 ? `
        <div style="margin-top: 8px; font-size: 0.68rem; color: #fb7185;">
          Corporate Exposures: ${s.corporate_emails.map(e => escapeHtml(e)).join(", ")}
        </div>
      ` : ''}
    `;
    container.appendChild(card);
  });
}

// Telemetry counters
function updateTelemetryUI() {
  const verifiedEl = document.getElementById("stat-verified-count");
  if (verifiedEl) verifiedEl.innerText = String(telemetry.verified);

  const pivotsEl = document.getElementById("stat-pivots-count");
  if (pivotsEl) pivotsEl.innerText = String(telemetry.pivots);

  const checksEl = document.getElementById("stat-completed-checks");
  if (checksEl) checksEl.innerText = String(telemetry.checked);

  const hudVerified = document.getElementById("hud-ip");
  if (hudVerified) hudVerified.innerText = `${telemetry.verified} Verified`;

  const hudProgress = document.getElementById("hud-conf");
  if (hudProgress) hudProgress.innerText = `${telemetry.checked} / ${telemetry.queued || telemetry.checked}`;

  document.getElementById("cat-count-dev") && (document.getElementById("cat-count-dev").innerText = String(telemetry.categories.DEV || 0));
  document.getElementById("cat-count-social") && (document.getElementById("cat-count-social").innerText = String(telemetry.categories.SOCIAL || 0));
  document.getElementById("cat-count-community") && (document.getElementById("cat-count-community").innerText = String(telemetry.categories.COMMUNITY || 0));
  document.getElementById("cat-count-gaming") && (document.getElementById("cat-count-gaming").innerText = String(telemetry.categories.GAMING || 0));
  document.getElementById("cat-count-finance") && (document.getElementById("cat-count-finance").innerText = String(telemetry.categories.FINANCE || 0));
}

// Analytics summary
function renderAnalyticsSummary(caseData) {
  const narrative = document.getElementById("footprint-summary");
  if (!narrative) return;

  const cats = caseData?.category_counts || telemetry.categories;
  const total = Object.values(cats).reduce((a, b) => a + b, 0) || 1;

  const topCats = Object.entries(cats)
    .filter(([k, v]) => v > 0)
    .sort((a, b) => b[1] - a[1]);

  if (topCats.length === 0) {
    narrative.innerText = `Scan for @${currentScanTarget} completed across ${telemetry.checked} platforms. No verified accounts were identified.`;
    return;
  }

  const breakdownText = topCats
    .map(([cat, count]) => `${cat} (${Math.round((count / total) * 100)}%)`)
    .join(", ");

  narrative.innerHTML = `
    <strong>Scan Summary:</strong><br>
    Identified ${telemetry.verified} verified accounts across ${telemetry.checked} scanned services.
    Dominant categories: <strong>${breakdownText}</strong>.
    ${telemetry.pivots > 0 ? `Extracted ${telemetry.pivots} linked identifier${telemetry.pivots === 1 ? '' : 's'}.` : ''}
  `;
}

// Entity details in inspector
function displayNodeDetails(data) {
  const inspector = document.getElementById("node-inspector-content");
  if (!inspector) return;

  const nodeType = (data.type || "UNKNOWN").toUpperCase();
  const meta = data.metadata || {};
  const avatarUrl = data.avatar_url || meta.avatar_url || null;

  if (nodeType === "THREAT_ACTOR" || nodeType === "TARGET") {
    const handle = meta.target || meta.target_handle || data.label.replace("Target: @", "").replace("Email: @", "");
    inspector.innerHTML = `
      <div class="profile-hero-card">
        <div class="profile-hero-top">
          <div class="profile-avatar-wrap">
            <div class="profile-avatar-fallback" style="background: rgba(239, 68, 68, 0.2); color: #f43f5e;">@</div>
            <span class="avatar-status-pip" style="background: #f43f5e;" title="Target"></span>
          </div>
          <div class="profile-hero-info">
            <div class="profile-platform-title">Target Entity</div>
            <div class="profile-handle-sub">${handle.includes("@") ? escapeHtml(handle) : `@${escapeHtml(handle)}`}</div>
            <div class="profile-badge-row">
              <span class="badge-pill" style="background: rgba(239, 68, 68, 0.15); color: #f43f5e; border: 1px solid rgba(239, 68, 68, 0.35);">ROOT TARGET</span>
              <span class="badge-pill badge-cyan">${telemetry.verified} Verified Accounts</span>
            </div>
          </div>
        </div>
      </div>

      <div class="inspector-section-label">Summary</div>
      <div class="forensic-meta-grid">
        <div class="meta-tile">
          <div class="meta-tile-lbl">Platforms Scanned</div>
          <div class="meta-tile-val highlight">${telemetry.checked}</div>
        </div>
        <div class="meta-tile">
          <div class="meta-tile-lbl">Accounts Found</div>
          <div class="meta-tile-val emerald">${telemetry.verified}</div>
        </div>
        <div class="meta-tile">
          <div class="meta-tile-lbl">Linked Identifiers</div>
          <div class="meta-tile-val" style="color: #ec4899;">${telemetry.pivots}</div>
        </div>
        <div class="meta-tile">
          <div class="meta-tile-lbl">Scan Date</div>
          <div class="meta-tile-val">${meta.first_seen || new Date().toISOString().split("T")[0]}</div>
        </div>
      </div>
    `;
    return;
  }

  if (nodeType === "EMAIL") {
    const emailVal = meta.email || data.label;
    inspector.innerHTML = `
      <div class="profile-hero-card">
        <div class="profile-hero-top">
          <div class="profile-avatar-wrap">
            <div class="profile-avatar-fallback" style="background: rgba(236, 72, 153, 0.2); color: #ec4899;">✉</div>
            <span class="avatar-status-pip" style="background: #ec4899;" title="Discovered Email"></span>
          </div>
          <div class="profile-hero-info">
            <div class="profile-platform-title">Discovered Email</div>
            <div class="profile-handle-sub" style="color: #f472b6;">${escapeHtml(emailVal)}</div>
            <div class="profile-badge-row">
              <span class="badge-pill" style="background: rgba(236, 72, 153, 0.15); color: #f472b6; border: 1px solid rgba(236, 72, 153, 0.35);">LINKED EMAIL</span>
            </div>
          </div>
        </div>
      </div>

      <div class="inspector-section-label">Email Address</div>
      <div class="pivot-chip">
        <div class="pivot-chip-left" style="color: #f472b6;">${escapeHtml(emailVal)}</div>
        <button class="btn-copy-chip" onclick="copyTextToClipboard('${escapeHtml(emailVal)}', this)">Copy</button>
      </div>

      ${meta.source ? `
        <div class="detail-item" style="margin-top: 12px;">
          <div class="detail-lbl">Evidence Source</div>
          <div class="detail-box">${escapeHtml(meta.source)}</div>
        </div>
      ` : ''}

      <div style="margin-top: 16px;">
        <button class="btn-cyber btn-glow-cyan" style="width: 100%; padding: 8px 12px;" onclick="pivotToNewScan('${escapeHtml(emailVal)}')">
          Scan This Email ➔
        </button>
      </div>
    `;
    return;
  }

  const platform = meta.platform || data.label;
  const rawHandle = meta.username || meta.handle || meta.name || currentScanTarget;
  const profileUrl = meta.url || data.url || "";
  const bio = meta.bio || meta.headline || data.bio || "";
  const category = meta.category || data.category || "OSINT";
  const platformLetter = platform.charAt(0).toUpperCase();

  let emails = [];
  if (meta.linked_emails && Array.isArray(meta.linked_emails)) {
    emails = emails.concat(meta.linked_emails);
  }
  if (meta.email && !emails.includes(meta.email)) {
    emails.push(meta.email);
  }

  let links = [];
  if (meta.links) {
    if (typeof meta.links === "string") {
      links = meta.links.split(",").map(l => l.trim()).filter(Boolean);
    } else if (Array.isArray(meta.links)) {
      links = meta.links;
    }
  }

  const knownKeys = [
    "platform", "url", "category", "status", "avatar_url", "bio", "headline",
    "linked_emails", "email", "linked_handles", "links"
  ];

  const telemetryItems = [];
  if (meta.name || meta.fullname || meta.display_name) {
    telemetryItems.push({ label: "Full Name", val: meta.name || meta.fullname || meta.display_name, highlight: true });
    knownKeys.push("name", "fullname", "display_name");
  }
  if (meta.followers !== undefined) {
    telemetryItems.push({ label: "Followers", val: meta.followers, highlight: true });
    knownKeys.push("followers");
  }
  if (meta.following !== undefined) {
    telemetryItems.push({ label: "Following", val: meta.following });
    knownKeys.push("following");
  }
  if (meta.public_repos !== undefined) {
    telemetryItems.push({ label: "Public Repos", val: meta.public_repos, highlight: true });
    knownKeys.push("public_repos");
  }
  if (meta.created_at || meta.joined || meta.created) {
    const d = meta.created_at || meta.joined || meta.created;
    telemetryItems.push({ label: "Member Since", val: String(d).includes("T") ? String(d).split("T")[0] : String(d) });
    knownKeys.push("created_at", "joined", "created");
  }
  if (meta.location) {
    telemetryItems.push({ label: "Location", val: meta.location });
    knownKeys.push("location");
  }

  const extraMeta = [];
  for (const [k, v] of Object.entries(meta)) {
    if (!knownKeys.includes(k) && v !== null && v !== undefined && v !== "") {
      extraMeta.push({ key: k, val: typeof v === "object" ? JSON.stringify(v) : String(v) });
    }
  }

  inspector.innerHTML = `
    <div class="profile-hero-card">
      <div class="profile-hero-top">
        <div class="profile-avatar-wrap">
          ${avatarUrl ? `
            <img src="${escapeHtml(avatarUrl)}" class="profile-avatar-img" alt="Avatar"
              onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\'profile-avatar-fallback\\'>${platformLetter}</div>';" />
            <span class="avatar-status-pip" title="Active Verified Account"></span>
          ` : `
            <div class="profile-avatar-fallback">${platformLetter}</div>
          `}
        </div>
        <div class="profile-hero-info">
          <div class="profile-platform-title">${escapeHtml(platform)}</div>
          <div class="profile-handle-sub">@${escapeHtml(rawHandle)}</div>
          <div class="profile-badge-row">
            <span class="badge-pill badge-emerald">VERIFIED ACCOUNT</span>
            <span class="badge-pill badge-cyan">${escapeHtml(category)}</span>
          </div>
        </div>
      </div>

      ${profileUrl ? `
        <a href="${escapeHtml(profileUrl)}" target="_blank" rel="noopener noreferrer" class="btn-profile-link">
          <span>Open Profile</span>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
        </a>
      ` : ''}
    </div>

    ${meta.confidence ? `
      <div class="inspector-section-label">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 14 14"></polyline></svg>
        Cross-Scan Correlation
      </div>
      <div class="profile-bio-box" style="display: flex; align-items: center; gap: 8px;">
        <span class="badge-pill ${String(meta.confidence).toLowerCase() === 'confirmed' ? 'badge-emerald' : String(meta.confidence).toLowerCase() === 'likely' ? 'badge-cyan' : 'badge-amber'}" style="font-weight: 700; text-transform: uppercase;">${escapeHtml(String(meta.confidence))}</span>
        <span style="font-size: 0.72rem; color: var(--text-secondary);">
          ${String(meta.confidence).toLowerCase() === 'confirmed' ? 'Direct anchor match (explicitly named in bio or links)' :
            String(meta.confidence).toLowerCase() === 'likely' ? 'Metadata matches primary target footprint' :
            String(meta.confidence).toLowerCase() === 'conflicting' ? 'Metadata points to a different entity' :
            'Candidate handle registered across platform'}
        </span>
      </div>
    ` : ''}

    ${bio ? `
      <div class="inspector-section-label">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        Profile Bio
      </div>
      <div class="profile-bio-box">${escapeHtml(bio)}</div>
    ` : ''}

    ${emails.length > 0 ? `
      <div class="inspector-section-label">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
        Linked Email Addresses (${emails.length})
      </div>
      <div class="pivot-chip-group">
        ${emails.map(em => `
          <div class="pivot-chip">
            <div class="pivot-chip-left">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
              <span style="color: #34d399;">${escapeHtml(em)}</span>
            </div>
            <button class="btn-copy-chip" onclick="copyTextToClipboard('${escapeHtml(em)}', this)">Copy</button>
          </div>
        `).join('')}
      </div>
    ` : ''}

    ${links.length > 0 ? `
      <div class="inspector-section-label">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
        Associated External Links
      </div>
      <div class="pivot-chip-group">
        ${links.map(lk => `
          <div class="pivot-chip">
            <div class="pivot-chip-left">
              <a href="${escapeHtml(lk)}" target="_blank" rel="noopener noreferrer" style="color: #38bdf8; text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                ${escapeHtml(lk)}
              </a>
            </div>
            <button class="btn-copy-chip" onclick="copyTextToClipboard('${escapeHtml(lk)}', this)">Copy</button>
          </div>
        `).join('')}
      </div>
    ` : ''}

    ${telemetryItems.length > 0 ? `
      <div class="inspector-section-label">Platform Metadata</div>
      <div class="forensic-meta-grid">
        ${telemetryItems.map(item => `
          <div class="meta-tile">
            <div class="meta-tile-lbl">${escapeHtml(item.label)}</div>
            <div class="meta-tile-val ${item.highlight ? 'highlight' : ''}">${escapeHtml(String(item.val))}</div>
          </div>
        `).join('')}
      </div>
    ` : ''}

    ${extraMeta.length > 0 ? `
      <div class="inspector-section-label">Additional Attributes</div>
      <div class="forensic-meta-grid">
        ${extraMeta.map(item => `
          <div class="meta-tile full-width">
            <div class="meta-tile-lbl">${escapeHtml(item.key)}</div>
            <div class="meta-tile-val">${escapeHtml(item.val)}</div>
          </div>
        `).join('')}
      </div>
    ` : ''}
  `;
}

// 1-Click pivot helper
function pivotToNewScan(newTarget) {
  if (!newTarget) return;
  const isEmailTarget = newTarget.includes("@");

  if (isEmailTarget) {
    switchPrimaryScanTab("email");
    const subSingle = document.getElementById("email-subtab-single");
    if (subSingle) subSingle.click();
    const emailInput = document.getElementById("scan-email-target");
    if (emailInput) emailInput.value = newTarget;
  } else {
    switchPrimaryScanTab("username");
    const subSingle = document.getElementById("user-subtab-single");
    if (subSingle) subSingle.click();
    const userInput = document.getElementById("scan-user-target");
    if (userInput) userInput.value = newTarget;
  }

  executeLiveScan();
}

function copyTextToClipboard(text, btnEl) {
  if (!navigator.clipboard) {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  } else {
    navigator.clipboard.writeText(text);
  }
  if (btnEl) {
    const originalText = btnEl.innerHTML;
    btnEl.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
    setTimeout(() => {
      btnEl.innerHTML = originalText;
    }, 1500);
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
