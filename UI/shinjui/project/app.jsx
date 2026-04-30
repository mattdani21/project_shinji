// Tessera AI Indexer — main app shell + state.
const { useState, useEffect, useMemo, useCallback } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "density": "comfortable",
  "appearance": "light",
  "accentHue": 250,
  "showHeaderMeta": true
}/*EDITMODE-END*/;

function App() {
  const { INBOX, QUEUE_GROUPS } = window.TESSERA_DATA;
  const [tweaks, setTweak] = window.useTweaks ? window.useTweaks(TWEAK_DEFAULTS) : [TWEAK_DEFAULTS, () => {}];

  // Selection state — what's open in the right panel
  const [selectedMailId, setSelectedMailId] = useState("m-8842");
  // Routing state — which mails have been processed into which queue
  const [queueState, setQueueState] = useState({
    "NEW BUSINESS": ["m-8842"],
    "MAINTENANCE": [],
    "CLAIMS": [],
  });
  const [processed, setProcessed] = useState(new Set(["m-8842"]));
  const [processing, setProcessing] = useState(false);

  // Apply accent hue from tweaks
  useEffect(() => {
    const h = tweaks.accentHue ?? 250;
    document.documentElement.style.setProperty("--accent", `oklch(62% 0.17 ${h})`);
    document.documentElement.style.setProperty("--accent-bg", `oklch(95% 0.04 ${h})`);
  }, [tweaks.accentHue]);

  // Apply appearance
  useEffect(() => {
    const r = document.documentElement.style;
    if (tweaks.appearance === "dark") {
      r.setProperty("--bg",        "oklch(18% 0.005 260)");
      r.setProperty("--bg-2",      "oklch(20% 0.005 260)");
      r.setProperty("--surface",   "oklch(23% 0.006 260)");
      r.setProperty("--surface-2", "oklch(26% 0.006 260)");
      r.setProperty("--hairline",  "oklch(32% 0.008 260)");
      r.setProperty("--hairline-2","oklch(28% 0.007 260)");
      r.setProperty("--text",      "oklch(96% 0.005 260)");
      r.setProperty("--text-2",    "oklch(78% 0.008 260)");
      r.setProperty("--text-3",    "oklch(58% 0.008 260)");
    } else {
      r.removeProperty("--bg");
      r.removeProperty("--bg-2");
      r.removeProperty("--surface");
      r.removeProperty("--surface-2");
      r.removeProperty("--hairline");
      r.removeProperty("--hairline-2");
      r.removeProperty("--text");
      r.removeProperty("--text-2");
      r.removeProperty("--text-3");
    }
  }, [tweaks.appearance]);

  // Process all: animate routing of pending mails into their target queues
  const processAll = useCallback(async () => {
    if (processing) return;
    const pending = INBOX.filter(m => !processed.has(m.id));
    if (pending.length === 0) return;
    setProcessing(true);
    for (const mail of pending) {
      await new Promise(r => setTimeout(r, 380));
      setQueueState(prev => ({
        ...prev,
        [mail.routedTo.queue]: [...(prev[mail.routedTo.queue] || []), mail.id],
      }));
      setProcessed(prev => new Set(prev).add(mail.id));
    }
    setProcessing(false);
  }, [INBOX, processed, processing]);

  const selectedMail = INBOX.find(m => m.id === selectedMailId);

  // Selecting a queue item also opens the source mail
  const onQueueSelect = (_qid, sourceMailId) => setSelectedMailId(sourceMailId);

  const selectedQueueItemId = useMemo(() => {
    if (!selectedMail) return null;
    const grp = QUEUE_GROUPS.find(g => g.name === selectedMail.routedTo.queue);
    if (!grp) return null;
    if (!(queueState[grp.name] || []).includes(selectedMail.id)) return null;
    const item = grp.items.find(i => i.source === selectedMail.id);
    return item?.id || null;
  }, [selectedMail, queueState, QUEUE_GROUPS]);

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", background: "var(--bg)" }}>
      <TopBar showMeta={tweaks.showHeaderMeta} />
      <main style={{
        flex: 1, minHeight: 0,
        display: "grid",
        gridTemplateColumns: tweaks.density === "compact" ? "300px 280px 1fr" : "340px 320px 1fr",
        gap: 0,
        background: "var(--bg)",
        borderTop: "0.5px solid var(--hairline)",
      }}>
        <div style={{ borderRight: "0.5px solid var(--hairline)", minHeight: 0 }}>
          <Inbox
            mails={INBOX}
            selectedId={selectedMailId}
            processed={processed}
            processedCount={processed.size}
            onSelect={setSelectedMailId}
            onProcess={processAll}
            processing={processing}
          />
        </div>
        <div style={{ borderRight: "0.5px solid var(--hairline)", minHeight: 0 }}>
          <WorkQueues
            groups={QUEUE_GROUPS}
            queueState={queueState}
            selectedItemId={selectedQueueItemId}
            onSelect={onQueueSelect}
          />
        </div>
        <div style={{ minHeight: 0 }}>
          <DetailView mail={selectedMail} />
        </div>
      </main>

      {/* Tweaks */}
      {window.TweaksPanel && (
        <window.TweaksPanel title="Tweaks">
          <window.TweakSection title="Appearance">
            <window.TweakRadio
              label="Theme"
              value={tweaks.appearance}
              options={[{value:"light", label:"Light"}, {value:"dark", label:"Dark"}]}
              onChange={v => setTweak("appearance", v)}
            />
            <window.TweakRadio
              label="Density"
              value={tweaks.density}
              options={[{value:"comfortable", label:"Comfy"}, {value:"compact", label:"Compact"}]}
              onChange={v => setTweak("density", v)}
            />
            <window.TweakSlider
              label="Accent hue" min={0} max={360} step={1}
              value={tweaks.accentHue}
              onChange={v => setTweak("accentHue", v)}
            />
            <window.TweakToggle
              label="Show header meta"
              value={tweaks.showHeaderMeta}
              onChange={v => setTweak("showHeaderMeta", v)}
            />
          </window.TweakSection>
        </window.TweaksPanel>
      )}
    </div>
  );
}

