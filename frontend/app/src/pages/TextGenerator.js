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
  const [generatedText, setGeneratedText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const platforms = [
    { id: 'twitter', name: 'Twitter', icon: AiOutlineTwitter, maxChars: 280, color: 'text-blue-400' },
    { id: 'facebook', name: 'Facebook', icon: AiOutlineFacebook, maxChars: 2000, color: 'text-blue-600' },
    { id: 'linkedin', name: 'LinkedIn', icon: AiOutlineLinkedin, maxChars: 1300, color: 'text-blue-700' },
    { id: 'email', name: 'Email', icon: AiOutlineMail, maxChars: null, color: 'text-gray-600' },
    { id: 'instagram', name: 'Instagram', icon: AiOutlineInstagram, maxChars: 2200, color: 'text-pink-500' },
  ];

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      // Conectando con tu backend real
      const response = await axios.post('http://localhost:8001/generate', {
        platform: selectedPlatform,
        topic: prompt,
      });
      setGeneratedText(response.data.content);
    } catch (error) {
      console.error('Error generating text:', error);
      setGeneratedText('Error al generar el texto. Por favor, intenta nuevamente.');
    }
    setIsGenerating(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Generador de Textos</h1>
          
          {/* Selector de plataforma */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
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
                        ? 'border-primary-100 bg-primary-100 text-white shadow-lg'
                        : 'border-gray-300 hover:border-primary-200 bg-white'
                    }`}
                  >
                    <Icon 
                      className={`mx-auto mb-2 ${selectedPlatform === platform.id ? 'text-white' : platform.color}`} 
                      size={24} 
                    />
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
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Describe el contenido que quieres crear:
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ej: Un post sobre los beneficios del ejercicio matutino, tono motivacional..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              rows="4"
            />
          </div>

          {/* Botón generar */}
          <button
            onClick={handleGenerate}
            disabled={!prompt.trim() || isGenerating}
            className={`w-full py-3 px-6 rounded-lg font-medium transition-colors ${
              !prompt.trim() || isGenerating
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-primary-100 hover:bg-primary-200 text-white'
            }`}
          >
            {isGenerating ? 'Generando...' : 'Generar Texto'}
          </button>

          {/* Resultado */}
          {generatedText && (
            <div className="mt-6 p-4 bg-primary-50 rounded-lg">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Texto Generado:</h3>
              <div className="whitespace-pre-wrap text-gray-700 bg-white p-4 rounded border">
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
                  className="flex items-center px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
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