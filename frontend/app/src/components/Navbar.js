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
    <nav className="bg-gray-50 border-b border-gray-200 text-gray-800 p-4 shadow-sm">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        {/* Logo y título */}
        <div className="flex items-center space-x-3">
          <img 
            src="/buddylog.png" 
            alt="AI Buddy Logo" 
            className="h-24 w-24 object-contain"
          />
          
        </div>
        
        <div className="flex space-x-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`flex items-center px-4 py-2 rounded-lg transition-all font-semibold ${
                  location.pathname === item.path
                    ? 'bg-primary-100 text-white shadow-md'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-primary-200'
                }`}
              >
                <Icon className="mr-2" size={18} />
                {item.label}
              </button>
            );
          })}
          
          <button
            onClick={handleLogout}
            className="flex items-center px-4 py-2 bg-primary-400 hover:bg-red-500 text-white rounded-lg transition-colors font-semibold ml-4"
          >
            <AiOutlineLogout className="mr-2" size={18} />
            Cerrar Sesión
          </button>
        </div>
      </div>
    </nav>
  );
}