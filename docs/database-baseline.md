# IKAROS Database Baseline

Este documento describe el estado real confirmado de la base de datos de
IKAROS en el momento de la auditoria administrativa de solo lectura.

No es una migracion ejecutable. No debe ejecutarse como SQL ni debe
interpretarse como una instruccion para recrear las tablas actuales.

## Alcance

- Esquema documentado: `public`.
- Tablas: `users`, `profiles`, `tasks` y `reminders`.
- Fuente principal: resultados de la auditoria administrativa de PostgreSQL.
- Fuente complementaria: codigo y tests actuales del backend.
- Datos existentes durante la auditoria:
  - `users`: 3 registros.
  - `profiles`: 0 registros.
  - `tasks`: 4 registros.
  - `reminders`: 1 registro.

## CONFIRMADO

### Tablas y columnas

#### `public.users`

| Columna | Tipo | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | No | No confirmado |
| `email` | `text` | No | No confirmado |
| `full_name` | `text` | No | No confirmado |
| `created_at` | `timestamptz` | No | `now()` |
| `updated_at` | `timestamptz` | No | `now()` |

#### `public.profiles`

| Columna | Tipo | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | No | `gen_random_uuid()` |
| `user_id` | `uuid` | No | No confirmado |
| `avatar_url` | `text` | Si | No confirmado |
| `created_at` | `timestamptz` | No | `now()` |
| `updated_at` | `timestamptz` | No | `now()` |

#### `public.tasks`

| Columna | Tipo | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | No | `gen_random_uuid()` |
| `user_id` | `uuid` | No | No confirmado |
| `title` | `text` | No | No confirmado |
| `description` | `text` | Si | No confirmado |
| `status` | `text` | No | `pending` |
| `priority` | `text` | No | `medium` |
| `due_date` | `timestamptz` | Si | No confirmado |
| `created_at` | `timestamptz` | No | `now()` |
| `updated_at` | `timestamptz` | No | `now()` |

#### `public.reminders`

| Columna | Tipo | Nullable | Default |
|---|---|---|---|
| `id` | `uuid` | No | `gen_random_uuid()` |
| `task_id` | `uuid` | No | No confirmado |
| `user_id` | `uuid` | No | No confirmado |
| `remind_at` | `timestamptz` | No | No confirmado |
| `status` | `text` | No | `pending` |
| `channel` | `text` | No | `in_app` |
| `created_at` | `timestamptz` | No | `now()` |
| `updated_at` | `timestamptz` | No | `now()` |

### Primary keys y relaciones

Primary keys confirmadas:

- `users.id` mediante `users_pkey`.
- `profiles.id` mediante `profiles_pkey`.
- `tasks.id` mediante `tasks_pkey`.
- `reminders.id` mediante `reminders_pkey`.

Foreign keys confirmadas:

| Tabla y columna | Referencia | ON DELETE | ON UPDATE |
|---|---|---|---|
| `profiles.user_id` | `users.id` | `CASCADE` | `NO ACTION` |
| `tasks.user_id` | `users.id` | `CASCADE` | `NO ACTION` |
| `reminders.task_id` | `tasks.id` | `CASCADE` | `NO ACTION` |
| `reminders.user_id` | `users.id` | `CASCADE` | `NO ACTION` |

No existe una foreign key confirmada entre `public.users` y `auth.users`.

### Unique constraints

- `users.email` mediante `users_email_key`.
- `profiles.user_id` mediante `profiles_user_id_key`.
- `reminders(task_id, remind_at, channel)` mediante
  `reminders_task_schedule_unique`.

### Check constraints

#### `tasks`

- `status IN ('pending', 'completed')`.
- `priority IN ('low', 'medium', 'high')`.

#### `reminders`

- `status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')`.
- `channel IN ('in_app', 'email', 'whatsapp', 'push')`.

No se confirmaron checks de longitud para `title` o `description`.

### Indices

#### `users`

- `users_pkey`: primary key sobre `id`.
- `users_email_key`: unique sobre `email`.

#### `profiles`

- `profiles_pkey`: primary key sobre `id`.
- `profiles_user_id_key`: unique sobre `user_id`.

#### `tasks`

- `tasks_pkey`: primary key sobre `id`.
- `tasks_user_id_idx`: `user_id`.
- `tasks_user_status_idx`: `user_id, status`.
- `tasks_user_due_date_idx`: `user_id, due_date`.

#### `reminders`

- `reminders_pkey`: primary key sobre `id`.
- `reminders_pending_due_idx`: `remind_at`, parcial con `status = 'pending'`.
- `reminders_status_due_idx`: `status, remind_at`.
- `reminders_task_idx`: `task_id`.
- `reminders_user_idx`: `user_id`.
- `reminders_task_schedule_unique`: unique sobre `task_id, remind_at, channel`.

### Triggers y funciones

#### Trigger de Auth

En `auth.users` existe:

- `ikaros_on_auth_user_created`.
- Evento: `AFTER INSERT`.
- Funcion: `public.handle_new_auth_user()`.

La funcion esta confirmada como:

- `SECURITY DEFINER`.
- `search_path = public`.
- Exige email no vacio.
- Obtiene `full_name` desde `raw_user_meta_data`.
- Exige `full_name`.
- Inserta `id`, `email` y `full_name` en `public.users`.

#### Triggers `updated_at`

Existe `public.set_updated_at()`, que asigna `NEW.updated_at = now()` y retorna
`NEW`.

