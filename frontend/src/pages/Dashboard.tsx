import { useEffect, useState } from "react";
import { Api } from "../api/client";

export function Dashboard() {
  const [health, setHealth] = useState<any>(null);
  const [datasets, setDatasets] = useState<unknown[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Api.healthCheck().then(setHealth).catch(e => setError(String(e)));
    fetch(`${Api.baseUrl}/datasets`).then(r => r.json()).then(setDatasets).catch(() => {});
  }, []);

  return (
    <div>
      <h2>Dashboard</h2>
      <p style={{ color: "#666" }}>Backend health and recent datasets.</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
          <h3>Health</h3>
          <pre style={{ background: "#f6f7f8", padding: 12, borderRadius: 8, overflow: "auto", fontSize: 12 }}>
            {error ? `Error: ${error}` : JSON.stringify(health, null, 2) || "Loading..."}
          </pre>
        </div>
        <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
          <h3>Recent datasets</h3>
          <p style={{ fontSize: 12, color: "#888" }}>GET /datasets (in-memory, persists until backend restart; DB persistence in Milestone 3)</p>
          {datasets.length === 0 ? <p style={{ color: "#888" }}>No datasets yet. Upload one.</p> :
            <ul>{datasets.map((d: unknown, i: number) => <li key={i} style={{ fontSize: 13 }}><code>{JSON.stringify(d).slice(0,120)}...</code></li>)}</ul>}
        </div>
      </div>
      <div style={{ marginTop: 16, background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <h3>Quick actions</h3>
        <div style={{ display: "flex", gap: 8 }}>
          <a href="/upload" style={{ padding: "8px 14px", background: "#111", color: "#fff", borderRadius: 8, textDecoration: "none" }}>Upload CSV</a>
          <a href="/descriptive" style={{ padding: "8px 14px", background: "#fff", border: "1px solid #ddd", borderRadius: 8, textDecoration: "none", color: "#111" }}>Descriptive</a>
          <a href="/tests" style={{ padding: "8px 14px", background: "#fff", border: "1px solid #ddd", borderRadius: 8, textDecoration: "none", color: "#111" }}>Statistical tests</a>
        </div>
      </div>
    </div>
  );
}
