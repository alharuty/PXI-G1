import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if url and key:
    supabase: Client = create_client(url, key)
    print("✅ Supabase conectado")
else:
    supabase = None
    print("⚠️ Supabase no configurado")