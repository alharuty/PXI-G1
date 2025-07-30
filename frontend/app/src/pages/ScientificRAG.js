import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import ArticleSearch from '../components/ArticleSearch';
import KnowledgeQA from '../components/KnowledgeQA';
import ResponseComparison from '../components/ResponseComparison';
import { 
  AiOutlineFileSearch,
  AiOutlineQuestionCircle,
  AiOutlineCompass,
  AiOutlineBook
} from 'react-icons/ai';

export default function ScientificRAG() {
  const [activeTab, setActiveTab] = useState('search');

  const tabs = [
    {
      id: 'search',
      name: 'Búsqueda de Artículos',
      icon: AiOutlineFileSearch,
      component: ArticleSearch,
      description: 'Busca y descarga artículos científicos de arXiv'
    },
    {
      id: 'qa',
      name: 'Consultar Base de Datos',
      icon: AiOutlineQuestionCircle,
      component: KnowledgeQA,
      description: 'Consulta la base de datos de artículos científicos'
    },
    {
      id: 'comparison',
      name: 'Evaluar Respuestas',
      icon: AiOutlineCompass,
      component: ResponseComparison,
      description: 'Evalúa la efectividad de respuestas RAG vs respuestas simples'
    }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="min-h-screen bg-dark-900">
      <Navbar />
      
      <div className="max-w-7xl mx-auto py-8 px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-full flex items-center justify-center mr-4">
              <AiOutlineBook className="text-white" size={32} />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-white">RAG Científico</h1>
              <p className="text-gray-300 text-lg">Sistema de Recuperación y Generación Aumentada para Artículos Científicos</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-dark-800 rounded-xl p-6 mb-6 border border-dark-700">
          <div className="flex flex-wrap gap-4 mb-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-6 py-4 rounded-lg transition-all transform hover:scale-105 ${
                    activeTab === tab.id
                      ? 'bg-gradient-to-r from-primary-100 to-primary-200 text-white shadow-lg'
                      : 'bg-dark-700 text-gray-300 hover:bg-dark-600 hover:text-white border border-dark-600'
                  }`}
                >
                  <Icon className="mr-3" size={20} />
                  <div className="text-left">
                    <div className="font-medium">{tab.name}</div>
                    <div className="text-xs opacity-80">{tab.description}</div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Active Component */}
          <div className="min-h-[600px]">
            {ActiveComponent && <ActiveComponent />}
          </div>
        </div>
      </div>
    </div>
  );
}