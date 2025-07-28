import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import axios from 'axios';
import { 
  AiOutlineDownload, 
  AiOutlineClear,
  AiOutlineCamera,
  AiOutlinePicture,
  AiOutlineLoading3Quarters
} from 'react-icons/ai';

export default function ImageGenerator() {
  const [prompt, setPrompt] = useState('');
  const [audiencia, setAudiencia] = useState('adultos');
  const [estilo, setEstilo] = useState('digital art');
  const [colores, setColores] = useState('colores vivos');
  const [detalles, setDetalles] = useState('');
  const [generatedImage, setGeneratedImage] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const audiencias = [
    { id: 'niños', name: 'Niños', description: 'Contenido infantil y familiar', color: 'from-yellow-400 to-orange-400' },
    { id: 'adolescentes', name: 'Adolescentes', description: 'Estilo juvenil y moderno', color: 'from-purple-400 to-pink-400' },
    { id: 'adultos', name: 'Adultos', description: 'Profesional y elegante', color: 'from-primary-100 to-primary-200' },
    { id: 'adultos mayores', name: 'Adultos Mayores', description: 'Clásico y tradicional', color: 'from-gray-500 to-gray-600' },
    { id: 'deportistas', name: 'Deportistas', description: 'Dinámico y energético', color: 'from-green-400 to-blue-400' },
  ];

  const estilos = [
    { id: 'digital art', name: 'Digital Art', description: 'Arte digital moderno', color: 'from-primary-100 to-primary-200' },
    { id: 'realista', name: 'Realista', description: 'Imágenes fotorrealistas', color: 'from-primary-300 to-primary-400' },
    { id: 'dibujo animado', name: 'Dibujo Animado', description: 'Estilo cartoon', color: 'from-purple-500 to-pink-500' },
    { id: 'acrilico', name: 'Acrílico', description: 'Pintura acrílica', color: 'from-red-400 to-orange-400' },
    { id: 'acuarela', name: 'Acuarela', description: 'Efecto acuarela suave', color: 'from-blue-400 to-teal-400' },
    { id: 'pixel art', name: 'Pixel Art', description: 'Estilo retro pixelado', color: 'from-green-400 to-cyan-400' },
  ];

  const coloresOptions = [
    { id: 'colores vivos', name: 'Colores Vivos', description: 'Colores brillantes y saturados', color: 'from-red-400 to-yellow-400' },
    { id: 'colores pastel', name: 'Colores Pastel', description: 'Tonos suaves y delicados', color: 'from-pink-200 to-purple-200' },
    { id: 'blanco y negro', name: 'Blanco y Negro', description: 'Monocromático clásico', color: 'from-gray-700 to-gray-900' },
    { id: 'tonos calidos', name: 'Tonos Cálidos', description: 'Rojos, naranjas y amarillos', color: 'from-yellow-400 to-red-500' },
    { id: 'tonos frios', name: 'Tonos Fríos', description: 'Azules, verdes y violetas', color: 'from-blue-400 to-purple-500' },
  ];

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      alert('Por favor describe la imagen que quieres crear');
      return;
    }

    setIsGenerating(true);
    setGeneratedImage('');
    setImageUrl('');

    try {
      // Llamada al endpoint del backend principal que maneja el microservicio
      const response = await axios.post('http://localhost:8000/generate-image', {
        tema: prompt,
        audiencia: audiencia,
        estilo: estilo,
        colores: colores,
        detalles: detalles
      });

      console.log('Respuesta del servidor:', response.data);

      if (response.data.imagen) {
        setGeneratedImage(`data:image/png;base64,${response.data.imagen}`);
      }
      
      if (response.data.url_supabase) {
        setImageUrl(response.data.url_supabase);
      }

      // Si hay algún mensaje de éxito
      if (response.data.mensaje) {
        console.log('Mensaje:', response.data.mensaje);
      }

    } catch (error) {
      console.error('Error generating image:', error);
      
      // Manejar diferentes tipos de errores
      if (error.response) {
        // Error del servidor
        const errorMessage = error.response.data?.detail || 'Error del servidor al generar la imagen';
        alert(`Error: ${errorMessage}`);
      } else if (error.request) {
        // Error de red
        alert('Error de conexión. Verifica que el servidor esté funcionando.');
      } else {
        // Otro tipo de error
        alert('Error inesperado al generar la imagen.');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (generatedImage) {
      const link = document.createElement('a');
      link.href = generatedImage;
      link.download = `buddy-imagen-${Date.now()}.png`;
      link.click();
    }
  };

  const handleGetLastImage = async () => {
    try {
      const response = await axios.get('http://localhost:8000/last-image');
      console.log('Última imagen:', response.data);
      
      if (response.data.filename) {
        // Si es una URL completa
        if (response.data.filename.startsWith('http')) {
          setImageUrl(response.data.filename);
          setGeneratedImage(response.data.filename);
        } else {
          // Si es solo el nombre del archivo, construir la URL
          const publicUrl = `https://your-supabase-url.supabase.co/storage/v1/object/public/imagenes/${response.data.filename}`;
          setImageUrl(publicUrl);
          setGeneratedImage(publicUrl);
        }
      }
    } catch (error) {
      console.error('Error obteniendo última imagen:', error);
      alert('Error al obtener la última imagen generada');
    }
  };

  return (
    <div className="min-h-screen bg-dark-900">
      <Navbar />
      
      <div className="max-w-6xl mx-auto py-8 px-4">
        <div className="bg-dark-800 rounded-xl shadow-2xl p-6 border border-dark-700">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-lg flex items-center justify-center mr-4">
                <AiOutlineCamera className="text-white" size={24} />
              </div>
              <h1 className="text-3xl font-bold text-white">Generador de Imágenes IA</h1>
            </div>
            {/* Botón para obtener última imagen */}
            <button
              onClick={handleGetLastImage}
              className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
            >
              Ver Última Imagen
            </button>
          </div>
          
          {/* Input del prompt principal */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Describe la imagen que quieres crear: *
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ej: Un paisaje montañoso al atardecer con un lago cristalino..."
              className="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              rows="3"
            />
          </div>

          {/* Detalles adicionales */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Detalles adicionales (opcional):
            </label>
            <textarea
              value={detalles}
              onChange={(e) => setDetalles(e.target.value)}
              placeholder="Ej: Con efectos de luz dramáticos, composición centrada, alta resolución..."
              className="w-full p-3 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              rows="2"
            />
          </div>

          <div className="grid lg:grid-cols-3 gap-6 mb-6">
            {/* Selector de audiencia */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Audiencia objetivo:
              </label>
              <div className="space-y-3">
                {audiencias.map((audienciaOption) => (
                  <label key={audienciaOption.id} className="flex items-center cursor-pointer group">
                    <input
                      type="radio"
                      name="audiencia"
                      value={audienciaOption.id}
                      checked={audiencia === audienciaOption.id}
                      onChange={(e) => setAudiencia(e.target.value)}
                      className="mr-3 text-primary-100 focus:ring-primary-100 bg-dark-700 border-dark-600"
                    />
                    <div className={`flex-1 p-3 rounded-lg border transition-all ${
                      audiencia === audienciaOption.id 
                        ? 'border-primary-100 bg-gradient-to-r ' + audienciaOption.color + ' text-white'
                        : 'border-dark-600 bg-dark-700 text-gray-300 group-hover:border-primary-200'
                    }`}>
                      <div className="font-medium">{audienciaOption.name}</div>
                      <div className="text-xs opacity-70">{audienciaOption.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Selector de estilo */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Estilo artístico:
              </label>
              <div className="space-y-3">
                {estilos.map((estiloOption) => (
                  <label key={estiloOption.id} className="flex items-center cursor-pointer group">
                    <input
                      type="radio"
                      name="estilo"
                      value={estiloOption.id}
                      checked={estilo === estiloOption.id}
                      onChange={(e) => setEstilo(e.target.value)}
                      className="mr-3 text-primary-100 focus:ring-primary-100 bg-dark-700 border-dark-600"
                    />
                    <div className={`flex-1 p-3 rounded-lg border transition-all ${
                      estilo === estiloOption.id 
                        ? 'border-primary-100 bg-gradient-to-r ' + estiloOption.color + ' text-white'
                        : 'border-dark-600 bg-dark-700 text-gray-300 group-hover:border-primary-200'
                    }`}>
                      <div className="font-medium">{estiloOption.name}</div>
                      <div className="text-xs opacity-70">{estiloOption.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Selector de colores */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                Paleta de colores:
              </label>
              <div className="space-y-3">
                {coloresOptions.map((colorOption) => (
                  <label key={colorOption.id} className="flex items-center cursor-pointer group">
                    <input
                      type="radio"
                      name="colores"
                      value={colorOption.id}
                      checked={colores === colorOption.id}
                      onChange={(e) => setColores(e.target.value)}
                      className="mr-3 text-primary-100 focus:ring-primary-100 bg-dark-700 border-dark-600"
                    />
                    <div className={`flex-1 p-3 rounded-lg border transition-all ${
                      colores === colorOption.id 
                        ? 'border-primary-100 bg-gradient-to-r ' + colorOption.color + ' text-white'
                        : 'border-dark-600 bg-dark-700 text-gray-300 group-hover:border-primary-200'
                    }`}>
                      <div className="font-medium">{colorOption.name}</div>
                      <div className="text-xs opacity-70">{colorOption.description}</div>
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
            className={`w-full py-4 px-6 rounded-lg font-medium transition-all flex items-center justify-center text-lg ${
              !prompt.trim() || isGenerating
                ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                : 'bg-gradient-to-r from-primary-100 to-primary-200 hover:from-primary-200 hover:to-primary-100 text-white shadow-lg transform hover:scale-105'
            }`}
          >
            {isGenerating ? (
              <>
                <AiOutlineLoading3Quarters className="mr-2 animate-spin" size={20} />
                Generando imagen con IA...
              </>
            ) : (
              <>
                <AiOutlinePicture className="mr-2" size={20} />
                Generar Imagen
              </>
            )}
          </button>

          {/* Indicador de progreso */}
          {isGenerating && (
            <div className="mt-4 text-center">
              <div className="text-gray-300 text-sm mb-2">
                Esto puede tomar unos segundos... 🎨
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div className="bg-gradient-to-r from-primary-100 to-primary-200 h-2 rounded-full animate-pulse"></div>
              </div>
            </div>
          )}

          {/* Resultado */}
          {generatedImage && (
            <div className="mt-8 text-center">
              <h3 className="text-xl font-bold text-white mb-4">✨ Imagen Generada con IA</h3>
              <div className="inline-block p-4 bg-dark-700 rounded-lg border border-dark-600 shadow-xl">
                <img
                  src={generatedImage}
                  alt="Imagen generada por IA"
                  className="max-w-full h-auto rounded shadow-lg"
                  style={{ maxHeight: '500px' }}
                />
              </div>
              
              {/* Información de la imagen */}
              <div className="mt-4 text-sm text-gray-400">
                <p><strong>Audiencia:</strong> {audiencia} | <strong>Estilo:</strong> {estilo} | <strong>Colores:</strong> {colores}</p>
              </div>

              {/* Botones de acción */}
              <div className="mt-6 flex justify-center space-x-4">
                <button
                  onClick={handleDownload}
                  className="flex items-center px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 transition-all shadow-md transform hover:scale-105"
                >
                  <AiOutlineDownload className="mr-2" size={18} />
                  Descargar
                </button>
                <button
                  onClick={() => {
                    setGeneratedImage('');
                    setImageUrl('');
                  }}
                  className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
                >
                  <AiOutlineClear className="mr-2" size={18} />
                  Limpiar
                </button>
                {imageUrl && (
                  <button
                    onClick={() => window.open(imageUrl, '_blank')}
                    className="flex items-center px-6 py-3 bg-primary-100 text-white rounded-lg hover:bg-primary-200 transition-colors"
                  >
                    Ver en Supabase
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}