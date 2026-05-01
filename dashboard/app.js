/* ──────────────────────────────────────────────────
   Tessera AI Indexer — Dashboard Application
   ────────────────────────────────────────────────── */

/* ── SVG Icon Library ── */
const ICONS = {
  paperclip: `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.5L12.5 21a5.5 5.5 0 0 1-7.8-7.8l9-9a3.7 3.7 0 0 1 5.2 5.2l-9 9a1.9 1.9 0 1 1-2.6-2.6l8-8"/></svg>`,
  check: `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5L20 7"/></svg>`,
  checkLg: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5L20 7"/></svg>`,
  sparkle: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4l1.6 4.4L18 10l-4.4 1.6L12 16l-1.6-4.4L6 10l4.4-1.6L12 4z"/><path d="M19 16l.7 1.8L21.5 18.5l-1.8.7L19 21l-.7-1.8-1.8-.7 1.8-.7L19 16z"/></svg>`,
  sparkleSm: `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4l1.6 4.4L18 10l-4.4 1.6L12 16l-1.6-4.4L6 10l4.4-1.6L12 4z"/><path d="M19 16l.7 1.8L21.5 18.5l-1.8.7L19 21l-.7-1.8-1.8-.7 1.8-.7L19 16z"/></svg>`,
  chevronDown: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>`,
  flag: `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4"/><path d="M5 4h12l-2 4 2 4H5"/></svg>`,
  flagLg: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4"/><path d="M5 4h12l-2 4 2 4H5"/></svg>`,
  dot: `<svg width="10" height="10" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>`,
  eye: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>`,
  doc: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/></svg>`,
  docLg: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/></svg>`,
  arrowRight: `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg>`,
  shield: `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/></svg>`,
  bolt: `<svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M13 3L4 14h7l-1 7 9-11h-7l1-7z"/></svg>`,
};

/* ── State ── */
const state = {
  inbox: [],
  queueGroups: [],
  queueState: {},
  processed: new Set(),
  selectedMailId: null,
  search: "",
  processing: false,
  collapsedQueues: new Set(),
};

const $ = (id) => document.getElementById(id);

/* ── Helpers ── */
const toneForConfidence = (c) => c >= 95 ? "green" : c >= 85 ? "blue" : c >= 75 ? "amber" : "red";
const toneColor = (c) => c >= 95 ? "var(--green)" : c >= 85 ? "var(--accent)" : c >= 75 ? "var(--amber)" : "var(--red)";
const initials = (name) => name.split(/\s+/).slice(0, 2).map((p) => p[0]).join("").toUpperCase();
const avatarHue = (name) => (name.charCodeAt(0) * 7) % 360;

const avatarStyle = (name) => {
  const h = avatarHue(name);
  return `background: oklch(92% 0.04 ${h}); color: oklch(38% 0.13 ${h}); border: 0.5px solid oklch(85% 0.04 ${h});`;
};

const escapeHtml = (v = "") => String(v)
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;").replaceAll("'", "&#039;");

