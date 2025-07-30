import React, { useState } from 'react';
import axios from 'axios';
import { 
  AiOutlineQuestionCircle,
  AiOutlineRobot,
  AiOutlineCopy,
  AiOutlineClear
} from 'react-icons/ai';

export default function KnowledgeQA() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!question.trim()) {
      alert('Por favor introduce una pregunta');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Pregunta sobre base de conocimientos:', question);
      
      // ⭐ USAR EL ENDPOINT QUE YA EXISTE
      const res = await axios.post(`${API_BASE_URL}/rag/generate`, null, {
        params: {
          query: question,
          top_k: 5,
          temperature: 0.7,
          max_tokens: 1024,
          stream: false
        }
      });
      
      setResponse(res.data.response);
    } catch (error) {
      console.error('Error asking knowledge base:', error);
      
      // Respuesta mock para desarrollo
      setResponse(`Respuesta basada en la base de conocimientos científicos sobre: "${question}"\n\nBasándome en los artículos disponibles en la base de conocimientos, puedo proporcionar información relevante sobre este tema. Sin embargo, el sistema RAG aún no está completamente implementado. \n\nEsta sería una respuesta generada utilizando técnicas de Retrieval-Augmented Generation, donde primero se buscan documentos relevantes y luego se genera una respuesta basada en esa información.`);
    }
    setIsLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center">
          <AiOutlineQuestionCircle className="mr-2" size={24} />
          Preguntas sobre la base de conocimientos
        </h3>
        
        <p className="text-gray-300 text-sm mb-6">
          Introduce una pregunta sobre los artículos científicos almacenados en la base de conocimientos
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tu pregunta:
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ej: ¿Cuáles son los últimos avances en inteligencia artificial para medicina?"
              className="w-full p-3 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              rows="4"
              required
            />
          </div>

          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            className={`w-full py-3 px-6 rounded-lg font-medium transition-all flex items-center justify-center ${
              !question.trim() || isLoading
                ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                : 'bg-gradient-to-r from-primary-100 to-primary-200 hover:from-primary-200 hover:to-primary-100 text-white shadow-lg'
            }`}
          >
            <AiOutlineRobot className="mr-2" size={20} />
            {isLoading ? 'Procesando...' : 'Obtener respuesta'}
          </button>
        </form>

        {/* Response */}
        {response && (
          <div className="mt-6 p-4 bg-dark-800 rounded-lg border border-dark-600">
            <h4 className="text-lg font-medium text-white mb-3 flex items-center">
              <AiOutlineRobot className="mr-2" size={20} />
              Respuesta del Sistema RAG:
            </h4>
            <div className="whitespace-pre-wrap text-gray-300 bg-dark-900 p-4 rounded-lg border border-dark-600 leading-relaxed">
              {response}
            </div>
            <div className="mt-4 flex space-x-3">
              <button
                onClick={() => navigator.clipboard.writeText(response)}
                className="flex items-center px-4 py-2 bg-primary-100 text-white rounded-lg hover:bg-primary-200 transition-colors"
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
  );
}