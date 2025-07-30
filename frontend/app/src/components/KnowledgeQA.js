import React, { useState } from 'react';
import axios from 'axios';
import { 
  AiOutlineQuestionCircle,
  AiOutlineRobot,
  AiOutlineCopy,
  AiOutlineClear,
  AiOutlineFileText,
  AiOutlineDatabase,
  AiOutlineWarning
} from 'react-icons/ai';

export default function KnowledgeQA() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [sourceDocuments, setSourceDocuments] = useState([]);
  const [documentsUsed, setDocumentsUsed] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('unknown');

  // ⭐ AGREGAR API_BASE_URL
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!question.trim()) {
      alert('Por favor introduce una pregunta');
      return;
    }

    setIsLoading(true);
    setResponse('');
    setSourceDocuments([]);
    setDocumentsUsed(0);
    
    try {
      console.log('🔍 Pregunta sobre base de conocimientos:', question);
      console.log('🌐 Endpoint:', `${API_BASE_URL}/rag/generate`);
      
      // ⭐ USAR EL ENDPOINT QUE YA EXISTE
      const res = await axios.post(`${API_BASE_URL}/rag/generate`, null, {
        params: {
          query: question,
          top_k: 5,
          temperature: 0.7,
          max_tokens: 1024,
          stream: false
        },
        timeout: 30000 // 30 segundos de timeout
      });
      
      console.log('✅ Respuesta del backend:', res.data);
      
      // ⭐ EXTRAER DATOS DE LA RESPUESTA
      setResponse(res.data.response || 'No se recibió respuesta del servidor');
      setSourceDocuments(res.data.source_documents || []);
      setDocumentsUsed(res.data.documents_retrieved || 0);
      setConnectionStatus('connected');
      
    } catch (error) {
      console.error('❌ Error asking knowledge base:', error);
      setConnectionStatus('error');
      
      // Mostrar error más específico
      if (error.response) {
        const errorMsg = error.response.data?.detail || 'Error del servidor';
        setResponse(`❌ Error del servidor: ${errorMsg}`);
      } else if (error.request) {
        setResponse(`❌ Error de conexión: No se pudo conectar al servidor RAG en ${API_BASE_URL}/rag/generate\n\n¿Está ejecutándose el backend en puerto 8000?`);
      } else {
        setResponse(`❌ Error inesperado: ${error.message}`);
      }
      
      setSourceDocuments([]);
      setDocumentsUsed(0);
    }
    setIsLoading(false);
  };

  const handleClearAll = () => {
    setQuestion('');
    setResponse('');
    setSourceDocuments([]);
    setDocumentsUsed(0);
    setConnectionStatus('unknown');
  };

  return (
    <div className="space-y-6">
      {/* Main Form */}
      <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-white flex items-center">
            <AiOutlineQuestionCircle className="mr-2" size={24} />
            Consultar Base de Conocimientos
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
          Introduce una pregunta sobre los artículos científicos almacenados en la base de conocimientos vectorial
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tu pregunta:
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ej: ¿Cuáles son los últimos avances en inteligencia artificial para medicina? ¿Qué dice la literatura sobre quantum computing?"
              className="w-full p-3 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              rows="4"
              required
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={!question.trim() || isLoading}
              className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all flex items-center justify-center ${
                !question.trim() || isLoading
                  ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                  : 'bg-gradient-to-r from-primary-100 to-primary-200 hover:from-primary-200 hover:to-primary-100 text-white shadow-lg'
              }`}
            >
              <AiOutlineRobot className="mr-2" size={20} />
              {isLoading ? 'Procesando...' : 'Obtener respuesta RAG'}
            </button>
            
            <button
              type="button"
              onClick={handleClearAll}
              className="px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors"
            >
              <AiOutlineClear size={20} />
            </button>
          </div>
        </form>
      </div>

      {/* Response Section */}
      {response && (
        <div className="space-y-4">
          {/* Source Documents Info */}
          <div className="bg-blue-900 bg-opacity-20 rounded-lg p-4 border border-blue-800">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-blue-300 font-medium flex items-center">
                <AiOutlineDatabase className="mr-2" size={18} />
                Información de la consulta
              </h4>
              <span className="text-blue-200 text-sm">
                {documentsUsed > 0 ? `${documentsUsed} documentos encontrados` : 'Sin documentos específicos'}
              </span>
            </div>
            <p className="text-blue-200 text-sm">
              {documentsUsed > 0 
                ? `La respuesta se basa en ${documentsUsed} fragmentos relevantes de la base de conocimientos vectorial.`
                : 'La respuesta se genera sin documentos específicos de la base de datos (respuesta general del modelo).'
              }
            </p>
          </div>

          {/* Source Documents List */}
          {sourceDocuments.length > 0 && (
            <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
              <h4 className="text-lg font-medium text-white mb-4 flex items-center">
                <AiOutlineFileText className="mr-2" size={20} />
                Artículos fuente utilizados ({sourceDocuments.length})
              </h4>
              
              <div className="space-y-3">
                {sourceDocuments.map((doc, index) => (
                  <div key={index} className="bg-dark-800 rounded-lg p-4 border border-dark-600">
                    <div className="flex justify-between items-start mb-2">
                      <h5 className="font-medium text-white text-sm">
                        📄 Fragmento {index + 1}
                      </h5>
                      {doc.score && (
                        <span className="text-xs text-gray-400 bg-dark-900 px-2 py-1 rounded">
                          Relevancia: {(doc.score * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                    
                    {doc.title && (
                      <p className="text-sm text-blue-300 mb-1">
                        <strong>Título:</strong> {doc.title}
                      </p>
                    )}
                    
                    {doc.authors && (
                      <p className="text-xs text-gray-400 mb-2">
                        <strong>Autores:</strong> {Array.isArray(doc.authors) ? doc.authors.join(', ') : doc.authors}
                      </p>
                    )}
                    
                    <div className="text-xs text-gray-300 bg-dark-900 p-2 rounded border-l-2 border-blue-500">
                      {doc.content || doc.text || doc.chunk || 'Contenido no disponible'}
                    </div>
                    
                    {doc.arxiv_id && (
                      <p className="text-xs text-gray-500 mt-2">
                        arXiv ID: {doc.arxiv_id}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Main Response */}
          <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
            <h4 className="text-lg font-medium text-white mb-3 flex items-center">
              <AiOutlineRobot className="mr-2" size={20} />
              Respuesta del Sistema RAG:
            </h4>
            
            <div className="whitespace-pre-wrap text-gray-300 bg-dark-900 p-4 rounded-lg border border-dark-600 leading-relaxed">
              {response}
            </div>
            
            <div className="mt-4 flex justify-between items-center">
              <div className="flex space-x-3">
                <button
                  onClick={() => navigator.clipboard.writeText(response)}
                  className="flex items-center px-4 py-2 bg-primary-100 text-white rounded-lg hover:bg-primary-200 transition-colors"
                >
                  <AiOutlineCopy className="mr-2" size={16} />
                  Copiar respuesta
                </button>
                
                {sourceDocuments.length > 0 && (
                  <button
                    onClick={() => {
                      const fullText = `Pregunta: ${question}\n\nRespuesta: ${response}\n\nFuentes:\n${sourceDocuments.map((doc, i) => `${i+1}. ${doc.title || 'Sin título'} - ${doc.content || doc.text || ''}`).join('\n\n')}`;
                      navigator.clipboard.writeText(fullText);
                    }}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <AiOutlineFileText className="mr-2" size={16} />
                    Copiar con fuentes
                  </button>
                )}
              </div>
              
              <span className="text-xs text-gray-500">
                Respuesta generada usando {documentsUsed > 0 ? 'RAG' : 'modelo base'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Help Section */}
      {!response && (
        <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
          <h4 className="text-white font-medium mb-3 flex items-center">
            <AiOutlineWarning className="mr-2" size={18} />
            Consejos para mejores resultados:
          </h4>
          <ul className="text-gray-300 text-sm space-y-2">
            <li>• Asegúrate de haber agregado artículos a la base de datos primero</li>
            <li>• Haz preguntas específicas sobre los temas de los artículos guardados</li>
            <li>• El sistema buscará fragmentos relevantes antes de generar la respuesta</li>
            <li>• Si no hay documentos relevantes, se generará una respuesta general</li>
          </ul>
        </div>
      )}
    </div>
  );
}