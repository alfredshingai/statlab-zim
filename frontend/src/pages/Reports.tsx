export function Reports() {
  return (
    <div>
      <h2>Report downloads</h2>
      <p style={{ color: "#666" }}>Milestone 7 — Reports containing project title, dataset info, methods, results, charts, interpretation, limitations, creation date.</p>
      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <p>Current: CSV exports per table + PNG chart exports (Streamlit).</p>
        <p>Next: <code>POST /reports/generate</code> → PDF/HTML with verified stats + AI explanations (Milestone 3 DB + Version 3).</p>
        <p style={{ fontSize: 12, color: "#888" }}>DB table <code>reports</code> already created in Milestone 3 (<code>backend/app/db/models.py</code>).</p>
      </div>
    </div>
  );
}
