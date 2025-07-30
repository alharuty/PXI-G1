#!/usr/bin/env python3
"""
Vector Store Configuration
Choose between local and cloud storage options
"""
from dotenv import load_dotenv

import os
from typing import Optional
from enum import Enum
load_dotenv()

class StorageType(Enum):
    """Available storage types"""
    LOCAL = "local"           # SimpleHuggingFaceStore (file-based)
    QDRANT_LOCAL = "qdrant_local"  # Local Qdrant
    QDRANT_CLOUD = "qdrant_cloud"  # Cloud Qdrant

class VectorStoreConfig:
    """Configuration for vector store selection"""
    
    def __init__(self):
        # Get storage type from environment variable
        self.storage_type = os.getenv("VECTOR_STORAGE_TYPE", "local")
        
        # Qdrant cloud configuration
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        # Qdrant local configuration
        self.qdrant_local_url = os.getenv("QDRANT_LOCAL_URL", "http://localhost:6333")
        
        # Embedding model configuration
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        
        # Chunking configuration
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "512"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
        
        # Collection names
        self.local_collection = os.getenv("LOCAL_COLLECTION", "arxiv_articles_local")
        self.cloud_collection = os.getenv("CLOUD_COLLECTION", "arxiv_articles_cloud")
    
    def get_storage_type(self) -> StorageType:
        """Get current storage type"""
        try:
            return StorageType(self.storage_type)
        except ValueError:
            print(f"⚠️ Unknown storage type: {self.storage_type}, falling back to local")
            return StorageType.LOCAL
    
    def is_cloud_enabled(self) -> bool:
        """Check if cloud storage is configured"""
        return (
            self.storage_type == "qdrant_cloud" and 
            self.qdrant_url and 
            self.qdrant_api_key
        )
    
    def is_qdrant_local_enabled(self) -> bool:
        """Check if local Qdrant is configured"""
        return self.storage_type == "qdrant_local"
    
    def get_storage_info(self) -> dict:
        """Get current storage configuration info"""
        storage_type = self.get_storage_type()
        
        info = {
            "storage_type": storage_type.value,
            "embedding_model": self.embedding_model,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }
        
        if storage_type == StorageType.QDRANT_CLOUD:
            info.update({
                "qdrant_url": self.qdrant_url,
                "collection_name": self.cloud_collection,
                "api_key_configured": bool(self.qdrant_api_key)
            })
        elif storage_type == StorageType.QDRANT_LOCAL:
            info.update({
                "qdrant_url": self.qdrant_local_url,
                "collection_name": self.local_collection
            })
        else:  # LOCAL
            info.update({
                "storage_method": "file_based",
                "cache_dir": "./huggingface_cache"
            })
        
        return info

# Global configuration instance
config = VectorStoreConfig()

def create_vector_store():
    """
    Create vector store based on configuration
    
    Returns:
        Configured vector store instance
    """
    storage_type = config.get_storage_type()
    
    if storage_type == StorageType.QDRANT_CLOUD:
        if not config.is_cloud_enabled():
            raise ValueError(
                "Qdrant cloud not properly configured. "
                "Set QDRANT_URL and QDRANT_API_KEY environment variables."
            )
        
        from app.qdrant_vector_store import QdrantVectorStore
        return QdrantVectorStore(
            collection_name=config.cloud_collection,
            qdrant_url=config.qdrant_url,
            qdrant_api_key=config.qdrant_api_key,
            embedding_model=config.embedding_model,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
    
    elif storage_type == StorageType.QDRANT_LOCAL:
        from app.qdrant_vector_store import QdrantVectorStore
        return QdrantVectorStore(
            collection_name=config.local_collection,
            qdrant_url=config.qdrant_local_url,
            embedding_model=config.embedding_model,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )
    
    else:  # LOCAL
        from app.local_vector_store import SimpleHuggingFaceStore
        return SimpleHuggingFaceStore(
            model_name=config.embedding_model,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )

def get_storage_status() -> dict:
    """
    Get current storage status and configuration
    
    Returns:
        Dictionary with storage status information
    """
    storage_type = config.get_storage_type()
    
    status = {
        "current_storage": storage_type.value,
        "available_storages": [st.value for st in StorageType],
        "configuration": config.get_storage_info()
    }
    
    # Check if cloud is properly configured
    if storage_type == StorageType.QDRANT_CLOUD:
        status["cloud_configured"] = config.is_cloud_enabled()
        if not config.is_cloud_enabled():
            status["cloud_issues"] = []
            if not config.qdrant_url:
                status["cloud_issues"].append("QDRANT_URL not set")
            if not config.qdrant_api_key:
                status["cloud_issues"].append("QDRANT_API_KEY not set")
    
    return status

# Environment variable examples
ENV_EXAMPLES = """
# Local storage (default)
VECTOR_STORAGE_TYPE=local

# Local Qdrant
VECTOR_STORAGE_TYPE=qdrant_local
QDRANT_LOCAL_URL=http://localhost:6333

# Cloud Qdrant
VECTOR_STORAGE_TYPE=qdrant_cloud
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key

# Optional configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=50
LOCAL_COLLECTION=arxiv_articles_local
CLOUD_COLLECTION=arxiv_articles_cloud
"""

if __name__ == "__main__":
    # Test configuration
    print("🔧 Vector Store Configuration")
    print("=" * 50)
    
    status = get_storage_status()
    print(f"Current storage: {status['current_storage']}")
    print(f"Available options: {status['available_storages']}")
    print(f"Configuration: {status['configuration']}")
    
    if status['current_storage'] == 'qdrant_cloud':
        if status.get('cloud_configured'):
            print("✅ Cloud Qdrant properly configured")
        else:
            print("❌ Cloud Qdrant configuration issues:")
            for issue in status.get('cloud_issues', []):
                print(f"  - {issue}")
    
    print("\n📝 Environment variable examples:")
    print(ENV_EXAMPLES) 