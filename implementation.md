Guía completa – Bot de Atención al Cliente AI (MVP clonable)

Objetivo: que cualquier negocio pequeño (food truck, tiendita) pueda clonar, configurar y correr un bot de atención en minutos, con UI sencilla, RAG/FAQs, pedidos simples y conectores opcionales (Web, WhatsApp, Telegram). Diseño para que un AI agent programador pueda implementarlo paso a paso sin ambigüedades.

0. Línea base (qué sí / qué no)

Sí (MVP):

Chat web embebible + panel admin sencillo.

Base de conocimiento local (FAQs/menu/documentos) con RAG ligero.

Flujo de pedido rápido (nombre → producto → cantidad → confirmación).

Conectores opcionales: WhatsApp (Twilio/Cloud API), Telegram.

Persistencia local (SQLite), llaves en .env, configuración en config.yaml.

No (v1): pagos en línea, inventario avanzado, CRM complejo, analítica pesada. (Se dejan ganchos.)

1. Fases de desarrollo (con entregables y criterios de aceptación)

Fase 1 — Estructura & Configuración (Día 1)

Entregables:

Repo inicial, README.md, requirements.txt, config_example.yaml, .env.example.

FastAPI + Uvicorn corriendo (/healthz).

Carga de settings desde .env y config.yaml.

Criterios: uvicorn app.main:app --reload levanta y /healthz devuelve {status:"ok"}.

Fase 2 — Modelo de datos & Persistencia (Día 1)

Entregables:

SQLite + SQLModel con tablas: Message, FAQ, Product, Order, Doc.

Repositorios CRUD básicos.

Criterios: tests de creación/listado OK; DB autocrea tablas al iniciar.

Fase 3 — RAG ligero + NLU (Día 2)

Entregables:

Índice FAISS con embeddings (sentence-transformers mini).

Cargador de FAQs/menu/docs → embeddings → faiss_index/.

NLU con reglas + similitud (umbral configurable).

Criterios: endpoint /api/search?q= retorna top-k con score; intención básica (faq/menu/pedido/desconocido).

Fase 4 — Orquestador de respuestas & Flujos (Día 2)

Entregables:

Router: intención → (FAQ/RAG) o (flujo pedido) o fallback.

Motor de flujos declarativo vía YAML.

Criterios: conversación por /api/chat resuelve FAQs, muestra menú, corre quick_order y guarda en DB.

Fase 5 — Panel Admin (Día 3)

Entregables:

UI server-rendered (Jinja2 + HTMX) con páginas: Onboarding, Conocimiento, Menú, Flujos, Canales, Playground, Pedidos, Analítica básica, Ajustes.

Botón Re-indexar.

Criterios: desde el panel se suben CSV/Docs, se editan Q&A y se prueba el bot en vivo.

Fase 6 — Widget Web (Día 3)

Entregables:

widget.js + widget.html (iframe) insertable con <script>.

Mensajes rápidos (botones sugeridos).

Criterios: copiar 1 línea de script y chatear con el bot en cualquier sitio.

Fase 7 — Conectores (Día 4)

Entregables:

Webhooks para WhatsApp (Twilio / Cloud API) y Telegram.

Mapeo de formatos entrantes/salientes → Message común.

Criterios: envío/recepción real de mensajes con sandbox.

Fase 8 — Logging, Analítica & Export (Día 4)

Entregables:

structlog con JSON logs.

Analítica liviana (volumen, top FAQs, tasa de fallback).

Export CSV de pedidos/conversaciones.

Criterios: panel muestra métricas y permite exportar.

2. Tech stack

Backend: Python 3.11+, FastAPI, Uvicorn, SQLModel/SQLAlchemy, Pydantic, Jinja2, HTMX.

Embeddings/RAG: sentence-transformers (ej. all-MiniLM-L6-v2), FAISS.

LLM (opcional): OpenAI/Groq/Gemini (API) o Ollama local (ej. llama3.1).

DB: SQLite (archivo db.sqlite).

Front: server-rendered + HTMX; widget web vanilla JS.

Infra: .env, config.yaml, Docker Compose (opcional), structlog.

3. Estilo visual (UI/UX) – Guía breve

Objetivo: limpio, legible, cero fricción.

Colores (modo claro):

Fondo: #F8FAFC (gris azulado muy claro)

Primario: #2563EB (azul medio)

Secundario: #0EA5E9 (celeste)

Texto principal: #0F172A (gris muy oscuro)

Bordes/sutil: #E2E8F0

Éxito: #22C55E, Peligro: #EF4444, Advertencia: #F59E0B

Tipografía: Inter / System UI, 14–16px base, 24px títulos.

Layout:

Panel con sidebar izquierda (secciones) y contenido a la derecha.

Tarjetas con sombra suave, radios 12–16px, espacios 16–24px.

Componentes clave:

Tabla editable para FAQs/menú.

Uploader con arrastrar/soltar.

Playground con ventana de chat y lado derecho mostrando trazas (fuentes usadas, score, intención).

Widget de chat:

Burbuja flotante en esquina inferior derecha.

Historial, quick replies (chips), caja de texto con placeholder.

Marca del negocio (logo opcional) y horario.

4. Arquitectura & módulos

