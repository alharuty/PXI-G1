import React, { useState } from 'react';
import axios from 'axios';
import { 
  AiOutlineExperiment,
  AiOutlineRobot,
  AiOutlineBulb,
  AiOutlineCopy,
  AiOutlineClear,
  AiOutlineDatabase,
  AiOutlineFileText,
  AiOutlineWarning
} from 'react-icons/ai';

export default function ResponseComparison() {
  const [question, setQuestion] = useState('');
  const [ragResponse, setRagResponse] = useState('');
  const [simpleResponse, setSimpleResponse] = useState('');
  const [ragDocuments, setRagDocuments] = useState([]);
  const [documentsUsed, setDocumentsUsed] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('unknown');
  const [comparisonMetrics, setComparisonMetrics] = useState(null);

  // ⭐ AGREGAR API_BASE_URL
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  const handleCompare = async () => {
    if (!question.trim()) {
      alert('Por favor introduce una pregunta');
      return;
    }

    setIsLoading(true);
    setRagResponse('');
    setSimpleResponse('');
    setRagDocuments([]);
    setDocumentsUsed(0);
    setComparisonMetrics(null);

    try {
      console.log('⚖️ Comparando respuestas para:', question);
      console.log('🌐 Endpoint:', `${API_BASE_URL}/rag/compare`);

      // ⭐ USAR EL ENDPOINT QUE YA EXISTE
      const response = await axios.get(`${API_BASE_URL}/rag/compare`, {
        params: {
          query: question,
          top_k: 5,
          temperature: 0.7,
          max_tokens: 1024
        },
        timeout: 45000 // 45 segundos de timeout
      });

      console.log('✅ Respuesta del backend:', response.data);

      // ⭐ EXTRAER DATOS DE LA RESPUESTA
      const data = response.data;
      
      // Respuestas
      setRagResponse(data.rag_response?.response || 'No se recibió respuesta RAG');
      setSimpleResponse(data.simple_response?.response || 'No se recibió respuesta simple');
      
      // Documentos utilizados
      setDocumentsUsed(data.rag_response?.documents_used || 0);
      
      // Métricas de comparación
      setComparisonMetrics(data.comparison || {});
      
      // Estado de conexión
      setConnectionStatus('connected');

    } catch (error) {
      console.error('❌ Error comparing responses:', error);
      setConnectionStatus('error');
      
      // Mostrar error más específico
      if (error.response) {
        const errorMsg = error.response.data?.detail || 'Error del servidor';
        setRagResponse(`❌ Error del servidor: ${errorMsg}`);
        setSimpleResponse(`❌ Error del servidor: ${errorMsg}`);
      } else if (error.request) {
        setRagResponse(`❌ Error de conexión: No se pudo conectar al servidor RAG en ${API_BASE_URL}/rag/compare\n\n¿Está ejecutándose el backend en puerto 8000?`);
        setSimpleResponse(`❌ Error de conexión: Verificar que el backend esté ejecutándose`);
      } else {
        setRagResponse(`❌ Error inesperado: ${error.message}`);
        setSimpleResponse(`❌ Error inesperado: ${error.message}`);
      }
      
      setDocumentsUsed(0);
      setComparisonMetrics(null);
    }
    setIsLoading(false);
  };

  const handleClearAll = () => {
    setQuestion('');
    setRagResponse('');
    setSimpleResponse('');
    setRagDocuments([]);
    setDocumentsUsed(0);
    setConnectionStatus('unknown');
    setComparisonMetrics(null);
  };

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    alert(`${type} copiada al portapapeles`);
  };

  const copyBothResponses = () => {
    const fullComparison = `
PREGUNTA: ${question}

RESPUESTA RAG (${documentsUsed} documentos):
${ragResponse}

RESPUESTA SIMPLE (sin documentos):
${simpleResponse}

MÉTRICAS:
- Documentos utilizados: ${documentsUsed}
- Longitud RAG: ${ragResponse.length} caracteres
- Longitud Simple: ${simpleResponse.length} caracteres
    `.trim();
    
    navigator.clipboard.writeText(fullComparison);
    alert('Comparación completa copiada al portapapeles');
  };

  return (
    <div className="space-y-6">
      {/* Main Form */}
      <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-white flex items-center">
            <AiOutlineExperiment className="mr-2" size={24} />
            Comparación RAG vs Respuesta Simple
          </h3>
          
          {/* Connection Status */}
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-2 ${
              connectionStatus === 'connected' ? 'bg-green-400' : 
              connectionStatus === 'error' ? 'bg-red-400' : 'bg-gray-400'
            }`}></div>
            <span className="text-sm text-gray-300">
              {connectionStatus === 'connected' ? 'Conectado' : 
               connectionStatus === 'error' ? 'Error conexión' : 'No probado'}
            </span>
          </div>
        </div>
        
        <p className="text-gray-300 text-sm mb-6">
          Compara respuestas generadas con RAG (usando documentos) vs respuestas simples del modelo
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Pregunta para comparar:
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ej: ¿Cuáles son los avances recientes en computación cuántica? ¿Qué aplicaciones tiene la inteligencia artificial en medicina?"
              className="w-full p-3 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              rows="4"
              required
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleCompare}
              disabled={!question.trim() || isLoading}
              className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all flex items-center justify-center ${
                !question.trim() || isLoading
                  ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg'
              }`}
            >
              <AiOutlineExperiment className="mr-2" size={20} />
              {isLoading ? 'Generando comparación...' : 'Comparar respuestas'}
            </button>
            
            <button
              onClick={handleClearAll}
              className="px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
            >
              <AiOutlineClear size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Comparison Results */}
      {(ragResponse || simpleResponse) && (
        <div className="space-y-6">
          {/* Comparison Metrics */}
          {comparisonMetrics && (
            <div className="bg-blue-900 bg-opacity-20 rounded-lg p-4 border border-blue-800">
              <h4 className="text-blue-300 font-medium mb-3 flex items-center">
                <AiOutlineDatabase className="mr-2" size={18} />
                Métricas de Comparación
              </h4>
              <div className="grid md:grid-cols-3 gap-4 text-sm">
                <div className="bg-blue-800 bg-opacity-30 p-3 rounded">
                  <p className="text-blue-200">
                    <strong>Documentos usados (RAG):</strong><br />
                    {documentsUsed > 0 ? `${documentsUsed} documentos` : 'Sin documentos específicos'}
                  </p>
                </div>
                <div className="bg-blue-800 bg-opacity-30 p-3 rounded">
                  <p className="text-blue-200">
                    <strong>Longitud respuesta RAG:</strong><br />
                    {comparisonMetrics.rag_response_length || ragResponse.length} caracteres
                  </p>
                </div>
                <div className="bg-blue-800 bg-opacity-30 p-3 rounded">
                  <p className="text-blue-200">
                    <strong>Longitud respuesta simple:</strong><br />
                    {comparisonMetrics.simple_response_length || simpleResponse.length} caracteres
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Side by Side Comparison */}
          <div className="grid lg:grid-cols-2 gap-6">
            {/* RAG Response */}
            <div className="bg-dark-700 rounded-lg p-6 border border-green-600">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-medium text-white flex items-center">
                  <AiOutlineRobot className="mr-2 text-green-400" size={20} />
                  Respuesta RAG
                  {documentsUsed > 0 && (
                    <span className="ml-2 text-xs bg-green-600 text-white px-2 py-1 rounded">
                      {documentsUsed} docs
                    </span>
                  )}
                </h4>
                <button
                  onClick={() => copyToClipboard(ragResponse, 'Respuesta RAG')}
                  className="flex items-center px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
                >
                  <AiOutlineCopy className="mr-1" size={14} />
                  Copiar
                </button>
              </div>
              
              <div className="whitespace-pre-wrap text-gray-300 bg-dark-900 p-4 rounded-lg border border-dark-600 leading-relaxed text-sm max-h-96 overflow-y-auto">
                {ragResponse}
              </div>
              
              <div className="mt-3 text-xs text-green-400">
                ✅ Basado en documentos de la base de conocimientos
              </div>
            </div>

            {/* Simple Response */}
            <div className="bg-dark-700 rounded-lg p-6 border border-orange-600">
              <div className="flex justify-between items-center mb-4">
                <h4 className="text-lg font-medium text-white flex items-center">
                  <AiOutlineBulb className="mr-2 text-orange-400" size={20} />
                  Respuesta Simple
                  <span className="ml-2 text-xs bg-orange-600 text-white px-2 py-1 rounded">
                    Sin docs
                  </span>
                </h4>
                <button
                  onClick={() => copyToClipboard(simpleResponse, 'Respuesta Simple')}
                  className="flex items-center px-3 py-1 bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors text-sm"
                >
                  <AiOutlineCopy className="mr-1" size={14} />
                  Copiar
                </button>
              </div>
              
              <div className="whitespace-pre-wrap text-gray-300 bg-dark-900 p-4 rounded-lg border border-dark-600 leading-relaxed text-sm max-h-96 overflow-y-auto">
                {simpleResponse}
              </div>
              
              <div className="mt-3 text-xs text-orange-400">
                ⚡ Conocimiento general del modelo base
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-center gap-4">
            <button
              onClick={copyBothResponses}
              className="flex items-center px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <AiOutlineFileText className="mr-2" size={16} />
              Copiar comparación completa
            </button>
          </div>

          {/* Analysis Tips */}
          <div className="bg-yellow-900 bg-opacity-20 rounded-lg p-4 border border-yellow-800">
            <h4 className="text-yellow-300 font-medium mb-2 flex items-center">
              <AiOutlineBulb className="mr-2" size={16} />
              Análisis de las diferencias:
            </h4>
            <div className="text-yellow-200 text-sm space-y-2">
              <p>• <strong>Respuesta RAG:</strong> Se basa en artículos específicos de la base de conocimientos, más precisa y actualizada</p>
              <p>• <strong>Respuesta Simple:</strong> Usa el conocimiento general del modelo, puede ser más genérica pero más fluida</p>
              <p>• <strong>Cuándo usar RAG:</strong> Para preguntas específicas sobre contenido de los artículos guardados</p>
              <p>• <strong>Cuándo usar Simple:</strong> Para preguntas generales o conceptos básicos</p>
            </div>
          </div>
        </div>
      )}

      {/* Help Section */}
      {!ragResponse && !simpleResponse && (
        <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
          <h4 className="text-white font-medium mb-3 flex items-center">
            <AiOutlineWarning className="mr-2" size={18} />
            Cómo usar la comparación:
          </h4>
          <ul className="text-gray-300 text-sm space-y-2">
            <li>• Haz la misma pregunta y compara cómo responde el sistema con y sin documentos</li>
            <li>• Observa las diferencias en precisión, detalles específicos y referencias</li>
            <li>• El RAG debería ser más específico si hay documentos relevantes en la base</li>
            <li>• La respuesta simple es útil para entender el conocimiento base del modelo</li>
          </ul>
        </div>
      )}
    </div>
  );
}