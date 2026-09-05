import { useState } from "react";
import { Api } from "../api/client";

export function Tests() {
  const [id, setId] = useState(localStorage.getItem("statlab_dataset_id") || "");
  const [testType, setTestType] = useState("pearson");
  const [xCol, setXCol] = useState("x");
  const [yCol, setYCol] = useState("y");
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setErr(null);
    try {
      const payload: Record<string, unknown> = { dataset_id: id, test_type: testType, alpha: 0.05 };
      if (["pearson", "spearman", "linear_regression"].includes(testType)) {
        payload.x_col = xCol; payload.y_col = yCol;
      } else if (testType === "ttest") {
        payload.numeric_col = xCol; payload.group_col = yCol;
      } else if (testType === "chi2") {
        payload.col1 = xCol; payload.col2 = yCol;
      }
      const r = await Api.runTest(payload as never);
      setRes(r);
    } catch (e) { setErr(String(e)); }
  }

  return (
    <div>
      <h2>Statistical tests</h2>
      <div style={{ background: "#fff", padding: 16, borderRadius: 12, border: "1px solid #e5e7eb" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8 }}>
          <input value={id} onChange={e => setId(e.target.value)} placeholder="dataset_id" style={{ padding: 8, borderRadius: 8, border: "1px solid #ddd" }} />
          <select value={testType} onChange={e => setTestType(e.target.value)} style={{ padding: 8, borderRadius: 8, border: "1px solid #ddd" }}>
            <option value="pearson">pearson</option>
            <option value="spearman">spearman</option>
            <option value="linear_regression">linear_regression</option>
            <option value="ttest">ttest</option>
            <option value="chi2">chi2</option>
          </select>
          <input value={xCol} onChange={e => setXCol(e.target.value)} placeholder="x_col / numeric_col / col1" style={{ padding: 8, borderRadius: 8, border: "1px solid #ddd" }} />
          <input value={yCol} onChange={e => setYCol(e.target.value)} placeholder="y_col / group_col / col2" style={{ padding: 8, borderRadius: 8, border: "1px solid #ddd" }} />
        </div>
        <button onClick={run} style={{ marginTop: 12, background: "#111", color: "#fff", padding: "8px 14px", borderRadius: 8, border: "none" }}>Run test</button>
        <p style={{ fontSize: 12, color: "#888" }}>POST /analyses/test — returns statistic, p_value, decision, interpretation, assumptions</p>
      </div>
      {err && <pre style={{ color: "#a00", background: "#fff1f1", padding: 12, borderRadius: 8 }}>{err}</pre>}
      {res && <pre style={{ background: "#fff", padding: 12, borderRadius: 8, border: "1px solid #eee", overflow: "auto", fontSize: 12 }}>{JSON.stringify(res, null, 2)}</pre>}
    </div>
  );
}
