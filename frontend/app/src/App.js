import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import AuthPage from "./pages/auth";
import Dashboard from "./pages/dashboard";
import { auth } from "./firebase";
import { useAuthState } from "react-firebase-hooks/auth";
import PromptForm from "./components/PromptForm";

export default function App() {
  const [user, loading] = useAuthState(auth);

  if (loading) return <p>Cargando...</p>;

  return (
    <Router>
      <Routes>
        <Route path="/" element={<AuthPage />} />
        <Route path="/dashboard" element={user ? <Dashboard /> : <Navigate to="/" />} />
        <Route path="*" element={<Navigate to="/" />} />
        <Route path="/agente" element={<PromptForm />} />
      </Routes>
    </Router>
  );
}
