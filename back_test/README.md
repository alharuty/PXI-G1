# 🧠 Simple RAG System

Простая система RAG (Retrieval-Augmented Generation) для поиска и ответов на вопросы на основе научных статей из arXiv.

## 🚀 Возможности

- **🔍 Поиск статей** - поиск научных статей в arXiv
- **📚 Векторная база** - создание эмбеддингов и семантический поиск
- **❓ Q&A система** - ответы на вопросы на основе найденных статей
- **🤖 LLM интеграция** - поддержка OpenAI GPT и Google Gemini
- **🌐 Веб-интерфейс** - удобный Streamlit фронтенд

## 📋 Требования

- Python 3.8+
- API ключи для OpenAI или Google Gemini

## ⚙️ Установка

1. **Клонируйте репозиторий:**
```bash
cd PXI-G1/back_test
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте переменные окружения:**
```bash
# Скопируйте шаблон
cp env_template.txt .env

# Отредактируйте .env файл, добавив ваши API ключи:
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
LLM_PROVIDER=openai  # или gemini
OPENAI_MODEL=gpt-4o-mini
```

## 🚀 Запуск

### 1. Запуск сервера (в одном терминале):
```bash
python main.py
```

Сервер запустится на http://127.0.0.1:8000

### 2. Запуск фронтенда (в другом терминале):
```bash
streamlit run frontend.py
```

Фронтенд откроется на http://localhost:8501

## 📖 Использование

### 1. Поиск статей
- Введите поисковый запрос (например: "quantum computing")
- Выберите количество результатов
- Нажмите "Найти статьи"

### 2. Добавление в RAG
- Введите тему для поиска статей
- Нажмите "Добавить в RAG"
- Статьи будут загружены в векторную базу

### 3. Задавание вопросов
- Введите ваш вопрос
- Выберите количество источников
- Получите ответ на основе загруженных статей

### 4. Статистика
- Просмотрите количество документов
- Проверьте статус моделей
- Очистите документы при необходимости

## 🔧 API Endpoints

- `GET /` - Статус системы
- `POST /search-arxiv` - Поиск статей в arXiv
- `POST /add-documents` - Добавление статей в RAG
- `POST /ask` - Задавание вопросов
- `GET /stats` - Статистика системы
- `POST /clear` - Очистка документов

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   External      │
│   (Streamlit)   │◄──►│   Backend       │◄──►│   APIs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   RAG System    │
                       │                 │
                       │ • Embeddings    │
                       │ • Vector Search │
                       │ • LLM Response  │
                       └─────────────────┘
```

## 🧠 Модели

- **Embedding модель:** BAAI/bge-large-en-v1.5
- **LLM провайдеры:** OpenAI GPT-4o-mini, Google Gemini
- **Векторный поиск:** Косинусное сходство

## 🔍 Примеры использования

### Поиск статей:
```bash
curl -X POST "http://127.0.0.1:8000/search-arxiv" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "max_results": 5}'
```

### Добавление в RAG:
```bash
curl -X POST "http://127.0.0.1:8000/add-documents" \
  -H "Content-Type: application/json" \
  -d '{"query": "quantum computing", "max_results": 10}'
```

### Задавание вопроса:
```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"topic": "general", "question": "What is quantum computing?", "max_results": 5}'
```

## 🐛 Устранение неполадок

### Ошибка загрузки embedding модели:
- Проверьте интернет-соединение
- Модель загружается при первом запуске (~1.5GB)

### Ошибка LLM API:
- Проверьте API ключи в .env файле
- Убедитесь, что у вас есть доступ к выбранной модели

### Ошибка поиска статей:
- Проверьте интернет-соединение
- arXiv API может быть временно недоступен

## 📝 Лицензия

MIT License

## 🤝 Вклад в проект

Приветствуются pull requests и issues!