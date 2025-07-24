import React, { useState } from 'react';
import axios from 'axios';
import Navbar from './Navbar';
import { auth } from "../firebase";

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
      const user = auth.currentUser;
      const uid = user?.uid || null;

      const res = await axios.post('http://localhost:8000/news-nlp', {
        prompt,
        language,
        coin_name: coinName || null,
        uid: uid,
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
      const res = await axios.post('http://localhost:8001/generate', {
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
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Servicios de IA</h1>
          
          {/* Selector de servicio */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Tipo de servicio:
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setServiceType('financial')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  serviceType === 'financial'
                    ? 'border-primary-100 bg-primary-100 text-white'
                    : 'border-gray-300 hover:border-primary-200 bg-white'
                }`}
              >
                <div className="font-medium">Análisis Financiero</div>
                <div className="text-sm opacity-70 mt-1">
                  Análisis de mercados y criptomonedas
                </div>
              </button>
              
              <button
                onClick={() => setServiceType('content')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  serviceType === 'content'
                    ? 'border-primary-100 bg-primary-100 text-white'
                    : 'border-gray-300 hover:border-primary-200 bg-white'
                }`}
              >
                <div className="font-medium">Generación de Contenido</div>
                <div className="text-sm opacity-70 mt-1">
                  Contenido para redes sociales
                </div>
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Input principal */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
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
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-100 focus:border-transparent"
                rows="4"
                required
              />
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {/* Selector de idioma */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Idioma de respuesta:
                </label>
                <select 
                  value={language} 
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-100 focus:border-transparent"
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
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Criptomoneda específica (opcional):
                  </label>
                  <input
                    type="text"
                    value={coinName}
                    onChange={(e) => setCoinName(e.target.value)}
                    placeholder="Ej: Bitcoin, Ethereum"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-100 focus:border-transparent"
                  />
                </div>
              )}
            </div>

            {/* Botón de envío */}
            <button
              type="submit"
              disabled={!prompt.trim() || isLoading}
              className={`w-full py-3 px-6 rounded-lg font-medium transition-colors ${
                !prompt.trim() || isLoading
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-primary-100 hover:bg-primary-200 text-white'
              }`}
            >
              {isLoading ? 'Procesando...' : 'Generar Respuesta'}
            </button>
          </form>

          {/* Resultado */}
          {response && (
            <div className="mt-6 p-4 bg-primary-50 rounded-lg">
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Respuesta del Agente:
              </h3>
              <div className="whitespace-pre-wrap text-gray-700 bg-white p-4 rounded border">
                {response}
              </div>
              <div className="mt-3 flex space-x-3">
                <button
                  onClick={() => navigator.clipboard.writeText(response)}
                  className="px-4 py-2 bg-primary-100 text-white rounded hover:bg-primary-200 transition-colors"
                >
                  Copiar
                </button>
                <button
                  onClick={() => setResponse('')}
                  className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
                >
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
