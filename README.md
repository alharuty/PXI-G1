# 🤖 BUDDY - AI Content Generation Platform

<img width="280" height="280" alt="Pine Tree Forest   Adventure Nature Logo (6)" src="https://github.com/user-attachments/assets/c4b0e234-137d-42d5-abf6-cc9f5354bebb" />


> **Plataforma integral de generación de contenido con IA, análisis financiero y sistema RAG científico**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[![Firebase](https://img.shields.io/badge/Firebase-039BE5?style=for-the-badge&logo=Firebase&logoColor=white)](https://firebase.google.com/)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)

## 📋 Índice

- [🎯 Descripción](#-descripción)
- [✨ Características Principales](#-características-principales)
- [🏗️ Arquitectura del Sistema](#️-arquitectura-del-sistema)
- [🛠️ Tecnologías Utilizadas](#️-tecnologías-utilizadas)
- [📋 Requisitos Previos](#-requisitos-previos)
- [🚀 Instalación](#-instalación)
- [⚙️ Configuración](#️-configuración)
- [🎮 Uso](#-uso)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [🔌 API Endpoints](#-api-endpoints)
- [Demo](#-Demo)
- [🤝 Contribución](#-contribución)
- [📄 Licencia](#-licencia)
- [🗒️ Articulo de Medium](#-https://medium.com/@jorge.luis.mateos.reyes/creando-buddy-una-plataforma-integral-de-ia-para-contenido-finanzas-y-ciencia-53c4af358915)

## 🎯 Descripción

**BUDDY** es una plataforma integral de generación de contenido potenciada por inteligencia artificial que combina múltiples servicios especializados:

- **Generación de Texto**: Creación automática de contenido para redes sociales, emails y más
- **Generación de Imágenes**: Creación de imágenes únicas usando modelos de difusión
- **Análisis Financiero**: Análisis inteligente de mercados, criptomonedas y tendencias
- **Sistema RAG Científico**: Búsqueda y análisis de artículos científicos con IA
- **Autenticación Completa**: Sistema de usuarios con Firebase Auth
- **Base de Datos Vectorial**: Almacenamiento y búsqueda semántica de documentos

## ✨ Características Principales

### 🎨 **Generación de Contenido**
- ✅ Texto para múltiples plataformas (Twitter, Facebook, LinkedIn, Instagram, Email)
- ✅ Generación de imágenes con Stable Diffusion
- ✅ Soporte multiidioma (Español, Inglés, Francés, Italiano)
- ✅ Personalización por audiencia y estilo

### 📊 **Análisis Financiero**
- ✅ Análisis de criptomonedas en tiempo real
- ✅ Seguimiento de acciones y mercados bursátiles
- ✅ Integración con APIs financieras (Alpha Vantage)
- ✅ Generación de reportes automáticos

### 🔬 **Sistema RAG Científico**
- ✅ Búsqueda automática en arXiv
- ✅ Descarga y procesamiento de PDFs
- ✅ Base de datos vectorial con embeddings
- ✅ Consultas inteligentes sobre artículos científicos
- ✅ Comparación RAG vs respuesta simple

### 👤 **Sistema de Usuarios**
- ✅ Autenticación con Firebase Auth
- ✅ Perfiles de usuario personalizables
- ✅ Historial de generaciones
- ✅ Trazabilidad de uso

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Servicios     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   Externos      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
│                      │                      │
├─ Dashboard          ├─ API Unificada       ├─ OpenAI/Groq
├─ Text Generator     ├─ Sistema RAG         ├─ Hugging Face
├─ Image Generator    ├─ Vector Store        ├─ Firebase
├─ Financial News     ├─ Auth Management     ├─ Supabase
├─ Scientific RAG     ├─ File Management     ├─ Alpha Vantage
└─ User Profile       └─ Data Processing     └─ arXiv API
```

## 🛠️ Tecnologías Utilizadas

### **Backend**
- **FastAPI** - Framework web moderno y rápido
- **Python 3.13** - Lenguaje principal
- **Groq** - API de LLM para generación de texto
- **Sentence Transformers** - Embeddings para búsqueda semántica
- **Qdrant** - Base de datos vectorial
- **PyPDF2** - Procesamiento de documentos PDF
- **Firebase Admin SDK** - Autenticación y base de datos
- **Supabase** - Base de datos PostgreSQL

### **Frontend**
- **React 18** - Biblioteca de interfaz de usuario
- **Tailwind CSS** - Framework de estilos
- **React Icons** - Iconografía
- **Axios** - Cliente HTTP
- **Firebase SDK** - Autenticación del cliente

### **APIs y Servicios**
- **Groq API** - Modelos de lenguaje Llama
- **Hugging Face** - Modelos de generación de imágenes
- **Alpha Vantage** - Datos financieros
- **arXiv API** - Artículos científicos
- **Firebase** - Autenticación y base de datos
- **Supabase** - Almacenamiento y analytics

## 📋 Requisitos Previos

- **Python 3.11+** instalado
- **Node.js 18+** y npm
- **Git** para clonar el repositorio
- Cuentas y API keys para:
  - Groq API
  - Hugging Face
  - Firebase
  - Supabase
  - Alpha Vantage (opcional)

## 🚀 Instalación

### 1. **Clonar el Repositorio**
```bash
git clone https://github.com/alharuty/PXI-G1.git
cd PXI-G1
```

### 2. **Configurar el Backend**
```bash
# Navegar al backend
cd backend

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# En Windows:
.venv\Scripts\activate
# En macOS/Linux:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. **Configurar el Frontend**
```bash
# Navegar al frontend
cd frontend/app

# Instalar dependencias
npm install
```

### 4. **Configurar Variables de Entorno**
```bash
# Copiar archivos de ejemplo
cp .env.example .env
cp frontend/app/.env.example frontend/app/.env

# Editar los archivos .env con tus API keys
```

## ⚙️ Configuración

### **Backend (.env)**
```env
# APIs Keys
GROQ_API_KEY=tu_groq_api_key
HUGGINGFACE_API_KEY=tu_huggingface_api_key
ALPHAVANTAGE_API_KEY=tu_alphavantage_api_key
OPENAI_API_KEY=tu_openai_api_key

# Supabase
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_key

# Firebase Service Account
FIREBASE_TYPE=service_account
FIREBASE_PROJECT_ID=tu_proyecto_id
FIREBASE_PRIVATE_KEY_ID=tu_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\ntu_private_key\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=tu_client_email
# ... otros campos de Firebase

# Vector Storage (opcional)
QDRANT_URL=tu_qdrant_url
QDRANT_API_KEY=tu_qdrant_api_key
VECTOR_STORAGE_TYPE=local  # o qdrant_cloud
```

### **Frontend (.env)**
```env
# Firebase Config (proyecto web)
REACT_APP_API_KEY=tu_firebase_api_key
REACT_APP_AUTH_DOMAIN=tu_proyecto.firebaseapp.com
REACT_APP_PROJECT_ID=tu_proyecto_id
REACT_APP_STORAGE_BUCKET=tu_proyecto.appspot.com
REACT_APP_MESSAGING_SENDER_ID=tu_sender_id
REACT_APP_APP_ID=tu_app_id

# Backend URL
REACT_APP_API_BASE_URL=http://localhost:8000
```

### **Configurar Firebase**
1. Crear proyecto en [Firebase Console](https://console.firebase.google.com/)
2. Habilitar Authentication con Email/Password
3. Crear Service Account y descargar JSON
4. Configurar variables de entorno con los datos del Service Account

### **Configurar Supabase**
1. Crear proyecto en [Supabase](https://supabase.com/)
2. Obtener URL y API Key
3. Ejecutar scripts SQL para crear tablas (si es necesario)

## 🎮 Uso

### **Iniciar el Backend**
```bash
cd backend
uvicorn main:app --reload
```
El backend estará disponible en: http://localhost:8000

### **Iniciar el Frontend**
```bash
cd frontend/app
npm start
```
El frontend estará disponible en: http://localhost:3000

### **Acceder a la Documentación API**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📁 Estructura del Proyecto

```
PXI-G1/
├── backend/                    # Servidor FastAPI
│   ├── app/                   # Módulos principales
│   │   ├── agents.py         # Agentes de generación de contenido
│   │   ├── arXiv.py          # Extractor de artículos científicos
│   │   ├── models.py         # Modelos Pydantic
│   │   ├── rag_generator.py  # Sistema RAG
│   │   ├── vector_store_config.py # Configuración vectorial
│   │   └── ...
│   ├── services/             # Servicios especializados
│   │   ├── nlp_generator.py  # Generación de texto
│   │   ├── img_generation_functions.py # Generación de imágenes
│   │   ├── alpha_client.py   # Cliente financiero
│   │   └── ...
│   ├── models/               # Modelos de datos
│   ├── DB/                   # Configuración de bases de datos
│   ├── main.py              # Aplicación principal
│   └── requirements.txt     # Dependencias Python
│
├── frontend/app/             # Aplicación React
│   ├── src/
│   │   ├── components/      # Componentes reutilizables
│   │   ├── pages/          # Páginas principales
│   │   │   ├── Dashboard.js
│   │   │   ├── TextGenerator.js
│   │   │   ├── ImageGenerator.js
│   │   │   ├── ScientificRAG.js
│   │   │   └── ...
│   │   ├── firebase.js     # Configuración Firebase
│   │   └── ...
│   ├── public/             # Archivos estáticos
│   └── package.json        # Dependencias Node.js
│
├── arxiv_papers/            # Artículos científicos descargados
├── huggingface_cache/       # Cache de modelos
├── .env.example            # Ejemplo de variables de entorno
└── README.md               # Este archivo
```

## 🔌 API Endpoints

### **Generación de Contenido**
- `POST /generate` - Generar texto para redes sociales
- `POST /generate-image` - Generar imágenes con IA
- `POST /news-nlp` - Análisis financiero inteligente

### **Sistema RAG Científico**
- `GET /arxiv/search` - Buscar artículos en arXiv
- `POST /vector/add_articles_from_search` - Agregar artículos a base vectorial
- `POST /rag/generate` - Consultar base de conocimientos
- `GET /rag/compare` - Comparar respuestas RAG vs simple

### **Gestión de Datos**
- `GET /vector/search` - Buscar en base vectorial
- `GET /vector/statistics` - Estadísticas de la base de datos
- `POST /api/trazabilidad` - Crear registro de trazabilidad

### **Información del Sistema**
- `GET /` - Estado del servidor
- `GET /health` - Health check completo
- `GET /docs` - Documentación Swagger

## Demo

Dashboard
<img width="1417" height="814" alt="Macbook-Air-localhost" src="https://github.com/user-attachments/assets/c45ebb42-8f4a-4181-ae24-1883e276b750" />

Generación de Texto
<img width="1417" height="814" alt="Macbook-Air-localhost (1)" src="https://github.com/user-attachments/assets/6df5d4e9-25f6-4925-b71a-6bb373873d16" />

Generación de Imágenes
<img width="1417" height="814" alt="Macbook-Air-localhost (2)" src="https://github.com/user-attachments/assets/e0af60f3-5340-41f6-a550-a34176769473" />
<img width="1417" height="814" alt="Macbook-Air-localhost (4)" src="https://github.com/user-attachments/assets/c6d64677-be48-4c14-97a8-29a1e47efd0d" />

Noticias Financieras
<img width="1417" height="814" alt="Macbook-Air-localhost (5)" src="https://github.com/user-attachments/assets/e9bfdd54-87be-41af-ae9f-02019a0c83f4" />

RAG científico 
<img width="1417" height="814" alt="Macbook-Air-localhost (6)" src="https://github.com/user-attachments/assets/5317aa6c-3afd-4862-8682-b39b8978e995" />
<img width="1417" height="814" alt="Macbook-Air-localhost (7)" src="https://github.com/user-attachments/assets/546faac2-f8b5-4330-9057-f069bb81449c" />
<img width="1417" height="814" alt="Macbook-Air-localhost (8)" src="https://github.com/user-attachments/assets/5eff592d-b4bd-4a42-8d32-a72ad4e01848" />


## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### **Estándares de Código**
- Python: Seguir PEP 8
- JavaScript: Usar ESLint y Prettier
- Commits: Usar conventional commits

## � Autores

Este proyecto fue desarrollado por un equipo talentoso de desarrolladores:

<div align="center">

[![alharuty](https://img.shields.io/badge/GitHub-alharuty-black?style=for-the-badge&logo=github&logoColor=white)](https://github.com/alharuty)
[![MarynaDRST](https://img.shields.io/badge/GitHub-MarynaDRST-black?style=for-the-badge&logo=github&logoColor=white)](https://github.com/MarynaDRST)
[![Jorgeluuu](https://img.shields.io/badge/GitHub-Jorgeluuu-black?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Jorgeluuu)
[![DarthVada36](https://img.shields.io/badge/GitHub-DarthVada36-black?style=for-the-badge&logo=github&logoColor=white)](https://github.com/DarthVada36)
[![MaximilianoScarlato](https://img.shields.io/badge/GitHub-MaximilianoScarlato-black?style=for-the-badge&logo=github&logoColor=white)](https://github.com/MaximilianoScarlato)

</div>

---

## �📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

## 🆘 Soporte

Si tienes problemas o preguntas:

1. Revisa la [documentación](#-uso)
2. Busca en los [issues existentes](https://github.com/alharuty/PXI-G1/issues)
3. Crea un [nuevo issue](https://github.com/alharuty/PXI-G1/issues/new)

---

<div align="center">
  <h3>🚀 ¡Desarrollado con ❤️ para la comunidad!</h3>
  <p>Si este proyecto te fue útil, considera darle una ⭐ en GitHub</p>
</div>
