export function Landing() {
  return (
    <div>
      <div style={{ background: "#fff", padding: 32, borderRadius: 16, border: "1px solid #e5e7eb" }}>
        <h1 style={{ fontSize: 32, marginBottom: 8 }}>📊 StatLab Zim — AI-ready Statistics for Zimbabwe</h1>
        <p style={{ color: "#555", lineHeight: 1.6 }}>
          Upload any CSV dataset to explore its structure, run descriptive analyses, visualize distributions and
          relationships, and perform common statistical tests — all with plain-language interpretations.
        </p>
        <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
          <a href="/upload" style={{ background: "#111", color: "#fff", padding: "10px 18px", borderRadius: 8, textDecoration: "none" }}>Upload dataset →</a>
          <a href="/dashboard" style={{ background: "#fff", border: "1px solid #ddd", padding: "10px 18px", borderRadius: 8, textDecoration: "none", color: "#111" }}>Go to Dashboard</a>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginTop: 24 }}>
          <div style={{ background: "#f9fafb", padding: 16, borderRadius: 12, border: "1px solid #eee" }}><strong>🔍 Overview</strong><p style={{ fontSize: 13, color: "#666" }}>Row/col counts, missing, duplicates</p></div>
          <div style={{ background: "#f9fafb", padding: 16, borderRadius: 12, border: "1px solid #eee" }}><strong>📈 Visuals</strong><p style={{ fontSize: 13, color: "#666" }}>Histogram, boxplot, heatmap</p></div>
          <div style={{ background: "#f9fafb", padding: 16, borderRadius: 12, border: "1px solid #eee" }}><strong>🧪 Tests</strong><p style={{ fontSize: 13, color: "#666" }}>Pearson, Spearman, t-test, χ²</p></div>
          <div style={{ background: "#f9fafb", padding: 16, borderRadius: 12, border: "1px solid #eee" }}><strong>📥 Reports</strong><p style={{ fontSize: 13, color: "#666" }}>Exports + interpretations</p></div>
        </div>
      </div>
      <div style={{ marginTop: 16, background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <h3>Version 2 — Full-stack</h3>
        <ul style={{ color: "#555", lineHeight: 1.8, fontSize: 14 }}>
          <li>Backend: FastAPI • Health at <code>GET /health</code> • Docs at <code>/docs</code></li>
          <li>Statistical API: <code>POST /datasets/upload</code> → <code>GET /datasets/{"{id}"}/profile</code> → <code>POST /analyses/*</code></li>
          <li>Database: PostgreSQL + SQLAlchemy (Milestone 3) — Users, Datasets, Projects, Results</li>
          <li>Frontend: React + TypeScript (this app) communicates with FastAPI via REST</li>
        </ul>
      </div>
    </div>
  );
}
