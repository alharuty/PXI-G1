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
      alert("Usuario registrado");
    } catch (err) {
      console.error(err);
      alert("Error al registrar usuario");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="nombre" placeholder="Nombre" onChange={handleChange} />
      <input name="apellido" placeholder="Apellido" onChange={handleChange} />
      <input name="email" type="email" placeholder="Email" onChange={handleChange} />
      <input name="password" type="password" placeholder="Contraseña" onChange={handleChange} />
      <select name="tipo" onChange={handleChange}>
        <option value="particular">Particular</option>
        <option value="empresa">Empresa</option>
      </select>
      <textarea name="bio" placeholder="Biografía" onChange={handleChange} />
      <button type="submit">Registrarse</button>
    </form>
  );
}
