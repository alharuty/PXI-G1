import React from "react";
import Navbar from "../components/Navbar";
import { useNavigate } from "react-router-dom";
import { 
  AiOutlineEdit, 
  AiOutlineCamera, 
  AiOutlineUser 
} from 'react-icons/ai';

export default function Dashboard() {
  const navigate = useNavigate();

  const features = [
    {
      title: "Generador de Textos",
      description: "Crea contenido para redes sociales, emails y más",
      icon: AiOutlineEdit,
      path: "/text-generator",
      color: "bg-primary-100"
    },
    {
      title: "Generador de Imágenes",
      description: "Genera imágenes únicas con IA usando descripciones",
      icon: AiOutlineCamera,
      path: "/image-generator",
      color: "bg-primary-300"
    },
    {
      title: "Mi Perfil",
      description: "Administra tu información personal",
      icon: AiOutlineUser,
      path: "/profile",
      color: "bg-primary-400"
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto py-12 px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Bienvenido a AI Creator
          </h1>
          <p className="text-xl text-gray-600 font-medium">
            Tu plataforma de creación de contenido con inteligencia artificial
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                onClick={() => navigate(feature.path)}
                className="bg-white rounded-lg shadow-lg p-6 cursor-pointer hover:shadow-xl transition-all transform hover:scale-105"
              >
                <div className={`w-16 h-16 ${feature.color} rounded-full flex items-center justify-center text-2xl mb-4`}>
                  <Icon className="text-white" size={28} />
                </div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-600 font-medium">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