ai-customer-bot/
├─ app/
│  ├─ main.py                # FastAPI app, routers, Jinja2, HTMX
│  ├─ settings.py            # .env + config.yaml
│  ├─ deps.py                # dependencias comunes
│  ├─ routes/
│  │  ├─ ui.py               # vistas del panel admin
│  │  ├─ api.py              # /api/chat, /api/search, etc.
│  │  ├─ webhook_web.py      # Web chat
│  │  ├─ webhook_twilio.py   # WhatsApp Twilio
│  │  └─ webhook_telegram.py # Telegram
│  ├─ services/
│  │  ├─ nlu.py              # intención, reglas + similitud
│  │  ├─ rag.py              # loaders, embeddings, FAISS, retrieve
│  │  ├─ llm.py              # API LLM u Ollama
│  │  ├─ flows.py            # motor de flujos (FSM)
│  │  ├─ responder.py        # orquestador principal
│  │  └─ templates.py        # plantillas/tone de respuestas
│  ├─ db/
│  │  ├─ models.py           # SQLModel
│  │  └─ repo.py             # CRUDs
│  ├─ templates/             # Jinja2 (panel)
│  └─ static/                # css/js
├─ web_widget/
│  ├─ widget.js              # script embebible
│  └─ widget.html            # iframe
├─ data/
│  ├─ faqs.csv
│  ├─ menu.csv
│  └─ docs/                  # pdf/txt/md
├─ faiss_index/              # generado
├─ tests/
├─ config_example.yaml
├─ .env.example
├─ docker-compose.yml
├─ requirements.txt
└─ README.md

5. Configuración

.env.example (reemplazar al deploy)

# LLM (opcional)
OPENAI_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
OLLAMA_HOST=http://localhost:11434

# WhatsApp Twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+1XXXXXXXXXX

# WhatsApp Cloud API
WHATSAPP_TOKEN=
PHONE_NUMBER_ID=
VERIFY_TOKEN=

# Telegram
TELEGRAM_BOT_TOKEN=

config_example.yaml

business:
  name: "La Tiendita Don Chepe"
  timezone: "America/Managua"
  language: "es"
  address: "Barrio X, frente a..."
  hours:
    mon_fri: "8:00-18:00"
    sat: "9:00-14:00"
    sun: "cerrado"

ai:
  mode: "rag_only"   # rag_only | api_llm | local_llm
  model_name: "gpt-4o-mini"
  temperature: 0.2

retrieval:
  top_k: 4
  min_score: 0.5

responses:
  tone: "cercano"
  fallback: "Perdóname, no te entendí. ¿Me lo repetís?"
  escalate: "Te paso con alguien del equipo en un momento."
  quick_replies: ["Ver menú", "Ubicación", "Horarios", "Hacer pedido"]

orders:
  enable: true
  notify_email: "pedidos@latiendita.com"
  notify_whatsapp: "whatsapp:+505XXXXXXXX"

flows:
  quick_order:
    steps:
      - ask: "¿Tu nombre?"
        var: name
      - ask: "¿Qué producto querés?"
        var: product
      - ask: "¿Cantidad?"
        var: qty
      - confirm: "Perfecto, {qty} x {product} a nombre de {name}. ¿Confirmamos?"

6. Esquema de datos (SQLModel)

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    channel: str
    user_id: str
    text: str
    intent: Optional[str] = None
    source: Optional[str] = None  # faq/menu/rag/llm/fallback
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FAQ(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str
    answer: str
    tags: Optional[str] = None

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    desc: Optional[str] = None
    available: bool = True
    tags: Optional[str] = None

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str
    phone: Optional[str] = None
    items_json: str  # [{product_id, name, qty, price}]
    status: str = "new"  # new|confirmed|cancelled|fulfilled
    channel: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Doc(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    path: str
    meta: Optional[str] = None

7. Endpoints principales (contratos)

Salud:

GET /healthz → {status:"ok"}

Chat:

POST /api/chat

Request { "channel": "web|whatsapp|telegram", "user_id": "string", "text": "hola", "meta": {} }

Response { "reply": "…", "quick_replies": ["Ver menú", …], "trace": { "intent": "faq", "source": "rag", "hits": [{"doc":"faqs","score":0.82}] } }

Búsqueda (RAG debug):

GET /api/search?q=… → {hits:[{text, score, source}]}

Pedidos:

GET /api/orders (panel), POST /api/orders (flujo), PATCH /api/orders/{id} (estado).

Admin UI (Jinja2):

/admin (dashboard)

/admin/onboarding, /admin/knowledge, /admin/menu, /admin/flows, /admin/channels, /admin/playground, /admin/orders, /admin/analytics, /admin/settings

Webhooks:

POST /webhook/web (widget)

POST /webhook/twilio (WhatsApp)

POST /webhook/telegram

8. Orquestación (pipeline de mensajes)

Normalizar entrada → MessageIn.

Detección de intención: reglas (palabras clave) + similitud embeddings (umbral min_score).

Router:

faq/menu → RAG.retrieve() → plantillas responder.

order → flows.run("quick_order").

unknown → fallback (o escalar a humano).

Guardar Message y trace.

Responder (texto + quick replies).

Reglas ejemplo:

Si texto contiene alguna de [horario, abren, cierran] → intent=faq.

Si contiene [menu, precios, sabor, promoción] → intent=menu.

Si contiene [quiero, pedido, ordenar] → intent=order.

9. RAG (embeddings + FAISS)

Cargadores: CSV (faqs/menu), TXT/MD/PDF (docs). Limpiar texto, segmentar (300–500 tokens), generar embeddings, guardar en índice FAISS + metadatos (origen/ID).

Retrieve: top_k por coseno; filtrar por min_score.

Respuesta:

Si rag_only: formar respuesta usando plantillas y el texto de las fuentes.

Si api_llm/local_llm: prompt con instrucciones + contexto (fuentes top-k) y generar respuesta breve.

Re-indexar: botón