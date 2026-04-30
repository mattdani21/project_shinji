// Panels: Inbox (left), WorkQueues (middle), DetailView (right) + small UI primitives.

const cls = (...xs) => xs.filter(Boolean).join(" ");

/* ────────────────  PRIMITIVES ──────────────── */

const Pill = ({ children, tone = "neutral", style }) => {
  const tones = {
    neutral: { bg: "var(--surface-2)", fg: "var(--text-2)", bd: "var(--hairline)" },
    blue:    { bg: "oklch(96% 0.03 250)", fg: "oklch(46% 0.15 250)", bd: "oklch(88% 0.06 250)" },
    green:   { bg: "oklch(96% 0.04 145)", fg: "oklch(42% 0.13 145)", bd: "oklch(86% 0.08 145)" },
    amber:   { bg: "oklch(97% 0.05 80)",  fg: "oklch(46% 0.13 70)",  bd: "oklch(88% 0.10 80)" },
    violet:  { bg: "oklch(96% 0.03 295)", fg: "oklch(46% 0.14 295)", bd: "oklch(88% 0.06 295)" },
    red:     { bg: "oklch(97% 0.04 27)",  fg: "oklch(48% 0.16 27)",  bd: "oklch(88% 0.09 27)" },
  };
  const t = tones[tone] || tones.neutral;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 8px", borderRadius: 999, fontSize: 11.5, fontWeight: 600,
      letterSpacing: 0.1, background: t.bg, color: t.fg,
      border: `0.5px solid ${t.bd}`, ...style,
    }}>{children}</span>
  );
};

const Avatar = ({ name, color }) => {
  const initials = name.split(" ").slice(0,2).map(w => w[0]).join("").toUpperCase();
  const hue = (name.charCodeAt(0) * 7) % 360;
  return (
    <div style={{
      width: 30, height: 30, flex: "0 0 30px", borderRadius: "50%",
      background: color || `oklch(92% 0.04 ${hue})`,
      color: `oklch(38% 0.13 ${hue})`,
      display: "grid", placeItems: "center", fontSize: 11.5, fontWeight: 700,
      fontFamily: '"Inter Tight"', letterSpacing: 0.2,
      border: "0.5px solid oklch(85% 0.04 " + hue + ")",
    }}>{initials}</div>
  );
};

const ConfidenceBar = ({ value }) => {
  const tone = value >= 95 ? "var(--green)" : value >= 85 ? "var(--accent)" : value >= 75 ? "var(--amber)" : "var(--red)";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{
        width: 96, height: 4, borderRadius: 999, background: "var(--hairline-2)",
        position: "relative", overflow: "hidden",
      }}>
        <div style={{
          width: `${value}%`, height: "100%", background: tone,
          transition: "width 600ms cubic-bezier(.2,.8,.2,1)",
        }} />
      </div>
      <span className="mono" style={{ fontSize: 12, color: "var(--text)", fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>
        {value}%
      </span>
    </div>
  );
};

/* ────────────────  COLUMN HEADER ──────────────── */
const ColHeader = ({ icon, title, count, right }) => (
  <div style={{
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "14px 16px 12px", borderBottom: "0.5px solid var(--hairline)",
    background: "var(--surface)", position: "sticky", top: 0, zIndex: 2,
  }}>
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span style={{ color: "var(--text-2)" }}>{icon}</span>
      <h2 style={{
        margin: 0, fontSize: 13, fontWeight: 600, letterSpacing: 0.3,
        color: "var(--text)", textTransform: "uppercase",
      }}>{title}</h2>
      {count != null && (
        <span className="mono" style={{
          fontSize: 11, color: "var(--text-3)", fontWeight: 500,
          padding: "1px 6px", borderRadius: 6, background: "var(--surface-2)",
        }}>{count}</span>
      )}
    </div>
    {right}
  </div>
);

