import React, { useEffect, useState } from "react"

const CHIPS = ['show merged PRs', 'open issues', 'what is being worked on', 'who are the top contributors', 'explain #990','show incidents']

export default function Home() {
  const [started, setStarted] = useState(false)
  const [q, setQ] = useState("")
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState("")
  const [owner, setOwner] = useState("withcoral")
  const [repo, setRepo] = useState("coral")

  const lines = [
    "Coral understands your engineering system.",
    "Coral connects GitHub, incidents, and pull requests.",
    "Coral helps teams investigate faster with AI.",
    "Ask questions about your codebase in natural language."
  ]

  const [lineIndex, setLineIndex] = useState(0)
  const [displayed, setDisplayed] = useState("")
  const [deleting, setDeleting] = useState(false)
  const [prExplain, setPrExplain] = useState(null)
  const [prLoading, setPrLoading] = useState(false)

  useEffect(() => {
    const current = lines[lineIndex]
    const timeout = setTimeout(() => {
      if (!deleting) {
        setDisplayed(current.slice(0, displayed.length + 1))
        if (displayed.length + 1 === current.length) {
          setTimeout(() => setDeleting(true), 1500)
        }
      } else {
        setDisplayed(current.slice(0, displayed.length - 1))
        if (displayed.length === 0) {
          setDeleting(false)
          setLineIndex((prev) => (prev + 1) % lines.length)
        }
      }
    }, deleting ? 30 : 50)
    return () => clearTimeout(timeout)
  }, [displayed, deleting, lineIndex])

  async function ask(query) {
    const question = query || q
    if (!question.trim()) return
    const explainMatch = question.match(/explain\s+#?(\d+)/i)
    if (explainMatch) {
      const prNumber = parseInt(explainMatch[1])
      setQ("")
      await explainPR(prNumber)
      return
    }
    if (!question.trim()) return
    setQ(question)
    setLoading(true)
    setRes(null)
    setLoadingStep("Querying Coral SQL...")
    try {
      const r = await fetch("https://coralmind-lite-backend.onrender.com/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, owner, repo })
      })
      setLoadingStep("Generating AI summary...")
      const data = await r.json()
      setRes({ ...data, question })
    } catch {
      setRes({ question, summary: "Backend not reachable. Is FastAPI running on port 8000?" })
    }
    setLoading(false)
    setLoadingStep("")
  }

  async function explainPR(number) {
    setPrLoading(true)
    setPrExplain({ number, explanation: null })
    try {
      const r = await fetch("https://coralmind-lite-backend.onrender.com/explain-pr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ number: parseInt(number), owner, repo })
      })
      const data = await r.json()
      setPrExplain({ number, explanation: data.explanation })
    } catch {
      setPrExplain({ number, explanation: "Could not fetch explanation." })
    }
    setPrLoading(false)
  }

  const badge = s => {
    const m = {
      open: { bg: "rgba(52,211,153,.1)", color: "#34d399" },
      merged: { bg: "rgba(167,139,250,.12)", color: "#a78bfa" },
      closed: { bg: "rgba(248,113,113,.1)", color: "#f87171" },
    }
    const c = m[s] || m.open
    return { fontSize: 10, padding: "2px 8px", borderRadius: 20, fontWeight: 500, background: c.bg, color: c.color }
  }

  const block = { background: "#0d0d14", border: "1px solid #1a1a2a", borderRadius: 10, overflow: "hidden", marginBottom: 0 }
  const bhead = color => ({ padding: "9px 14px", borderBottom: "1px solid #16161f", display: "flex", alignItems: "center", gap: 7, fontSize: 11, fontFamily: "monospace", letterSpacing: ".08em", fontWeight: 500, color })
  const dot = bg => ({ width: 7, height: 7, borderRadius: "50%", background: bg, flexShrink: 0 })
  const brow = { display: "flex", alignItems: "center", gap: 9, padding: "9px 16px", borderBottom: "1px solid #0f0f0f", fontSize: 12, cursor: "default", transition: "background .1s" }

  const githubCount = res?.correlated_data?.length || 0
  const incidentCount = res?.incidents?.length || 0
  const issueCount = res?.open_issues?.length || 0

  return (
    <div style={{
      minHeight: "100vh",
      background: "#050505",
      color: "#fff",
      fontFamily: '-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',
      overflow: "hidden",
      position: "relative"
    }}>
      <div style={{
        position: "absolute",
        top: -300,
        left: "50%",
        transform: "translateX(-50%)",
        width: 1000,
        height: 1000,
        borderRadius: "50%",
        background: "rgba(124,58,237,.13)",
        filter: "blur(140px)"
      }} />

      <div style={{
        position: "relative",
        zIndex: 2,
        padding: "30px 40px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: "linear-gradient(135deg, #7c3aed, #4f46e5)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18, boxShadow: "0 0 20px rgba(124,58,237,0.4)"
          }}>
            ◈
          </div>
          <span style={{ fontSize: 22, fontWeight: 600, letterSpacing: "-0.04em" }}>CoralMind</span>
        </div>
        {started && (
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              value={owner}
              onChange={e => setOwner(e.target.value)}
              placeholder="owner"
              style={{ background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.08)", borderRadius: 8, padding: "8px 12px", fontSize: 13, color: "#a0a0c0", width: 90, outline: "none", fontFamily: "inherit" }}
            />
            <span style={{ color: "#3a3a5a" }}>/</span>
            <input
              value={repo}
              onChange={e => setRepo(e.target.value)}
              placeholder="repo"
              style={{ background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.08)", borderRadius: 8, padding: "8px 12px", fontSize: 13, color: "#a0a0c0", width: 90, outline: "none", fontFamily: "inherit" }}
            />
          </div>
        )}
      </div>

      {!started ? (
        <div style={{
          position: "relative",
          zIndex: 2,
          minHeight: "85vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: "0 24px"
        }}>
          <div style={{ maxWidth: 1300 }}>
            <div style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 10,
              padding: "12px 20px",
              borderRadius: 999,
              background: "rgba(255,255,255,.03)",
              border: "1px solid rgba(255,255,255,.06)",
              backdropFilter: "blur(20px)",
              marginBottom: 36
            }}>
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#7c3aed", boxShadow: "0 0 20px #7c3aed" }} />
              <span style={{ color: "#a1a1aa", fontSize: 14, letterSpacing: ".12em", textTransform: "uppercase" }}>
                AI Engineering Workspace
              </span>
            </div>

            <h1 style={{ fontSize: "clamp(70px,11vw,160px)", lineHeight: 0.9, letterSpacing: "-0.08em", fontWeight: 600, margin: 0 }}>
              Understand your<br />
              engineering system
              <span style={{ color: "#7c3aed" }}>.</span>
            </h1>

            <div style={{ height: 90, marginTop: 42, display: "flex", justifyContent: "center", alignItems: "center" }}>
              <p style={{ color: "#71717a", fontSize: 28, lineHeight: 1.8, maxWidth: 900 }}>
                {displayed}<span style={{ color: "#7c3aed" }}>|</span>
              </p>
            </div>

            <div style={{ marginTop: 55 }}>
              <button
                onClick={() => setStarted(true)}
                style={{ background: "#fff", color: "#000", border: "none", padding: "20px 42px", borderRadius: 22, fontSize: 18, fontWeight: 600, cursor: "pointer", boxShadow: "0 10px 40px rgba(255,255,255,.08)" }}
              >
                Get Started →
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ position: "relative", zIndex: 2, maxWidth: 1000, margin: "0 auto", padding: "40px 24px 80px" }}>

          <div style={{ textAlign: "center", marginBottom: 40 }}>
            <h1 style={{ fontSize: "clamp(48px,6vw,80px)", lineHeight: 0.95, letterSpacing: "-0.06em", fontWeight: 600, margin: 0, marginBottom: 16 }}>
              Ask your codebase<br />anything<span style={{ color: "#7c3aed" }}>.</span>
            </h1>
          </div>

          <div style={{ background: "rgba(255,255,255,.03)", border: "1px solid rgba(255,255,255,.05)", borderRadius: 30, padding: 16, display: "flex", alignItems: "center", gap: 16, backdropFilter: "blur(20px)", marginBottom: 16 }}>
            <div style={{ color: "#666", fontSize: 24, paddingLeft: 8 }}>⌘</div>
            <input
              value={q}
              onChange={e => setQ(e.target.value)}
              onKeyDown={e => e.key === "Enter" && ask()}
              placeholder="Why are incidents increasing this week?"
              style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: "#fff", fontSize: 20, fontFamily: "inherit" }}
            />
            <button
              onClick={() => ask()}
              disabled={loading}
              style={{ width: 58, height: 58, borderRadius: 18, border: "none", background: loading ? "#4c1d95" : "#7c3aed", color: "#fff", fontSize: 22, cursor: "pointer" }}
            >
              {loading ? "…" : "↑"}
            </button>
          </div>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 24, justifyContent: "center" }}>
            {CHIPS.map(c => (
              <button key={c} onClick={() => ask(c)}
                style={{ padding: "8px 16px", borderRadius: 999, border: "1px solid rgba(255,255,255,.08)", background: "rgba(255,255,255,.03)", color: "#71717a", fontSize: 13, cursor: "pointer", fontFamily: "inherit" }}>
                {c}
              </button>
            ))}
          </div>

          {loading && (
            <div style={{ ...block, padding: 24, textAlign: "center", marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
                <div style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid #7c3aed", borderTopColor: "#a78bfa", animation: "spin 0.8s linear infinite" }} />
                <div style={{ color: "#5050a0", fontFamily: "monospace", fontSize: 12 }}>{loadingStep}</div>
              </div>
            </div>
          )}

          {res && !loading && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>

              <div style={{ alignSelf: "flex-end", background: "#1a1530", border: "1px solid #2a2045", color: "#a78bfa", borderRadius: "10px 10px 2px 10px", padding: "9px 14px", fontSize: 13, maxWidth: "70%" }}>
                {res.question}
              </div>

              {/* Stats — only show when there is data */}
              {(githubCount > 0 || incidentCount > 0 || issueCount > 0) && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
                  {[
                    { n: githubCount, l: 'github results', c: '#34d399' },
                    { n: incidentCount, l: 'incidents', c: '#f87171' },
                    { n: issueCount, l: 'open issues', c: '#fbbf24' }
                  ].map(s => (
                    <div key={s.l} style={{ background: "#0d0d14", border: "1px solid #1a1a2a", borderRadius: 10, padding: "14px 13px", textAlign: "center", position: "relative", overflow: "hidden" }}>
                      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: s.c }} />
                      <div style={{ fontSize: 24, fontWeight: 600, fontFamily: "monospace", color: s.c, lineHeight: 1, marginBottom: 4 }}>{s.n}</div>
                      <div style={{ fontSize: 10, color: "#2a2a3a", letterSpacing: ".05em", textTransform: "uppercase" }}>{s.l}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Release Analytics — only show when there is data */}
              {(res.correlated_data?.length > 0 || res.deployments?.length > 0) && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 8, marginTop: 4 }}>
                  {[
                    { label: "merged PRs", value: res.correlated_data?.filter(r => r.merged_at)?.length || 0, color: "#a78bfa", icon: "⬆" },
                    { label: "sources", value: res.sources_used?.length || 0, color: "#fbbf24", icon: "🔗" },
                    { label: "deployments", value: res.deployments?.length || 0, color: "#34d399", icon: "🚀" },
                    { label: "contributors", value: res.correlated_data?.filter(r => r.login)?.length || 0, color: "#60a0f0", icon: "👤" }
                  ].map(s => (
                    <div key={s.label} style={{ background: "#0d0d14", border: "1px solid #1a1a2a", borderRadius: 10, padding: "12px 13px", textAlign: "center", position: "relative", overflow: "hidden" }}>
                      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: s.color }} />
                      <div style={{ fontSize: 18, marginBottom: 4 }}>{s.icon}</div>
                      <div style={{ fontSize: 20, fontWeight: 500, fontFamily: "monospace", color: s.color }}>{s.value}</div>
                      <div style={{ fontSize: 11, color: "#2a2a3a", marginTop: 2 }}>{s.label}</div>
                    </div>
                  ))}
                </div>
              )}

              {res.sources_used?.length > 0 && (
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {res.sources_used.map(s => (
                    <span key={s} style={{ fontSize: 10, padding: "2px 10px", borderRadius: 20, background: "rgba(124,58,237,.1)", color: "#a78bfa", border: "1px solid rgba(124,58,237,.2)" }}>
                      {s}
                    </span>
                  ))}
                </div>
              )}

              {(res.summary || prExplain) && (
                <div style={{ background: "linear-gradient(135deg,rgba(124,58,237,.08),rgba(67,56,202,.04))", border: "1px solid rgba(124,58,237,.2)", borderRadius: 12, overflow: "hidden" }}>
                  <div style={{ ...bhead("#a78bfa"), justifyContent: "space-between", borderBottom: "1px solid rgba(124,58,237,.12)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                      <span style={dot("#a78bfa")} />
                      {prExplain ? `PR #${prExplain.number} — AI EXPLANATION` : "AI SUMMARY"}
                    </div>
                    {prExplain && (
                      <span onClick={() => setPrExplain(null)} style={{ cursor: "pointer", color: "#555", fontSize: 14 }}>✕</span>
                    )}
                  </div>
                  <p style={{ padding: "12px 14px", fontSize: 13, color: "#9090c0", lineHeight: 1.85, margin: 0 }}>
                    {prExplain ? (prLoading ? "Analyzing PR..." : prExplain.explanation) : res.summary}
                  </p>
                </div>
              )}

              {res.incidents?.length > 0 && (
                <div style={{ ...block, borderLeft: "2px solid #f87171" }}>
                  <div style={bhead("#f87171")}><span style={dot("#f87171")} />INCIDENTS</div>
                  {res.incidents.map((inc, i) => (
                    <div key={inc.id} style={{ ...brow, flexDirection: "column", alignItems: "flex-start", borderBottom: i === res.incidents.length - 1 ? "none" : "1px solid #16161f" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", width: "100%", marginBottom: 4 }}>
                        <span style={{ fontFamily: "monospace", fontSize: 11, color: "#f87171" }}>{inc.id}</span>
                        <span style={{
                          fontSize: 10, padding: "2px 8px", borderRadius: 20, fontWeight: 500,
                          background: inc.severity === "high" ? "rgba(248,113,113,.1)" : inc.severity === "medium" ? "rgba(251,191,36,.1)" : "rgba(100,100,100,.1)",
                          color: inc.severity === "high" ? "#f87171" : inc.severity === "medium" ? "#fbbf24" : "#6b7280"
                        }}>{inc.severity}</span>
                      </div>
                      <span style={{ color: "#7070a0", fontSize: 12 }}>{inc.description}</span>
                      <div style={{ display: "flex", gap: 12, marginTop: 4, fontSize: 10, color: "#3a3a5a" }}>
                        <span>service: {inc.service}</span>
                        {inc.issue_number && <span>issue #{inc.issue_number}</span>}
                        <span style={{ color: inc.status === "open" ? "#f87171" : inc.status === "investigating" ? "#fbbf24" : "#34d399" }}>{inc.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {res.deployments?.length > 0 && (
                <div style={{ ...block, borderLeft: "2px solid #34d399" }}>
                  <div style={bhead("#34d399")}><span style={dot("#34d399")} />DEPLOYMENTS</div>
                  {res.deployments.map((dep, i) => (
                    <div key={dep.id} style={{ ...brow, flexDirection: "column", alignItems: "flex-start", borderBottom: i === res.deployments.length - 1 ? "none" : "1px solid #16161f" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", width: "100%", marginBottom: 4 }}>
                        <span style={{ fontFamily: "monospace", fontSize: 11, color: "#34d399" }}>{dep.id}</span>
                        <span style={{
                          fontSize: 10, padding: "2px 8px", borderRadius: 20, fontWeight: 500,
                          background: dep.status === "hotfix" ? "rgba(251,191,36,.1)" : "rgba(52,211,153,.1)",
                          color: dep.status === "hotfix" ? "#fbbf24" : "#34d399"
                        }}>{dep.status}</span>
                      </div>
                      <span style={{ color: "#7070a0", fontSize: 12 }}>PR {dep.version} — {dep.service}</span>
                      <div style={{ display: "flex", gap: 12, marginTop: 4, fontSize: 10, color: "#3a3a5a" }}>
                        <span>env: {dep.environment}</span>
                        <span>by: {dep.deployed_by}</span>
                        {dep.timestamp && <span>{dep.timestamp.slice(0, 10)}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {res.correlated_data?.length > 0 && res.correlated_data[0]?.login && (
                <div style={{ ...block, borderLeft: "2px solid #60a0f0" }}>
                  <div style={bhead("#60a0f0")}><span style={dot("#60a0f0")} />TOP CONTRIBUTORS</div>
                  {res.correlated_data.filter(row => row.number && row.title).map((row, i, arr) => (
                    <div key={i} style={{ ...brow, justifyContent: "space-between", borderBottom: i === res.correlated_data.length - 1 ? "none" : "1px solid #16161f" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{
                          width: 24, height: 24, borderRadius: "50%",
                          background: i === 0 ? "#fbbf24" : i === 1 ? "#9ca3af" : i === 2 ? "#b45309" : "#1a1a2a",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontSize: 10, fontWeight: 700, color: i < 3 ? "#000" : "#3a3a5a"
                        }}>
                          {i + 1}
                        </div>
                        <span
                          onClick={() => ask(`prs by ${row.login}`)}
                          style={{ color: "#a78bfa", fontFamily: "monospace", fontSize: 12, cursor: "pointer", textDecoration: "underline" }}
                        >
                          @{row.login}
                        </span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{
                          height: 4, borderRadius: 2, background: "#7c3aed",
                          width: Math.max(20, (row.contributions / res.correlated_data[0].contributions) * 80)
                        }} />
                        <span style={{ color: "#3a3a5a", fontSize: 11, minWidth: 60, textAlign: "right" }}>
                          {row.contributions} commits
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {res.correlated_data?.length > 0 && !res.correlated_data[0]?.login && (
                <div style={{ ...block, borderLeft: "2px solid #34d399" }}>
                  <div style={bhead("#34d399")}><span style={dot("#34d399")} />GITHUB DATA</div>
                  {res.correlated_data.filter(row => row.number && row.title).map((row, i, arr) => (
                    <div key={i} style={{ ...brow, borderBottom: i === res.correlated_data.length - 1 ? "none" : "1px solid #16161f" }}>
                      <span style={dot(row.state === "open" ? "#34d399" : "#a78bfa")} />
                      <span
                        onClick={() => explainPR(row.number)}
                        style={{ fontFamily: "monospace", fontSize: 11, minWidth: 34, color: "#34d399", cursor: "pointer", textDecoration: "underline" }}
                      >
                        #{row.number}
                      </span>
                      <span style={{ flex: 1, color: "#7070a0" }}>{row.title}</span>
                      {row.state && <span style={badge(row.state)}>{row.state}</span>}
                      {row.merged_at && <span style={badge("merged")}>merged</span>}
                    </div>
                  ))}
                </div>
              )}

              {res.open_issues?.length > 0 && (
                <div style={{ ...block, borderLeft: "2px solid #fbbf24" }}>
                  <div style={bhead("#fbbf24")}><span style={dot("#fbbf24")} />SUPPORTING DATA</div>
                  {res.open_issues.filter(row => row.number && row.title).map((row, i, arr) => (
                    <div key={i} style={{ ...brow, borderBottom: i === arr.length - 1 ? "none" : "1px solid #16161f" }}>
                      <span style={dot("#fbbf24")} />
                      <span style={{ fontFamily: "monospace", fontSize: 11, minWidth: 34, color: "#fbbf24" }}>#{row.number}</span>
                      <span style={{ flex: 1, color: "#7070a0" }}>{row.title}</span>
                    </div>
                  ))}
                </div>
              )}

              {res.correlated_data?.length === 0 && res.open_issues?.length === 0 && (
                <div style={{ ...block, padding: 24, textAlign: "center" }}>
                  <div style={{ color: "#3a3a5a", fontFamily: "monospace", fontSize: 12 }}>
                    No repository data found. Check owner/repo and try again.
                  </div>
                </div>
              )}

              {res.sql_queries?.length > 0 && (
                <details style={{ ...block, borderLeft: "2px solid #4a90d9" }}>
                  <summary style={{ ...bhead("#60a0f0"), cursor: "pointer", listStyle: "none" }}>
                    <span style={dot("#60a0f0")} />SQL QUERIES (click to expand)
                  </summary>
                  {res.sql_queries.map((q, i) => (
                    <pre key={i} style={{ background: "#07070e", padding: "11px 14px", fontFamily: "monospace", fontSize: 12, color: "#f0c060", whiteSpace: "pre-wrap", wordBreak: "break-all", lineHeight: 1.7, margin: 0, borderTop: "1px solid #16161f" }}>{q}</pre>
                  ))}
                </details>
              )}

            </div>
          )}
        </div>
      )}
    </div>
  )
}