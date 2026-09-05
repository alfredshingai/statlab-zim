export function Projects() {
  return (
    <div>
      <h2>Saved projects</h2>
      <p style={{ color: "#666" }}>Milestone 3 + 5 — Persistent projects (DB + auth). Currently in-memory; will persist to PostgreSQL with user-specific projects.</p>
      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <p>Schema: <code>projects</code> table — id, name, description, owner_id, created_at. Linked to datasets + analysis_results + reports.</p>
        <p style={{ fontSize: 12, color: "#888" }}>Once auth is added (Milestone 5), this page will list <code>GET /projects</code> for the logged-in user.</p>
      </div>
    </div>
  );
}