Se ejecuta antes de actualizar cada una de estas tablas:

- `public.users` mediante `users_set_updated_at`.
- `public.profiles` mediante `profiles_set_updated_at`.
- `public.tasks` mediante `tasks_set_updated_at`.
- `public.reminders` mediante `reminders_set_updated_at`.

### RLS y policies

RLS esta habilitado en:

- `users`.
- `profiles`.
- `tasks`.
- `reminders`.

`force RLS` esta deshabilitado en las cuatro tablas.

#### `users`

- `users_select_own`.
- `users_update_own`.
- `users_insert_blocked`.
- `users_delete_blocked`.

Las policies de lectura y actualizacion usan `id = auth.uid()`.
Las policies de insercion y eliminacion tienen condicion `false`.

#### `profiles`

- `profiles_select_own`.
- `profiles_insert_own`.
- `profiles_update_own`.
- `profiles_delete_own`.

#### `tasks`

- `tasks_select_own`.
- `tasks_insert_own`.
- `tasks_update_own`.
- `tasks_delete_own`.

#### `reminders`

- `reminders_select_own`.
- `reminders_insert_own`.
- `reminders_update_own`.
- `reminders_delete_own`.

Las policies de insercion y actualizacion de reminders tambien verifican que la
tarea relacionada pertenezca al `auth.uid()` correspondiente.

## NO VERIFICADO

Los siguientes puntos no forman parte de este baseline confirmado:

- Definiciones SQL completas de todas las policies.
- Propietario exacto de cada funcion y trigger.
- Privilegios efectivos de cada rol de PostgreSQL.
- Si `SUPABASE_WORKER_KEY` corresponde exactamente a un rol que omite RLS.
- Comportamiento de acceso de roles distintos de los cubiertos por las policies.
- Reglas adicionales de la tabla `auth.users` administrada por Supabase Auth.

No se agregan columnas, constraints, checks, indices, triggers ni policies que
no hayan sido confirmados.

## DECISIONES FUTURAS

### Futuras migraciones

Las migraciones futuras deben ser incrementales y partir de este baseline. No
deben recrear las cuatro tablas ni asumir una base vacia.

Antes de cada migracion se debe:

1. Comparar el estado real con este documento.
2. Revisar los objetos que ya existan.
3. Preparar cambios reversibles cuando sea posible.
4. Validar el impacto sobre los tres usuarios, cuatro tasks y un reminder
   existentes.
5. Ejecutar primero en un entorno controlado.

### Auth y `public.users`

El trigger actual sincroniza inserts desde `auth.users` hacia `public.users`,
pero no existe una foreign key confirmada entre ambos registros. Cualquier
decision futura sobre esa integridad debe considerar el comportamiento de
Supabase Auth antes de añadir una constraint.

### Longitud de tareas

El backend valida actualmente:

- `title`: entre 3 y 100 caracteres.
- `description`: hasta 500 caracteres.

La base no tiene checks confirmados para esas longitudes. Esto no se propone
modificar en este baseline; debe decidirse en una futura migracion.

### Schedule de reminders

La base impide duplicar la combinacion `(task_id, remind_at, channel)`. El
backend no crea una validacion previa para esa combinacion, pero transforma un
conflicto `23505` en una respuesta de conflicto.

### Worker

El worker consulta reminders `pending`, vencidos, ordenados por `remind_at` y
limitados por batch. Los indices `reminders_pending_due_idx` y
`reminders_status_due_idx` respaldan esas consultas.

El worker usa una clave separada y privilegiada. La forma exacta de sus
privilegios efectivos debe mantenerse como decision operativa independiente de
las policies de usuarios.

## Comparacion con el backend

### Coincidencias

- Las columnas de `tasks` coinciden con `TaskCreate`, `TaskUpdate` y
  `TaskResponse`.
- Los valores de `tasks.status` y `tasks.priority` coinciden con los enums del
  backend.
- Las columnas y estados de `reminders` coinciden con los schemas y el worker.
- Los canales de `reminders` coinciden con `ReminderChannel`.
- `profiles.user_id` unique coincide con el manejo de conflicto del servicio de
  perfiles.
- La unicidad de reminders coincide con el manejo de errores `23505` del
  servicio.
- Las policies de pertenencia coinciden con los filtros por usuario usados por
  los services.
- La policy de ownership de task para reminders coincide con
  `_validate_task_ownership()`.
- Los indices del worker coinciden con los filtros de `reminder_processor.py`.

### Discrepancias o riesgos reales

1. No hay una foreign key confirmada entre `public.users` y `auth.users`, aunque
   existe un trigger de sincronizacion. La sincronizacion depende de la funcion
   y no de integridad referencial declarativa.
2. El backend valida longitudes de `title` y `description`, pero la base no
   tiene checks confirmados equivalentes.
3. El backend no conoce ni valida directamente la unicidad de
   `(task_id, remind_at, channel)` antes del insert; depende del error de base
   `23505` para responder conflicto.
4. La funcion de Auth exige `email` y `full_name`; cualquier flujo que cree
   usuarios sin esos datos podria fallar al sincronizar `public.users`.

No se identificaron discrepancias de columnas, estados, canales, foreign keys
entre las tablas publicas, filtros del worker o indices necesarios para el
flujo actual.

## Estado del documento

Este archivo es una referencia documental del estado confirmado. No es una
migracion, no contiene SQL ejecutable y no autoriza cambios sobre Supabase.
