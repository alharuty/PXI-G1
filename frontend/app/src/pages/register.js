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

  const inputClass = "w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <input 
          name="nombre" 
          placeholder="Nombre" 
          value={form.nombre} 
          onChange={handleChange} 
          className={inputClass}
          required 
        />
        <input 
          name="apellido" 
          placeholder="Apellido" 
          value={form.apellido} 
          onChange={handleChange} 
          className={inputClass}
          required 
        />
      </div>
      <input 
        name="email" 
        type="email" 
        placeholder="Email" 
        value={form.email} 
        onChange={handleChange} 
        className={inputClass}
        required 
      />
      <input 
        name="password" 
        type="password" 
        placeholder="Contraseña" 
        value={form.password} 
        onChange={handleChange} 
        className={inputClass}
        required 
      />
      <select 
        name="tipo" 
        value={form.tipo} 
        onChange={handleChange} 
        className={inputClass}
        required
      >
        <option value="particular">Particular</option>
        <option value="empresa">Empresa</option>
      </select>
      <textarea 
        name="bio" 
        placeholder="Biografía" 
        value={form.bio} 
        onChange={handleChange} 
        className={inputClass}
        rows="3"
        required 
      />
      <button 
        type="submit"
        className="w-full py-3 bg-gradient-to-r from-primary-100 to-primary-200 text-white font-semibold rounded-lg hover:from-primary-200 hover:to-primary-100 transition-all shadow-lg"
      >
        Registrarse
      </button>
    </form>
  );
}
