export function Charts() {
  return (
    <div>
      <h2>Charts</h2>
      <p style={{ color: "#666" }}>Milestone 4 — Charts page (placeholder). Visualizations are currently served by Streamlit; React charts will consume <code>POST /analyses/descriptive</code> + client-side Plotly.</p>
      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <ul style={{ lineHeight: 1.8, fontSize: 14 }}>
          <li>Histogram — numeric selector + bins slider (Plotly)</li>
          <li>Boxplot, Bar, Scatter, Line (date + value), Correlation heatmap</li>
          <li>Data source: <code>GET /datasets/{"{id}"}/profile</code> numeric_summary + <code>GET /datasets/{"{id}"}</code> preview</li>
        </ul>
        <p style={{ fontSize: 12, color: "#888" }}>Run Streamlit at <code>streamlit run app.py</code> for full Plotly charts today; React Plotly integration is next.</p>
      </div>
    </div>
  );
}
