import { useState } from "react";
import { Api } from "../api/client";

export function DatasetOverview() {
  const [id, setId] = useState(localStorage.getItem("statlab_dataset_id") || "");
  const [data, setData] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const d = await Api.getDataset(id);
      setData(d);
      const p = await Api.getProfile(id);
      setProfile(p);
    } catch (e) { setErr(String(e)); }
  }

  return (
    <div>
      <h2>Dataset overview</h2>
      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <div style={{ display: "flex", gap: 8 }}>
          <input value={id} onChange={e => setId(e.target.value)} placeholder="dataset_id (from upload)" style={{ flex: 1, padding: 8, borderRadius: 8, border: "1px solid #ddd" }} />
          <button onClick={load} style={{ background: "#111", color: "#fff", padding: "8px 14px", borderRadius: 8, border: "none" }}>Load</button>
        </div>
        <p style={{ fontSize: 12, color: "#888" }}>GET /datasets/{"{id}"} + GET /datasets/{"{id}"}/profile</p>
      </div>
      {err && <pre style={{ color: "#a00", background: "#fff1f1", padding: 12, borderRadius: 8 }}>{err}</pre>}
      {data && <pre style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #eee", overflow: "auto", fontSize: 12 }}>{JSON.stringify(data, null, 2)}</pre>}
      {profile && <pre style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #eee", overflow: "auto", fontSize: 12, marginTop: 8 }}>{JSON.stringify(profile, null, 2)}</pre>}
    </div>
  );
}
