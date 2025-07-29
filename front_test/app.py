import streamlit as st
import requests
import json
from components.form_generator import FormGenerator
from components.content_display import ContentDisplay
from utils.api_client import APIClient
import uuid
import urllib.parse


def get_pdf_size(pdf_url):
    """Получает размер PDF файла в МБ"""
    try:
        response = requests.head(pdf_url, timeout=5)
        if response.status_code == 200:
            size_bytes = int(response.headers.get('content-length', 0))
            size_mb = size_bytes / (1024 * 1024)
            return f"{size_mb:.1f} MB"
        return "Unknown"
    except:
        return "Unknown"





st.set_page_config(
    page_title="Hybrid RAG Content Generator",
    page_icon="🧠",
    layout="wide"
)

def main():
    st.title("🧠 Hybrid RAG Content Generator")
    st.markdown("Generate high-quality content using hybrid RAG (Semantic + BM25) with scientific sources")
    
    api_client = APIClient()
    form_generator = FormGenerator()
    content_display = ContentDisplay()
    
    # Sidebar для настройки RAG
    with st.sidebar:
        st.header("⚙️ RAG Configuration")
        
        # Статистика RAG
        if st.button("📊 Get RAG Stats"):
            try:
                stats = api_client.get_rag_stats()
                st.json(stats)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # Очистка RAG
        if st.button("🗑️ Clear RAG"):
            try:
                result = api_client.clear_rag()
                st.success("RAG cleared successfully!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.markdown("---")
        
        # Настройки поиска
        st.subheader("🔍 Search Settings")
        search_type = st.selectbox(
            "Search Type",
            ["hybrid", "semantic", "bm25"],
            help="Hybrid: Combines semantic and keyword search\nSemantic: Only semantic similarity\nBM25: Only keyword-based search"
        )
        
        top_k = st.slider(
            "Number of Sources",
            min_value=3,
            max_value=15,
            value=8,
            help="Number of relevant sources to retrieve"
        )
        
        language = st.selectbox(
            "Output Language",
            ["en", "es", "ru"],
            help="Language for generated content"
        )
    
    # Основной контент
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📋 Generate Content")
        
        # Форма для генерации контента
        topic = st.text_input(
            "Topic",
            placeholder="Enter a scientific topic (e.g., 'quantum computing', 'machine learning')",
            help="The topic you want to generate content about"
        )
        
        # Кнопки генерации
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🧠 Generate with RAG", type="primary"):
                if topic:
                    with st.spinner("Generating content with hybrid RAG..."):
                        try:
                            rag_params = {
                                "topic": topic,
                                "language": language,
                                "search_type": search_type,
                                "top_k": top_k
                            }
                            response = api_client.generate_popular_science_rag(rag_params)
                            st.session_state.generated_content = response
                            st.success("✅ RAG content generated successfully!")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Please enter a topic")
        
        with col_btn2:
            if st.button("🎯 Generate Regular Content"):
                if topic:
                    with st.spinner("Generating regular content..."):
                        try:
                            content_params = {
                                "topic": topic,
                                "platform": "blog",
                                "tone": "professional"
                            }
                            response = api_client.generate_content(content_params)
                            st.session_state.generated_content = response
                            st.success("✅ Regular content generated successfully!")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("⚠️ Please enter a topic")
        
        # Загрузка статей из arXiv
        st.markdown("---")
        st.subheader("📚 Load Articles from arXiv")
        
        arxiv_topic = st.text_input(
            "arXiv Topic",
            placeholder="Search topic for arXiv articles",
            key="arxiv_topic"
        )
        
        arxiv_count = st.number_input(
            "Number of Articles",
            min_value=1,
            max_value=20,
            value=5,
            key="arxiv_count"
        )
        
        if st.button("🔍 Search arXiv"):
            if arxiv_topic:
                with st.spinner("Searching arXiv..."):
                    try:
                        articles = api_client.search_arxiv({
                            "query": arxiv_topic,
                            "max_results": arxiv_count
                        })
                        st.session_state["arxiv_articles"] = articles
                        st.success(f"✅ Found {len(articles)} articles")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("⚠️ Please enter a search topic")
        
        # Отображение найденных статей
        if "arxiv_articles" in st.session_state:
            st.subheader("📄 Found Articles")
            
            # Статистика статей
            articles = st.session_state["arxiv_articles"]
            pdf_available = sum(1 for art in articles if art.get('pdf_url'))
            
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            with col_stats1:
                st.metric("Total Articles", len(articles))
            with col_stats2:
                st.metric("PDF Available", pdf_available)
            with col_stats3:
                st.metric("PDF %", f"{(pdf_available/len(articles)*100):.1f}%" if articles else "0%")
            
            selected_articles = []
            
            for i, art in enumerate(st.session_state["arxiv_articles"]):
                with st.expander(f"📄 {art['title'][:50]}..."):
                    st.markdown(f"**Title:** {art['title']}")
                    st.markdown(f"**Authors:** {', '.join(art['authors'])}")
                    
                    # Дополнительная информация
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        if art.get('published_date'):
                            st.markdown(f"**Published:** {art['published_date'][:10]}")
                        if art.get('doi'):
                            st.markdown(f"**DOI:** {art['doi']}")
                    
                    with col_info2:
                        if art.get('categories'):
                            st.markdown(f"**Categories:** {', '.join(art['categories'][:3])}")
                    
                    st.markdown(f"**Summary:** {art['summary'][:200]}...")
                    
                    # Кнопки для действий со статьей
                    st.markdown("**Actions:**")
                    col_actions1, col_actions2, col_actions3 = st.columns([1, 1, 2])
                    
                    with col_actions1:
                        if st.checkbox(f"Add to RAG", key=f"add_{i}", help="Add this article to the RAG system for content generation"):
                            selected_articles.append(art)
                    
                    with col_actions2:
                        # Кнопка для скачивания PDF
                        if art.get('pdf_url'):
                            try:
                                # Получаем имя файла из URL
                                pdf_filename = f"{art['title'][:30].replace(' ', '_').replace('/', '_')}.pdf"
                                
                                # Проверяем доступность PDF и получаем размер
                                pdf_response = requests.head(art['pdf_url'], timeout=5)
                                if pdf_response.status_code == 200:
                                    pdf_size = get_pdf_size(art['pdf_url'])
                                    st.download_button(
                                        label=f"📥 Download ({pdf_size})",
                                        data=requests.get(art['pdf_url']).content,
                                        file_name=pdf_filename,
                                        mime="application/pdf",
                                        key=f"download_pdf_{i}",
                                        help="Download PDF file to your computer"
                                    )
                                else:
                                    st.error("PDF недоступен")
                            except Exception as e:
                                st.error(f"Ошибка загрузки PDF: {str(e)}")
                        else:
                            st.info("PDF недоступен")
                    
                    with col_actions3:
                        # Кнопки для открытия статьи
                        # Кнопка для открытия PDF в браузере
                        if art.get('pdf_url'):
                            st.markdown(f'<a href="{art["pdf_url"]}" target="_blank" title="Open PDF in new tab">📄 Open PDF</a>', unsafe_allow_html=True)
                        else:
                            st.info("PDF недоступен")
                        
                        st.markdown("---")  # Разделитель
                        
                        # Кнопка для открытия страницы статьи
                        if art.get('link'):
                            st.markdown(f'<a href="{art["link"]}" target="_blank" title="Open article page in new tab">🔗 Article Page</a>', unsafe_allow_html=True)
            
            if selected_articles:
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("📥 Add Selected to RAG"):
                        with st.spinner("Adding articles to RAG..."):
                            try:
                                selected_docs = []
                                for art in selected_articles:
                                    selected_docs.append({
                                        "id": str(uuid.uuid4()),
                                        "text": art.get("summary", ""),
                                        "metadata": {
                                            "title": art.get("title", ""),
                                            "authors": art.get("authors", []),
                                            "link": art.get("link", ""),
                                            "pdf_url": art.get("pdf_url", ""),
                                            "source": "arxiv"
                                        }
                                    })
                                
                                result = api_client.upsert_documents(selected_docs)
                                st.success(f"✅ Added {result['count']} articles to RAG!")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                with col_btn2:
                    # Массовое скачивание PDF
                    pdf_articles = [art for art in selected_articles if art.get('pdf_url')]
                    if pdf_articles:
                        if st.button("📚 Download All PDFs"):
                            st.info(f"📥 Готово к скачиванию {len(pdf_articles)} PDF файлов")
                            for i, art in enumerate(pdf_articles):
                                try:
                                    pdf_filename = f"{art['title'][:30].replace(' ', '_').replace('/', '_')}.pdf"
                                    st.download_button(
                                        label=f"📥 {pdf_filename}",
                                        data=requests.get(art['pdf_url']).content,
                                        file_name=pdf_filename,
                                        mime="application/pdf",
                                        key=f"batch_download_{i}"
                                    )
                                except Exception as e:
                                    st.error(f"Ошибка загрузки {art['title'][:30]}: {str(e)}")
                    else:
                        st.info("Нет PDF для массового скачивания")
    
    with col2:
        st.header("📄 Generated Content")
        if hasattr(st.session_state, 'generated_content'):
            content_display.render(st.session_state.generated_content)
        else:
            st.info("🎯 Generate content to see the result here")
    
    # Секция вопросов к RAG
    st.markdown("---")
    st.header("❓ Ask Questions to RAG")
    
    col_q1, col_q2 = st.columns([3, 1])
    
    with col_q1:
        question = st.text_input(
            "Your Question",
            placeholder="Ask a question about the loaded documents...",
            key="rag_question"
        )
    
    with col_q2:
        question_search_type = st.selectbox(
            "Search Type",
            ["hybrid", "semantic", "bm25"],
            key="question_search_type"
        )
    
    if st.button("🤔 Ask Question"):
        if question:
            with st.spinner("Generating answer..."):
                try:
                    answer = api_client.ask_rag({
                        "question": question,
                        "search_type": question_search_type,
                        "top_k": 5
                    })
                    
                    # Отображаем ответ
                    st.subheader("💡 Answer")
                    st.markdown(answer["answer"])
                    
                    # Отображаем источники
                    if answer.get("sources"):
                        st.subheader("📚 Sources")
                        for i, source in enumerate(answer["sources"], 1):
                            with st.expander(f"Source {i}: {source.get('title', 'Unknown')}"):
                                st.markdown(f"**Content:** {source.get('content', '')[:300]}...")
                                st.metric("Relevance", f"{source.get('relevance_score', 0):.3f}")
                    
                    # Показываем метрики
                    col_met1, col_met2, col_met3 = st.columns(3)
                    with col_met1:
                        st.metric("Confidence", f"{answer.get('confidence', 0):.3f}")
                    with col_met2:
                        st.metric("Sources Used", answer.get("total_sources", 0))
                    with col_met3:
                        st.metric("Search Type", answer.get("search_type", "").title())
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter a question")

if __name__ == "__main__":
    main()