const TopBar = ({ showMeta }) => (
  <header style={{
    height: 48, flex: "0 0 48px",
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "0 16px",
    background: "var(--surface)",
    borderBottom: "0.5px solid var(--hairline)",
    backdropFilter: "saturate(180%) blur(20px)",
  }}>
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div style={{
        width: 22, height: 22, borderRadius: 6,
        background: "linear-gradient(135deg, var(--text) 0%, oklch(40% 0.01 260) 100%)",
        display: "grid", placeItems: "center",
        boxShadow: "inset 0 0.5px 0 rgba(255,255,255,0.15), 0 1px 2px rgba(0,0,0,0.08)",
      }}>
        {/* Tessera mark — stacked tile glyph */}
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
          <rect x="0.5" y="0.5" width="4" height="4" rx="1" stroke="white" strokeOpacity="0.85" />
          <rect x="7" y="0.5" width="4" height="4" rx="1" fill="white" fillOpacity="0.9" />
          <rect x="0.5" y="7" width="4" height="4" rx="1" fill="white" fillOpacity="0.5" />
          <rect x="7" y="7" width="4" height="4" rx="1" stroke="white" strokeOpacity="0.85" />
        </svg>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{
          fontSize: 13.5, fontWeight: 700, letterSpacing: 0.2, color: "var(--text)",
        }}>Tessera</span>
        <span style={{
          fontSize: 12, color: "var(--text-3)", fontWeight: 500,
        }}>AI Indexer</span>
      </div>
      {showMeta && (
        <>
          <span style={{ width: 1, height: 16, background: "var(--hairline)", margin: "0 6px" }} />
          <NavTab active>Triage</NavTab>
          <NavTab>Audit</NavTab>
          <NavTab>Replay</NavTab>
          <NavTab>Settings</NavTab>
        </>
      )}
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      {showMeta && (
        <div className="mono" style={{ fontSize: 11, color: "var(--text-3)", display: "flex", alignItems: "center", gap: 8 }}>
          <span>v0.4.2</span>
          <span style={{ width: 1, height: 12, background: "var(--hairline)" }} />
          <span>uptime 14d</span>
        </div>
      )}
      <div style={{
        display: "flex", alignItems: "center", gap: 6,
        padding: "4px 9px 4px 8px", borderRadius: 999,
        background: "oklch(96% 0.04 145)", border: "0.5px solid oklch(86% 0.08 145)",
        color: "oklch(38% 0.13 145)", fontSize: 11.5, fontWeight: 600,
      }}>
        <span style={{
          width: 7, height: 7, borderRadius: "50%", background: "oklch(60% 0.17 145)",
          boxShadow: "0 0 0 3px oklch(85% 0.10 145 / 0.5)",
        }} />
        On-prem
      </div>
      <div style={{
        width: 28, height: 28, borderRadius: "50%",
        background: "linear-gradient(135deg, oklch(80% 0.08 30), oklch(70% 0.12 60))",
        color: "white", fontSize: 11, fontWeight: 700,
        display: "grid", placeItems: "center",
        border: "0.5px solid oklch(70% 0.10 50)",
      }}>JL</div>
    </div>
  </header>
);

const NavTab = ({ children, active }) => (
  <button style={{
    all: "unset", cursor: "pointer",
    padding: "4px 10px", borderRadius: 7, fontSize: 12.5, fontWeight: 500,
    color: active ? "var(--text)" : "var(--text-2)",
    background: active ? "var(--surface-2)" : "transparent",
    border: active ? "0.5px solid var(--hairline)" : "0.5px solid transparent",
  }}>{children}</button>
);

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
