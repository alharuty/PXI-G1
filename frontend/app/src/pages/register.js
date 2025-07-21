import React, { useState } from "react";
import { createUserWithEmailAndPassword } from "firebase/auth";
import { doc, setDoc } from "firebase/firestore";
import { auth, db } from "../firebase";

export default function Register() {
  const [form, setForm] = useState({
    nombre: "", apellido: "", email: "", password: "",
    tipo: "particular", bio: ""
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { email, password, nombre, apellido, tipo, bio } = form;
    try {
      const res = await createUserWithEmailAndPassword(auth, email, password);
      await setDoc(doc(db, "users", res.user.uid), {
        nombre, apellido, email, tipo, bio, uid: res.user.uid
      });
    } catch (err) {
      console.error(err);
      alert(`Error al registrar usuario: ${err.message}`);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="nombre" placeholder="Nombre" value={form.nombre} onChange={handleChange} required />
      <input name="apellido" placeholder="Apellido" value={form.apellido} onChange={handleChange} required />
      <input name="email" type="email" placeholder="Email" value={form.email} onChange={handleChange} required />
      <input name="password" type="password" placeholder="Contraseña" value={form.password} onChange={handleChange} required />
      <select name="tipo" value={form.tipo} onChange={handleChange} required>
        <option value="particular">Particular</option>
        <option value="empresa">Empresa</option>
      </select>
      <textarea name="bio" placeholder="Biografía" value={form.bio} onChange={handleChange} required />
      <button type="submit">Registrarse</button>
    </form>
  );
}
