import React from 'react';
import { signOut } from 'firebase/auth';
import { auth } from '../firebase';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  AiOutlineHome, 
  AiOutlineEdit, 
  AiOutlineCamera, 
  AiOutlineUser,
  AiOutlineLogout,
  AiOutlineRobot
} from 'react-icons/ai';

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await signOut(auth);
    navigate('/');
  };

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: AiOutlineHome },
    { path: '/text-generator', label: 'Generar Textos', icon: AiOutlineEdit },
    { path: '/image-generator', label: 'Generar Imágenes', icon: AiOutlineCamera },
    { path: '/ai-services', label: 'Servicios IA', icon: AiOutlineRobot },
    { path: '/profile', label: 'Perfil', icon: AiOutlineUser },
  ];

  return (
    <nav className="bg-primary-200 text-white p-4 shadow-lg">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold">AI Creator</h1>
        
        <div className="flex space-x-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? 'bg-primary-300 text-primary-200'
                    : 'hover:bg-primary-100'
                }`}
              >
                <Icon className="mr-2" size={18} />
                {item.label}
              </button>
            );
          })}
          
          <button
            onClick={handleLogout}
            className="flex items-center px-4 py-2 bg-primary-400 hover:bg-red-600 rounded-lg transition-colors"
          >
            <AiOutlineLogout className="mr-2" size={18} />
            Cerrar Sesión
          </button>
        </div>
      </div>
    </nav>
  );
}