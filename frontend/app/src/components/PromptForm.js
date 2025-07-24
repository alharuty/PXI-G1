import React, { useState } from 'react';
import axios from 'axios';
import Navbar from './Navbar';
import { 
  AiOutlineRobot,
  AiOutlineLineChart,
  AiOutlineEdit,
  AiOutlineCopy,
  AiOutlineClear
} from 'react-icons/ai';

function PromptForm() {
  const [prompt, setPrompt] = useState('');
  const [language, setLanguage] = useState('es');
  const [coinName, setCoinName] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [serviceType, setServiceType] = useState('financial'); // 'financial' o 'content'

  const handleFinancialSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const res = await axios.post('http://localhost:8000/news-nlp', {
        prompt,
        language,
        coin_name: coinName || null,
      });
      setResponse(res.data.response);
    } catch (error) {
      console.error('Error al generar respuesta financiera:', error);
      setResponse('Ocurrió un error al procesar tu solicitud financiera.');
    }
    setIsLoading(false);
  };

  const handleContentSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      // Usando el endpoint del backend/app/main.py
      const res = await axios.post('http://localhost:8000/generate', {
        platform: 'twitter', // Puedes hacer esto dinámico
        topic: prompt,
      });
      setResponse(res.data.content);
    } catch (error) {
      console.error('Error al generar contenido:', error);
      setResponse('Ocurrió un error al procesar tu solicitud de contenido.');
    }
    setIsLoading(false);
  };

  const handleSubmit = serviceType === 'financial' ? handleFinancialSubmit : handleContentSubmit;

  return (
    <div className="min-h-screen bg-dark-900">
      <Navbar />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-dark-800 rounded-xl shadow-2xl p-6 border border-dark-700">
          <div className="flex items-center mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex items-center justify-center mr-4">
              <AiOutlineRobot className="text-white" size={24} />
            </div>
            <h1 className="text-3xl font-bold text-white">Servicios de IA</h1>
          </div>
          
          {/* Selector de servicio */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Tipo de servicio:
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setServiceType('financial')}
                className={`p-6 rounded-xl border-2 transition-all transform hover:scale-105 ${
                  serviceType === 'financial'
                    ? 'border-primary-100 bg-gradient-to-br from-primary-100 to-primary-200 text-white shadow-lg'
                    : 'border-dark-600 bg-dark-700 hover:border-primary-200 text-gray-300'
                }`}
              >
                <AiOutlineLineChart className="mx-auto mb-3" size={32} />
                <div className="font-bold text-lg">Análisis Financiero</div>
                <div className="text-sm opacity-80 mt-2">
                  Análisis de mercados y criptomonedas
                </div>
              </button>
              
              <button
                onClick={() => setServiceType('content')}
                className={`p-6 rounded-xl border-2 transition-all transform hover:scale-105 ${
                  serviceType === 'content'
                    ? 'border-primary-100 bg-gradient-to-br from-primary-100 to-primary-200 text-white shadow-lg'
                    : 'border-dark-600 bg-dark-700 hover:border-primary-200 text-gray-300'
                }`}
              >
                <AiOutlineEdit className="mx-auto mb-3" size={32} />
                <div className="font-bold text-lg">Generación de Contenido</div>
                <div className="text-sm opacity-80 mt-2">
                  Contenido para redes sociales
                </div>
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Input principal */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                {serviceType === 'financial' 
                  ? 'Consulta sobre mercado financiero:' 
                  : 'Describe el contenido que quieres crear:'
                }
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={
                  serviceType === 'financial'
                    ? "Ej: Analiza el rendimiento de Bitcoin en el último mes"
                    : "Ej: Un post motivacional sobre emprendimiento"
                }
                className="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
                rows="4"
                required
              />
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {/* Selector de idioma */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Idioma de respuesta:
                </label>
                <select 
                  value={language} 
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-100 focus:border-transparent"
                >
                  <option value="es">Español</option>
                  <option value="en">Inglés</option>
                  <option value="fr">Francés</option>
                  <option value="it">Italiano</option>
                </select>
              </div>

              {/* Campo de criptomoneda (solo para análisis financiero) */}
              {serviceType === 'financial' && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Criptomoneda específica (opcional):
                  </label>
                  <input
                    type="text"
                    value={coinName}
                    onChange={(e) => setCoinName(e.target.value)}
                    placeholder="Ej: Bitcoin, Ethereum"
                    className="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
                  />
                </div>
              )}
            </div>

            {/* Botón de envío */}
            <button
              type="submit"
              disabled={!prompt.trim() || isLoading}
              className={`w-full py-3 px-6 rounded-lg font-medium transition-all ${
                !prompt.trim() || isLoading
                  ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                  : 'bg-gradient-to-r from-primary-100 to-primary-200 hover:from-primary-200 hover:to-primary-100 text-white shadow-lg transform hover:scale-105'
              }`}
            >
              {isLoading ? 'Procesando...' : 'Generar Respuesta'}
            </button>
          </form>

          {/* Resultado */}
          {response && (
            <div className="mt-6 p-4 bg-dark-700 rounded-lg border border-dark-600">
              <h3 className="text-lg font-medium text-white mb-3">
                Respuesta del Agente:
              </h3>
              <div className="whitespace-pre-wrap text-gray-300 bg-dark-900 p-4 rounded-lg border border-dark-600">
                {response}
              </div>
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={() => navigator.clipboard.writeText(response)}
                  className="flex items-center px-4 py-2 bg-primary-100 text-white rounded-lg hover:bg-primary-200 transition-colors shadow-md"
                >
                  <AiOutlineCopy className="mr-2" size={16} />
                  Copiar
                </button>
                <button
                  onClick={() => setResponse('')}
                  className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
                >
                  <AiOutlineClear className="mr-2" size={16} />
                  Limpiar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PromptForm;
