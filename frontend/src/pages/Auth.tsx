import { useState } from "react";
import { Api } from "../api/client";

export function Auth() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("register");
  const [msg, setMsg] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("statlab_token"));

  async function submit() {
    setMsg(null);
    try {
      if (mode === "register") {
        const r = await fetch(`${Api.baseUrl}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name: email.split("@")[0] }),
        });
        if (!r.ok) throw new Error(await r.text());
        setMsg("Registered — now log in");
        setMode("login");
      } else {
        const form = new URLSearchParams();
        form.set("username", email);
        form.set("password", password);
        const r = await fetch(`${Api.baseUrl}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: form.toString(),
        });
        if (!r.ok) throw new Error(await r.text());
        const j = await r.json();
        localStorage.setItem("statlab_token", j.access_token);
        setToken(j.access_token);
        setMsg(`Logged in as ${j.email}`);
      }
    } catch (e) { setMsg(String(e)); }
  }

  function logout() {
    localStorage.removeItem("statlab_token");
    setToken(null);
    setMsg("Logged out");
  }

  return (
    <div>
      <h2>Authentication — Milestone 5</h2>
      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb", maxWidth: 520 }}>
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <button onClick={() => setMode("register")} style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid #ddd", background: mode === "register" ? "#111" : "#fff", color: mode === "register" ? "#fff" : "#111" }}>Register</button>
          <button onClick={() => setMode("login")} style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid #ddd", background: mode === "login" ? "#111" : "#fff", color: mode === "login" ? "#fff" : "#111" }}>Login</button>
          {token && <button onClick={logout} style={{ marginLeft: "auto", padding: "6px 12px", borderRadius: 8, border: "1px solid #fca5a5", background: "#fff", color: "#a00" }}>Logout</button>}
        </div>
        <input value={email} onChange={e => setEmail(e.target.value)} placeholder="email" style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ddd", marginBottom: 8 }} />
        <input value={password} onChange={e => setPassword(e.target.value)} placeholder="password (≥8 chars, never stored plain)" type="password" style={{ width: "100%", padding: 8, borderRadius: 8, border: "1px solid #ddd", marginBottom: 8 }} />
        <button onClick={submit} style={{ background: "#111", color: "#fff", padding: "8px 16px", borderRadius: 8, border: "none", width: "100%" }}>{mode === "register" ? "Create account" : "Log in"}</button>
        {msg && <pre style={{ background: "#f6f7f8", padding: 12, borderRadius: 8, marginTop: 12, overflow: "auto", fontSize: 12 }}>{msg}</pre>}
        {token && <pre style={{ background: "#eef6ff", padding: 12, borderRadius: 8, marginTop: 8, fontSize: 11, overflow: "auto" }}>JWT: {token.slice(0,60)}… (send as Authorization: Bearer)</pre>}
        <p style={{ fontSize: 12, color: "#888", marginTop: 8 }}>POST /auth/register, POST /auth/login (OAuth2), GET /auth/me, protected GET /projects — passwords hashed with bcrypt, no plain storage.</p>
      </div>
    </div>
  );
}