/* ── API ── */
async function requestJson(path, options) {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

/* ── State Application ── */
function applyServerState(payload) {
  state.inbox = payload.inbox;
  state.queueGroups = payload.queueGroups;
  state.queueState = payload.queueState;
  state.processed = new Set(payload.processed);
  if (!state.selectedMailId && payload.inbox.length) state.selectedMailId = payload.inbox[0].id;
  renderSovereignty(payload.sovereignty);
  render();
}

function selectedMail() {
  return state.inbox.find((m) => m.id === state.selectedMailId) || null;
}

function selectedQueueItemId() {
  const mail = selectedMail();
  if (!mail) return null;
  const g = state.queueGroups.find((c) => c.name === mail.routedTo.queue);
  if (!g || !(state.queueState[g.name] || []).includes(mail.id)) return null;
  const item = g.items.find((c) => c.source === mail.id);
  return item ? item.id : null;
}

/* ── Sovereignty Stats ── */
function renderSovereignty(stats) {
  $("stat-processed").textContent = stats.mailsProcessedToday.toLocaleString();
  $("stat-api").textContent = stats.externalApiCallsToday.toLocaleString();
  $("stat-egress").textContent = stats.customerDataEgress;
  $("stat-latency").textContent = `${stats.averageInferenceLatencyMs}ms`;
}

/* ── Master Render ── */
function render() { renderInbox(); renderQueues(); renderDetail(); }

/* ── Inbox ── */
function renderInbox() {
  const filtered = state.inbox.filter((m) => {
    const hay = `${m.fromName} ${m.subject} ${m.preview} ${m.classification.client}`.toLowerCase();
    return hay.includes(state.search.toLowerCase());
  });
  const pending = state.inbox.length - state.processed.size;

  $("mail-count").textContent = state.inbox.length;
  $("pending-count").textContent = pending;
  $("routed-count").textContent = state.processed.size;

  const btn = $("process-all");
  btn.disabled = state.processing || pending === 0;
  btn.innerHTML = state.processing
    ? `<span class="spinner"></span> Processing…`
    : pending === 0
      ? `${ICONS.checkLg} All routed`
      : `${ICONS.sparkle} Process all (${pending})`;

  $("inbox-list").innerHTML = filtered.map((mail) => {
    const done = state.processed.has(mail.id);
    const sel = state.selectedMailId === mail.id;
    return `
      <button class="mail-row${sel ? " selected" : ""}" type="button" data-mail-id="${escapeHtml(mail.id)}">
        ${done ? "" : '<span class="unread-dot"></span>'}
        <span class="mail-line">
          <span class="avatar" style="${avatarStyle(mail.fromName)}">${escapeHtml(initials(mail.fromName))}</span>
          <span class="mail-copy">
            <span class="mail-meta">
              <span class="mail-name">${escapeHtml(mail.fromName)}</span>
              <span class="mail-time mono">${escapeHtml(mail.received)}</span>
            </span>
            <span class="mail-subject">${escapeHtml(mail.subject)}</span>
            <span class="mail-preview">${escapeHtml(mail.preview)}</span>
            <span class="mail-tags">
              <span class="attachment mono">${ICONS.paperclip} ${escapeHtml(mail.attachments[0].name)}</span>
              ${done ? `<span class="pill green" style="margin-left:auto;">${ICONS.check} routed</span>` : ""}
            </span>
          </span>
        </span>
      </button>`;
  }).join("");

  document.querySelectorAll(".mail-row").forEach((row) => {
    row.addEventListener("click", () => { state.selectedMailId = row.dataset.mailId; render(); });
  });
}

/* ── Work Queues ── */
function renderQueues() {
  const selId = selectedQueueItemId();
  const total = Object.values(state.queueState).reduce((s, ids) => s + ids.length, 0);
  const reviewCount = state.inbox.filter((m) => m.classification.status === "needs-review" && state.processed.has(m.id)).length;

  $("queue-count").textContent = total;
  $("queue-footer-total").textContent = `${total} · ${reviewCount} needs review`;

  $("queue-list").innerHTML = state.queueGroups.map((group) => {
    const ids = state.queueState[group.name] || [];
    const items = ids.map((sid) => group.items.find((i) => i.source === sid)).filter(Boolean);
    const collapsed = state.collapsedQueues.has(group.name);

    const itemsHtml = items.length
      ? items.map((item) => `
          <button class="queue-item${selId === item.id ? " selected" : ""}" type="button" data-source-id="${escapeHtml(item.source)}">
            <span class="queue-branch mono">└─</span>
            <span class="queue-item-label">${escapeHtml(item.label)}</span>
            ${item.note ? `<span class="pill amber">${ICONS.flag} NOTE</span>` : ""}
          </button>`).join("")
      : '<div class="queue-empty">Empty — process inbox to populate</div>';

    return `
      <div class="queue-group">
        <button class="queue-group-header" type="button" data-queue-name="${escapeHtml(group.name)}">
          <span class="queue-chevron${collapsed ? " collapsed" : ""}">${ICONS.chevronDown}</span>
          <span class="queue-color" style="background:${escapeHtml(group.color)}"></span>
          <span class="queue-name">${escapeHtml(group.name)}</span>
          <span class="queue-group-count counter">${items.length}</span>
        </button>
        <div class="queue-items${collapsed ? " hidden" : ""}">${itemsHtml}</div>
      </div>`;
  }).join("");

  document.querySelectorAll(".queue-group-header").forEach((hdr) => {
    hdr.addEventListener("click", () => {
      const name = hdr.dataset.queueName;
      if (state.collapsedQueues.has(name)) state.collapsedQueues.delete(name);
      else state.collapsedQueues.add(name);
      renderQueues();
    });
  });

  document.querySelectorAll(".queue-item").forEach((item) => {
    item.addEventListener("click", () => { state.selectedMailId = item.dataset.sourceId; render(); });
  });
}

/* ── Detail View ── */
function renderDetail() {
  const mail = selectedMail();
  const badges = $("detail-badges");
  const detail = $("detail-view");

  if (!mail) {
    badges.innerHTML = "";
    detail.innerHTML = `
      <div class="empty-detail">
        <div class="empty-detail-icon">${ICONS.docLg}</div>
        <strong>Select an item</strong>
        <p>Pick an email from the mailbox or a routed task from a queue to inspect its body, attachment and classification.</p>
      </div>`;
    return;
  }

  const c = mail.classification;
  const att = mail.attachments[0];
  const tone = toneForConfidence(c.confidence);
  const fillColor = toneColor(c.confidence);

  badges.innerHTML = `
    <span class="pill ${tone}">${ICONS.sparkleSm} AI classified</span>
    ${c.status === "needs-review" ? `<span class="pill amber">${ICONS.flag} NOTE</span>` : ""}`;

  const pageChips = Array.from({ length: Math.min(att.pages, 5) }, (_, i) =>
    `<span>p.${i + 1}</span>`).join("") + (att.pages > 5 ? `<span>+${att.pages - 5}</span>` : "");

  detail.innerHTML = `
    <article class="detail-card">
      <div class="detail-sender">
        <span class="avatar" style="${avatarStyle(mail.fromName)}">${escapeHtml(initials(mail.fromName))}</span>
        <div class="detail-sender-copy">
          <div class="detail-sender-top">
            <strong>${escapeHtml(mail.fromName)}</strong>
            <span class="detail-time mono">today · ${escapeHtml(mail.received)}</span>
          </div>
          <div class="detail-from mono">${escapeHtml(mail.from)}</div>
        </div>
      </div>
      <h1 class="detail-title">${escapeHtml(mail.subject)}</h1>
      <pre class="body-text">${escapeHtml(mail.body)}</pre>
    </article>

    <section class="detail-section">
      <div class="section-title">
        <h3>Attachment</h3>
        <span class="mono muted">1 file</span>
      </div>
      <div class="pdf-preview">
        <div class="pdf-page" aria-hidden="true">
          <div class="pdf-line title"></div>
          <div class="pdf-line" style="width:100%"></div>
          <div class="pdf-line" style="width:92%"></div>
          <div class="pdf-line" style="width:60%"></div>
          <div class="pdf-line" style="width:100%; margin-top:8px;"></div>
          <div class="pdf-line" style="width:88%"></div>
          <div class="pdf-line" style="width:100%"></div>
          <div class="pdf-signature"></div>
          <span class="pdf-page-num mono">p.1</span>
        </div>
        <div class="pdf-copy">
          <div>
            <div class="pdf-name mono">${escapeHtml(att.name)}</div>
            <div class="pdf-meta">${att.pages} pages · ${escapeHtml(att.size)} · PDF</div>
            <div class="page-chips mono">${pageChips}</div>
          </div>
          <div class="action-bar" style="justify-content:flex-start; padding:10px 0 0;">
            <button class="dark-action" type="button">${ICONS.eye} View PDF</button>
            <button class="ghost-action" type="button">${ICONS.doc} Open email</button>
          </div>
        </div>
      </div>
    </section>

    <div class="detail-grid">
      <section class="detail-section">
        <div class="section-title">
          <h3>Classification</h3>
          <div class="confidence">
            <span class="confidence-track"><span class="confidence-fill" style="width:${c.confidence}%; background:${fillColor}"></span></span>
            <span class="mono" style="font-size:12px; font-weight:600; font-variant-numeric:tabular-nums;">${c.confidence}%</span>
          </div>
        </div>
        ${kv("Type", `<span class="pill ${tone}">${ICONS.dot} ${escapeHtml(c.type)}</span>`)}
        ${kv("Tier", escapeHtml(c.tier), true)}
        ${kv("Status", `<span class="pill ${c.status === "pending" ? "neutral" : "amber"}">${c.status === "pending" ? ICONS.dot : ICONS.flag} ${escapeHtml(c.status)}</span>`)}
        ${kv("Routed to", `<span class="muted">queue</span> ${ICONS.arrowRight} <strong>${escapeHtml(mail.routedTo.queue)}</strong>`)}
        ${c.note ? `<div class="note">${ICONS.flagLg}<span><b>Indexer note:</b> ${escapeHtml(c.note)}</span></div>` : ""}
      </section>

      <section class="detail-section">
        <div class="section-title">
          <h3>Record</h3>
          <span class="pill green">${ICONS.shield} on-prem</span>
        </div>
        ${kv("Policy", escapeHtml(c.policy), true)}
        ${kv("Client", escapeHtml(c.client))}
        ${kv("Pages", escapeHtml(c.pages))}
        ${kv("Source", escapeHtml(mail.id), true)}
      </section>
    </div>

    <div class="action-bar">
      <button class="ghost-action" type="button">Reassign queue</button>
      <button class="ghost-action" type="button">Flag for review</button>
      <button class="dark-action" type="button">${ICONS.checkLg} Approve & finalize</button>
    </div>`;
}

function kv(label, value, mono = false) {
  return `<div class="kv"><div class="kv-label">${escapeHtml(label)}</div><div class="kv-value${mono ? " mono" : ""}">${value}</div></div>`;
}

/* ── Process All (staggered animation) ── */
async function processAll() {
  if (state.processing) return;
  state.processing = true;
  renderInbox();
  try {
    const payload = await requestJson("/api/process-all", { method: "POST" });
    // Animate items appearing one by one
    const newProcessed = payload.processed.filter((id) => !state.processed.has(id));
    state.queueGroups = payload.queueGroups;

    for (const id of newProcessed) {
      await new Promise((r) => setTimeout(r, 380));
      state.processed.add(id);
      // Update queue state incrementally
      const mail = state.inbox.find((m) => m.id === id);
      if (mail) {
        const q = mail.routedTo.queue;
        if (!state.queueState[q]) state.queueState[q] = [];
        if (!state.queueState[q].includes(id)) state.queueState[q].push(id);
      }
      render();
    }
    renderSovereignty(payload.sovereignty);
  } finally {
    state.processing = false;
    renderInbox();
  }
}

/* ── Generate Batch ── */
async function generateBatch() {
  const btn = $("generate-batch");
  btn.disabled = true;
  btn.textContent = "Generating…";
  try {
    const payload = await requestJson("/api/generate-batch", {
      method: "POST",
      body: JSON.stringify({ count: 10 }),
    });
    state.selectedMailId = null;
    state.collapsedQueues.clear();
    applyServerState(payload);
  } finally {
    btn.disabled = false;
    btn.textContent = "Generate batch (10)";
  }
}

/* ── Keyboard Shortcuts ── */
function setupKeyboard() {
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      $("mail-search").focus();
    }
  });
}

/* ── Live Updates ── */
async function pollState() {
  if (state.processing) return; // Don't interrupt processing animation
  try {
    const payload = await requestJson("/api/state");
    // Only re-render if the inbox length changed to avoid UI flickering
    if (payload.inbox.length !== state.inbox.length) {
      applyServerState(payload);
    } else {
      // Always update sovereignty stats (they might change due to queue processing)
      renderSovereignty(payload.sovereignty);
    }
  } catch (err) {
    console.warn("Live poll failed:", err);
  }
}

/* ── Boot ── */
async function boot() {
  $("mail-search").addEventListener("input", (e) => { state.search = e.target.value; renderInbox(); });
  $("process-all").addEventListener("click", processAll);
  $("generate-batch").addEventListener("click", generateBatch);
  setupKeyboard();
  const payload = await requestJson("/api/state");
  applyServerState(payload);
  
  // Start live polling every 3 seconds
  setInterval(pollState, 3000);
}

boot().catch((err) => {
  $("app").innerHTML = `<div class="empty-detail" style="height:100vh;"><div class="empty-detail-icon">${ICONS.docLg}</div><strong>Dashboard failed to load</strong><p>${escapeHtml(err.message)}</p></div>`;
});
