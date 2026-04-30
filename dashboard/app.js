const state = {
  inbox: [],
  queueGroups: [],
  queueState: {},
  processed: new Set(),
  selectedMailId: null,
  search: "",
  processing: false,
};

const $ = (id) => document.getElementById(id);

const toneForConfidence = (confidence) => {
  if (confidence >= 95) return "green";
  if (confidence >= 85) return "blue";
  if (confidence >= 75) return "amber";
  return "amber";
};

const initials = (name) => name.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();

const avatarStyle = (name) => {
  const hue = (name.charCodeAt(0) * 7) % 360;
  return `background: oklch(92% 0.04 ${hue}); color: oklch(38% 0.13 ${hue}); border: 0.5px solid oklch(85% 0.04 ${hue});`;
};

const escapeHtml = (value = "") => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

async function requestJson(path, options) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function applyServerState(payload) {
  state.inbox = payload.inbox;
  state.queueGroups = payload.queueGroups;
  state.queueState = payload.queueState;
  state.processed = new Set(payload.processed);
  if (!state.selectedMailId && payload.inbox.length) {
    state.selectedMailId = payload.inbox[0].id;
  }
  renderSovereignty(payload.sovereignty);
  render();
}

function selectedMail() {
  return state.inbox.find((mail) => mail.id === state.selectedMailId) || null;
}

function selectedQueueItemId() {
  const mail = selectedMail();
  if (!mail) return null;
  const group = state.queueGroups.find((candidate) => candidate.name === mail.routedTo.queue);
  if (!group || !(state.queueState[group.name] || []).includes(mail.id)) return null;
  const item = group.items.find((candidate) => candidate.source === mail.id);
  return item ? item.id : null;
}

function renderSovereignty(stats) {
  $("stat-processed").textContent = stats.mailsProcessedToday.toLocaleString();
  $("stat-api").textContent = stats.externalApiCallsToday.toLocaleString();
  $("stat-egress").textContent = stats.customerDataEgress;
  $("stat-latency").textContent = `${stats.averageInferenceLatencyMs}ms`;
}

function render() {
  renderInbox();
  renderQueues();
  renderDetail();
}

function renderInbox() {
  const filtered = state.inbox.filter((mail) => {
    const haystack = `${mail.fromName} ${mail.subject} ${mail.preview} ${mail.classification.client}`.toLowerCase();
    return haystack.includes(state.search.toLowerCase());
  });
  const pending = state.inbox.length - state.processed.size;

  $("mail-count").textContent = state.inbox.length;
  $("pending-count").textContent = pending;
  $("routed-count").textContent = state.processed.size;
  $("process-all").disabled = state.processing || pending === 0;
  $("process-all").textContent = state.processing
    ? "Processing..."
    : pending === 0
      ? "All routed"
      : `Process all (${pending})`;

  $("inbox-list").innerHTML = filtered.map((mail) => {
    const processed = state.processed.has(mail.id);
    return `
      <button class="mail-row ${state.selectedMailId === mail.id ? "selected" : ""}" type="button" data-mail-id="${escapeHtml(mail.id)}">
        ${processed ? "" : '<span class="unread-dot"></span>'}
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
              <span class="attachment mono">⌘ ${escapeHtml(mail.attachments[0].name)}</span>
              ${processed ? '<span class="pill green" style="margin-left:auto;">✓ routed</span>' : ""}
            </span>
          </span>
        </span>
      </button>
    `;
  }).join("");

  document.querySelectorAll(".mail-row").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedMailId = row.dataset.mailId;
      render();
    });
  });
}

function renderQueues() {
  const selectedId = selectedQueueItemId();
  const total = Object.values(state.queueState).reduce((sum, ids) => sum + ids.length, 0);
  $("queue-count").textContent = total;
  $("queue-footer-total").textContent = `${total} · 1 needs review`;

  $("queue-list").innerHTML = state.queueGroups.map((group) => {
    const ids = state.queueState[group.name] || [];
    const items = ids.map((sourceId) => group.items.find((item) => item.source === sourceId)).filter(Boolean);
    const itemMarkup = items.length
      ? items.map((item) => `
        <button class="queue-item ${selectedId === item.id ? "selected" : ""}" type="button" data-source-id="${escapeHtml(item.source)}">
          <span class="queue-branch mono">└─</span>
          <span class="queue-item-label">${escapeHtml(item.label)}</span>
          ${item.note ? '<span class="pill amber">⚑ NOTE</span>' : ""}
        </button>
      `).join("")
      : '<div class="queue-empty">Empty - process inbox to populate</div>';

    return `
      <div class="queue-group">
        <div class="queue-group-header">
          <span class="queue-chevron">⌄</span>
          <span class="queue-color" style="background:${escapeHtml(group.color)}"></span>
          <span class="queue-name">${escapeHtml(group.name)}</span>
          <span class="queue-group-count counter">${items.length}</span>
        </div>
        <div class="queue-items">${itemMarkup}</div>
      </div>
    `;
  }).join("");

  document.querySelectorAll(".queue-item").forEach((item) => {
    item.addEventListener("click", () => {
      state.selectedMailId = item.dataset.sourceId;
      render();
    });
  });
}

