import { useState } from "react";
import { Api } from "../api/client";

export function AI() {
  const [datasetId, setDatasetId] = useState(localStorage.getItem("statlab_dataset_id") || "");
  const [question, setQuestion] = useState("Which product has the highest average sales?");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function ask() {
    setLoading(true); setErr(null);
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
    setLoading(true); setErr(null);
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
    setLoading(true); setErr(null);
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

  return (
    <div>
      <h2>🤖 AI StatLab — Version 3</h2>
      <p style={{ color: "#666", fontSize: 13 }}>
        Architecture: <code>Question → interpretation → candidate selection → Python verification → AI explanation → answer</code>. AI never calculates; all numbers from verified Python engine. Mock provider by default (no API key); set <code>AI_PROVIDER=openai|ollama</code> for live LLM.
      </p>
      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <input value={datasetId} onChange={e => setDatasetId(e.target.value)} placeholder="dataset_id" style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ddd", marginBottom: 8 }} />
        <textarea value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask about your dataset..." rows={3} style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ddd" }} />
        <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
          <button onClick={ask} disabled={loading || !datasetId} style={{ background: "#111", color: "#fff", padding: "8px 14px", borderRadius: 8, border: "none" }}>{loading ? "Thinking…" : "Ask (full pipeline)"}</button>
          <button onClick={suggest} disabled={loading || !datasetId} style={{ background: "#fff", border: "1px solid #ddd", padding: "8px 14px", borderRadius: 8 }}>Suggest analyses</button>
          <button onClick={cleaning} disabled={loading || !datasetId} style={{ background: "#fff", border: "1px solid #ddd", padding: "8px 14px", borderRadius: 8 }}>Cleaning assistant</button>
        </div>
        <div style={{ marginTop: 12, fontSize: 12, color: "#888" }}>
          Examples: “Which product has the highest average sales?” “Is satisfaction different between age groups?” “What variables are related to revenue?” “Explain this regression result.”
        </div>
      </div>
      {err && <pre style={{ color: "#a00", background: "#fff1f1", padding: 12, borderRadius: 8, marginTop: 12 }}>{err}</pre>}
      {result && <pre style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #eee", overflow: "auto", fontSize: 12, marginTop: 12, whiteSpace: "pre-wrap" }}>{JSON.stringify(result, null, 2)}</pre>}
      <div style={{ marginTop: 16, background: "#eef6ff", padding: 12, borderRadius: 12, border: "1px solid #bfdbfe", fontSize: 12, color: "#333" }}>
        <strong>Privacy & Responsible AI:</strong> dataset contents are not sent to external LLM beyond aggregated stats; raw data stays in Python verification. For Ollama local (`AI_PROVIDER=ollama`), no data leaves your machine. Destructive cleaning suggestions require approval. Uncertainty is communicated in explanations.
      </div>
    </div>
  );
}
