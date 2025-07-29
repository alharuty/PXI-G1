# 🌤️ Cloud Qdrant Setup Guide

## Overview

This guide will help you set up cloud storage Qdrant for your ArXiv Search & RAG project.

## 🚀 Setup Steps

### 1. Qdrant Cloud Registration

1. Go to [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create an account
3. Create a new cluster
4. Get API key and cluster URL

### 2. Install Dependencies

```bash
pip install qdrant-client sentence-transformers
```

### 3. Environment Variables Configuration

Create a `.env` file in the project root:

```bash
# Storage configuration
VECTOR_STORAGE_TYPE=qdrant_cloud

# Qdrant Cloud configuration
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key-here

# Optional configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=50
CLOUD_COLLECTION=arxiv_articles_cloud
```

### 4. Configuration Verification

Run the configuration test:

```bash
cd PXI-G1/backend
python app/vector_store_config.py
```

Expected output:
```
🔧 Vector Store Configuration
==================================================
Current storage: qdrant_cloud
Available options: ['local', 'qdrant_local', 'qdrant_cloud']
Configuration: {'storage_type': 'qdrant_cloud', 'qdrant_url': 'https://your-cluster.qdrant.io', 'collection_name': 'arxiv_articles_cloud', 'api_key_configured': True}
✅ Cloud Qdrant properly configured
```

## 🔄 Switching Between Storage Types

### Local Storage (default)
```bash
VECTOR_STORAGE_TYPE=local
```

### Local Qdrant
```bash
VECTOR_STORAGE_TYPE=qdrant_local
QDRANT_LOCAL_URL=http://localhost:6333
```

### Cloud Qdrant
```bash
VECTOR_STORAGE_TYPE=qdrant_cloud
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
```

## 🧪 Testing

### 1. Start Server
```bash
cd PXI-G1/backend
uvicorn main:app --reload --port 8000
```

### 2. Check Storage Status
```bash
curl http://localhost:8000/vector/statistics
```

### 3. Add Test Data
```bash
curl -X GET "http://localhost:8000/arxiv/search?topic=quantum%20computing&max_results=2"
```

### 4. Search in Cloud Storage
```bash
curl -X GET "http://localhost:8000/vector/search?query=quantum%20computing&top_k=5"
```

## 📊 Monitoring

### Check Statistics
```bash
curl http://localhost:8000/vector/statistics | jq
```

Example response:
```json
{
  "statistics": {
    "collection_name": "arxiv_articles_cloud",
    "total_points": 150,
    "vector_size": 384,
    "distance_metric": "Cosine",
    "embedding_model": 384,
    "chunk_size": 512,
    "chunk_overlap": 50,
    "storage_type": "qdrant_cloud"
  },
  "storage_config": {
    "current_storage": "qdrant_cloud",
    "available_storages": ["local", "qdrant_local", "qdrant_cloud"],
    "configuration": {
      "storage_type": "qdrant_cloud",
      "qdrant_url": "https://your-cluster.qdrant.io",
      "collection_name": "arxiv_articles_cloud",
      "api_key_configured": true
    },
    "cloud_configured": true
  }
}
```

## 🔧 Troubleshooting

### Error: "Qdrant cloud not properly configured"
```bash
# Check environment variables
echo $QDRANT_URL
echo $QDRANT_API_KEY

# Make sure they are set
export QDRANT_URL="https://your-cluster.qdrant.io"
export QDRANT_API_KEY="your-api-key"
```

### Error: "Connection failed"
```bash
# Check cluster URL
curl -H "api-key: your-api-key" https://your-cluster.qdrant.io/collections

# Make sure API key is correct
```

### Error: "Collection not found"
```bash
# Collection is created automatically on first use
# Try adding documents via API
```

## 💰 Pricing

Qdrant Cloud offers:
- **Free tier**: 1GB storage, 1000 requests/day
- **Paid plans**: From $10/month for additional resources

## 🔒 Security

- Store API keys in environment variables
- Don't commit `.env` files to git
- Use HTTPS for all connections
- Rotate API keys regularly

## 📈 Performance

### Performance Comparison:

| Metric | Local | Qdrant Local | Qdrant Cloud |
|--------|-------|--------------|--------------|
| Search Speed | Medium | High | Very High |
| Scalability | Limited | Medium | Unlimited |
| Reliability | Low | Medium | High |
| Cost | Free | Free | Paid |

## 🎯 Recommendations

### For Development:
- Use `VECTOR_STORAGE_TYPE=local`
- Quick setup and debugging

### For Testing:
- Use `VECTOR_STORAGE_TYPE=qdrant_local`
- Test Qdrant performance

### For Production:
- Use `VECTOR_STORAGE_TYPE=qdrant_cloud`
- High reliability and scalability 