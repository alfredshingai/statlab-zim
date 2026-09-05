import { Link, useLocation } from "react-router-dom";

export function Layout({ children }: { children: React.ReactNode }) {
  const loc = useLocation();
  const nav = [
    { to: "/", label: "Landing" },
    { to: "/dashboard", label: "Dashboard" },
    { to: "/upload", label: "Upload" },
    { to: "/dataset", label: "Dataset" },
    { to: "/descriptive", label: "Descriptive" },
    { to: "/tests", label: "Tests" },
    { to: "/charts", label: "Charts" },
    { to: "/projects", label: "Projects" },
    { to: "/reports", label: "Reports" },
    { to: "/auth", label: "Auth" },
  ];
  return (
    <div style={{ fontFamily: "system-ui, sans-serif", minHeight: "100vh", background: "#f6f7fb" }}>
      <header style={{ background: "#fff", borderBottom: "1px solid #e5e7eb", padding: "12px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Link to="/" style={{ fontWeight: 800, fontSize: 20, textDecoration: "none", color: "#111" }}>📊 StatLab Zim</Link>
        <span style={{ fontSize: 12, color: "#666" }}>React + FastAPI • Version 2</span>
      </header>
      <nav style={{ display: "flex", gap: 8, padding: "12px 24px", flexWrap: "wrap", background: "#fff", borderBottom: "1px solid #eee" }}>
        {nav.map(n => (
          <Link
            key={n.to}
            to={n.to}
            style={{
              padding: "6px 12px",
              borderRadius: 8,
              textDecoration: "none",
              fontSize: 14,
              background: loc.pathname === n.to ? "#111" : "#f3f4f6",
              color: loc.pathname === n.to ? "#fff" : "#111",
              border: "1px solid #e5e7eb",
            }}
          >
            {n.label}
          </Link>
        ))}
      </nav>
      <main style={{ padding: 24, maxWidth: 1100, margin: "0 auto" }}>{children}</main>
      <footer style={{ textAlign: "center", padding: 24, color: "#888", fontSize: 12 }}>
        Built for learners in Zimbabwe • <a href="http://localhost:8000/docs" target="_blank">API Docs</a> • <a href="http://localhost:8000/health" target="_blank">Health</a>
      </footer>
    </div>
  );
}
