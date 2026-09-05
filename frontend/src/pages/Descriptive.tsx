import { useState } from "react";
import { Api } from "../api/client";

export function Descriptive() {
  const [id, setId] = useState(localStorage.getItem("statlab_dataset_id") || "");
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setErr(null);
    try {
      const r = await Api.descriptive(id);
      setRes(r);
    } catch (e) { setErr(String(e)); }
  }
  return (
    <div>
      <h2>Descriptive statistics</h2>
      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb", display: "flex", gap: 8 }}>
        <input value={id} onChange={e => setId(e.target.value)} placeholder="dataset_id" style={{ flex: 1, padding: 8, borderRadius: 8, border: "1px solid #ddd" }} />
        <button onClick={run} style={{ background: "#111", color: "#fff", padding: "8px 14px", borderRadius: 8, border: "none" }}>Run</button>
      </div>
      <p style={{ fontSize: 12, color: "#888" }}>POST /analyses/descriptive — numeric_summary, categorical_overview, frequency_tables</p>
      {err && <pre style={{ color: "#a00", background: "#fff1f1", padding: 12, borderRadius: 8 }}>{err}</pre>}
      {res && <pre style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #eee", overflow: "auto", fontSize: 12 }}>{JSON.stringify(res, null, 2)}</pre>}
    </div>
  );
}
