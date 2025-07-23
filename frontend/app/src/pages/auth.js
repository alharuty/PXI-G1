import React, { useState } from "react";
import { useAuthState } from "react-firebase-hooks/auth";
import { auth } from "../firebase";
import { Navigate } from "react-router-dom";
import Login from "./login";
import Register from "./register";

export default function AuthPage() {
  const [user, loading] = useAuthState(auth);
  const [mode, setMode] = useState("login");

  if (loading)
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-200 to-primary-100 flex items-center justify-center">
        <div className="text-white text-xl">Cargando...</div>
      </div>
    );
  if (user) return <Navigate to="/dashboard" />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-200 to-primary-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Creator</h1>
          <p className="text-gray-600">Tu plataforma de creación con IA</p>
        </div>

        <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setMode("login")}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              mode === "login"
                ? "bg-white text-primary-200 shadow"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Iniciar Sesión
          </button>
          <button
            onClick={() => setMode("register")}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              mode === "register"
                ? "bg-white text-primary-200 shadow"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Crear Cuenta
          </button>
        </div>

        {mode === "login" ? <Login /> : <Register />}
      </div>
    </div>
  );
}
