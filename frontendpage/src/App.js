import { useState, useRef, useEffect, useCallback } from "react";

const THEMES = {
  light: {
    page: "#ffffff", sidebar: "#f9f9f9", sidebarBorder: "#e5e5e5",
    header: "#0d0d0d", subtitle: "#8e8ea0", userBubble: "#0d0d0d", userText: "#fff",
    agentBubble: "#f4f4f4", agentText: "#0d0d0d", inputBg: "#fff", inputText: "#0d0d0d",
    inputWrapper: "#fff", sendBtn: "#0d0d0d", sendIcon: "#fff",
    thinkingBubble: "#f4f4f4", emptyText: "#c5c5d2", toggleBg: "#ececec", toggleColor: "#555",
    historyText: "#0d0d0d", historyMeta: "#8e8ea0", historyHover: "#ececec",
    historyActive: "#e3e3e3", sectionLabel: "#8e8ea0", menuBg: "#fff",
    menuBorder: "#e5e5e5", menuText: "#0d0d0d", menuHover: "#f4f4f4",
    scoreGreen: "#16a34a", scoreBg: "#f0fdf4", scoreBorder: "#bbf7d0",
    memoryBadgeBg: "#f0fdf4", memoryBadgeColor: "#16a34a", memoryBadgeBorder: "#bbf7d0",
  },
  dark: {
    page: "#212121", sidebar: "#171717", sidebarBorder: "#2f2f2f",
    header: "#ececec", subtitle: "#8e8ea0", userBubble: "#2f2f2f", userText: "#ececec",
    agentBubble: "#2f2f2f", agentText: "#ececec", inputBg: "#2f2f2f", inputText: "#ececec",
    inputWrapper: "#212121", sendBtn: "#ececec", sendIcon: "#212121",
    thinkingBubble: "#2f2f2f", emptyText: "#4e4e5a", toggleBg: "#2f2f2f", toggleColor: "#aaa",
    historyText: "#ececec", historyMeta: "#8e8ea0", historyHover: "#2a2a2a",
    historyActive: "#343434", sectionLabel: "#8e8ea0", menuBg: "#2f2f2f",
    menuBorder: "#3f3f3f", menuText: "#ececec", menuHover: "#3a3a3a",
    scoreGreen: "#4ade80", scoreBg: "#052e16", scoreBorder: "#166534",
    memoryBadgeBg: "#052e16", memoryBadgeColor: "#4ade80", memoryBadgeBorder: "#166534",
  },
};

const SendIcon = ({ color }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);
const MoonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);
const SunIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
  </svg>
);
const SidebarIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" /><line x1="9" y1="3" x2="9" y2="21" />
  </svg>
);
const DotsIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <circle cx="5" cy="12" r="2" /><circle cx="12" cy="12" r="2" /><circle cx="19" cy="12" r="2" />
  </svg>
);
const DownloadIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);
const NewChatIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

function TypingDots({ t }) {
  return (
    <div style={{ alignSelf: "flex-start", backgroundColor: t.thinkingBubble, padding: "14px 18px",
      borderRadius: "18px 18px 18px 4px", display: "flex", alignItems: "center", gap: "6px" }}>
      <style>{`@keyframes bounce{0%,80%,100%{transform:translateY(0);opacity:.3}40%{transform:translateY(-6px);opacity:1}}`}</style>
      {[0, 0.15, 0.3].map((d, i) => (
        <div key={i} style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: "#888",
          animation: "bounce 1.2s infinite", animationDelay: `${d}s` }} />
      ))}
    </div>
  );
}

