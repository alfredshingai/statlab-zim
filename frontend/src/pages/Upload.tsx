import { useState } from "react";
import { Api } from "../api/client";

export function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onUpload() {
    if (!file) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const r = await Api.uploadDataset(file);
      setResult(r);
      // Persist dataset_id for other pages
      localStorage.setItem("statlab_dataset_id", (r as { dataset_id: string }).dataset_id);
    } catch (e) {
      setError(String(e));
    } finally { setLoading(false); }
  }

  return (
    <div>
      <h2>Upload dataset</h2>
      <div style={{ background: "#fff", padding: 20, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <p style={{ color: "#666" }}>POST /datasets/upload — CSV only, UTF-8, header required, max 50MB.</p>
        <input type="file" accept=".csv" onChange={e => setFile(e.target.files?.[0] || null)} />
        <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
          <button onClick={onUpload} disabled={!file || loading} style={{ background: "#111", color: "#fff", padding: "8px 16px", borderRadius: 8, border: "none", cursor: "pointer" }}>
            {loading ? "Uploading…" : "Upload"}
          </button>
          {result && <span style={{ color: "green", fontSize: 13 }}>✔ Uploaded — dataset_id saved to localStorage</span>}
        </div>
        {error && <pre style={{ color: "#a00", background: "#fff1f1", padding: 12, borderRadius: 8, marginTop: 12 }}>{error}</pre>}
        {result && <pre style={{ background: "#f6f7f8", padding: 12, borderRadius: 8, marginTop: 12, overflow: "auto", fontSize: 12 }}>{JSON.stringify(result, null, 2)}</pre>}
      </div>
      <div style={{ marginTop: 16, background: "#fff", padding: 12, borderRadius: 12, border: "1px solid #e5e7eb", fontSize: 13, color: "#666" }}>
        Flow: Upload → <code>dataset_id</code> → Dataset overview / Descriptive / Tests / Charts — all call <code>POST /analyses/*</code> with that id.
      </div>
    </div>
  );
}
