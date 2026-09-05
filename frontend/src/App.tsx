import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Landing } from "./pages/Landing";
import { Dashboard } from "./pages/Dashboard";
import { Upload } from "./pages/Upload";
import { DatasetOverview } from "./pages/DatasetOverview";
import { Descriptive } from "./pages/Descriptive";
import { Tests } from "./pages/Tests";
import { Charts } from "./pages/Charts";
import { Projects } from "./pages/Projects";
import { Reports } from "./pages/Reports";
import { Auth } from "./pages/Auth";

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/dataset" element={<DatasetOverview />} />
          <Route path="/descriptive" element={<Descriptive />} />
          <Route path="/tests" element={<Tests />} />
          <Route path="/charts" element={<Charts />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/auth" element={<Auth />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
