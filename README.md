# IKAROS

IKAROS es actualmente un backend para autenticacion, perfiles, tareas y
recordatorios. Su proposito es proporcionar una API HTTP protegida y persistir
los datos mediante Supabase.

Tecnologias actuales:

- Python
- FastAPI
- Uvicorn
- Pydantic
- Supabase Auth y Supabase Database
- Pytest

## Estado actual

El backend actual incluye:

- FastAPI con endpoints de health check.
- Autenticacion mediante registro, login y verificacion de token con Supabase Auth.
- Perfiles asociados al usuario autenticado.
- Tareas con operaciones de consulta, creacion, actualizacion y eliminacion.
- Reminders con operaciones de consulta, creacion, actualizacion y eliminacion.
- Un reminder worker independiente que procesa reminders vencidos por lotes.
- Una suite de tests para autenticacion, tareas, reminders, schemas, routers y worker.

Calendar, IA, Memory, WhatsApp, Android e iOS no estan implementados actualmente.

## Arquitectura actual

```text
FastAPI
  |
  v
Routers
  |
  v
Services
  |
  v
Supabase
```

- La autenticacion utiliza Supabase Auth.
- Las operaciones normales identifican al usuario mediante el usuario autenticado.
- Las operaciones de usuario utilizan el cliente Supabase autenticado con su token.
- El reminder worker utiliza una configuracion privilegiada separada mediante `SUPABASE_WORKER_KEY`.

## Estructura del proyecto

```text
apps/backend/app/
├── core/
├── db/
├── routers/
├── schemas/
├── services/
└── workers/

tests/
├── fakes/
└── test_*.py
```

## Requisitos

- Python instalado.
- Una instancia de Supabase.
- Un entorno virtual recomendado para aislar las dependencias.
- Las variables de entorno indicadas en `.env.example`.

La version de Python no esta fijada en este repositorio.

## Instalacion

Desde la raiz del proyecto, en Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si PowerShell bloquea la activacion del entorno, debe ajustarse la politica de
ejecucion de la maquina segun las reglas del entorno local.

## Variables de entorno

Crea un archivo `.env` local tomando `.env.example` como referencia. No uses
valores reales en el repositorio.

- `SUPABASE_URL`: URL del proyecto Supabase.
- `SUPABASE_PUBLIC_KEY`: clave publica usada por las operaciones normales.
- `SUPABASE_WORKER_KEY`: clave privilegiada usada exclusivamente por el worker.
- `REMINDER_WORKER_INTERVAL_SECONDS`: intervalo positivo entre ciclos del worker.
- `REMINDER_WORKER_BATCH_SIZE`: cantidad positiva maxima de reminders por ciclo.

`SUPABASE_URL`, `SUPABASE_PUBLIC_KEY` y `SUPABASE_WORKER_KEY` son obligatorias.
Las dos variables del worker tienen valores predeterminados positivos en la
configuracion.

## Ejecucion del backend

Desde la raiz del proyecto, con el entorno virtual activo:

```powershell
uvicorn apps.backend.app.main:app --reload
```

La aplicacion expone, entre otros, los grupos de endpoints de health,
autenticacion, perfiles, tareas y reminders.

## Tests

Suite completa:

```powershell
python -m pytest -v
```

Suite completa con cobertura:

```powershell
python -m pytest --cov=apps.backend.app --cov-report=term-missing -v
```

Los tests utilizan un fake local de Supabase y no requieren conectarse a una
instancia real.

## Reminder Worker

El worker es independiente de FastAPI y se ejecuta como modulo separado:

```powershell
python -m apps.backend.app.workers.reminder_worker
```

Lee la configuracion del worker desde el entorno, obtiene reminders pendientes
y vencidos, los reclama de forma condicional y actualiza sus estados durante
el procesamiento. Se detiene al recibir `KeyboardInterrupt`.

## Seguridad

- No coloques secretos reales, tokens ni passwords en Git.
- Mantén los valores reales en el archivo `.env` local.
- Usa `.env.example` solo con placeholders seguros.
- No utilices `SUPABASE_WORKER_KEY` para operaciones normales de usuario.

## Roadmap

### Futuro / Roadmap

- Calendar.
- IA y assistant tools.
- Memory.
- Rutinas y recurrencia.
- Notificaciones avanzadas.
- Android.
- WhatsApp.
- iOS.
