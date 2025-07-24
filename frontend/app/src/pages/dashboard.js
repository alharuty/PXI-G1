import React from "react";
import Navbar from "../components/Navbar";
import { useNavigate } from "react-router-dom";
import { 
  AiOutlineEdit, 
  AiOutlineCamera, 
  AiOutlineUser,
  AiOutlineRobot,
  AiOutlineHeart,
  AiOutlineGithub,
  AiOutlineMail,
  AiOutlineTwitter
} from 'react-icons/ai';

export default function Dashboard() {
  const navigate = useNavigate();

  const features = [
    {
      title: "Generador de Textos",
      description: "Crea contenido para redes sociales, emails y más",
      icon: AiOutlineEdit,
      path: "/text-generator",
      color: "bg-primary-100",
      gradient: "from-primary-100 to-primary-200"
    },
    {
      title: "Generador de Imágenes",
      description: "Genera imágenes únicas con IA usando descripciones",
      icon: AiOutlineCamera,
      path: "/image-generator",
      color: "bg-primary-300",
      gradient: "from-primary-300 to-primary-400"
    },
    {
      title: "Servicios IA",
      description: "Análisis financiero y generación de contenido avanzado",
      icon: AiOutlineRobot,
      path: "/ai-services",
      color: "bg-primary-200",
      gradient: "from-primary-200 to-primary-100"
    },
    {
      title: "Mi Perfil",
      description: "Administra tu información personal",
      icon: AiOutlineUser,
      path: "/profile",
      color: "bg-primary-400",
      gradient: "from-primary-400 to-red-400"
    }
  ];

  return (
    <div className="min-h-screen bg-dark-900 flex flex-col">
      <Navbar />
      
      {/* Contenido principal del dashboard */}
      <div className="flex-grow">
        <div className="max-w-7xl mx-auto py-12 px-4">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-white mb-4">
              Bienvenido a BUDDY
            </h1>
            <p className="text-xl text-gray-300 font-medium">
              Tu plataforma de creación de contenido con inteligencia artificial
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div
                  key={index}
                  onClick={() => navigate(feature.path)}
                  className="bg-dark-800 rounded-xl shadow-xl p-6 cursor-pointer hover:shadow-2xl hover:scale-105 transition-all duration-300 border border-dark-700 hover:border-primary-100"
                >
                  <div className={`w-16 h-16 bg-gradient-to-br ${feature.gradient} rounded-full flex items-center justify-center text-2xl mb-4 shadow-lg`}>
                    <Icon className="text-white" size={28} />
                  </div>
                  <h3 className="text-xl font-bold mb-2 text-white">{feature.title}</h3>
                  <p className="text-gray-400 font-medium leading-relaxed">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Sección de la mascota */}
      <div className="relative">
        <div className="absolute bottom-0 left-8 z-10">
          <div className="group">
            <img 
              src="/mascot.png" 
              alt="Buddy Mascot" 
              className="h-32 w-auto object-contain transition-all duration-300 group-hover:scale-110 drop-shadow-2xl"
            />
            {/* Tooltip de la mascota */}
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <div className="bg-dark-800 text-white px-3 py-2 rounded-lg shadow-lg border border-dark-600 text-sm whitespace-nowrap">
                ¡Hola! Soy Buddy, tu asistente de IA 🤖
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-dark-800"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-dark-800 border-t border-dark-700 mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Logo y descripción */}
            <div className="md:col-span-2">
              <div className="flex items-center mb-4">
                <img 
                  src="/buddylog.png" 
                  alt="Buddy Logo" 
                  className="h-8 w-8 object-contain mr-3"
                />
                <h3 className="text-xl font-bold text-white">BUDDY</h3>
              </div>
              <p className="text-gray-400 mb-4 leading-relaxed">
                Tu plataforma integral de creación de contenido con inteligencia artificial. 
                Genera textos, imágenes y análisis financieros de forma rápida y eficiente.
              </p>
              <div className="flex space-x-4">
                <a 
                  href="#" 
                  className="text-gray-400 hover:text-primary-100 transition-colors"
                  aria-label="Twitter"
                >
                  <AiOutlineTwitter size={20} />
                </a>
                <a 
                  href="#" 
                  className="text-gray-400 hover:text-primary-100 transition-colors"
                  aria-label="GitHub"
                >
                  <AiOutlineGithub size={20} />
                </a>
                <a 
                  href="#" 
                  className="text-gray-400 hover:text-primary-100 transition-colors"
                  aria-label="Email"
                >
                  <AiOutlineMail size={20} />
                </a>
              </div>
            </div>

            {/* Enlaces rápidos */}
            <div>
              <h4 className="text-lg font-semibold text-white mb-4">Enlaces Rápidos</h4>
              <ul className="space-y-2">
                <li>
                  <button 
                    onClick={() => navigate('/text-generator')}
                    className="text-gray-400 hover:text-primary-100 transition-colors"
                  >
                    Generar Textos
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => navigate('/image-generator')}
                    className="text-gray-400 hover:text-primary-100 transition-colors"
                  >
                    Generar Imágenes
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => navigate('/ai-services')}
                    className="text-gray-400 hover:text-primary-100 transition-colors"
                  >
                    Servicios IA
                  </button>
                </li>
                <li>
                  <button 
                    onClick={() => navigate('/profile')}
                    className="text-gray-400 hover:text-primary-100 transition-colors"
                  >
                    Mi Perfil
                  </button>
                </li>
              </ul>
            </div>

            {/* Información */}
            <div>
              <h4 className="text-lg font-semibold text-white mb-4">Soporte</h4>
              <ul className="space-y-2">
                <li>
                  <a href="/help-center" className="text-gray-400 hover:text-primary-100 transition-colors">
                    Centro de Ayuda
                  </a>
                </li>
                <li>
                  <a href="/terms-of-service" className="text-gray-400 hover:text-primary-100 transition-colors">
                    Términos de Servicio
                  </a>
                </li>
                <li>
                  <a href="/privacy-policy" className="text-gray-400 hover:text-primary-100 transition-colors">
                    Política de Privacidad
                  </a>
                </li>
                <li>
                  <a href="/contact" className="text-gray-400 hover:text-primary-100 transition-colors">
                    Contacto
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Línea divisoria y copyright */}
          <div className="border-t border-dark-700 mt-8 pt-6">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="flex items-center text-gray-400 text-sm">
                <span>© 2025 BUDDY. Hecho con</span>
                <AiOutlineHeart className="mx-1 text-red-400" size={16} />
                <span>para crear contenido increíble.</span>
              </div>
              <div className="text-gray-400 text-sm mt-2 md:mt-0">
                Versión 1.0.0
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
