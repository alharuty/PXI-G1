import React from "react";
import { auth } from "../firebase";
import { signOut } from "firebase/auth";

export default function Dashboard() {
  return (
    <div>
      <h2>Bienvenido al Dashboard</h2>
      <button onClick={() => signOut(auth)}>Cerrar sesión</button>
    </div>
  );
}
