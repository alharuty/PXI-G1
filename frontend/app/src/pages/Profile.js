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

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-2xl mx-auto py-8 px-4">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center">
              <AiOutlineUser className="text-primary-100 mr-3" size={32} />
              <h1 className="text-3xl font-bold text-gray-900">Mi Perfil</h1>
            </div>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="flex items-center px-4 py-2 bg-primary-100 text-white rounded hover:bg-primary-200 transition-colors"
              >
                <AiOutlineEdit className="mr-2" size={16} />
                Editar
              </button>
            ) : (
              <div className="space-x-2">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
                >
                  <AiOutlineSave className="mr-2" size={16} />
                  {isSaving ? 'Guardando...' : 'Guardar'}
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="flex items-center px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
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
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre
                </label>
                <input
                  type="text"
                  name="nombre"
                  value={userInfo.nombre}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className={`w-full p-3 border rounded-lg transition-colors ${
                    isEditing 
                      ? 'border-gray-300 focus:ring-2 focus:ring-primary-100 focus:border-primary-100' 
                      : 'border-gray-200 bg-gray-50'
                  }`}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Apellido
                </label>
                <input
                  type="text"
                  name="apellido"
                  value={userInfo.apellido}
                  onChange={handleChange}
                  disabled={!isEditing}
                  className={`w-full p-3 border rounded-lg transition-colors ${
                    isEditing 
                      ? 'border-gray-300 focus:ring-2 focus:ring-primary-100 focus:border-primary-100' 
                      : 'border-gray-200 bg-gray-50'
                  }`}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={userInfo.email}
                disabled={true}
                className="w-full p-3 border border-gray-200 bg-gray-50 rounded-lg text-gray-500"
              />
              <p className="text-xs text-gray-500 mt-1">El email no se puede modificar</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de cuenta
              </label>
              <select
                name="tipo"
                value={userInfo.tipo}
                onChange={handleChange}
                disabled={!isEditing}
                className={`w-full p-3 border rounded-lg transition-colors ${
                  isEditing 
                    ? 'border-gray-300 focus:ring-2 focus:ring-primary-100 focus:border-primary-100' 
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <option value="particular">Particular</option>
                <option value="empresa">Empresa</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Biografía
              </label>
              <textarea
                name="bio"
                value={userInfo.bio}
                onChange={handleChange}
                disabled={!isEditing}
                rows="4"
                className={`w-full p-3 border rounded-lg transition-colors ${
                  isEditing 
                    ? 'border-gray-300 focus:ring-2 focus:ring-primary-100 focus:border-primary-100' 
                    : 'border-gray-200 bg-gray-50'
                }`}
              />
            </div>
          </div>

          {/* Información adicional */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <h3 className="flex items-center text-lg font-medium text-gray-900 mb-4">
              <AiOutlineIdcard className="mr-2 text-primary-100" size={20} />
              Información de la cuenta
            </h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Usuario ID:</span>
                <p className="text-gray-600 break-all">{user?.uid}</p>
              </div>
              <div className="flex items-start">
                <AiOutlineCalendar className="mr-2 text-primary-100 mt-0.5" size={16} />
                <div>
                  <span className="font-medium">Fecha de registro:</span>
                  <p className="text-gray-600">
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
  );
}