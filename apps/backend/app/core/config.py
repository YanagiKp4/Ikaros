from dotenv import load_dotenv
import os

# Cargar variables del archivo .env
load_dotenv()

# Configuración pública de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_PUBLIC_KEY = os.getenv("SUPABASE_PUBLIC_KEY")
