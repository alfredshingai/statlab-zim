import { useState } from "react";
import { Api } from "../api/client";

export function Reports() {
  const [datasetId, setDatasetId] = useState(localStorage.getItem("statlab_dataset_id") || "");
  const [title, setTitle] = useState("Q1 Sales Report");
  const [aiReport, setAiReport] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function genAI() {
    setLoading(true); setErr(null);
    try {
      const r = await fetch(`${Api.baseUrl}/ai/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: datasetId, title }),
      });
      if (!r.ok) throw new Error(await r.text());
      setAiReport(await r.json());
    } catch (e) { setErr(String(e)); } finally { setLoading(false); }
  }

  return (
    <div>
      <h2>Report downloads — Version 3 Polish</h2>
      <p style={{ color: "#666", fontSize: 13 }}>Milestone 7 — project title, dataset info, methods, results, charts, interpretation, limitations, creation date. AI-assisted but verified.</p>

      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <h3>AI Report Preview</h3>
        <input value={datasetId} onChange={e => setDatasetId(e.target.value)} placeholder="dataset_id" style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ddd", marginBottom: 8 }} />
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Report title" style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ddd", marginBottom: 8 }} />
        <button onClick={genAI} disabled={loading || !datasetId} style={{ background: "#111", color: "#fff", padding: "8px 14px", borderRadius: 8, border: "none" }}>{loading ? "Generating…" : "Generate AI Report"}</button>
        <p style={{ fontSize: 11, color: "#888", marginTop: 6 }}>POST /ai/report → verified numbers + AI prose (executive_summary, methods, results, limitations). Optionally persist via POST /reports/generate if you have a project_id + JWT.</p>
      </div>

      {err && <pre style={{ color: "#a00", background: "#fff1f1", padding: 12, borderRadius: 8, marginTop: 12 }}>{err}</pre>}

      {aiReport && (
        <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb", marginTop: 12 }}>
          <h3>📄 {aiReport.title}</h3>
          <p style={{ fontSize: 12, color: "#666" }}>Created: {new Date().toISOString()} | Provenance: {aiReport.provenance}</p>
          <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
            <section style={{ background: "#f6f7fb", padding: 12, borderRadius: 8 }}><strong>Executive Summary</strong><p style={{ fontSize: 13 }}>{aiReport.report.executive_summary}</p></section>
            <section style={{ background: "#f6f7fb", padding: 12, borderRadius: 8 }}><strong>Methods</strong><p style={{ fontSize: 13 }}>{aiReport.report.methods}</p></section>
            <section style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #eee" }}><strong>Verified Results</strong><pre style={{ fontSize: 11, overflow: "auto", maxHeight: 200 }}>{JSON.stringify(aiReport.verified, null, 2)}</pre></section>
            <section style={{ background: "#fff3e0", padding: 12, borderRadius: 8 }}><strong>Limitations</strong><p style={{ fontSize: 13 }}>{aiReport.report.limitations}</p></section>
            <section style={{ background: "#e8f5e9", padding: 12, borderRadius: 8 }}><strong>Recommendations</strong><p style={{ fontSize: 13 }}>{aiReport.report.recommendations}</p></section>
          </div>
          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
            <button onClick={() => navigator.clipboard.writeText(JSON.stringify(aiReport, null, 2))} style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid #ddd", background: "#fff" }}>Copy JSON</button>
            <button onClick={() => window.print()} style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid #ddd", background: "#fff" }}>Print (browser → Save as PDF)</button>
          </div>
          <p style={{ fontSize: 11, color: "#888", marginTop: 8 }}>For persisted reports: <code>POST /reports/generate</code> (auth) → <code>GET /reports/{"{id}"}/html</code> → <code>GET /reports/{"{id}"}/download</code> (HTML file, print to PDF).</p>
        </div>
      )}

      <div style={{ background: "#fff", padding: 12, borderRadius: 12, border: "1px solid #e5e7eb", marginTop: 12, fontSize: 12, color: "#666" }}>
        <strong>Download persisted report:</strong> after login + project creation, <code>Authorization: Bearer &lt;JWT&gt;</code> → <code>GET /reports/{"{id}"}/html</code> (view) or <code>/download</code> (file). Uses <code>backend/app/api/routes/reports.py:1</code> HTML renderer.
      </div>
    </div>
  );
}