function renderDetail() {
  const mail = selectedMail();
  const badges = $("detail-badges");
  const detail = $("detail-view");

  if (!mail) {
    badges.innerHTML = "";
    detail.innerHTML = '<div class="empty-detail"><div><strong>Select an item</strong><p>Pick an email from the mailbox or a routed task from a queue to inspect its body, attachment and classification.</p></div></div>';
    return;
  }

  const classification = mail.classification;
  const attachment = mail.attachments[0];
  const tone = toneForConfidence(classification.confidence);
  badges.innerHTML = `
    <span class="pill ${tone}">✦ AI classified</span>
    ${classification.status === "needs-review" ? '<span class="pill amber">⚑ NOTE</span>' : ""}
  `;

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
            <div class="pdf-name mono">${escapeHtml(attachment.name)}</div>
            <div class="pdf-meta">${attachment.pages} pages · ${escapeHtml(attachment.size)} · PDF</div>
            <div class="page-chips mono">
              ${Array.from({ length: Math.min(attachment.pages, 5) }, (_, index) => `<span>p.${index + 1}</span>`).join("")}
              ${attachment.pages > 5 ? `<span>+${attachment.pages - 5}</span>` : ""}
            </div>
          </div>
          <div class="action-bar" style="justify-content:flex-start; padding:10px 0 0;">
            <button class="dark-action" type="button">View PDF</button>
            <button class="ghost-action" type="button">Open email</button>
          </div>
        </div>
      </div>
    </section>

    <div class="detail-grid">
      <section class="detail-section">
        <div class="section-title">
          <h3>Classification</h3>
          <div class="confidence">
            <span class="confidence-track"><span class="confidence-fill" style="width:${classification.confidence}%"></span></span>
            <span class="mono">${classification.confidence}%</span>
          </div>
        </div>
        ${kv("Type", `<span class="pill ${tone}">● ${escapeHtml(classification.type)}</span>`)}
        ${kv("Tier", escapeHtml(classification.tier), true)}
        ${kv("Status", `<span class="pill ${classification.status === "pending" ? "neutral" : "amber"}">${classification.status === "pending" ? "●" : "⚑"} ${escapeHtml(classification.status)}</span>`)}
        ${kv("Routed to", `<span class="muted">queue</span> → <strong>${escapeHtml(mail.routedTo.queue)}</strong>`)}
        ${classification.note ? `<div class="note"><span>⚑</span><span><b>Indexer note:</b> ${escapeHtml(classification.note)}</span></div>` : ""}
      </section>

      <section class="detail-section">
        <div class="section-title">
          <h3>Record</h3>
          <span class="pill green">Shield on-prem</span>
        </div>
        ${kv("Policy", escapeHtml(classification.policy), true)}
        ${kv("Client", escapeHtml(classification.client))}
        ${kv("Pages", escapeHtml(classification.pages))}
        ${kv("Source", escapeHtml(mail.id), true)}
      </section>
    </div>

    <div class="action-bar">
      <button class="ghost-action" type="button">Reassign queue</button>
      <button class="ghost-action" type="button">Flag for review</button>
      <button class="dark-action" type="button">✓ Approve & finalize</button>
    </div>
  `;
}

function kv(label, value, mono = false) {
  return `
    <div class="kv">
      <div class="kv-label">${escapeHtml(label)}</div>
      <div class="kv-value ${mono ? "mono" : ""}">${value}</div>
    </div>
  `;
}

async function processAll() {
  if (state.processing) return;
  state.processing = true;
  renderInbox();
  try {
    const payload = await requestJson("/api/process-all", { method: "POST" });
    applyServerState(payload);
  } finally {
    state.processing = false;
    renderInbox();
  }
}

async function boot() {
  $("mail-search").addEventListener("input", (event) => {
    state.search = event.target.value;
    renderInbox();
  });
  $("process-all").addEventListener("click", processAll);
  const payload = await requestJson("/api/state");
  applyServerState(payload);
}

boot().catch((error) => {
  $("app").innerHTML = `<main class="empty-detail"><div><strong>Dashboard failed to load</strong><p>${escapeHtml(error.message)}</p></div></main>`;
});
