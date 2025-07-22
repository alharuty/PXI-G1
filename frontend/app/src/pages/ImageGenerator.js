import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import { 
  AiOutlineDownload, 
  AiOutlineClear,
  AiOutlineCamera,
  AiOutlinePicture
} from 'react-icons/ai';

export default function ImageGenerator() {
  const [prompt, setPrompt] = useState('');
  const [style, setStyle] = useState('realistic');
  const [size, setSize] = useState('1024x1024');
  const [generatedImage, setGeneratedImage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const styles = [
    { id: 'realistic', name: 'Realista', description: 'Imágenes fotorrealistas' },
    { id: 'artistic', name: 'Artístico', description: 'Estilo artístico y creativo' },
    { id: 'cartoon', name: 'Cartoon', description: 'Estilo de dibujo animado' },
    { id: 'abstract', name: 'Abstracto', description: 'Arte abstracto y conceptual' },
  ];

  const sizes = [
    { id: '512x512', name: '512x512', description: 'Cuadrado pequeño' },
    { id: '1024x1024', name: '1024x1024', description: 'Cuadrado estándar' },
    { id: '1024x768', name: '1024x768', description: 'Horizontal' },
    { id: '768x1024', name: '768x1024', description: 'Vertical' },
  ];

  const handleGenerate = async () => {
    setIsGenerating(true);
    // Simulación del generador de imágenes
    setTimeout(() => {
      // Aquí pondrías la URL de la imagen generada
      setGeneratedImage('https://via.placeholder.com/512x512/00AFB9/FFFFFF?text=Imagen+Generada');
      setIsGenerating(false);
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-4xl mx-auto py-8 px-4">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-6">
            <AiOutlineCamera className="text-primary-100 mr-3" size={32} />
            <h1 className="text-3xl font-bold text-gray-900">Generador de Imágenes</h1>
          </div>
          
          {/* Input del prompt */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Describe la imagen que quieres crear:
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ej: Un paisaje montañoso al atardecer con un lago cristalino..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              rows="3"
            />
          </div>

          <div className="grid md:grid-cols-2 gap-6 mb-6">
            {/* Selector de estilo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Estilo de imagen:
              </label>
              <div className="space-y-2">
                {styles.map((styleOption) => (
                  <label key={styleOption.id} className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="style"
                      value={styleOption.id}
                      checked={style === styleOption.id}
                      onChange={(e) => setStyle(e.target.value)}
                      className="mr-3 text-primary-100 focus:ring-primary-100"
                    />
                    <div>
                      <div className="font-medium">{styleOption.name}</div>
                      <div className="text-sm text-gray-500">{styleOption.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Selector de tamaño */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Tamaño de imagen:
              </label>
              <div className="space-y-2">
                {sizes.map((sizeOption) => (
                  <label key={sizeOption.id} className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="size"
                      value={sizeOption.id}
                      checked={size === sizeOption.id}
                      onChange={(e) => setSize(e.target.value)}
                      className="mr-3 text-primary-100 focus:ring-primary-100"
                    />
                    <div>
                      <div className="font-medium">{sizeOption.name}</div>
                      <div className="text-sm text-gray-500">{sizeOption.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Botón generar */}
          <button
            onClick={handleGenerate}
            disabled={!prompt.trim() || isGenerating}
            className={`w-full py-3 px-6 rounded-lg font-medium transition-colors flex items-center justify-center ${
              !prompt.trim() || isGenerating
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-primary-100 hover:bg-primary-200 text-white'
            }`}
          >
            <AiOutlinePicture className="mr-2" size={20} />
            {isGenerating ? 'Generando imagen...' : 'Generar Imagen'}
          </button>

          {/* Resultado */}
          {generatedImage && (
            <div className="mt-6 text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Imagen Generada:</h3>
              <div className="inline-block p-4 bg-gray-100 rounded-lg">
                <img
                  src={generatedImage}
                  alt="Imagen generada"
                  className="max-w-full h-auto rounded"
                />
              </div>
              <div className="mt-4 flex justify-center space-x-3">
                <button
                  onClick={() => {
                    const link = document.createElement('a');
                    link.href = generatedImage;
                    link.download = 'imagen-generada.png';
                    link.click();
                  }}
                  className="flex items-center px-4 py-2 bg-primary-100 text-white rounded hover:bg-primary-200 transition-colors"
                >
                  <AiOutlineDownload className="mr-2" size={16} />
                  Descargar
                </button>
                <button
                  onClick={() => setGeneratedImage('')}
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