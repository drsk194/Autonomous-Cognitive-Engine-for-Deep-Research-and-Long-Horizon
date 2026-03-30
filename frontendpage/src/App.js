import { useState, useRef, useEffect, useCallback } from "react";

const THEMES = {
  light: {
    page: "#f5f0e8", sidebar: "#ede8e0", sidebarBorder: "#ddd8ce",
    header: "#1a1a1a", subtitle: "#888", userBubble: "#1a1a1a", userText: "#fff",
    agentBubble: "#fff", agentText: "#1a1a1a", inputBg: "#fff", inputText: "#1a1a1a",
    inputWrapper: "#f5f0e8", sendBtn: "#1a1a1a", sendIcon: "#fff",
    thinkingBubble: "#fff", emptyText: "#bbb", toggleBg: "#e8e3db", toggleColor: "#555",
    historyItem: "#fff", historyItemHover: "#f0ebe3", historyText: "#1a1a1a",
    historyMeta: "#999", historyBorder: "#e8e3db", taskDone: "#16a34a", taskPending: "#888",
    sectionTitle: "#555",
  },
  dark: {
    page: "#0f0f0f", sidebar: "#161616", sidebarBorder: "#2a2a2a",
    header: "#f0f0f0", subtitle: "#666", userBubble: "#2a2a2a", userText: "#f0f0f0",
    agentBubble: "#1c1c1c", agentText: "#e8e8e8", inputBg: "#1c1c1c", inputText: "#f0f0f0",
    inputWrapper: "#0f0f0f", sendBtn: "#f0f0f0", sendIcon: "#0f0f0f",
    thinkingBubble: "#1c1c1c", emptyText: "#444", toggleBg: "#2a2a2a", toggleColor: "#aaa",
    historyItem: "#1c1c1c", historyItemHover: "#252525", historyText: "#e0e0e0",
    historyMeta: "#666", historyBorder: "#2a2a2a", taskDone: "#4ade80", taskPending: "#666",
    sectionTitle: "#888",
  },
};

function SendIcon({ color }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color}
      strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}
function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}
function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" />
      <line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
      <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
      <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  );
}
function HistoryIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1 4 1 10 7 10" /><path d="M3.51 15a9 9 0 1 0 .49-4.95" />
    </svg>
  );
}

function TypingDots({ t }) {
  return (
    <div style={{ alignSelf: "flex-start", backgroundColor: t.thinkingBubble, padding: "14px 18px",
      borderRadius: "18px 18px 18px 4px", boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
      display: "flex", alignItems: "center", gap: "8px" }}>
      <style>{`@keyframes bounce{0%,80%,100%{transform:translateY(0);opacity:.3}40%{transform:translateY(-5px);opacity:1}}`}</style>
      {[0, 0.2, 0.4].map((d, i) => (
        <div key={i} style={{ width: "7px", height: "7px", borderRadius: "50%",
          backgroundColor: "#888", animation: "bounce 1.2s infinite", animationDelay: `${d}s` }} />
      ))}
    </div>
  );
}

