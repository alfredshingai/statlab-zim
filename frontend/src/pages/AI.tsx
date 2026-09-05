import { useState, useEffect } from "react";
import { Api } from "../api/client";

function CandidateCard({ c }: { c: any }) {
  const feasible = c.feasible;
  return (
    <div style={{ border: `1px solid ${feasible ? "#bbf7d0" : "#fecaca"}`, background: feasible ? "#f0fdf4" : "#fef2f2", padding: 12, borderRadius: 10, flex: "1 1 260px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <strong style={{ fontSize: 13 }}>{c.test_type}</strong>
        <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 999, background: feasible ? "#22c55e" : "#ef4444", color: "#fff" }}>{feasible ? "Feasible" : "Not feasible"}</span>
      </div>
      <p style={{ fontSize: 12, color: "#444", margin: "6px 0" }}><em>Reason:</em> {c.reason}</p>
      <p style={{ fontSize: 11, color: "#666" }}><em>Required:</em> {c.required_columns}</p>
      <p style={{ fontSize: 11, color: "#666" }}><em>Assumptions:</em> {c.assumptions}</p>
    </div>
  );
}

function VerifiedCard({ v }: { v: any }) {
  const r = v.result || {};
  const isOk = v.verified;
  return (
    <div style={{ border: "1px solid #e5e7eb", background: isOk ? "#fff" : "#fffbeb", padding: 12, borderRadius: 10, flex: "1 1 300px" }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <strong style={{ fontSize: 13 }}>{v.test_type}</strong>
        <span style={{ fontSize: 11, background: isOk ? "#111" : "#f59e0b", color: "#fff", padding: "2px 8px", borderRadius: 999 }}>{isOk ? "Verified Python" : "Failed"}</span>
        <span style={{ fontSize: 11, color: "#888" }}>{v.engine}</span>
      </div>
      {isOk ? (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginTop: 8, fontSize: 12 }}>
            <span><strong>Statistic:</strong> {r.statistic ?? "—"}</span>
            <span><strong>p-value:</strong> {r.p_value ?? "—"}</span>
            <span><strong>Decision:</strong> {r.decision ?? "—"}</span>
          </div>
          <p style={{ fontSize: 12, color: "#444", marginTop: 6 }}><em>Interpretation:</em> {r.interpretation || "—"}</p>
          {r.warnings?.length > 0 && <p style={{ fontSize: 11, color: "#b45309" }}>⚠️ {r.warnings.join("; ")}</p>}
          <details style={{ marginTop: 6 }}><summary style={{ fontSize: 11, cursor: "pointer" }}>Raw verified JSON (diff view)</summary><pre style={{ fontSize: 11, overflow: "auto", maxHeight: 160, background: "#f6f7f8", padding: 8, borderRadius: 6 }}>{JSON.stringify(r, null, 2)}</pre></details>
        </>
      ) : (
        <p style={{ fontSize: 12, color: "#92400e" }}>Error: {v.error || JSON.stringify(v)}</p>
      )}
    </div>
  );
}

