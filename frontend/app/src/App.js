import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import AuthPage from "./pages/auth";
import Dashboard from "./pages/dashboard";
import TextGenerator from "./pages/TextGenerator";
import ImageGenerator from "./pages/ImageGenerator";
import Profile from "./pages/Profile";
import { auth } from "./firebase";
import { useAuthState } from "react-firebase-hooks/auth";
import PromptForm from "./components/PromptForm";

export default function App() {
  const [user, loading] = useAuthState(auth);

  if (loading) return (
    <div className="min-h-screen bg-gradient-to-br from-primary-200 to-primary-100 flex items-center justify-center">
      <div className="text-white text-xl">Cargando...</div>
    </div>
  );

  return (
    <Router>
      <Routes>
        <Route path="/" element={<AuthPage />} />
        <Route path="/dashboard" element={user ? <Dashboard /> : <Navigate to="/" />} />
        <Route path="/text-generator" element={user ? <TextGenerator /> : <Navigate to="/" />} />
        <Route path="/image-generator" element={user ? <ImageGenerator /> : <Navigate to="/" />} />
        <Route path="/profile" element={user ? <Profile /> : <Navigate to="/" />} />
        <Route path="*" element={<Navigate to="/" />} />
        <Route path="/agente" element={<PromptForm />} />
      </Routes>
    </Router>
  );
}
