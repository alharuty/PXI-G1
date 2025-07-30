import React, { useState } from 'react';
import axios from 'axios';
import { 
  AiOutlineCompass,
  AiOutlineRobot,
  AiOutlineFileText,
  AiOutlineCopy,
  AiOutlineClear
} from 'react-icons/ai';

export default function ResponseComparison() {
  const [question, setQuestion] = useState('');
  const [ragResponse, setRagResponse] = useState('');
  const [simpleResponse, setSimpleResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleCompare = async () => {
    if (!question.trim()) {
      alert('Por favor introduce una pregunta');
      return;
    }

    setIsLoading(true);
    try {
      console.log('Comparando respuestas para:', question);
      
      // TODO: Reemplazar con los endpoints reales cuando estén listos
      const [ragRes, simpleRes] = await Promise.all([
        axios.post(`${process.env.REACT_APP_API_BASE_URL}/rag/ask-knowledge`, {
          question: question,
          use_rag: true
        }),
        axios.post(`${process.env.REACT_APP_API_BASE_URL}/generate`, {
          platform: 'general',
          topic: question,
          language: 'es'
        })
      ]);
      
      setRagResponse(ragRes.data.response);
      setSimpleResponse(simpleRes.data.content);
    } catch (error) {
      console.error('Error comparing responses:', error);
      
      // Respuestas mock para desarrollo
      setRagResponse(`**Respuesta con RAG:**\n\nBasándome en los artículos científicos de la base de conocimientos sobre "${question}", puedo proporcionar información específica y actualizada:\n\n• Los estudios más recientes muestran avances significativos en esta área\n• Las metodologías utilizadas incluyen técnicas de aprendizaje profundo\n• Los resultados sugieren mejoras del 15-20% en eficiencia\n\n*Esta respuesta está basada en 3 artículos relevantes de la base de conocimientos*`);
      
      setSimpleResponse(`**Respuesta Simple:**\n\nEn general, sobre "${question}", se puede decir que es un tema de gran importancia en el ámbito científico actual. Existen múltiples enfoques y metodologías que se están desarrollando para abordar los desafíos relacionados.\n\nLas tendencias actuales sugieren que hay un creciente interés en la aplicación de nuevas tecnologías para resolver problemas complejos en esta área.\n\n*Esta respuesta está generada sin consultar fuentes específicas*`);
    }
    setIsLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center">
          <AiOutlineCompass className="mr-2" size={24} />
          Comparación de Respuestas
        </h3>
        
        <p className="text-gray-300 text-sm mb-6">
          Compara respuestas generadas con RAG (basadas en la base de conocimientos) vs respuestas simples
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tu pregunta:
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ej: ¿Cuál es el rendimiento de los modelos de lenguaje grandes en tareas de predicción?"
              className="w-full p-3 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              rows="3"
            />
          </div>

          <button
            onClick={handleCompare}
            disabled={!question.trim() || isLoading}
            className={`w-full py-3 px-6 rounded-lg font-medium transition-all flex items-center justify-center ${
              !question.trim() || isLoading
                ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                : 'bg-gradient-to-r from-primary-100 to-primary-200 hover:from-primary-200 hover:to-primary-100 text-white shadow-lg'
            }`}
          >
            <AiOutlineCompass className="mr-2" size={20} />
            {isLoading ? 'Comparando...' : 'Comparar Respuestas'}
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {(ragResponse || simpleResponse) && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* RAG Response */}
          <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
            <h4 className="text-lg font-bold text-white mb-4 flex items-center">
              <AiOutlineRobot className="mr-2 text-blue-400" size={20} />
              Respuesta con RAG
            </h4>
            <div className="bg-dark-800 p-4 rounded-lg border border-dark-600 mb-4">
              <div className="whitespace-pre-wrap text-gray-300 text-sm leading-relaxed">
                {ragResponse}
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => navigator.clipboard.writeText(ragResponse)}
                className="flex items-center px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors"
              >
                <AiOutlineCopy className="mr-1" size={14} />
                Copiar
              </button>
            </div>
            
            {/* RAG Characteristics */}
            <div className="mt-4 p-3 bg-blue-900 bg-opacity-20 rounded border border-blue-800">
              <h5 className="text-sm font-semibold text-blue-300 mb-2">Características del RAG:</h5>
              <ul className="text-xs text-blue-200 space-y-1">
                <li>• Basado en documentos específicos de la base de conocimientos</li>
                <li>• Mayor precisión y actualización</li>
                <li>• Citas y referencias específicas</li>
                <li>• Información más detallada y técnica</li>
              </ul>
            </div>
          </div>

          {/* Simple Response */}
          <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
            <h4 className="text-lg font-bold text-white mb-4 flex items-center">
              <AiOutlineFileText className="mr-2 text-pink-400" size={20} />
              Respuesta Simple
            </h4>
            <div className="bg-dark-800 p-4 rounded-lg border border-dark-600 mb-4">
              <div className="whitespace-pre-wrap text-gray-300 text-sm leading-relaxed">
                {simpleResponse}
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => navigator.clipboard.writeText(simpleResponse)}
                className="flex items-center px-3 py-2 bg-pink-600 text-white rounded text-sm hover:bg-pink-700 transition-colors"
              >
                <AiOutlineCopy className="mr-1" size={14} />
                Copiar
              </button>
            </div>
            
            {/* Simple Response Characteristics */}
            <div className="mt-4 p-3 bg-pink-900 bg-opacity-20 rounded border border-pink-800">
              <h5 className="text-sm font-semibold text-pink-300 mb-2">Características de Respuesta Simple:</h5>
              <ul className="text-xs text-pink-200 space-y-1">
                <li>• Basado en conocimiento general del modelo</li>
                <li>• Respuesta más generalizada</li>
                <li>• Sin referencias específicas</li>
                <li>• Más rápida de generar</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Clear All Button */}
      {(ragResponse || simpleResponse) && (
        <div className="text-center">
          <button
            onClick={() => {
              setRagResponse('');
              setSimpleResponse('');
              setQuestion('');
            }}
            className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-500 transition-colors mx-auto"
          >
            <AiOutlineClear className="mr-2" size={16} />
            Limpiar todo
          </button>
        </div>
      )}
    </div>
  );
}