export function AI() {
  const [datasetId, setDatasetId] = useState(localStorage.getItem("statlab_dataset_id") || "");
  const [question, setQuestion] = useState("Which product has the highest average sales?");
  const [result, setResult] = useState<any>(null);
  const [streamed, setStreamed] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [approvals, setApprovals] = useState<Record<string, boolean>>({});

  // Streaming effect for explanation (mock streaming, no extra LLM call)
  useEffect(() => {
    if (!result?.explanation) { setStreamed(""); return; }
    const text: string = result.explanation;
    setStreamed("");
    let i = 0;
    const id = setInterval(() => {
      i += 18;
      setStreamed(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, 30);
    return () => clearInterval(id);
  }, [result?.explanation]);

  async function ask() {
    setLoading(true); setErr(null); setResult(null);
    try {
      const r = await fetch(`${Api.baseUrl}/ai/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: datasetId, question }),
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setErr(String(e)); } finally { setLoading(false); }
  }

  async function suggest() {
    setLoading(true); setErr(null); setResult(null);
    try {
      const r = await fetch(`${Api.baseUrl}/ai/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: datasetId, question }),
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setErr(String(e)); } finally { setLoading(false); }
  }

  async function cleaning() {
    setLoading(true); setErr(null); setResult(null); setApprovals({});
    try {
      const r = await fetch(`${Api.baseUrl}/ai/cleaning-suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: datasetId }),
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setErr(String(e)); } finally { setLoading(false); }
  }

  async function explainCandidate(c: any) {
    setLoading(true); setErr(null);
    try {
      // Map candidate to explain payload (auto-pick minimal feasible for demo)
      const body: any = { dataset_id: datasetId, test_type: c.test_type, alpha: 0.05 };
      // For demo we let backend auto-pick columns via /ai/explain fallback? Use ask's verified if available
      // Instead we call /ai/explain with x/y if we have verified parameters
      const verified = result?.verified?.find((v: any) => v.test_type === c.test_type);
      if (verified?.parameters) Object.assign(body, verified.parameters);
      const r = await fetch(`${Api.baseUrl}/ai/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      setResult((prev: any) => ({ ...prev, explain_detail: j }));
    } catch (e) { setErr(String(e)); } finally { setLoading(false); }
  }

  const candidates: any[] = result?.candidates || [];
  const verified: any[] = result?.verified || [];
  const suggestions: any[] = result?.suggestions || [];

  return (
    <div>
      <h2>🤖 AI StatLab — Version 3</h2>
      <p style={{ color: "#666", fontSize: 13 }}>
        <code>Question → interpretation → candidate selection → Python verification → AI explanation → answer</code>. AI never calculates; all numbers from verified engine. Mock by default; set <code>AI_PROVIDER=openai|ollama</code> for live LLM.
      </p>

      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <input value={datasetId} onChange={e => setDatasetId(e.target.value)} placeholder="dataset_id (from Upload)" style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ddd", marginBottom: 8 }} />
        <textarea value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask about your dataset..." rows={3} style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ddd" }} />
        <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
          <button onClick={ask} disabled={loading || !datasetId} style={{ background: "#111", color: "#fff", padding: "8px 14px", borderRadius: 8, border: "none" }}>{loading ? "Thinking…" : "Ask (full pipeline)"}</button>
          <button onClick={suggest} disabled={loading || !datasetId} style={{ background: "#fff", border: "1px solid #ddd", padding: "8px 14px", borderRadius: 8 }}>Suggest analyses</button>
          <button onClick={cleaning} disabled={loading || !datasetId} style={{ background: "#fff", border: "1px solid #ddd", padding: "8px 14px", borderRadius: 8 }}>Cleaning assistant</button>
        </div>
        <div style={{ marginTop: 8, fontSize: 11, color: "#888" }}>
          Examples: “Which product has the highest average sales?” “Is satisfaction different between age groups?” “What variables are related to revenue?” “Explain this regression result.”
        </div>
      </div>

      {err && <pre style={{ color: "#a00", background: "#fff1f1", padding: 12, borderRadius: 8, marginTop: 12 }}>{err}</pre>}

      {/* Candidates */}
      {candidates.length > 0 && (
        <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb", marginTop: 12 }}>
          <h3 style={{ marginTop: 0 }}>Candidates (with reasons)</h3>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {candidates.map((c: any, i: number) => (
              <div key={i} style={{ flex: "1 1 280px", display: "flex", flexDirection: "column", gap: 8 }}>
                <CandidateCard c={c} />
                <button onClick={() => explainCandidate(c)} disabled={loading} style={{ fontSize: 11, padding: "4px 8px", borderRadius: 6, border: "1px solid #ddd", background: "#fff" }}>Explain this candidate ↓</button>
              </div>
            ))}
          </div>
          {result?.ai_suggestions && <p style={{ fontSize: 12, color: "#444", marginTop: 8, background: "#f6f7fb", padding: 8, borderRadius: 6 }}><strong>AI suggestions:</strong> {result.ai_suggestions}</p>}
        </div>
      )}

      {/* Verified */}
      {verified.length > 0 && (
        <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb", marginTop: 12 }}>
          <h3 style={{ marginTop: 0 }}>Verified Python Results (diff view)</h3>
          <p style={{ fontSize: 11, color: "#888" }}>Provenance: {result?.provenance || "All numbers from Python verification"}</p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {verified.map((v: any, i: number) => <VerifiedCard key={i} v={v} />)}
          </div>
        </div>
      )}

      {/* Streaming explanation */}
      {result?.explanation && (
        <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb", marginTop: 12 }}>
          <h3 style={{ marginTop: 0 }}>AI Explanation (streaming, linked to verified numbers)</h3>
          <p style={{ fontSize: 12, color: "#666" }}>Provider: {result.llm_meta?.provider} | Model: {result.llm_meta?.model} | Uncertainty communicated below</p>
          <div style={{ background: "#f6f7fb", padding: 12, borderRadius: 8, minHeight: 80, whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.6 }}>
            {streamed}<span style={{ opacity: streamed.length < (result.explanation?.length || 0) ? 1 : 0, animation: "blink 1s infinite" }}>▌</span>
          </div>
          <details style={{ marginTop: 8 }}><summary style={{ fontSize: 11 }}>Full raw explanation</summary><pre style={{ fontSize: 11, whiteSpace: "pre-wrap", background: "#f6f7f8", padding: 8, borderRadius: 6 }}>{result.explanation}</pre></details>
        </div>
      )}

      {/* Cleaning with approval */}
      {suggestions.length > 0 && (
        <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb", marginTop: 12 }}>
          <h3 style={{ marginTop: 0 }}>Cleaning Assistant — Approval Required</h3>
          {suggestions.map((s: any, i: number) => (
            <div key={i} style={{ display: "flex", gap: 12, alignItems: "center", padding: "8px 0", borderBottom: "1px solid #eee" }}>
              <span style={{ fontSize: 11, background: s.destructive ? "#fee2e2" : "#dcfce7", color: s.destructive ? "#991b1b" : "#166534", padding: "2px 8px", borderRadius: 999 }}>{s.issue}</span>
              <span style={{ flex: 1, fontSize: 12 }}>{s.suggestion}</span>
              <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: 12 }}>
                <input type="checkbox" checked={!!approvals[s.column]} onChange={e => setApprovals(prev => ({ ...prev, [s.column]: e.target.checked }))} />
                Approve
              </label>
            </div>
          ))}
          <p style={{ fontSize: 11, color: "#888", marginTop: 8 }}>{result?.note} — Destructive transforms (text→numeric, parse_dates) require checkbox before backend would apply (future PATCH /datasets/{"{id}"}/clean).</p>
          {result?.ai_summary && <p style={{ fontSize: 12, background: "#f6f7fb", padding: 8, borderRadius: 6 }}><strong>AI summary:</strong> {result.ai_summary}</p>}
        </div>
      )}

      {/* Explain detail */}
      {result?.explain_detail && (
        <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb", marginTop: 12 }}>
          <h3>Explain Detail (Verified → AI)</h3>
          <pre style={{ fontSize: 11, overflow: "auto", maxHeight: 220, background: "#f6f7f8", padding: 8, borderRadius: 6 }}>{JSON.stringify(result.explain_detail, null, 2)}</pre>
        </div>
      )}

      {/* Fallback raw */}
      {result && !candidates.length && !verified.length && !suggestions.length && (
        <pre style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #eee", overflow: "auto", fontSize: 12, marginTop: 12, whiteSpace: "pre-wrap" }}>{JSON.stringify(result, null, 2)}</pre>
      )}

      <div style={{ marginTop: 16, background: "#eef6ff", padding: 12, borderRadius: 12, border: "1px solid #bfdbfe", fontSize: 12, color: "#333" }}>
        <strong>Privacy & Responsible AI:</strong> raw data never sent beyond aggregated stats; use <code>AI_PROVIDER=ollama</code> for offline. Destructive cleaning requires approval. Uncertainty + assumptions shown per test.
      </div>
    </div>
  );
}
