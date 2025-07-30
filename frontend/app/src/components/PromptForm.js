import React, { useState } from 'react';
import axios from 'axios';
import Navbar from './Navbar';
import { 
  AiOutlineLineChart,
  AiOutlineDollarCircle,
  AiOutlineCopy,
  AiOutlineClear,
  AiOutlineRise,        // ⭐ CAMBIAR: AiOutlineTrendingUp → AiOutlineRise
  AiOutlineStock        // ⭐ ESTE TAMPOCO EXISTE, CAMBIAR POR AiOutlineBarChart
} from 'react-icons/ai';
import { auth } from "../firebase";

function PromptForm() {
  const [prompt, setPrompt] = useState('');
  const [language, setLanguage] = useState('es');
  const [coinName, setCoinName] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
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

  const handleClear = () => {
    setPrompt('');
    setCoinName('');
    setResponse('');
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(response);
    // Pequeña animación visual o feedback
    const button = document.getElementById('copy-button');
    if (button) {
      button.textContent = '✅ Copiado';
      setTimeout(() => {
        button.innerHTML = '<svg class="mr-2" width="16" height="16">...</svg>Copiar';
      }, 2000);
    }
  };

  return (
    <div className="min-h-screen bg-dark-900">
      <Navbar />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-dark-800 rounded-xl shadow-2xl p-6 border border-dark-700">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-primary-100 to-primary-200 rounded-xl flex items-center justify-center mx-auto mb-4">
              <AiOutlineLineChart className="text-white" size={32} />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Análisis Financiero Inteligente</h1>
            <p className="text-gray-400 text-lg">
              Obtén análisis detallados de mercados, criptomonedas y tendencias financieras
            </p>
          </div>

          {/* Features Info */}
          <div className="grid md:grid-cols-3 gap-4 mb-8">
            <div className="bg-dark-700 p-4 rounded-lg border border-dark-600 text-center">
              <AiOutlineRise className="text-green-400 mx-auto mb-2" size={24} />
              <h3 className="text-white font-medium mb-1">Análisis de Tendencias</h3>
              <p className="text-gray-400 text-sm">Seguimiento de movimientos del mercado</p>
            </div>
            <div className="bg-dark-700 p-4 rounded-lg border border-dark-600 text-center">
              <AiOutlineDollarCircle className="text-yellow-400 mx-auto mb-2" size={24} />
              <h3 className="text-white font-medium mb-1">Datos de Criptomonedas</h3>
              <p className="text-gray-400 text-sm">Información actualizada de precios</p>
            </div>
            <div className="bg-dark-700 p-4 rounded-lg border border-dark-600 text-center">
              <AiOutlineLineChart className="text-blue-400 mx-auto mb-2" size={24} />
              <h3 className="text-white font-medium mb-1">Análisis de Acciones</h3>
              <p className="text-gray-400 text-sm">Evaluación de mercados bursátiles</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Input principal */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Consulta sobre mercado financiero:
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ej: Analiza el rendimiento de Bitcoin en el último mes, ¿Cuál es la tendencia actual del S&P 500?, Compara Ethereum vs Solana"
                className="w-full p-4 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent transition-all"
                rows="4"
                required
              />
            </div>

            <div className="grid md:grid-cols-2 gap-6">
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
                  <option value="es">🇪🇸 Español</option>
                  <option value="en">🇺🇸 Inglés</option>
                  <option value="fr">🇫🇷 Francés</option>
                  <option value="it">🇮🇹 Italiano</option>
                </select>
              </div>

              {/* Campo de criptomoneda */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Criptomoneda específica (opcional):
                </label>
                <input
                  type="text"
                  value={coinName}
                  onChange={(e) => setCoinName(e.target.value)}
                  placeholder="Ej: Bitcoin, Ethereum, Solana, Cardano"
                  className="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  💡 Especifica una criptomoneda para obtener datos de precio en tiempo real
                </p>
              </div>
            </div>

            {/* Botones de acción */}
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={!prompt.trim() || isLoading}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all flex items-center justify-center ${
                  !prompt.trim() || isLoading
                    ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                    : 'bg-gradient-to-r from-primary-100 to-primary-200 hover:from-primary-200 hover:to-primary-100 text-white shadow-lg transform hover:scale-105'
                }`}
              >
                <AiOutlineLineChart className="mr-2" size={20} />
                {isLoading ? 'Analizando mercados...' : 'Generar Análisis Financiero'}
              </button>
              
              <button
                type="button"
                onClick={handleClear}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
              >
                <AiOutlineClear size={20} />
              </button>
            </div>
          </form>

          {/* Resultado */}
          {response && (
            <div className="mt-8 p-6 bg-dark-700 rounded-lg border border-dark-600">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-white flex items-center">
                  <AiOutlineLineChart className="mr-2 text-primary-100" size={20} />
                  Análisis Financiero:
                </h3>
                <div className="flex space-x-3">
                  <button
                    id="copy-button"
                    onClick={copyToClipboard}
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
              
              <div className="whitespace-pre-wrap text-gray-300 bg-dark-900 p-4 rounded-lg border border-dark-600 leading-relaxed">
                {response}
              </div>
              
              {/* Metadata del análisis */}
              <div className="mt-4 pt-4 border-t border-dark-600">
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span>📊 Análisis generado con IA financiera</span>
                  <span>{new Date().toLocaleString('es-ES')}</span>
                </div>
              </div>
            </div>
          )}

          {/* Tips de uso */}
          {!response && (
            <div className="mt-8 bg-blue-900 bg-opacity-20 rounded-lg p-4 border border-blue-800">
              <h4 className="text-blue-300 font-medium mb-2">💡 Consejos para mejores análisis:</h4>
              <ul className="text-blue-200 text-sm space-y-1">
                <li>• Especifica el marco temporal: "en el último mes", "esta semana", etc.</li>
                <li>• Menciona métricas específicas: precio, volumen, capitalización de mercado</li>
                <li>• Compara activos: "Bitcoin vs Ethereum", "Apple vs Microsoft"</li>
                <li>• Incluye el contexto: "durante la subida de tasas", "después del último halving"</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PromptForm;