function downloadTxt(topic, summary) {
  const blob = new Blob([`${topic}\n${"=".repeat(60)}\n\n${summary}`], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${topic.slice(0, 40).replace(/[^a-z0-9]/gi, "_")}.txt`;
  a.click();
}
function downloadPdf(topic, summary) {
  const win = window.open("", "_blank");
  win.document.write(`<html><head><title>${topic}</title>
    <style>body{font-family:Georgia,serif;max-width:800px;margin:40px auto;line-height:1.7;color:#111}
    h1{font-size:22px;border-bottom:2px solid #333;padding-bottom:8px}pre{white-space:pre-wrap;font-family:inherit}</style></head>
    <body><h1>${topic}</h1><pre>${summary}</pre></body></html>`);
  win.document.close(); win.focus();
  setTimeout(() => { win.print(); win.close(); }, 400);
}
function downloadDocx(topic, summary) {
  const rtf = `{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Times New Roman;}}\\f0\\fs24{\\b\\fs32 ${topic.replace(/[{}\\]/g, "")}\\par}\\par${summary.replace(/[{}\\]/g, "").replace(/\n/g, "\\par\n")}}`;
  const blob = new Blob([rtf], { type: "application/rtf" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${topic.slice(0, 40).replace(/[^a-z0-9]/gi, "_")}.rtf`;
  a.click();
}

function groupByRecency(items) {
  const now = Date.now(), DAY = 86400000;
  const groups = { Today: [], Yesterday: [], "This Week": [], "This Month": [], Older: [] };
  items.forEach((item, idx) => {
    const ts = item.timestamp ? new Date(item.timestamp).getTime() : now - idx * DAY * 2;
    const diff = now - ts;
    const entry = { ...item, _idx: idx };
    if (diff < DAY) groups["Today"].push(entry);
    else if (diff < 2 * DAY) groups["Yesterday"].push(entry);
    else if (diff < 7 * DAY) groups["This Week"].push(entry);
    else if (diff < 30 * DAY) groups["This Month"].push(entry);
    else groups["Older"].push(entry);
  });
  return groups;
}

function HistorySidebar({ t, onSelect, onNewChat, refreshTrigger, activeIdx }) {
  const [items, setItems] = useState([]);
  const [menuOpen, setMenuOpen] = useState(null); // "section-idx" string key
  const menuRef = useRef(null);

  const load = useCallback(() => {
    fetch("http://127.0.0.1:8000/memory").then((r) => r.json()).then(setItems).catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load, refreshTrigger]);
  useEffect(() => {
    const h = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(null); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const btn = { width: "100%", padding: "10px 14px", border: "none", textAlign: "left",
    backgroundColor: "transparent", color: t.menuText, cursor: "pointer",
    fontSize: "14px", display: "flex", alignItems: "center", gap: "10px", fontFamily: "inherit" };

  const renderItem = (item, idx, section = "default") => {
    const menuKey = `${section}-${idx}`;
    const isActive = activeIdx === idx;
    const short = (item.label || item.topic || "Untitled").slice(0, 30) + ((item.label || item.topic || "").length > 30 ? "..." : "");
    return (
      <div key={menuKey} style={{ position: "relative" }}>
        <div onClick={() => onSelect(item, idx)}
          style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "8px 12px", cursor: "pointer", borderRadius: "8px", margin: "1px 6px",
            backgroundColor: isActive ? t.historyActive : "transparent" }}
          onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = t.historyHover; }}
          onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = "transparent"; }}>
          <span style={{ fontSize: "14px", color: t.historyText, overflow: "hidden",
            textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
            {item.starred ? "★ " : ""}{short}
          </span>
          <button onClick={(e) => { e.stopPropagation(); setMenuOpen(menuOpen === menuKey ? null : menuKey); }}
            style={{ width: "24px", height: "24px", borderRadius: "4px", border: "none",
              backgroundColor: "transparent", color: t.historyMeta, cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
              opacity: isActive || menuOpen === menuKey ? 1 : 0, transition: "opacity 0.1s" }}
            className="dots-btn">
            <DotsIcon />
          </button>
        </div>

        {menuOpen === menuKey && (
          <div ref={menuRef} style={{ position: "absolute", right: "10px", top: "36px",
            backgroundColor: t.menuBg, border: `1px solid ${t.menuBorder}`,
            borderRadius: "12px", boxShadow: "0 4px 20px rgba(0,0,0,0.18)",
            zIndex: 200, minWidth: "185px", overflow: "hidden" }}>

            <button style={btn}
              onClick={(e) => { e.stopPropagation();
                fetch("http://127.0.0.1:8000/memory/star", { method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ index: idx, starred: !item.starred }) })
                  .then(() => load()); setMenuOpen(null); }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = t.menuHover}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}>
              <span>{item.starred ? "★" : "☆"}</span> {item.starred ? "Unstar" : "Star"}
            </button>

            <button style={btn}
              onClick={(e) => { e.stopPropagation();
                const n = window.prompt("Rename:", item.topic);
                if (n && n.trim()) {
                  fetch("http://127.0.0.1:8000/memory/rename", { method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ index: idx, topic: n.trim() }) })
                    .then(() => load());
                } setMenuOpen(null); }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = t.menuHover}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}>
              <span>✏️</span> Rename
            </button>

            <button style={btn}
              onClick={(e) => { e.stopPropagation(); downloadPdf(item.topic, item.summary); setMenuOpen(null); }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = t.menuHover}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}>
              <span>📄</span> Download PDF
            </button>
            <button style={btn}
              onClick={(e) => { e.stopPropagation(); downloadDocx(item.topic, item.summary); setMenuOpen(null); }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = t.menuHover}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}>
              <span>📝</span> Download Word
            </button>
            <button style={btn}
              onClick={(e) => { e.stopPropagation(); downloadTxt(item.topic, item.summary); setMenuOpen(null); }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = t.menuHover}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}>
              <span>📃</span> Download TXT
            </button>

            <div style={{ height: "1px", backgroundColor: t.menuBorder, margin: "4px 0" }} />

            <button style={{ ...btn, color: "#ef4444" }}
              onClick={(e) => { e.stopPropagation();
                if (window.confirm("Delete this session?")) {
                  fetch(`http://127.0.0.1:8000/memory/${idx}`, { method: "DELETE" }).then(() => load());
                } setMenuOpen(null); }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = t.menuHover}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}>
              <span>🗑️</span> Delete
            </button>
          </div>
        )}
      </div>
    );
  };

  const groups = groupByRecency(items);
  const ORDER = ["Today", "Yesterday", "This Week", "This Month", "Older"];
  // Use indexed items (with _idx) for starred section
  const allIndexed = Object.values(groups).flat();
  const starred = allIndexed.filter((item) => item.starred === true);

  return (
    <div style={{ width: "260px", minWidth: "260px", height: "100vh", display: "flex",
      flexDirection: "column", backgroundColor: t.sidebar, borderRight: `1px solid ${t.sidebarBorder}`, flexShrink: 0 }}>
      <style>{`div:hover .dots-btn { opacity: 1 !important; }`}</style>

      <div style={{ padding: "12px 12px 8px", display: "flex", alignItems: "center",
        justifyContent: "space-between", flexShrink: 0 }}>
        <span style={{ fontSize: "15px", fontWeight: "600", color: t.historyText, display: "flex", alignItems: "center", gap: "8px" }}>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="22" height="22">
            <circle cx="50" cy="50" r="26" fill="none" stroke="#6d28d9" strokeWidth="5"/>
            <circle cx="50" cy="50" r="18" fill="#6d28d9"/>
            <rect x="43" y="43" width="5" height="5" rx="1" fill="white"/>
            <rect x="52" y="43" width="5" height="5" rx="1" fill="white"/>
            <path d="M44 54 Q50 59 56 54" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round"/>
            <circle cx="50" cy="36" r="2.5" fill="none" stroke="white" strokeWidth="2"/>
            <line x1="50" y1="24" x2="50" y2="16" stroke="#6d28d9" strokeWidth="3"/>
            <circle cx="50" cy="13" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
            <line x1="24" y1="50" x2="16" y2="44" stroke="#6d28d9" strokeWidth="3"/>
            <circle cx="13" cy="44" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
            <line x1="24" y1="50" x2="16" y2="56" stroke="#6d28d9" strokeWidth="3"/>
            <circle cx="13" cy="56" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
            <line x1="76" y1="50" x2="84" y2="44" stroke="#6d28d9" strokeWidth="3"/>
            <circle cx="87" cy="44" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
            <line x1="76" y1="50" x2="84" y2="56" stroke="#6d28d9" strokeWidth="3"/>
            <circle cx="87" cy="56" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
            <line x1="33" y1="28" x2="26" y2="19" stroke="#6d28d9" strokeWidth="3"/>
            <circle cx="23" cy="16" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
            <line x1="67" y1="28" x2="74" y2="19" stroke="#6d28d9" strokeWidth="3"/>
            <circle cx="77" cy="16" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
            <line x1="50" y1="76" x2="44" y2="84" stroke="#6d28d9" strokeWidth="3"/>
            <circle cx="44" cy="87" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
            <line x1="50" y1="76" x2="56" y2="84" stroke="#6d28d9" strokeWidth="3"/>
            <circle cx="56" cy="87" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
          </svg>
          Deep Research
        </span>
        <button onClick={onNewChat} title="New chat"
          style={{ width: "32px", height: "32px", borderRadius: "8px", border: "none",
            backgroundColor: "transparent", color: t.historyMeta, cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center" }}>
          <NewChatIcon />
        </button>
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: "4px 0" }}>
        {items.length === 0 && (
          <div style={{ padding: "32px 16px", textAlign: "center", color: t.historyMeta, fontSize: "13px" }}>
            No past sessions yet
          </div>
        )}

        {starred.length > 0 && (
          <div>
            <div style={{ padding: "8px 12px 4px", fontSize: "12px", fontWeight: "600", color: t.sectionLabel }}>
              ★ Starred
            </div>
            {starred.map((item) => renderItem(item, item._idx !== undefined ? item._idx : items.indexOf(item), "starred"))}
          </div>
        )}

        {ORDER.map((group) => {
          const g = groups[group];
          if (!g || g.length === 0) return null;
          return (
            <div key={group}>
              <div style={{ padding: "8px 12px 4px", fontSize: "12px", fontWeight: "600", color: t.sectionLabel }}>
                {group}
              </div>
              {g.map((item) => renderItem(item, item._idx, group))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function JudgeCard({ scores, t }) {
  const dims = ["completeness", "accuracy", "structure", "depth", "actionability"];
  const colors = { 5: "#16a34a", 4: "#65a30d", 3: "#ca8a04", 2: "#ea580c", 1: "#dc2626" };
  return (
    <div style={{ marginTop: "12px", backgroundColor: t.agentBubble,
      border: `1px solid ${t.sidebarBorder}`, borderRadius: "12px", padding: "14px 16px", maxWidth: "360px" }}>
      <div style={{ fontSize: "12px", fontWeight: "600", color: t.historyMeta,
        textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "10px" }}>
        ⚖️ LLM Judge — Quality Breakdown
      </div>
      {dims.map((dim) => {
        const val = scores[dim] || 0;
        const color = colors[val] || "#888";
        return (
          <div key={dim} style={{ marginBottom: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginBottom: "3px" }}>
              <span style={{ color: t.historyText, textTransform: "capitalize" }}>{dim}</span>
              <span style={{ color, fontWeight: "600" }}>{val}/5</span>
            </div>
            <div style={{ height: "5px", borderRadius: "3px", backgroundColor: t.sidebarBorder, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${(val / 5) * 100}%`, backgroundColor: color,
                borderRadius: "3px", transition: "width 0.4s ease" }} />
            </div>
          </div>
        );
      })}
      <div style={{ marginTop: "10px", paddingTop: "10px", borderTop: `1px solid ${t.sidebarBorder}`,
        display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "13px", fontWeight: "600", color: t.historyText }}>Overall</span>
        <span style={{ fontSize: "15px", fontWeight: "700", color: colors[Math.round(scores.overall)] || "#888" }}>
          {scores.overall}/5
        </span>
      </div>
    </div>
  );
}

function DownloadDropdown({ t, dark, messages }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);
  const getText = () => messages.map((m) => `${m.role === "user" ? "You" : "Agent"}:\n${m.text}`).join("\n\n---\n\n");
  const getTopic = () => { const f = messages.find((m) => m.role === "user"); return f ? f.text.slice(0, 60) : "conversation"; };
  const opts = [
    { label: "Download as PDF",  icon: "📄", action: () => downloadPdf(getTopic(), getText()) },
    { label: "Download as Word", icon: "📝", action: () => downloadDocx(getTopic(), getText()) },
    { label: "Download as TXT",  icon: "📃", action: () => downloadTxt(getTopic(), getText()) },
  ];
  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button onClick={() => setOpen((o) => !o)} title="Download conversation"
        style={{ width: "36px", height: "36px", borderRadius: "8px", border: "none",
          backgroundColor: open ? (dark ? "#3f3f3f" : "#ececec") : "transparent",
          color: t.historyMeta, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <DownloadIcon />
      </button>
      {open && (
        <div style={{ position: "absolute", right: 0, top: "42px", backgroundColor: t.menuBg,
          border: `1px solid ${t.menuBorder}`, borderRadius: "12px",
          boxShadow: "0 8px 24px rgba(0,0,0,0.15)", zIndex: 200, minWidth: "190px", overflow: "hidden" }}>
          {opts.map(({ label, icon, action }) => (
            <button key={label} onClick={() => { action(); setOpen(false); }}
              style={{ width: "100%", padding: "11px 16px", border: "none", textAlign: "left",
                backgroundColor: "transparent", color: t.menuText, cursor: "pointer",
                fontSize: "14px", display: "flex", alignItems: "center", gap: "10px", fontFamily: "inherit" }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = t.menuHover}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}>
              <span>{icon}</span> {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dark, setDark] = useState(() => window.matchMedia("(prefers-color-scheme: dark)").matches);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [activeIdx, setActiveIdx] = useState(null);
  const textareaRef = useRef(null);
  const bottomRef = useRef(null);
  const t = dark ? THEMES.dark : THEMES.light;

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 140) + "px";
  };

  const handleKeyDown = (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); runAgent(); } };

  const runAgent = async () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setQuery("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setLoading(true); setActiveIdx(null);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 180000);
    try {
      const res = await fetch("http://127.0.0.1:8000/run", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: trimmed }), signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "agent", text: data.report,
        score: data.is_simple ? null : data.score, fromMemory: data.from_memory,
        judgeScores: data.judge_scores || {} }]);
      setRefreshTrigger((n) => n + 1);
    } catch (err) {
      clearTimeout(timeoutId);
      setMessages((prev) => [...prev, { role: "agent",
        text: err.name === "AbortError" ? "Request timed out after 3 minutes." : `Error: ${err.message}` }]);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", backgroundColor: t.page }}>

      <div style={{ width: sidebarOpen ? "260px" : "0", minWidth: sidebarOpen ? "260px" : "0",
        overflow: "hidden", transition: "width 0.2s ease, min-width 0.2s ease", flexShrink: 0 }}>
        <HistorySidebar t={t} onSelect={(item, idx) => {
            setActiveIdx(idx);
            setMessages([
              { role: "user", text: item.topic },  // original query, not the renamed label
              { role: "agent", text: item.summary, fromMemory: true },
            ]);
          }}
          onNewChat={() => { setMessages([]); setActiveIdx(null); setQuery(""); }}
          refreshTrigger={refreshTrigger} activeIdx={activeIdx}
        />
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", position: "relative", minWidth: 0 }}>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", flexShrink: 0 }}>
          <button onClick={() => setSidebarOpen((o) => !o)} title="Toggle sidebar"
            style={{ width: "36px", height: "36px", borderRadius: "8px", border: "none",
              backgroundColor: "transparent", color: t.historyMeta, cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center" }}>
            <SidebarIcon />
          </button>
          <span style={{ fontSize: "15px", fontWeight: "600", color: t.header }}>Deep Research Agent</span>
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            {messages.some((m) => m.role === "agent" && m.text) && (
              <DownloadDropdown t={t} dark={dark} messages={messages} />
            )}
            <button onClick={() => setDark((d) => !d)} title={dark ? "Light mode" : "Dark mode"}
              style={{ width: "36px", height: "36px", borderRadius: "8px", border: "none",
                backgroundColor: "transparent", color: t.historyMeta, cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center" }}>
              {dark ? <SunIcon /> : <MoonIcon />}
            </button>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "0 max(5%, 24px) 16px",
          display: "flex", flexDirection: "column", gap: "24px" }}>
          {messages.length === 0 && !loading && (
            <div style={{ textAlign: "center", color: t.emptyText, marginTop: "80px" }}>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="56" height="56" style={{ marginBottom: "16px" }}>
                <circle cx="50" cy="50" r="26" fill="none" stroke="#6d28d9" strokeWidth="5"/>
                <circle cx="50" cy="50" r="18" fill="#6d28d9"/>
                <rect x="43" y="43" width="5" height="5" rx="1" fill="white"/>
                <rect x="52" y="43" width="5" height="5" rx="1" fill="white"/>
                <path d="M44 54 Q50 59 56 54" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round"/>
                <circle cx="50" cy="36" r="2.5" fill="none" stroke="white" strokeWidth="2"/>
                <line x1="50" y1="24" x2="50" y2="16" stroke="#6d28d9" strokeWidth="3"/>
                <circle cx="50" cy="13" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
                <line x1="24" y1="50" x2="16" y2="44" stroke="#6d28d9" strokeWidth="3"/>
                <circle cx="13" cy="44" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
                <line x1="24" y1="50" x2="16" y2="56" stroke="#6d28d9" strokeWidth="3"/>
                <circle cx="13" cy="56" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
                <line x1="76" y1="50" x2="84" y2="44" stroke="#6d28d9" strokeWidth="3"/>
                <circle cx="87" cy="44" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
                <line x1="76" y1="50" x2="84" y2="56" stroke="#6d28d9" strokeWidth="3"/>
                <circle cx="87" cy="56" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
                <line x1="33" y1="28" x2="26" y2="19" stroke="#6d28d9" strokeWidth="3"/>
                <circle cx="23" cy="16" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
                <line x1="67" y1="28" x2="74" y2="19" stroke="#6d28d9" strokeWidth="3"/>
                <circle cx="77" cy="16" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
                <line x1="50" y1="76" x2="44" y2="84" stroke="#6d28d9" strokeWidth="3"/>
                <circle cx="44" cy="87" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
                <line x1="50" y1="76" x2="56" y2="84" stroke="#6d28d9" strokeWidth="3"/>
                <circle cx="56" cy="87" r="4" fill="none" stroke="#6d28d9" strokeWidth="3"/>
              </svg>
              <div style={{ fontSize: "28px", fontWeight: "600", color: t.header, marginBottom: "8px" }}>Deep Research Agent</div>
              <div style={{ fontSize: "15px" }}>Ask anything to start a research session</div>
            </div>
          )}
          {messages.map((msg, i) =>
            msg.role === "user" ? (
              <div key={i} style={{ alignSelf: "flex-end", backgroundColor: t.userBubble, color: t.userText,
                padding: "12px 18px", borderRadius: "18px 18px 4px 18px", maxWidth: "75%",
                fontSize: "15px", lineHeight: "1.6", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                {msg.text}
              </div>
            ) : (
              <div key={i} style={{ alignSelf: "flex-start", maxWidth: "85%" }}>
                {msg.fromMemory && (
                  <span style={{ display: "inline-flex", alignItems: "center", gap: "5px",
                    backgroundColor: t.memoryBadgeBg, color: t.memoryBadgeColor,
                    border: `1px solid ${t.memoryBadgeBorder}`, borderRadius: "20px",
                    padding: "2px 10px", fontSize: "12px", fontWeight: "500", marginBottom: "8px" }}>
                    ⚡ Retrieved from past memory
                  </span>
                )}
                <div style={{ backgroundColor: t.agentBubble, color: t.agentText,
                  padding: "16px 20px", borderRadius: "4px 18px 18px 18px",
                  fontSize: "15px", lineHeight: "1.7", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {msg.text}
                </div>
                {msg.score && (
                  <span style={{ display: "inline-block", marginTop: "8px", backgroundColor: t.scoreBg,
                    color: t.scoreGreen, border: `1px solid ${t.scoreBorder}`, borderRadius: "20px",
                    padding: "3px 12px", fontSize: "13px", fontWeight: "500" }}>
                    Quality score: {msg.score}/10
                  </span>
                )}
                {msg.judgeScores && Object.keys(msg.judgeScores).length > 0 && (
                  <JudgeCard scores={msg.judgeScores} t={t} />
                )}
              </div>
            )
          )}
          {loading && <TypingDots t={t} />}
          <div ref={bottomRef} />
        </div>

        <div style={{ padding: "12px max(5%, 24px) 24px", backgroundColor: t.inputWrapper, flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "flex-end", backgroundColor: t.inputBg,
            borderRadius: "16px", padding: "10px 12px 10px 16px",
            boxShadow: dark ? "0 0 0 1px #3f3f3f" : "0 0 0 1px #e5e5e5", gap: "8px" }}>
            <textarea ref={textareaRef} rows={1}
              style={{ flex: 1, border: "none", outline: "none", resize: "none", fontSize: "15px",
                color: t.inputText, backgroundColor: "transparent", lineHeight: "1.6",
                maxHeight: "140px", overflowY: "auto", padding: "2px 0", fontFamily: "inherit" }}
              placeholder="Message Deep Research Agent..."
              value={query}
              onChange={(e) => { setQuery(e.target.value); autoResize(); }}
              onKeyDown={handleKeyDown}
            />
            <button onClick={runAgent} disabled={!query.trim() || loading}
              style={{ width: "34px", height: "34px", borderRadius: "8px", border: "none",
                backgroundColor: query.trim() && !loading ? t.sendBtn : (dark ? "#3f3f3f" : "#d9d9e3"),
                cursor: query.trim() && !loading ? "pointer" : "default",
                display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <SendIcon color={query.trim() && !loading ? t.sendIcon : (dark ? "#666" : "#aaa")} />
            </button>
          </div>
          <div style={{ textAlign: "center", fontSize: "12px", color: t.emptyText, marginTop: "8px" }}>
            Deep Research Agent can make mistakes. Verify important information.
          </div>
        </div>
      </div>
    </div>
  );
}