/* ────────────────  INBOX ──────────────── */
const InboxRow = ({ mail, selected, processed, onClick }) => (
  <button
    onClick={onClick}
    style={{
      all: "unset", display: "block", width: "100%", cursor: "pointer",
      padding: "10px 14px", borderBottom: "0.5px solid var(--hairline-2)",
      background: selected ? "var(--accent-bg)" : "transparent",
      transition: "background 120ms ease",
      position: "relative",
    }}
    onMouseEnter={e => { if (!selected) e.currentTarget.style.background = "var(--surface-2)"; }}
    onMouseLeave={e => { if (!selected) e.currentTarget.style.background = "transparent"; }}
  >
    {!processed && (
      <span style={{
        position: "absolute", left: 6, top: 18,
        width: 6, height: 6, borderRadius: "50%", background: "var(--accent)",
      }} />
    )}
    <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
      <Avatar name={mail.fromName} />
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
          <span style={{
            fontSize: 13, fontWeight: 600, color: "var(--text)",
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
          }}>{mail.fromName}</span>
          <span className="mono" style={{ fontSize: 11, color: "var(--text-3)", flex: "0 0 auto" }}>
            {mail.received}
          </span>
        </div>
        <div style={{
          fontSize: 12.5, color: "var(--text)", marginTop: 1, fontWeight: 500,
          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
        }}>{mail.subject}</div>
        <div style={{
          fontSize: 11.5, color: "var(--text-3)", marginTop: 2,
          overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
        }}>{mail.preview}</div>
        <div style={{ display: "flex", gap: 6, marginTop: 6, alignItems: "center" }}>
          {mail.attachments[0] && (
            <span style={{
              display: "inline-flex", alignItems: "center", gap: 4,
              fontSize: 10.5, color: "var(--text-3)", fontFamily: '"JetBrains Mono"',
            }}>
              <I.Paperclip size={11} />
              {mail.attachments[0].name}
            </span>
          )}
          {processed && (
            <Pill tone="green" style={{ marginLeft: "auto" }}>
              <I.Check size={10} stroke={2.4} /> routed
            </Pill>
          )}
        </div>
      </div>
    </div>
  </button>
);

const Inbox = ({ mails, selectedId, processed, onSelect, onProcess, processing, processedCount }) => {
  const pending = mails.length - processedCount;
  return (
    <section style={{ display: "flex", flexDirection: "column", height: "100%", background: "var(--surface)" }}>
      <ColHeader
        icon={<I.Inbox size={15} />}
        title="Mailbox"
        count={mails.length}
        right={<span className="mono" style={{ fontSize: 11, color: "var(--text-3)" }}>indexer@tessera</span>}
      />
      <div style={{ padding: "8px 12px 4px" }}>
        <div style={{
          display: "flex", alignItems: "center", gap: 6,
          background: "var(--surface-2)", border: "0.5px solid var(--hairline)",
          borderRadius: 8, padding: "6px 10px",
        }}>
          <I.Search size={13} style={{ color: "var(--text-3)" }} />
          <input
            placeholder="Search mail"
            style={{
              all: "unset", flex: 1, fontSize: 12.5, color: "var(--text)",
              fontFamily: "inherit",
            }}
          />
          <span className="mono" style={{ fontSize: 10.5, color: "var(--text-3)", padding: "1px 5px", border: "0.5px solid var(--hairline)", borderRadius: 4 }}>⌘K</span>
        </div>
      </div>
      <div style={{ flex: 1, overflowY: "auto", paddingBottom: 8 }}>
        {mails.map(m => (
          <InboxRow
            key={m.id} mail={m} selected={selectedId === m.id}
            processed={processed.has(m.id)}
            onClick={() => onSelect(m.id)}
          />
        ))}
      </div>
      {/* Footer: process action + stats */}
      <div style={{
        borderTop: "0.5px solid var(--hairline)", padding: 12,
        background: "var(--surface)",
        display: "flex", flexDirection: "column", gap: 10,
      }}>
        <button
          onClick={onProcess}
          disabled={processing || pending === 0}
          style={{
            all: "unset", cursor: processing || pending === 0 ? "default" : "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
            padding: "10px 14px", borderRadius: 10,
            background: pending === 0
              ? "var(--surface-2)"
              : "linear-gradient(180deg, oklch(66% 0.18 250), oklch(58% 0.18 250))",
            color: pending === 0 ? "var(--text-3)" : "white",
            fontSize: 13, fontWeight: 600, letterSpacing: 0.1,
            boxShadow: pending === 0 ? "none" : "0 1px 0 rgba(255,255,255,0.3) inset, 0 1px 2px rgba(15,17,21,0.12), 0 6px 18px -8px oklch(58% 0.18 250 / 0.45)",
            transition: "transform 100ms ease",
          }}
          onMouseDown={e => { if (pending) e.currentTarget.style.transform = "translateY(0.5px)"; }}
          onMouseUp={e => e.currentTarget.style.transform = "translateY(0)"}
        >
          {processing ? (
            <>
              <span style={{
                width: 12, height: 12, borderRadius: "50%",
                border: "1.5px solid rgba(255,255,255,0.4)",
                borderTopColor: "white", animation: "spin 700ms linear infinite",
              }} />
              Processing…
            </>
          ) : pending === 0 ? (
            <><I.Check size={14} stroke={2.2} /> All routed</>
          ) : (
            <><I.Sparkle size={14} stroke={2} /> Process all ({pending})</>
          )}
        </button>
        <div style={{
          display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8,
          fontSize: 11, color: "var(--text-3)",
        }}>
          <Stat label="Pending" value={pending} />
          <Stat label="Routed" value={processedCount} tone="var(--green)" />
          <Stat label="Avg conf." value="94%" tone="var(--accent)" />
        </div>
      </div>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </section>
  );
};