function HistorySidebar({ t, onSelect, refreshTrigger }) {
  const [items, setItems] = useState([]);
  const [expanded, setExpanded] = useState(null);

  const load = useCallback(() => {
    fetch("http://127.0.0.1:8000/memory")
      .then((r) => r.json())
      .then(setItems)
      .catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load, refreshTrigger]);

  const agentColor = { researcher: "#3b82f6", analyst: "#f59e0b", writer: "#8b5cf6", summarizer: "#10b981" };

  return (
    <div style={{ width: "280px", minWidth: "280px", height: "100vh", overflowY: "auto",
      backgroundColor: t.sidebar, borderRight: `1px solid ${t.sidebarBorder}`,
      display: "flex", flexDirection: "column", flexShrink: 0 }}>

      <div style={{ padding: "20px 16px 12px", borderBottom: `1px solid ${t.sidebarBorder}` }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", color: t.sectionTitle, fontSize: "13px", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          <HistoryIcon /> Past Sessions ({items.length})
        </div>
      </div>

      {items.length === 0 && (
        <div style={{ padding: "24px 16px", color: t.historyMeta, fontSize: "13px", textAlign: "center" }}>
          No saved sessions yet
        </div>
      )}

      <div style={{ flex: 1, overflowY: "auto" }}>
        {items.map((item, i) => (
          <div key={i} style={{ borderBottom: `1px solid ${t.historyBorder}` }}>
            {/* Session header */}
            <div
              onClick={() => setExpanded(expanded === i ? null : i)}
              style={{ padding: "12px 16px", cursor: "pointer", backgroundColor: expanded === i ? t.historyItemHover : "transparent",
                transition: "background-color 0.15s" }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = t.historyItemHover}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = expanded === i ? t.historyItemHover : "transparent"}
            >
              <div style={{ fontSize: "13px", fontWeight: "500", color: t.historyText,
                overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box",
                WebkitLineClamp: 2, WebkitBoxOrient: "vertical", lineHeight: "1.4", marginBottom: "6px" }}>
                {item.topic}
              </div>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {(item.todos || []).slice(0, 3).map((todo, j) => (
                  <span key={j} style={{ fontSize: "11px", color: todo.status === "completed" ? t.taskDone : t.taskPending }}>
                    {todo.status === "completed" ? "✓" : "○"} {todo.task.split(" ").slice(0, 3).join(" ")}…
                  </span>
                ))}
              </div>
            </div>

            {/* Expanded detail */}
            {expanded === i && (
              <div style={{ backgroundColor: t.historyItem, padding: "0 16px 14px" }}>

                {/* Tasks */}
                <div style={{ fontSize: "11px", fontWeight: "600", color: t.sectionTitle,
                  textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "8px", marginTop: "4px" }}>
                  Tasks
                </div>
                {(item.todos || []).map((todo, j) => (
                  <div key={j} style={{ display: "flex", gap: "8px", marginBottom: "5px", alignItems: "flex-start" }}>
                    <span style={{ color: todo.status === "completed" ? t.taskDone : t.taskPending, fontSize: "12px", marginTop: "1px", flexShrink: 0 }}>
                      {todo.status === "completed" ? "✓" : "○"}
                    </span>
                    <span style={{ fontSize: "12px", color: t.historyText, lineHeight: "1.4" }}>{todo.task}</span>
                  </div>
                ))}

                {/* Delegation log */}
                {item.delegation_log && item.delegation_log.length > 0 && (
                  <>
                    <div style={{ fontSize: "11px", fontWeight: "600", color: t.sectionTitle,
                      textTransform: "uppercase", letterSpacing: "0.05em", margin: "10px 0 6px" }}>
                      Delegations
                    </div>
                    {item.delegation_log.map((entry, j) => {
                      const agent = entry.split("->")[1]?.split(":")[0]?.trim() || "agent";
                      return (
                        <div key={j} style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                          <span style={{ fontSize: "10px", fontWeight: "600", padding: "1px 7px",
                            borderRadius: "10px", backgroundColor: agentColor[agent] + "22",
                            color: agentColor[agent] || t.historyMeta, textTransform: "capitalize" }}>
                            {agent}
                          </span>
                          <span style={{ fontSize: "11px", color: t.historyMeta, overflow: "hidden",
                            textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {entry.split(":")[1]?.trim() || ""}
                          </span>
                        </div>
                      );
                    })}
                  </>
                )}

                {/* Load report button */}
                <button
                  onClick={() => onSelect(item)}
                  style={{ marginTop: "12px", width: "100%", padding: "7px", borderRadius: "8px",
                    border: `1px solid ${t.historyBorder}`, backgroundColor: "transparent",
                    color: t.historyText, fontSize: "12px", cursor: "pointer", fontFamily: "inherit" }}
                >
                  Load report →
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dark, setDark] = useState(() => window.matchMedia("(prefers-color-scheme: dark)").matches);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);
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

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); runAgent(); }
  };

  const runAgent = async () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;
    setMessages((prev) => [...prev, { role: "user", text: trimmed }]);
    setQuery("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setLoading(true);
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
      setMessages((prev) => [...prev, { role: "agent", text: data.report, score: data.score, fromMemory: data.from_memory }]);
      setRefreshTrigger((n) => n + 1); // refresh sidebar after new result
    } catch (err) {
      clearTimeout(timeoutId);
      setMessages((prev) => [...prev, { role: "agent",
        text: err.name === "AbortError" ? "Request timed out after 3 minutes." : `Error: ${err.message}` }]);
    }
    setLoading(false);
  };

  const handleSelectMemory = (item) => {
    setMessages([
      { role: "user", text: item.topic },
      { role: "agent", text: item.summary, score: null, fromMemory: true },
    ]);
  };

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden",
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      backgroundColor: t.page, transition: "background-color 0.2s" }}>

      {/* Sidebar */}
      <div style={{ width: sidebarOpen ? "280px" : "0", minWidth: sidebarOpen ? "280px" : "0",
        overflow: "hidden", transition: "width 0.25s ease, min-width 0.25s ease", flexShrink: 0 }}>
        <HistorySidebar t={t} onSelect={handleSelectMemory} refreshTrigger={refreshTrigger} />
      </div>

      {/* Main chat area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", position: "relative" }}>

        {/* Sidebar toggle — top left */}
        <button onClick={() => setSidebarOpen((o) => !o)}
          title={sidebarOpen ? "Hide history" : "Show history"}
          style={{ position: "absolute", top: "16px", left: "16px", width: "36px", height: "36px",
            borderRadius: "50%", border: "none", backgroundColor: t.toggleBg, color: t.toggleColor,
            cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
            zIndex: 10, transition: "background-color 0.2s" }}>
          <HistoryIcon />
        </button>

        {/* Theme toggle — top right */}
        <button onClick={() => setDark((d) => !d)} title={dark ? "Light mode" : "Dark mode"}
          style={{ position: "absolute", top: "16px", right: "20px", width: "36px", height: "36px",
            borderRadius: "50%", border: "none", backgroundColor: t.toggleBg, color: t.toggleColor,
            cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
            zIndex: 10, transition: "background-color 0.2s" }}>
          {dark ? <SunIcon /> : <MoonIcon />}
        </button>

        {/* Header */}
        <div style={{ textAlign: "center", padding: "40px 24px 0", flexShrink: 0 }}>
          <h1 style={{ fontSize: "26px", fontWeight: "600", color: t.header, margin: "0 0 6px" }}>
            Deep Research Agent
          </h1>
          <p style={{ fontSize: "14px", color: t.subtitle, margin: "0 0 24px" }}>
            Autonomous multi-step research powered by LangGraph
          </p>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "0 10%", display: "flex",
          flexDirection: "column", gap: "20px" }}>
          {messages.length === 0 && !loading && (
            <div style={{ textAlign: "center", color: t.emptyText, marginTop: "60px", fontSize: "15px" }}>
              Ask anything or load a past session from the sidebar
            </div>
          )}
          {messages.map((msg, i) =>
            msg.role === "user" ? (
              <div key={i} style={{ alignSelf: "flex-end", backgroundColor: t.userBubble, color: t.userText,
                padding: "12px 16px", borderRadius: "18px 18px 4px 18px", maxWidth: "80%",
                fontSize: "15px", lineHeight: "1.5", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                {msg.text}
              </div>
            ) : (
              <div key={i}>
                {msg.fromMemory && (
                  <div style={{ fontSize: "12px", color: t.historyMeta, marginBottom: "6px",
                    paddingLeft: "4px", display: "flex", alignItems: "center", gap: "5px" }}>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: "5px",
                      backgroundColor: dark ? "#1a2a1a" : "#f0fdf4",
                      color: dark ? "#4ade80" : "#16a34a",
                      border: `1px solid ${dark ? "#2d4a2d" : "#bbf7d0"}`,
                      borderRadius: "20px", padding: "3px 10px", fontSize: "12px", fontWeight: "500" }}>
                      ⚡ Retrieved from past memory
                    </span>
                  </div>
                )}
                <div style={{ alignSelf: "flex-start", backgroundColor: t.agentBubble, color: t.agentText,
                  padding: "16px 20px", borderRadius: "18px 18px 18px 4px", maxWidth: "90%",
                  fontSize: "15px", lineHeight: "1.6", whiteSpace: "pre-wrap", wordBreak: "break-word",
                  boxShadow: "0 1px 4px rgba(0,0,0,0.08)" }}>
                  {msg.text}
                </div>
                {msg.score && (
                  <div style={{ paddingLeft: "4px", marginTop: "8px" }}>
                    <span style={{ display: "inline-block", backgroundColor: "#f0fdf4", color: "#16a34a",
                      border: "1px solid #bbf7d0", borderRadius: "20px", padding: "3px 12px",
                      fontSize: "13px", fontWeight: "500" }}>
                      Quality score: {msg.score}/10
                    </span>
                  </div>
                )}
              </div>
            )
          )}
          {loading && <TypingDots t={t} />}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ padding: "16px 10% 28px", backgroundColor: t.inputWrapper, flexShrink: 0,
          transition: "background-color 0.2s" }}>
          <div style={{ display: "flex", alignItems: "flex-end", backgroundColor: t.inputBg,
            borderRadius: "24px", padding: "10px 12px 10px 16px",
            boxShadow: "0 2px 12px rgba(0,0,0,0.10)", gap: "8px", transition: "background-color 0.2s" }}>
            <textarea ref={textareaRef} rows={1}
              style={{ flex: 1, border: "none", outline: "none", resize: "none", fontSize: "15px",
                color: t.inputText, backgroundColor: "transparent", lineHeight: "1.5",
                maxHeight: "140px", overflowY: "auto", padding: "4px 0", fontFamily: "inherit" }}
              placeholder="Reply..."
              value={query}
              onChange={(e) => { setQuery(e.target.value); autoResize(); }}
              onKeyDown={handleKeyDown}
            />
            <button onClick={runAgent} title="Send"
              style={{ width: "34px", height: "34px", borderRadius: "50%", border: "none",
                backgroundColor: t.sendBtn, cursor: "pointer", display: "flex",
                alignItems: "center", justifyContent: "center", flexShrink: 0,
                transition: "background-color 0.2s" }}>
              <SendIcon color={t.sendIcon} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
