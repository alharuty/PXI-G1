import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { 
  AiOutlineTwitter, 
  AiOutlineFacebook, 
  AiOutlineLinkedin, 
  AiOutlineMail, 
  AiOutlineInstagram,
  AiOutlineCopy,
  AiOutlineClear
} from 'react-icons/ai';

export default function TextGenerator() {
  const [selectedPlatform, setSelectedPlatform] = useState('twitter');
  const [prompt, setPrompt] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('es'); // ⭐ NUEVO
  const [generatedText, setGeneratedText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // ⭐ CONFIGURACIÓN DE LA API BASE URL
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  const platforms = [
    { id: 'twitter', name: 'Twitter', icon: AiOutlineTwitter, maxChars: 280, color: 'from-blue-400 to-blue-500' },
    { id: 'facebook', name: 'Facebook', icon: AiOutlineFacebook, maxChars: 2000, color: 'from-blue-600 to-blue-700' },
    { id: 'linkedin', name: 'LinkedIn', icon: AiOutlineLinkedin, maxChars: 1300, color: 'from-blue-700 to-blue-800' },
    { id: 'email', name: 'Email', icon: AiOutlineMail, maxChars: null, color: 'from-gray-600 to-gray-700' },
    { id: 'instagram', name: 'Instagram', icon: AiOutlineInstagram, maxChars: 2200, color: 'from-pink-500 to-purple-600' },
  ];

  // ⭐ NUEVO: Opciones de idioma
  const languages = [
    { code: 'es', name: 'Español', flag: '🇪🇸' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
    { code: 'fr', name: 'Français', flag: '🇫🇷' },
    { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  ];

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      console.log('🔗 API URL:', `${API_BASE_URL}/generate`); // Debug
      console.log('📤 Payload:', { platform: selectedPlatform, topic: prompt, language: selectedLanguage });

      const response = await axios.post(`${API_BASE_URL}/generate`, {
        platform: selectedPlatform,
        topic: prompt,
        language: selectedLanguage // ⭐ AGREGAR IDIOMA
      });
      
      console.log('📥 Response:', response.data); // Debug
      setGeneratedText(response.data.content);
    } catch (error) {
      console.error('❌ Error generating text:', error);
      console.error('🔍 Error details:', error.response?.data); // Debug mejorado
      
      if (error.response?.status === 404) {
        setGeneratedText('❌ Error: El servidor no se encuentra disponible. Verifica que el backend esté corriendo en http://localhost:8000');
      } else {
        setGeneratedText('❌ Error al generar el texto. Por favor, intenta nuevamente.');
      }
    }
    setIsGenerating(false);
  };

  return (
    <div className="min-h-screen bg-dark-900">
      <Navbar />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-dark-800 rounded-xl shadow-2xl p-6 border border-dark-700">
          <h1 className="text-3xl font-bold text-white mb-6">Generador de Textos</h1>
          
          {/* ⭐ NUEVO: Selector de idioma */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Selecciona el idioma:
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {languages.map((language) => (
                <button
                  key={language.code}
                  onClick={() => setSelectedLanguage(language.code)}
                  className={`p-3 rounded-lg border-2 transition-all transform hover:scale-105 ${
                    selectedLanguage === language.code
                      ? 'border-primary-100 bg-gradient-to-br from-primary-100 to-primary-200 text-white shadow-lg'
                      : 'border-dark-600 bg-dark-700 hover:border-primary-200 text-gray-300 hover:text-white'
                  }`}
                >
                  <div className="text-2xl mb-1">{language.flag}</div>
                  <div className="text-sm font-medium">{language.name}</div>
                </button>
              ))}
            </div>
          </div>
          
          {/* Selector de plataforma */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Selecciona la plataforma:
            </label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {platforms.map((platform) => {
                const Icon = platform.icon;
                return (
                  <button
                    key={platform.id}
                    onClick={() => setSelectedPlatform(platform.id)}
                    className={`p-4 rounded-lg border-2 transition-all transform hover:scale-105 ${
                      selectedPlatform === platform.id
                        ? 'border-primary-100 bg-gradient-to-br from-primary-100 to-primary-200 text-white shadow-lg'
                        : 'border-dark-600 bg-dark-700 hover:border-primary-200 text-gray-300 hover:text-white'
                    }`}
                  >
                    <Icon className="mx-auto mb-2" size={24} />
                    <div className="text-sm font-medium">{platform.name}</div>
                    {platform.maxChars && (
                      <div className="text-xs opacity-70 mt-1">
                        Max: {platform.maxChars} chars
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Input del prompt */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Describe el contenido que quieres crear:
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ej: Un post sobre los beneficios del ejercicio matutino, tono motivacional..."
              className="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              rows="4"
            />
          </div>

          {/* ⭐ INFORMACIÓN DE DEBUG */}
          <div className="mb-4 p-3 bg-dark-700 rounded text-xs text-gray-400">
            🔗 API: {API_BASE_URL} | 🌐 Plataforma: {selectedPlatform} | 🗣️ Idioma: {selectedLanguage}
          </div>

          {/* Botón generar */}
          <button
            onClick={handleGenerate}
            disabled={!prompt.trim() || isGenerating}
            className={`w-full py-3 px-6 rounded-lg font-medium transition-all ${
              !prompt.trim() || isGenerating
                ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                : 'bg-gradient-to-r from-primary-100 to-primary-200 hover:from-primary-200 hover:to-primary-100 text-white shadow-lg'
            }`}
          >
            {isGenerating ? 'Generando...' : 'Generar Texto'}
          </button>

          {/* Resultado */}
          {generatedText && (
            <div className="mt-6 p-4 bg-dark-700 rounded-lg border border-dark-600">
              <h3 className="text-lg font-medium text-white mb-2">Texto Generado:</h3>
              <div className="whitespace-pre-wrap text-gray-300 bg-dark-900 p-4 rounded border border-dark-600">
                {generatedText}
              </div>
              <div className="mt-3 flex space-x-3">
                <button
                  onClick={() => navigator.clipboard.writeText(generatedText)}
                  className="flex items-center px-4 py-2 bg-primary-100 text-white rounded hover:bg-primary-200 transition-colors"
                >
                  <AiOutlineCopy className="mr-2" size={16} />
                  Copiar
                </button>
                <button
                  onClick={() => setGeneratedText('')}
                  className="flex items-center px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500 transition-colors"
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