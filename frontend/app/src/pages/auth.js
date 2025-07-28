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
      <div className="min-h-screen bg-gradient-to-br from-dark-900 to-dark-800 flex items-center justify-center">
        <div className="text-white text-xl">Cargando...</div>
      </div>
    );
  if (user) return <Navigate to="/dashboard" />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-primary-200 flex items-center justify-center p-4">
      <div className="bg-dark-800 rounded-2xl shadow-2xl p-8 w-full max-w-md border border-dark-700">
        <div className="text-center mb-8">
          {/* Logo en la página de auth */}
          <div className="w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <img
              src="/buddylog.png"
              alt="AI Creator Logo"
              className="h-12 w-12 object-contain"
            />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">AI Creator</h1>
          <p className="text-gray-400 font-medium">Tu plataforma de creación con IA</p>
        </div>

        <div className="flex mb-6 bg-dark-700 rounded-xl p-1">
          <button
            onClick={() => setMode("login")}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all ${
              mode === "login"
                ? "bg-primary-100 text-white shadow-lg"
                : "text-gray-400 hover:text-white"
            }`}
          >
            Iniciar Sesión
          </button>
          <button
            onClick={() => setMode("register")}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all ${
              mode === "register"
                ? "bg-primary-100 text-white shadow-lg"
                : "text-gray-400 hover:text-white"
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
