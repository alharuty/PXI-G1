import uvicorn
from .images_services import app

if __name__ == "__main__":
    print("🚀 Iniciando Microservicio de Generación de Imágenes...")
    print("📍 Puerto: 8001")
    print("🔗 Endpoints disponibles:")
    print("   POST /generar_imagen")
    print("   GET  /historial") 
    print("   GET  /imagen/{nombre}")
    print("   GET  /")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8001,
        reload=True,
        log_level="info"
    )