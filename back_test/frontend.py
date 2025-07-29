import streamlit as st
import requests
import json

st.set_page_config(page_title="Simple RAG System", layout="wide")

st.title("🧠 Simple RAG System")
st.markdown("Система поиска и ответов на вопросы на основе научных статей")

# Боковая панель для настроек
with st.sidebar:
    st.header("⚙️ Настройки")
    
    # Выбор API
    api_url = st.text_input("API URL", value="http://127.0.0.1:8000")
    
    # Проверка подключения
    if st.button("🔍 Проверить подключение"):
        try:
            response = requests.get(f"{api_url}/")
            if response.status_code == 200:
                st.success("✅ Подключение успешно!")
                data = response.json()
                st.info(f"Документов в системе: {data['docs_count']}")
            else:
                st.error("❌ Ошибка подключения")
        except Exception as e:
            st.error(f"❌ Ошибка: {e}")

# Основной контент
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Поиск статей", "📚 Добавить в RAG", "❓ Задать вопрос", "📊 Статистика"])

with tab1:
    st.header("Поиск статей в arXiv")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("Поисковый запрос", placeholder="например: quantum computing")
    with col2:
        max_results = st.number_input("Количество результатов", min_value=1, max_value=20, value=5)
    
    if st.button("🔍 Найти статьи"):
        if search_query:
            with st.spinner("Поиск статей..."):
                try:
                    response = requests.post(f"{api_url}/search-arxiv", 
                                           json={"query": search_query, "max_results": max_results})
                    
                    if response.status_code == 200:
                        data = response.json()
                        articles = data["articles"]
                        
                        st.success(f"Найдено {len(articles)} статей")
                        
                        for i, article in enumerate(articles, 1):
                            with st.expander(f"{i}. {article['title']}"):
                                st.write(f"**Авторы:** {', '.join(article['authors'])}")
                                st.write(f"**Ссылка:** {article['link']}")
                                st.write(f"**Аннотация:** {article['summary']}")
                    else:
                        st.error("Ошибка при поиске статей")
                        
                except Exception as e:
                    st.error(f"Ошибка: {e}")
        else:
            st.warning("Введите поисковый запрос")

with tab2:
    st.header("Добавить статьи в RAG систему")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        rag_query = st.text_input("Поисковый запрос для RAG", placeholder="например: machine learning")
    with col2:
        rag_max_results = st.number_input("Количество статей", min_value=1, max_value=20, value=5)
    
    if st.button("📚 Добавить в RAG"):
        if rag_query:
            with st.spinner("Добавление статей в RAG..."):
                try:
                    response = requests.post(f"{api_url}/add-documents", 
                                           json={"query": rag_query, "max_results": rag_max_results})
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(data["message"])
                        st.info(f"Всего документов: {data['total_docs']}")
                    else:
                        st.error("Ошибка при добавлении документов")
                        
                except Exception as e:
                    st.error(f"Ошибка: {e}")
        else:
            st.warning("Введите поисковый запрос")

with tab3:
    st.header("Задать вопрос к RAG системе")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        question = st.text_input("Ваш вопрос", placeholder="например: Что такое квантовые вычисления?")
    with col2:
        question_max_results = st.number_input("Количество источников", min_value=1, max_value=10, value=5)
    
    if st.button("❓ Получить ответ"):
        if question:
            with st.spinner("Генерация ответа..."):
                try:
                    response = requests.post(f"{api_url}/ask", 
                                           json={"topic": "general", "question": question, "max_results": question_max_results})
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Ответ
                        st.subheader("🤖 Ответ:")
                        st.write(data["answer"])
                        
                        # Уверенность
                        confidence = data["confidence"]
                        st.metric("Уверенность", f"{confidence:.2f}")
                        
                        # Источники
                        if data["sources"]:
                            st.subheader("📚 Источники:")
                            for i, source in enumerate(data["sources"], 1):
                                with st.expander(f"{i}. {source['title']} (сходство: {source['similarity']:.2f})"):
                                    st.write(f"**Авторы:** {', '.join(source['authors'])}")
                                    st.write(f"**Ссылка:** {source['link']}")
                        else:
                            st.info("Источники не найдены")
                            
                    else:
                        st.error("Ошибка при получении ответа")
                        
                except Exception as e:
                    st.error(f"Ошибка: {e}")
        else:
            st.warning("Введите вопрос")

with tab4:
    st.header("Статистика системы")
    
    if st.button("📊 Обновить статистику"):
        try:
            response = requests.get(f"{api_url}/stats")
            
            if response.status_code == 200:
                data = response.json()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Документов", data["total_documents"])
                with col2:
                    st.metric("Embedding модель", data["embedding_model"])
                with col3:
                    st.metric("LLM провайдер", data["llm_provider"])
                
                st.info(f"LLM модель: {data['llm_model']}")
                
            else:
                st.error("Ошибка при получении статистики")
                
        except Exception as e:
            st.error(f"Ошибка: {e}")
    
    # Кнопка очистки
    if st.button("🗑️ Очистить все документы"):
        try:
            response = requests.post(f"{api_url}/clear")
            
            if response.status_code == 200:
                st.success("Все документы очищены!")
            else:
                st.error("Ошибка при очистке")
                
        except Exception as e:
            st.error(f"Ошибка: {e}")

# Инструкции
st.markdown("---")
st.markdown("""
### 📖 Инструкция по использованию:

1. **🔍 Поиск статей** - найдите статьи в arXiv
2. **📚 Добавить в RAG** - загрузите статьи в систему для ответов на вопросы
3. **❓ Задать вопрос** - получите ответ на основе загруженных статей
4. **📊 Статистика** - посмотрите состояние системы

### ⚙️ Настройка:
1. Скопируйте `env_template.txt` в `.env`
2. Добавьте ваши API ключи
3. Запустите сервер: `python main.py`
4. Запустите фронтенд: `streamlit run frontend.py`
""") 