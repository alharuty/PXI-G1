import React, { useState, useEffect } from 'react';
import { doc, getDoc, updateDoc } from 'firebase/firestore';
import { auth, db } from '../firebase';
import { useAuthState } from 'react-firebase-hooks/auth';
import Navbar from '../components/Navbar';
import { 
  AiOutlineEdit, 
  AiOutlineSave, 
  AiOutlineClose,
  AiOutlineUser,
  AiOutlineIdcard,
  AiOutlineCalendar
} from 'react-icons/ai';

export default function Profile() {
  const [user] = useAuthState(auth);
  const [userInfo, setUserInfo] = useState({
    nombre: '',
    apellido: '',
    email: '',
    tipo: 'particular',
    bio: ''
  });
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchUserData = async () => {
      if (user) {
        const userDoc = await getDoc(doc(db, 'users', user.uid));
        if (userDoc.exists()) {
          setUserInfo(userDoc.data());
        }
      }
    };
    fetchUserData();
  }, [user]);

  const handleChange = (e) => {
    setUserInfo({ ...userInfo, [e.target.name]: e.target.value });
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await updateDoc(doc(db, 'users', user.uid), userInfo);
      setIsEditing(false);
      alert('Perfil actualizado correctamente');
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Error al actualizar el perfil');
    }
    setIsSaving(false);
  };

  const inputClass = (isEditable) => `w-full p-3 border rounded-lg transition-colors ${
    isEditable 
      ? 'bg-dark-700 border-dark-600 text-white focus:ring-2 focus:ring-primary-100 focus:border-primary-100' 
      : 'border-dark-600 bg-dark-800 text-gray-400'
  }`;

  return (
    <div className="min-h-screen bg-dark-900">
      <Navbar />
      
      <div className="max-w-2xl mx-auto py-8 px-4">
        <div className="bg-dark-800 rounded-xl shadow-2xl p-6 border border-dark-700">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex items-center justify-center mr-4">
                <AiOutlineUser className="text-white" size={24} />
              </div>
              <h1 className="text-3xl font-bold text-white">Mi Perfil</h1>
            </div>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center px-4 py-2 bg-gradient-to-r from-primary-100 to-primary-200 text-white rounded-lg hover:from-primary-200 hover:to-primary-100 transition-all shadow-md"
              >
                <AiOutlineEdit className="mr-2" size={16} />
                Editar
              </button>
            ) : (
              <div className="space-x-2">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors shadow-md"
                >
                  <AiOutlineSave className="mr-2" size={16} />
                  {isSaving ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
                >
                  <AiOutlineClose className="mr-2" size={16} />
                  Cancelar
                </button>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Nombre
                </label>
                <input
                  type="text"
                  name="nombre"
                  value={userInfo.nombre}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className={inputClass(isEditing)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Apellido
                </label>
                <input
                  type="text"
                  name="apellido"
                  value={userInfo.apellido}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className={inputClass(isEditing)}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={userInfo.email}
                disabled={true}
                className="w-full p-3 border border-dark-600 bg-dark-800 rounded-lg text-gray-500"
              />
              <p className="text-xs text-gray-500 mt-1">El email no se puede modificar</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Tipo de cuenta
              </label>
              <select
                name="tipo"
                value={userInfo.tipo}
                onChange={handleChange}
                disabled={!isEditing}
                className={inputClass(isEditing)}
              >
                <option value="particular">Particular</option>
                <option value="empresa">Empresa</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Biografía
              </label>
              <textarea
                name="bio"
                value={userInfo.bio}
                onChange={handleChange}
                disabled={!isEditing}
                rows="4"
                className={inputClass(isEditing)}
                placeholder="Cuéntanos sobre ti..."
              />
            </div>
          </div>

          {/* Información adicional */}
          <div className="mt-8 pt-6 border-t border-dark-700">
            <h3 className="flex items-center text-lg font-medium text-white mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex items-center justify-center mr-3">
                <AiOutlineIdcard className="text-white" size={16} />
              </div>
              Información de la cuenta
            </h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div className="bg-dark-700 p-4 rounded-lg border border-dark-600">
                <span className="font-medium text-gray-300">Usuario ID:</span>
                <p className="text-gray-400 break-all mt-1">{user?.uid}</p>
              </div>
              <div className="bg-dark-700 p-4 rounded-lg border border-dark-600">
                <div className="flex items-start">
                  <AiOutlineCalendar className="mr-2 text-primary-100 mt-0.5" size={16} />
                  <div>
                    <span className="font-medium text-gray-300">Fecha de registro:</span>
                    <p className="text-gray-400 mt-1">
                      {user?.metadata?.creationTime 
                        ? new Date(user.metadata.creationTime).toLocaleDateString()
                        : 'No disponible'
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}