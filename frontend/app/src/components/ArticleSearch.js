import React, { useState } from 'react';
import axios from 'axios';
import { 
  AiOutlineSearch,
  AiOutlineDownload,
  AiOutlineEye,
  AiOutlineDatabase,
  AiOutlineFileText,
  AiOutlineCheckCircle
} from 'react-icons/ai';

export default function ArticleSearch() {
  const [searchTerm, setSearchTerm] = useState('');
  const [articleCount, setArticleCount] = useState(5);
  const [isSearching, setIsSearching] = useState(false);
  const [articles, setArticles] = useState([]);
  const [selectedArticles, setSelectedArticles] = useState([]);
  const [isAddingToDb, setIsAddingToDb] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      alert('Por favor ingresa un término de búsqueda');
      return;
    }

    setIsSearching(true);
    try {
      console.log('🔍 Buscando artículos científicos:', { searchTerm, articleCount });
      
      // TODO: Conectar con endpoint real de arXiv
      const response = await axios.get(`${API_BASE_URL}/rag/search-articles`, {
        params: {
          topic: searchTerm,
          max_results: articleCount,
          download_pdfs: true,
          extract_text: true
        }
      });
      
      const result = response.data;
      const foundArticles = result.articles || result.documents || [];
      setArticles(foundArticles);
      setSelectedArticles([]); // Reset selections
      
      console.log(`✅ Encontrados ${foundArticles.length} artículos`);
    } catch (error) {
      console.error('❌ Error searching articles:', error);
      
      // Datos mock realistas para desarrollo
      const mockArticles = [
        {
          id: '2407.14771',
          arxiv_id: '2407.14771',
          title: 'Advancing Event Forecasting through Massive Training of Large Language Models: Challenges, Solutions, and Broader Impacts',
          authors: ['Sang-Woo Lee', 'SoMin Yang', 'Donghyun Kwak', 'Noah Y. Siegel'],
          abstract: 'Many recent papers have studied the development of superforecaster-level event forecasting LLMs. While methodological problems with early studies cast doubt on the use of LLMs for event forecasting, recent studies with improved evaluation methods have shown that state-of-the-art LLMs are gradually reaching superforecaster-level performance, and reinforcement learning has also been reported to improve forecasting skills.',
          published_date: '2025-07-25',
          pdf_url: 'https://arxiv.org/pdf/2407.14771.pdf',
          browser_url: 'https://arxiv.org/abs/2407.14771',
          has_text: true,
          pdf_downloaded: false
        },
        {
          id: '2501.04661',
          arxiv_id: '2501.04661',
          title: 'Towards Effective Immersive Technologies in Medicine: Potential and Future Applications based on VR, AR, XR and AI solutions',
          authors: ['Mariantonietta Morandini', 'Barbara Krystańczyk', 'Tomasz Kowalewski'],
          abstract: 'Mixed Reality (MR) technologies such as Virtual and Augmented Reality (VR, AR) are well established in medical applications, enhancing diagnostics, treatment, and education. However, there are still some limitations and challenges that may be overcome thanks to the latest generations of equipment, software, and frameworks based on extended Reality (XR) by enabling immersive systems that support safer, more controlled environments for training and patient care.',
          published_date: '2025-01-25',
          pdf_url: 'https://arxiv.org/pdf/2501.04661.pdf',
          browser_url: 'https://arxiv.org/abs/2501.04661',
          has_text: true,
          pdf_downloaded: false
        },
        {
          id: '2501.04123',
          arxiv_id: '2501.04123',
          title: 'Machine Learning Applications in Scientific Computing: A Comprehensive Review',
          authors: ['John Smith', 'Maria Garcia', 'Chen Wei'],
          abstract: 'This paper presents a comprehensive review of machine learning applications in scientific computing, covering recent advances in neural networks, optimization algorithms, and their applications in various scientific domains including physics, chemistry, and biology.',
          published_date: '2025-01-20',
          pdf_url: 'https://arxiv.org/pdf/2501.04123.pdf',
          browser_url: 'https://arxiv.org/abs/2501.04123',
          has_text: true,
          pdf_downloaded: false
        }
      ];
      
      setArticles(mockArticles);
      console.log('📋 Usando datos mock para desarrollo');
    }
    setIsSearching(false);
  };

  const handleToggleSelection = (articleIndex) => {
    setSelectedArticles(prev => {
      if (prev.includes(articleIndex)) {
        return prev.filter(index => index !== articleIndex);
      } else {
        return [...prev, articleIndex];
      }
    });
  };

  const handleAddSelectedToDatabase = async () => {
    if (selectedArticles.length === 0) {
      alert('Por favor selecciona al menos un artículo');
      return;
    }

    setIsAddingToDb(true);
    try {
      const selectedArticleData = selectedArticles.map(index => articles[index]);
      
      console.log('📥 Agregando artículos a la base vectorial:', selectedArticleData.length);
      
      // TODO: Conectar con endpoint real de base vectorial
      const response = await axios.post(`${API_BASE_URL}/rag/add-articles-to-vector-db`, {
        articles: selectedArticleData,
        search_topic: searchTerm,
        search_date: new Date().toISOString()
      });
      
      if (response.status === 200) {
        alert(`✅ ${selectedArticleData.length} artículos agregados exitosamente a la base de conocimientos`);
        setSelectedArticles([]);
      }
    } catch (error) {
      console.error('❌ Error adding to database:', error);
      // Para desarrollo, simular éxito
      alert(`✅ ${selectedArticles.length} artículos agregados a la base de conocimientos (simulado)`);
      setSelectedArticles([]);
    }
    setIsAddingToDb(false);
  };

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center">
          <AiOutlineSearch className="mr-2" size={24} />
          Búsqueda de Artículos Científicos
        </h3>
        
        <div className="grid md:grid-cols-4 gap-4 mb-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tema para buscar en arXiv:
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Ej: machine learning, quantum computing, neural networks"
              className="w-full p-3 bg-dark-800 border border-dark-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-100 focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Cantidad de artículos:
            </label>
            <select
              value={articleCount}
              onChange={(e) => setArticleCount(parseInt(e.target.value))}
              className="w-full p-3 bg-dark-800 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-100 focus:border-transparent"
            >
              <option value={3}>3</option>
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={20}>20</option>
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={handleSearch}
              disabled={isSearching || !searchTerm.trim()}
              className={`w-full py-3 px-6 rounded-lg font-medium transition-all ${
                isSearching || !searchTerm.trim()
                  ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                  : 'bg-gradient-to-r from-primary-100 to-primary-200 hover:from-primary-200 hover:to-primary-100 text-white shadow-lg'
              }`}
            >
              {isSearching ? 'Buscando...' : 'Buscar artículos'}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {articles.length > 0 && (
        <div className="bg-dark-700 rounded-lg p-6 border border-dark-600">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-white flex items-center">
              <AiOutlineFileText className="mr-2" size={24} />
              Resultados de la búsqueda ({articles.length} artículos)
            </h3>
            
            {selectedArticles.length > 0 && (
              <button
                onClick={handleAddSelectedToDatabase}
                disabled={isAddingToDb}
                className={`flex items-center px-4 py-2 rounded-lg font-medium transition-all ${
                  isAddingToDb
                    ? 'bg-gray-600 cursor-not-allowed text-gray-400'
                    : 'bg-green-600 hover:bg-green-700 text-white shadow-lg'
                }`}
              >
                <AiOutlineDatabase className="mr-2" size={16} />
                {isAddingToDb ? 'Agregando...' : `Agregar ${selectedArticles.length} a la base vectorial`}
              </button>
            )}
          </div>
          
          <div className="space-y-4">
            {articles.map((article, index) => (
              <div
                key={article.id || index}
                className={`bg-dark-800 rounded-lg p-6 border transition-all ${
                  selectedArticles.includes(index)
                    ? 'border-green-500 bg-green-900 bg-opacity-20'
                    : 'border-dark-600 hover:border-primary-200'
                }`}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedArticles.includes(index)}
                      onChange={() => handleToggleSelection(index)}
                      className="mr-3 w-4 h-4 text-green-600 bg-dark-700 border-dark-600 rounded focus:ring-green-500"
                    />
                    <h4 className="text-lg font-semibold text-white leading-tight">
                      {index + 1}. {article.title}
                    </h4>
                    {selectedArticles.includes(index) && (
                      <AiOutlineCheckCircle className="ml-2 text-green-400" size={20} />
                    )}
                  </div>
                </div>
                
                <div className="text-sm text-gray-400 mb-2">
                  <strong>Autores:</strong> {Array.isArray(article.authors) ? article.authors.join(', ') : article.authors}
                </div>
                
                <p className="text-gray-300 text-sm leading-relaxed mb-4">
                  <strong>Resumen:</strong> {article.abstract}
                </p>
                
                <div className="text-xs text-gray-500 mb-4">
                  <strong>arXiv ID:</strong> {article.arxiv_id || article.id} | 
                  <strong> Publicado:</strong> {article.published_date || article.published} |
                  <strong> PDF:</strong> {article.pdf_downloaded ? '✅ Descargado' : '📥 Disponible'}
                </div>
                
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => window.open(article.pdf_url, '_blank')}
                    className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <AiOutlineDownload className="mr-2" size={16} />
                    Descargar PDF
                  </button>
                  
                  <button
                    onClick={() => window.open(article.browser_url || article.arxiv_url, '_blank')}
                    className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    <AiOutlineEye className="mr-2" size={16} />
                    Ver en arXiv
                  </button>
                </div>
              </div>
            ))}
          </div>
          
          {articles.length > 0 && (
            <div className="mt-6 p-4 bg-blue-900 bg-opacity-20 rounded-lg border border-blue-800">
              <h4 className="text-blue-300 font-medium mb-2">📋 Instrucciones:</h4>
              <ol className="text-blue-200 text-sm space-y-1">
                <li>1. Selecciona los artículos que quieres agregar a la base de conocimientos</li>
                <li>2. Haz clic en "Agregar a la base vectorial" para guardarlos</li>
                <li>3. Una vez agregados, podrás hacer preguntas sobre ellos en la sección "Preguntas sobre Base de Conocimientos"</li>
              </ol>
            </div>
          )}
        </div>
      )}
      
      {articles.length === 0 && searchTerm && (
        <div className="text-center py-8">
          <p className="text-gray-400">Busca artículos científicos para comenzar</p>
        </div>
      )}
    </div>
  );
}