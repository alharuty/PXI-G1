import React, { useState } from "react";
import { useAuthState } from "react-firebase-hooks/auth";
import { auth } from "../firebase";
import { Navigate } from "react-router-dom";
import Login from "./login";
import Register from "./register";

export default function AuthPage() {
  const [user, loading] = useAuthState(auth);
  const [mode, setMode] = useState("login");

  if (loading) return <p>Cargando...</p>;
  if (user) return <Navigate to="/dashboard" />;

  return (
    <div>
      <div style={{ marginBottom: "1rem" }}>
        {mode !== "login" && (
          <button onClick={() => setMode("login")}>Iniciar sesión</button>
        )}
        {mode !== "register" && (
          <button onClick={() => setMode("register")}>Crear cuenta</button>
        )}
      </div>

      {mode === "login" ? <Login /> : <Register />}
    </div>
  );
}