const Stat = ({ label, value, tone }) => (
  <div style={{
    background: "var(--surface-2)", borderRadius: 8,
    border: "0.5px solid var(--hairline)", padding: "6px 8px",
  }}>
    <div className="mono" style={{ fontSize: 14, fontWeight: 600, color: tone || "var(--text)", fontVariantNumeric: "tabular-nums" }}>{value}</div>
    <div style={{ fontSize: 10, color: "var(--text-3)", marginTop: 1, letterSpacing: 0.2, textTransform: "uppercase" }}>{label}</div>
  </div>
);

/* ────────────────  WORK QUEUES ──────────────── */
const QueueGroup = ({ group, items, selectedItemId, onSelect }) => {
  const [open, setOpen] = React.useState(true);
  return (
    <div style={{ borderBottom: "0.5px solid var(--hairline-2)" }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          all: "unset", cursor: "pointer", width: "100%",
          display: "flex", alignItems: "center", gap: 8,
          padding: "10px 14px",
        }}
      >
        <I.ChevronDown size={12} style={{
          color: "var(--text-3)",
          transition: "transform 160ms ease",
          transform: open ? "rotate(0deg)" : "rotate(-90deg)",
        }} />
        <span style={{
          width: 6, height: 6, borderRadius: 2, background: group.color,
        }} />
        <span style={{
          fontSize: 11.5, fontWeight: 700, letterSpacing: 0.5,
          color: "var(--text-2)", textTransform: "uppercase",
        }}>{group.name}</span>
        <span className="mono" style={{
          marginLeft: "auto", fontSize: 11, color: "var(--text-3)",
          padding: "1px 6px", borderRadius: 6, background: "var(--surface-2)",
        }}>{items.length}</span>
      </button>
      {open && (
        <div style={{ padding: "0 8px 8px" }}>
          {items.length === 0 && (
            <div style={{
              padding: "10px 12px", fontSize: 11.5, color: "var(--text-3)",
              fontStyle: "italic",
            }}>Empty — process inbox to populate</div>
          )}
          {items.map(it => (
            <QueueItemRow
              key={it.id} item={it}
              selected={selectedItemId === it.id}
              onClick={() => onSelect(it.id, it.source)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const QueueItemRow = ({ item, selected, onClick }) => (
  <button
    onClick={onClick}
    style={{
      all: "unset", display: "flex", alignItems: "center", gap: 8,
      width: "100%", padding: "8px 10px", borderRadius: 8, cursor: "pointer",
      background: selected ? "var(--accent-bg)" : "transparent",
      border: selected ? "0.5px solid oklch(85% 0.07 250)" : "0.5px solid transparent",
      transition: "background 120ms ease",
      marginBottom: 2,
    }}
    onMouseEnter={e => { if (!selected) e.currentTarget.style.background = "var(--surface-2)"; }}
    onMouseLeave={e => { if (!selected) e.currentTarget.style.background = "transparent"; }}
  >
    <span className="mono" style={{ color: "var(--text-3)", fontSize: 12 }}>└─</span>
    <span style={{
      fontSize: 12.5, color: "var(--text)", fontWeight: selected ? 600 : 500,
      flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
    }}>{item.label}</span>
    {item.note && (
      <Pill tone="amber"><I.Flag size={9} stroke={2.4} /> NOTE</Pill>
    )}
  </button>
);

const WorkQueues = ({ groups, queueState, selectedItemId, onSelect }) => {
  const totalRouted = Object.values(queueState).reduce((a, arr) => a + arr.length, 0);
  return (
    <section style={{ display: "flex", flexDirection: "column", height: "100%", background: "var(--surface)" }}>
      <ColHeader
        icon={<I.Layers size={15} />}
        title="Work queues"
        count={totalRouted}
        right={
          <Pill tone="blue"><I.Bolt size={10} stroke={2.4} /> auto-route</Pill>
        }
      />
      <div style={{ flex: 1, overflowY: "auto" }}>
        {groups.map(g => (
          <QueueGroup
            key={g.name}
            group={g}
            items={(queueState[g.name] || []).map(srcId => g.items.find(i => i.source === srcId)).filter(Boolean)}
            selectedItemId={selectedItemId}
            onSelect={onSelect}
          />
        ))}
      </div>
      <div style={{
        borderTop: "0.5px solid var(--hairline)", padding: "10px 14px",
        fontSize: 11, color: "var(--text-3)",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <span>Routed today</span>
        <span className="mono" style={{ color: "var(--text-2)", fontWeight: 600 }}>
          {totalRouted} · 1 needs review
        </span>
      </div>
    </section>
  );
};

/* ────────────────  DETAIL VIEW ──────────────── */
const KV = ({ label, children, mono }) => (
  <div style={{
    display: "grid", gridTemplateColumns: "120px 1fr", gap: 12,
    padding: "8px 0", borderBottom: "0.5px solid var(--hairline-2)",
    alignItems: "center",
  }}>
    <div style={{ fontSize: 12, color: "var(--text-3)", fontWeight: 500 }}>{label}</div>
    <div className={mono ? "mono" : ""} style={{ fontSize: 13, color: "var(--text)", fontWeight: 500 }}>
      {children}
    </div>
  </div>
);

const Section = ({ title, children, right }) => (
  <div style={{
    background: "var(--surface)", border: "0.5px solid var(--hairline)",
    borderRadius: 12, padding: "14px 16px", boxShadow: "var(--shadow-sm)",
  }}>
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "center",
      marginBottom: 8,
    }}>
      <h3 style={{
        margin: 0, fontSize: 11, fontWeight: 700, letterSpacing: 0.6,
        color: "var(--text-3)", textTransform: "uppercase",
      }}>{title}</h3>
      {right}
    </div>
    {children}
  </div>
);

const PdfPreview = ({ attachment, classification }) => (
  <div style={{
    background: "linear-gradient(180deg, oklch(98% 0.003 100), oklch(96% 0.004 100))",
    border: "0.5px solid var(--hairline)", borderRadius: 12,
    padding: 14, display: "flex", gap: 14, alignItems: "stretch",
    boxShadow: "var(--shadow-sm)",
  }}>
    {/* Mock page */}
    <div style={{
      width: 110, flex: "0 0 110px", aspectRatio: "8.5 / 11",
      background: "white", border: "0.5px solid var(--hairline)",
      borderRadius: 6, padding: 10, position: "relative",
      boxShadow: "0 1px 0 rgba(0,0,0,0.04), 0 6px 16px -8px rgba(0,0,0,0.12)",
    }}>
      <div style={{ height: 6, width: "70%", background: "oklch(90% 0.005 100)", borderRadius: 2, marginBottom: 6 }} />
      <div style={{ height: 4, width: "100%", background: "oklch(94% 0.004 100)", borderRadius: 2, marginBottom: 3 }} />
      <div style={{ height: 4, width: "92%", background: "oklch(94% 0.004 100)", borderRadius: 2, marginBottom: 3 }} />
      <div style={{ height: 4, width: "60%", background: "oklch(94% 0.004 100)", borderRadius: 2, marginBottom: 8 }} />
      <div style={{ height: 4, width: "100%", background: "oklch(94% 0.004 100)", borderRadius: 2, marginBottom: 3 }} />
      <div style={{ height: 4, width: "88%", background: "oklch(94% 0.004 100)", borderRadius: 2, marginBottom: 3 }} />
      <div style={{ height: 4, width: "100%", background: "oklch(94% 0.004 100)", borderRadius: 2, marginBottom: 8 }} />
      <div style={{ height: 22, width: "40%", background: "oklch(96% 0.003 100)", borderRadius: 3, border: "0.5px dashed oklch(85% 0.005 100)" }} />
      <span className="mono" style={{
        position: "absolute", bottom: 6, right: 8, fontSize: 8.5, color: "var(--text-3)",
      }}>p.1</span>
    </div>
    <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
      <div>
        <div className="mono" style={{ fontSize: 12.5, color: "var(--text)", fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {attachment.name}
        </div>
        <div style={{ fontSize: 11.5, color: "var(--text-3)", marginTop: 2 }}>
          {attachment.pages} pages · {attachment.size} · PDF
        </div>
        <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
          {Array.from({ length: Math.min(attachment.pages, 5) }).map((_, i) => (
            <span key={i} className="mono" style={{
              fontSize: 10, padding: "2px 6px", borderRadius: 5,
              background: "var(--surface)", color: "var(--text-2)",
              border: "0.5px solid var(--hairline)",
            }}>p.{i+1}</span>
          ))}
          {attachment.pages > 5 && (
            <span className="mono" style={{ fontSize: 10, color: "var(--text-3)" }}>+{attachment.pages - 5}</span>
          )}
        </div>
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <button style={btnPrimary}><I.Eye size={12} stroke={2} /> View PDF</button>
        <button style={btnGhost}><I.Doc size={12} /> Open email</button>
      </div>
    </div>
  </div>
);

const btnPrimary = {
  all: "unset", cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 6,
  padding: "6px 12px", borderRadius: 8,
  background: "var(--text)", color: "white", fontSize: 12, fontWeight: 600,
  boxShadow: "0 1px 0 rgba(255,255,255,0.08) inset",
};
const btnGhost = {
  all: "unset", cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 6,
  padding: "6px 12px", borderRadius: 8,
  background: "var(--surface)", color: "var(--text)", fontSize: 12, fontWeight: 600,
  border: "0.5px solid var(--hairline)",
};

const DetailView = ({ mail }) => {
  if (!mail) {
    return (
      <section style={{
        display: "flex", flexDirection: "column", alignItems: "center",
        justifyContent: "center", height: "100%", background: "var(--bg-2)",
        color: "var(--text-3)", padding: 32, textAlign: "center", gap: 10,
      }}>
        <div style={{
          width: 44, height: 44, borderRadius: 10,
          background: "var(--surface)", border: "0.5px solid var(--hairline)",
          display: "grid", placeItems: "center", color: "var(--text-3)",
          boxShadow: "var(--shadow-sm)",
        }}><I.Doc size={20} /></div>
        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-2)" }}>Select an item</div>
        <div style={{ fontSize: 12, maxWidth: 240 }}>
          Pick an email from the mailbox or a routed task from a queue to inspect its body, attachment and classification.
        </div>
      </section>
    );
  }

  const c = mail.classification;
  const att = mail.attachments[0];
  const tone = c.confidence >= 95 ? "green" : c.confidence >= 85 ? "blue" : c.confidence >= 75 ? "amber" : "red";

  return (
    <section style={{ display: "flex", flexDirection: "column", height: "100%", background: "var(--bg-2)" }}>
      <ColHeader
        icon={<I.Doc size={15} />}
        title="Detail view"
        right={
          <div style={{ display: "flex", gap: 6 }}>
            <Pill tone={tone}><I.Sparkle size={10} stroke={2} /> AI classified</Pill>
            {c.status === "needs-review" && <Pill tone="amber"><I.Flag size={10} stroke={2.4} /> NOTE</Pill>}
          </div>
        }
      />
      <div style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
        {/* Email header card */}
        <div style={{
          background: "var(--surface)", border: "0.5px solid var(--hairline)",
          borderRadius: 14, padding: 16, boxShadow: "var(--shadow-sm)",
        }}>
          <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <Avatar name={mail.fromName} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "baseline" }}>
                <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>{mail.fromName}</span>
                <span className="mono" style={{ fontSize: 11.5, color: "var(--text-3)" }}>today · {mail.received}</span>
              </div>
              <div className="mono" style={{ fontSize: 11.5, color: "var(--text-3)", marginTop: 1 }}>
                {mail.from}
              </div>
            </div>
          </div>
          <h2 style={{
            margin: "14px 0 10px", fontSize: 17, fontWeight: 600, color: "var(--text)",
            letterSpacing: -0.1, textWrap: "pretty",
          }}>{mail.subject}</h2>
          <pre style={{
            margin: 0, whiteSpace: "pre-wrap", fontFamily: "inherit",
            fontSize: 13.5, lineHeight: 1.55, color: "var(--text-2)",
            textWrap: "pretty",
          }}>{mail.body}</pre>
        </div>

        {/* Attachment */}
        <Section title="Attachment" right={
          <span className="mono" style={{ fontSize: 11, color: "var(--text-3)" }}>1 file</span>
        }>
          <PdfPreview attachment={att} classification={c} />
        </Section>

        {/* Classification + Record metadata side-by-side */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <Section title="Classification" right={<ConfidenceBar value={c.confidence} />}>
            <KV label="Type">
              <Pill tone={tone === "green" ? "green" : "blue"}>
                <I.Dot size={10} /> {c.type}
              </Pill>
            </KV>
            <KV label="Tier" mono>{c.tier}</KV>
            <KV label="Status">
              <Pill tone={c.status === "pending" ? "neutral" : "amber"}>
                {c.status === "pending" ? <I.Dot size={10} style={{ color: "var(--accent)" }} /> : <I.Flag size={10} stroke={2.4} />}
                {c.status}
              </Pill>
            </KV>
            <KV label="Routed to">
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                <span style={{ color: "var(--text-3)" }}>queue</span>
                <I.ArrowRight size={11} style={{ color: "var(--text-3)" }} />
                <span style={{ fontWeight: 600 }}>{mail.routedTo.queue}</span>
              </span>
            </KV>
            {c.note && (
              <div style={{
                marginTop: 10, padding: "10px 12px",
                background: "oklch(98% 0.04 80)", border: "0.5px solid oklch(88% 0.08 80)",
                borderRadius: 8, fontSize: 12, color: "oklch(38% 0.13 70)", display: "flex", gap: 8,
              }}>
                <I.Flag size={13} stroke={2.2} style={{ flex: "0 0 13px", marginTop: 1 }} />
                <span><b>Indexer note:</b> {c.note}</span>
              </div>
            )}
          </Section>

          <Section title="Record" right={
            <Pill tone="green"><I.Shield size={10} stroke={2} /> on-prem</Pill>
          }>
            <KV label="Policy" mono>{c.policy}</KV>
            <KV label="Client">{c.client}</KV>
            <KV label="Pages">{c.pages}</KV>
            <KV label="Source">
              <span className="mono" style={{ fontSize: 12 }}>{mail.id}</span>
            </KV>
          </Section>
        </div>

        {/* Action bar */}
        <div style={{
          display: "flex", gap: 8, justifyContent: "flex-end",
          padding: "12px 0 4px",
        }}>
          <button style={btnGhost}>Reassign queue</button>
          <button style={btnGhost}>Flag for review</button>
          <button style={btnPrimary}><I.Check size={12} stroke={2.4} /> Approve & finalize</button>
        </div>
      </div>
    </section>
  );
};

Object.assign(window, { Pill, Avatar, ConfidenceBar, ColHeader, Inbox, WorkQueues, DetailView });
