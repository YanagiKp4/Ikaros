from dotenv import load_dotenv
import os

# Cargar variables del archivo .env
load_dotenv()

# Configuración pública de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_PUBLIC_KEY = os.getenv("SUPABASE_PUBLIC_KEY")

# Configuración del worker de reminders
SUPABASE_WORKER_KEY = os.getenv("SUPABASE_WORKER_KEY")
REMINDER_WORKER_INTERVAL_SECONDS = float(
    os.getenv("REMINDER_WORKER_INTERVAL_SECONDS", "10")
)
REMINDER_WORKER_BATCH_SIZE = int(
    os.getenv("REMINDER_WORKER_BATCH_SIZE", "10")
)
