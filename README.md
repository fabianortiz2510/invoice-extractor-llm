# invoice-extractor-llm

Aplicación que permite cargar una factura de servicios (imagen o PDF), extraer
sus datos clave usando un LLM con capacidad de visión, y visualizarlos en una
interfaz web. Arquitectura: **backend FastAPI + PostgreSQL** (SQLAlchemy 2.0
async + Alembic) y **frontend React + Vite**, en un monorepo.

## Datos extraídos

- **Fecha de emisión** (normalizada a `YYYY-MM-DD`) — obligatorio
- **Valor total a pagar** — obligatorio
- Moneda, proveedor/emisor y número de factura — opcionales, no rompen el
  flujo si el modelo no logra identificarlos (quedan como `null`)

## Estructura del proyecto

```
invoice-extractor-llm/
├── backend/                       # API FastAPI
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic/                    # migraciones
│   └── src/
│       ├── core/                   # config, conexión a BD
│       ├── shared/models/          # mixin compartido (id, created_at)
│       └── domains/invoices/       # modelo, schemas, service, router,
│                                     # extractor.py y llm_clients.py (capa LLM)
├── frontend/                       # SPA React + Vite + TypeScript + Tailwind
│   └── src/
│       ├── lib/api.ts               # cliente axios
│       ├── components/              # ExtractView, HistoryView
│       └── App.tsx
├── docker-compose.yml               # Postgres + backend
├── .env / .env.example
└── docs/                             # coloca aquí facturas de prueba
```

## Instalación y arranque

### 1. Variables de entorno

Copia `.env.example` a `.env` en la raíz del repo y completa:

- `LLM_PROVIDER`: `openai`, `anthropic` o `gemini`.
- La API key del proveedor elegido (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY` o
  `GEMINI_API_KEY`). Ninguna key está hardcodeada; cada cliente la lee de su
  propia variable de entorno.
- Las variables de Postgres (`POSTGRES_USER`, `POSTGRES_PASSWORD`,
  `POSTGRES_DB`, `DATABASE_URL`) ya vienen con valores por defecto que
  funcionan tal cual con `docker-compose.yml`.

### 2. Backend + base de datos (Docker)

```bash
docker compose up --build
```

Esto levanta Postgres, corre las migraciones de Alembic automáticamente y
arranca la API en `http://localhost:8000` (con recarga en caliente). Verifica
que esté arriba:

```bash
curl http://localhost:8000/health
```

Documentación interactiva de la API (Swagger): `http://localhost:8000/docs`.

> **Correr el backend fuera de Docker:** instala `backend/requirements.txt` en
> un entorno virtual, cambia el host `db` por `localhost` en `DATABASE_URL`,
> corre `alembic upgrade head` dentro de `backend/` y luego `uvicorn main:app
> --reload`.
>
> ⚠️ **En Windows**, si el Postgres al que apuntas corre en un contenedor de
> Docker Desktop (aunque sea solo `docker compose up db`), esto puede fallar
> con `ConnectionDoesNotExistError` / conexión reseteada — es una
> incompatibilidad conocida entre `asyncpg` y el proxy de red de Docker
> Desktop/WSL2 en Windows, no un bug del proyecto. En ese caso usa la Opción A
> (todo en Docker) o instala PostgreSQL nativamente en Windows (sin Docker de
> por medio) para esta combinación.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173`. El frontend ya viene configurado (`.env.local`)
para apuntar a `http://localhost:8000`.

### 4. Usar la app

1. Pestaña **"Extraer factura"**: sube un PNG, JPG o PDF, presiona "Extraer
   datos" y verás los campos estructurados + el JSON crudo del LLM.
2. Pestaña **"Historial"**: lista todas las facturas procesadas, leídas
   directamente de PostgreSQL.

Antes de entregar el proyecto, coloca al menos una factura de prueba (real o
ficticia) en `docs/` — ver `docs/README.txt`.

## API

| Método | Ruta                        | Descripción                                  |
| ------ | --------------------------- | --------------------------------------------- |
| POST   | `/api/v1/invoices/extract`  | Sube una factura (`multipart/form-data`, campo `file`), la extrae y la persiste |
| GET    | `/api/v1/invoices`          | Historial de facturas (más recientes primero) |
| GET    | `/api/v1/invoices/{id}`     | Detalle de una factura, incluyendo el JSON crudo del LLM |
| GET    | `/health`                   | Health check                                  |

## Decisiones técnicas

**Arquitectura backend/frontend separados (en vez de Streamlit)**
Streamlit es ideal para un prototipo de un solo archivo, pero un backend REST
+ SPA separa responsabilidades de forma más estándar en la industria:
el backend es reutilizable por cualquier cliente (web, móvil, CLI), y el
frontend puede evolucionar independientemente. Se mantiene un monorepo
(`backend/` + `frontend/`) por simplicidad, dado que es un solo desarrollador
entregando ambas piezas como una unidad.

**PostgreSQL + SQLAlchemy 2.0 async + Alembic**
Reemplaza el SQLite + acceso directo por `sqlite3` de la versión Streamlit.
`asyncpg` + SQLAlchemy async evita bloquear el event loop de FastAPI en cada
consulta; Alembic versiona el esquema de la base de datos en vez de depender
de `CREATE TABLE IF NOT EXISTS`, lo cual es la práctica estándar para
evolucionar un esquema en el tiempo sin perder datos.

**`extract_invoice_data` corre en threadpool**
Los SDKs de OpenAI/Anthropic/Gemini son síncronos. Para no bloquear el event
loop async de FastAPI mientras se espera la respuesta del LLM, el router la
invoca con `fastapi.concurrency.run_in_threadpool`.

**¿Por qué visión directa en vez de OCR?**
La imagen (o la primera página del PDF convertida a imagen con PyMuPDF) se
envía directamente al modelo con capacidad de visión, sin una etapa de OCR
intermedia que podría introducir errores de transcripción y pierde la
disposición espacial del documento (útil para que el modelo entienda tablas y
layouts de factura).

**¿Cómo se valida el JSON del LLM?**
1. El prompt de sistema le pide al modelo responder **exclusivamente** con un
   JSON de esquema fijo.
2. La respuesta se parsea (`json.loads`, limpiando posibles fences ```json)
   y se valida con un modelo **Pydantic** (`llm_schema.py: InvoiceExtraction`).
3. Si falla el parseo o la validación, se hace **un reintento** enviando al
   modelo el error obtenido y pidiéndole explícitamente que corrija el
   formato.
4. Si el segundo intento también falla, el endpoint devuelve `422` con el
   error — la extracción fallida **no se persiste** — sin que la API se caiga.
5. La fecha se normaliza aparte con `dateutil.parser` a `YYYY-MM-DD`; si no se
   puede interpretar, se guarda tal cual y se marca `fecha_emision_valida =
   false` en vez de fallar en silencio.

**Capa de abstracción de proveedores (`llm_clients.py`)**
`BaseLLMClient` define una interfaz común (`extract(...)`) implementada por
`OpenAIVisionClient`, `AnthropicVisionClient` y `GeminiVisionClient`. La
factory `get_llm_client()` decide cuál instanciar según `LLM_PROVIDER` — este
este archivo es código puro sin dependencias de framework.
