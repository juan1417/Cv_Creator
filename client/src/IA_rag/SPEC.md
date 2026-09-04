# Especificación Técnica: Sistema RAG para Cv_Creator

**Estado:** Borrador  
**Autor:** @sdd-spec  
**Fecha:** 2026-09-04  
**Versión:** 1.0

---

## 1. Resumen

El sistema RAG (Retrieval-Augmented Generation) de Cv_Creator permite a los usuarios conversar con un asistente que lee su CV desde la base de datos, lo adapta a puestos específicos y mantiene contexto entre mensajes. **No es un RAG vectorial** — no hay embeddings ni búsqueda semántica. Es un RAG basado en contexto estructurado: el LLM recibe el CV completo del usuario como contexto y genera adaptaciones basadas en la descripción del puesto.

---

## 2. Problemas del Estado Actual

| # | Problema | Impacto | Ubicación |
|---|----------|---------|-----------|
| 1 | `openrouter.py` ejecuta código al importar (`response = client.chat.completions.create(...)`) | Imposible reusar como módulo; crashea al importar | `IA_rag/openrouter.py:11-18` |
| 2 | CV tiene FK 1:1 a Experience/Skills/Education en lugar de 1:N | Un usuario solo puede tener 1 experiencia, 1 skill, 1 educación | `models/cv.py:14-16` |
| 3 | Sin FastAPI app ni main.py | No hay servidor ejecutable | — |
| 4 | Sin endpoints de chat ni historial | No hay forma de interactuar con el RAG | — |
| 5 | Modelo Chat es单条 (user_message + assistant_response) | No soporta conversaciones multi-turno | `models/chat.py` |

---

## 3. Arquitectura del RAG

### 3.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │ /api/chat     │    │ /api/cv      │                   │
│  │ (endpoints)   │    │ (endpoints)  │                   │
│  └──────┬───────┘    └──────────────┘                   │
│         │                                               │
│         ▼                                               │
│  ┌──────────────────────────────────────┐               │
│  │         RAG Orchestrator             │               │
│  │  (client/src/IA_rag/orchestrator.py) │               │
│  └──────┬───────────────┬──────────────┘               │
│         │               │                               │
│         ▼               ▼                               │
│  ┌─────────────┐  ┌──────────────────┐                  │
│  │  Retriever   │  │    Generator     │                  │
│  │ (retrieval)  │  │  (openrouter)    │                  │
│  └──────┬──────┘  └────────┬─────────┘                  │
│         │                  │                            │
│         ▼                  ▼                            │
│  ┌─────────────┐  ┌──────────────────┐                  │
│  │ PostgreSQL   │  │  OpenRouter API  │                  │
│  │ (Neon)       │  │  minimax-m3      │                  │
│  └─────────────┘  └──────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Componentes

| Componente | Archivo | Responsabilidad |
|------------|---------|-----------------|
| **Retriever** | `IA_rag/retriever.py` | Leer CV del usuario desde la BD, formatear como contexto |
| **Generator** | `IA_rag/openrouter.py` | Enviar prompts a OpenRouter y recibir respuestas |
| **Orchestrator** | `IA_rag/orchestrator.py` | Coordinar retrieval + generation, manejar historial |
| **Chat Model** | `models/chat.py` | Almacenar mensajes de conversación |
| **Endpoints** | `client/router/chat_routes.py` | API REST para interactuar con el RAG |

---

## 4. Modelo de Datos (Corregido)

### 4.1 Relaciones Cambiadas: 1:N → Tabla Pivote

**Problema:** `CV.experience`, `CV.skills`, `CV.education` son FK únicas (1:1).  
**Solución:** Eliminar esas FKs de CV y usar la relación existente `idUser` en cada modelo.

```
User (1) ──── (N) Experience    [idUser FK]
User (1) ──── (N) Skills        [idUser FK]
User (1) ──── (N) Education     [idUser FK]
User (1) ──── (N) CV            [idUser FK]
User (1) ──── (N) Chat          [idUser FK]
```

**Cambios en `models/cv.py`:**
- Eliminar: `experience: UUID = Field(foreign_key="experience.id")`
- Eliminar: `skills: UUID = Field(foreign_key="skills.id")`
- Eliminar: `education: UUID = Field(foreign_key="education.id")`
- Mantener: `idUser: UUID = Field(foreign_key="user.id")`

### 4.2 Modelo Chat Renombrado y Expandido

```python
# models/chat.py
class ChatMessage(Model, table=True):
    __tablename__ = "chat_message"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    role: str = Field(...)           # "user" | "assistant" | "system"
    content: str = Field(...)        # Texto del mensaje
    at_Created: datetime = Field(default_factory=datetime.utcnow)
    session_id: UUID = Field(...)    # ID de la sesión de conversación
    idUser: UUID = Field(foreign_key="user.id")
```

**Nueva tabla de sesión:**
```python
# models/chat.py
class ChatSession(Model, table=True):
    __tablename__ = "chat_session"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(default="Nueva conversación")  # Título automático
    target_job: Optional[str] = None                    # Puesto objetivo (si el usuario lo mencionó)
    at_Created: datetime = Field(default_factory=datetime.utcnow)
    at_Updated: datetime = Field(default_factory=datetime.utcnow)
    idUser: UUID = Field(foreign_key="user.id")
```

### 4.3 Diagrama ER Corregido

```
┌──────────┐     ┌────────────────┐     ┌──────────────┐
│   User   │────<│   CV           │     │              │
│          │     │  idUser FK     │     │              │
│  id (PK) │────<├────────────────┤     │              │
│          │     │ Experience     │     │              │
│          │     │  idUser FK     │     │              │
│          │────<├────────────────┤     │              │
│          │     │ Skills         │     │              │
│          │     │  idUser FK     │     │              │
│          │────<├────────────────┤     │              │
│          │     │ Education      │     │              │
│          │     │  idUser FK     │     │              │
│          │────<├────────────────┤     │              │
│          │     │ ChatSession    │     │              │
│          │     │  idUser FK     │     │              │
│          │────<├────────────────┤     │              │
│          │     │ ChatMessage    │     │              │
│          │     │  idUser FK     │     │              │
│          │     │  session_id FK │>────│ ChatSession  │
└──────────┘     └────────────────┘     └──────────────┘
```

---

## 5. System Prompt del Asistente

```python
SYSTEM_PROMPT = """Eres un asistente experto en creación y adaptación de currículums vitae.

## Tu Rol
- Ayudas a los usuarios a mejorar y adaptar sus CVs a puestos específicos
- Consultas el CV real del usuario desde la base de datos
- Generas versiones adaptadas del CV para cada puesto de interés
- Mantienes contexto de la conversación para recomendaciones progresivas

## Lo que tienes acceso
- El CV completo del usuario (nombre, email, teléfono, dirección, sobre mí, portafolio, LinkedIn)
- Todas las experiencias laborales del usuario
- Todas las habilidades del usuario
- Toda la formación académica del usuario
- El historial de mensajes de esta conversación

## Reglas
1. SIEMPRE consulta el CV del usuario antes de hacer recomendaciones
2. Cuando el usuario describa un puesto, adapta el CV enfatizando las habilidades y experiencias más relevantes
3. Responde en el mismo idioma que el usuario use
4. Sé específico: menciona secciones concretas del CV que deben cambiarse
5. Ofrece texto alternativo listo para copiar cuando sea posible
6. Si el usuario pregunta sobre algo que no está en su CV, indícalo claramente

## Formato de Respuesta
- Usa markdown para estructurar tus respuestas
- Cuando adaptes una sección, muestra el "antes" y el "después"
- Resalta en **negrita** los cambios importantes
"""
```

---

## 6. Módulo Retriever

**Archivo:** `client/src/IA_rag/retriever.py`

### 6.1 Funciones

```python
def get_user_cv(user_id: UUID, session: Session) -> dict | None:
    """
    Obtiene el CV del usuario junto con todas sus relaciones.
    
    Returns:
        {
            "cv": { name, email, phone, address, about, porfolio, linkedin },
            "experience": [{ title, company, start_date, end_date, description }, ...],
            "skills": [{ name, level }, ...],
            "education": [{ degree, institution, start_date, end_date, description }, ...]
        }
        None si el usuario no tiene CV.
    """

def format_cv_as_context(cv_data: dict) -> str:
    """
    Convierte el CV del usuario a texto estructurado para el system prompt.
    
    Returns:
        """
        # === DATOS PERSONALES ===
        Nombre: Juan Pérez
        Email: juan@email.com
        ...
        
        # === EXPERIENCIA LABORAL ===
        ## Desarrollador Senior | TechCorp | 2022-2024
        Descripción: ...
        
        # === HABILIDADES ===
        - Python (Avanzado)
        - React (Intermedio)
        
        # === FORMACIÓN ACADÉMICA ===
        ## Ingeniería en Sistemas | Universidad XYZ | 2018-2022
        """
```

### 6.2 Flujo de Retrieval

```
1. user_id llega desde el endpoint
2. Consultar CV WHERE idUser = user_id
3. Consultar Experience WHERE idUser = user_id (ORDER BY start_date DESC)
4. Consultar Skills WHERE idUser = user_id
5. Consultar Education WHERE idUser = user_id (ORDER BY start_date DESC)
6. Formatear todo como texto estructurado
7. Retornar string listo para inyectar en el prompt
```

---

## 7. Módulo Generator (OpenRouter)

**Archivo:** `client/src/IA_rag/openrouter.py`

### 7.1 Refactorización

**Antes (actual):**
```python
# Ejecuta al importar - PROBLEMA
response = client.chat.completions.create(...)
print(response.choices[0].message.content)
```

**Después (propuesto):**
```python
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

_client: OpenAI | None = None

def get_client() -> OpenAI:
    """Retorna instancia singleton del cliente OpenRouter."""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API"),
        )
    return _client

def generate_response(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """
    Envía mensajes a OpenRouter y retorna la respuesta.
    
    Args:
        messages: Lista de mensajes [{role, content}, ...]
        model: Modelo a usar (default: variable de entorno MODELO)
        temperature: Creatividad (0.0-1.0)
        max_tokens: Máximo de tokens en la respuesta
    
    Returns:
        Texto de la respuesta del asistente
    
    Raises:
        OpenRouterError: Si la API falla
    """
    client = get_client()
    response = client.chat.completions.create(
        model=model or os.getenv("MODELO"),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content
```

---

## 8. Módulo Orchestrator

**Archivo:** `client/src/IA_rag/orchestrator.py`

### 8.1 Función Principal

```python
def chat(
    user_id: UUID,
    user_message: str,
    session_id: UUID | None = None,
) -> dict:
    """
    Flujo completo: retrieval → construir prompt → generar → guardar.
    
    Returns:
        {
            "session_id": UUID,
            "response": str,
            "target_job": str | None
        }
    """
```

### 8.2 Flujo Interno

```
┌─────────────────────────────────────────────────────────┐
│  1. CREAR/OBTENER SESIÓN                                │
│     - Si session_id es None → crear nueva sesión        │
│     - Si session_id existe → cargar mensajes previos     │
│                                                          │
│  2. RETRIEVAL                                            │
│     - get_user_cv(user_id) → cv_context                  │
│     - Si no hay CV → error "Completa tu CV primero"     │
│                                                          │
│  3. CONSTRUIR PROMPT                                     │
│     - system: SYSTEM_PROMPT + "\n\n## CV del Usuario\n"  │
│              + cv_context                                │
│     - history: últimos 10 mensajes de la sesión          │
│     - user: user_message actual                          │
│                                                          │
│  4. GENERACIÓN                                           │
│     - generate_response(messages) → respuesta            │
│                                                          │
│  5. PERSISTENCIA                                         │
│     - Guardar mensaje del usuario (ChatMessage)          │
│     - Guardar respuesta del asistente (ChatMessage)      │
│     - Actualizar at_Updated de la sesión                 │
│     - Si es primer mensaje → extraer target_job          │
│                                                          │
│  6. RESPUESTA                                            │
│     - Retornar { session_id, response, target_job }      │
└─────────────────────────────────────────────────────────┘
```

### 8.3 Construcción del Prompt

```python
def _build_messages(
    cv_context: str,
    history: list[ChatMessage],
    user_message: str,
) -> list[dict]:
    """
    Construye la lista de mensajes para el LLM.
    
    Estructura:
    [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n## CV del Usuario\n" + cv_context},
        {"role": "user", "content": "Mensaje anterior 1"},
        {"role": "assistant", "content": "Respuesta anterior 1"},
        ...
        {"role": "user", "content": user_message}
    ]
    """
```

---

## 9. Endpoints de la API

**Archivo:** `client/src/client/router/chat_routes.py`

### 9.1 Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/chat/sessions` | Crear nueva sesión de conversación |
| `GET` | `/api/chat/sessions` | Listar sesiones del usuario |
| `GET` | `/api/chat/sessions/{session_id}` | Obtener mensajes de una sesión |
| `POST` | `/api/chat/sessions/{session_id}/messages` | Enviar mensaje y recibir respuesta |
| `DELETE` | `/api/chat/sessions/{session_id}` | Eliminar sesión |

### 9.2 Esquemas de Request/Response

```python
# --- Request: Crear sesión ---
class CreateSessionRequest(BaseModel):
    user_id: UUID
    target_job: str | None = None  # Puesto objetivo opcional

# --- Response: Sesión creada ---
class SessionResponse(BaseModel):
    session_id: UUID
    title: str
    target_job: str | None
    created_at: datetime

# --- Request: Enviar mensaje ---
class SendMessageRequest(BaseModel):
    user_id: UUID
    content: str

# --- Response: Respuesta del asistente ---
class ChatResponse(BaseModel):
    session_id: UUID
    response: str
    target_job: str | None

# --- Response: Lista de sesiones ---
class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
```

### 9.3 Implementación de Endpoints

```python
router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/sessions", response_model=SessionResponse)
async def create_session(req: CreateSessionRequest):
    """Crea una nueva sesión de conversación."""
    session = ChatSession(
        idUser=req.user_id,
        target_job=req.target_job,
    )
    # Guardar en BD y retornar

@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(session_id: UUID, req: SendMessageRequest):
    """
    Envía un mensaje y retorna la respuesta del asistente.
    Flujo completo: retrieval → prompt → generation → persist.
    """
    result = chat(
        user_id=req.user_id,
        user_message=req.content,
        session_id=session_id,
    )
    return ChatResponse(**result)

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(user_id: UUID):
    """Retorna todas las sesiones del usuario."""
    # SELECT * FROM chat_session WHERE idUser = user_id ORDER BY at_Updated DESC

@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: UUID, user_id: UUID):
    """Retorna los mensajes de una sesión específica."""
    # SELECT * FROM chat_message WHERE session_id = session_id AND idUser = user_id ORDER BY at_Created ASC
```

---

## 10. Flujo Completo: Usuario → RAG → Respuesta

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Frontend │────>│ FastAPI  │────>│Retriever │────>│    BD    │
│           │     │ Endpoint │     │          │     │ (Neon)   │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                       │                                  │
                       │<─────────── CV Context ──────────│
                       │
                       ▼
                 ┌──────────┐     ┌──────────────┐
                 │Orchestrator│───>│  OpenRouter   │
                 │           │<───│  (minimax-m3) │
                 └──────────┘     └──────────────┘
                       │
                       ▼
                 ┌──────────┐
                 │ Guardar  │
                 │ Mensajes │
                 └──────────┘
                       │
                       ▼
                 ┌──────────┐
                 │ Response │
                 │ al Front │
                 └──────────┘
```

### 10.1 Ejemplo de Conversación

```
Usuario: "Hola, quiero adaptar mi CV para un puesto de Frontend Developer en Google"

Sistema:
1. [RETRIEVE] Leer CV del usuario desde BD
   → name: "Juan Pérez", experience: [...], skills: [...]
2. [BUILD] Construir prompt:
   - System: SYSTEM_PROMPT + CV del usuario
   - User: "Quiero adaptar mi CV para un puesto de Frontend Developer en Google"
3. [GENERATE] LLM responde:
   "He revisado tu CV Juan. Para el puesto de Frontend Developer en Google, 
   te recomiendo los siguientes cambios:
   
   **Sección Habilidades:**
   - Mover React y JavaScript al inicio (Google valora mucho esto)
   - Agregar: Testing (Jest, Cypress), Performance Optimization
   
   **Sección Experiencia:**
   - Reescribir la descripción de tu último puesto enfatizando:
     - Métricas de rendimiento (Lighthouse scores, Core Web Vitals)
     - Impacto en usuarios (X usuarios impactados)
   
   **Sección Sobre Mí:**
   - Propuesta: 'Desarrollador Frontend especializado en React y 
     optimización de rendimiento, con experiencia en aplicaciones 
     de alta escala...'
   
   ¿Quieres que te genere el texto completo de alguna sección?"
4. [PERSIST] Guardar mensaje usuario + respuesta en ChatMessage
```

---

## 11. Manejo de Errores

### 11.1 Errores por Capa

| Capa | Error | Manejo |
|------|-------|--------|
| **Retriever** | Usuario no tiene CV | HTTP 404: "Completa tu CV primero para usar el asistente" |
| **Retriever** | Error de conexión a BD | HTTP 503: "Servicio de base de datos no disponible" |
| **Generator** | OpenRouter API falla | HTTP 502: "Servicio de IA no disponible, intenta más tarde" |
| **Generator** | Rate limit exceeded | HTTP 429: "Demasiadas solicitudes, espera un momento" |
| **Generator** | Token limit excedido | Truncar contexto del CV (mantener datos personales + ultimas 5 experiencias) |
| **Orchestrator** | Sesión no encontrada | HTTP 404: "Sesión no encontrada" |
| **Orchestrator** | Sesión pertenece a otro usuario | HTTP 403: "Acceso denegado" |
| **Endpoint** | Body inválido | HTTP 422: "Datos de entrada inválidos" |

### 11.2 Fallback Strategy

```python
def chat_with_fallback(user_id: UUID, message: str, session_id: UUID | None) -> dict:
    try:
        return chat(user_id, message, session_id)
    except DatabaseError:
        raise HTTPException(503, "Servicio de base de datos no disponible")
    except OpenRouterError as e:
        if "rate_limit" in str(e):
            raise HTTPException(429, "Demasiadas solicitudes, espera un momento")
        raise HTTPException(502, "Servicio de IA no disponible")
    except Exception as e:
        logger.exception(f"Error inesperado en RAG: {e}")
        raise HTTPException(500, "Error interno del servidor")
```

---

## 12. Estructura de Archivos Propuesta

```
client/src/
├── IA_rag/
│   ├── __init__.py
│   ├── openrouter.py          # Refactorizado: singleton + generate_response()
│   ├── retriever.py           # Nuevo: get_user_cv(), format_cv_as_context()
│   ├── orchestrator.py        # Nuevo: chat(), _build_messages()
│   ├── prompts.py             # Nuevo: SYSTEM_PROMPT
│   └── SPEC.md                # Este archivo
├── models/
│   ├── __init__.py
│   ├── user.py                # Sin cambios
│   ├── cv.py                  # Cambiado: eliminar FKs 1:1
│   ├── experience.py          # Sin cambios (ya tiene idUser)
│   ├── skill.py               # Sin cambios (ya tiene idUser)
│   ├── education.py           # Sin cambios (ya tiene idUser)
│   └── chat.py                # Cambiado: ChatMessage + ChatSession
├── client/router/
│   ├── routing.py             # Sin cambios
│   └── chat_routes.py         # Nuevo: endpoints de chat
└── database/
    ├── DB.py                  # Sin cambios
    └── get_user.py            # Sin cambios
```

---

## 13. Dependencias

```toml
# Agregar a pyproject.toml
[project]
dependencies = [
    # ... existentes ...
    "openai>=1.0.0",       # Cliente OpenRouter
    "sqlmodel>=0.0.14",    # Modelos de BD
    "fastapi>=0.104.0",    # Framework web
    "uvicorn>=0.24.0",     # Servidor ASGI
    "python-dotenv>=1.0.0" # Variables de entorno
]
```

---

## 14. Checklist de Implementación

- [ ] **Fase 1: Corregir modelos**
  - [ ] Eliminar FKs 1:1 de `cv.py` (experience, skills, education)
  - [ ] Renombrar tabla `chat` → `chat_message`
  - [ ] Agregar campos `role`, `session_id` a ChatMessage
  - [ ] Crear modelo ChatSession
  - [ ] Ejecutar migración en BD

- [ ] **Fase 2: Refactorizar OpenRouter**
  - [ ] Eliminar ejecución al importar
  - [ ] Implementar singleton `get_client()`
  - [ ] Implementar `generate_response()`

- [ ] **Fase 3: Crear Retriever**
  - [ ] Implementar `get_user_cv()`
  - [ ] Implementar `format_cv_as_context()`
  - [ ] Tests unitarios

- [ ] **Fase 4: Crear Orchestrator**
  - [ ] Implementar `chat()`
  - [ ] Implementar `_build_messages()`
  - [ ] Implementar `chat_with_fallback()`
  - [ ] Tests de integración

- [ ] **Fase 5: Crear Endpoints**
  - [ ] `POST /api/chat/sessions`
  - [ ] `GET /api/chat/sessions`
  - [ ] `GET /api/chat/sessions/{id}/messages`
  - [ ] `POST /api/chat/sessions/{id}/messages`
  - [ ] `DELETE /api/chat/sessions/{id}`
  - [ ] Crear `main.py` con FastAPI app
  - [ ] Tests de endpoints

- [ ] **Fase 6: Integración**
  - [ ] Conectar frontend al chat API
  - [ ] Probar flujo completo
  - [ ] Deploy

---

## 15. Decisiones de Diseño

| Decisión | Alternativa | Justificación |
|----------|-------------|---------------|
| RAG basado en contexto (no vectorial) | RAG vectorial con embeddings | El CV es estructurado y pequeño; no necesita búsqueda semántica. Leer todo es más simple y preciso. |
| ChatSession separado de ChatMessage | Mantener modelo actual (1 mensaje = 1 fila) | Permite conversaciones multi-turno y agrupar mensajes por sesión |
| singleton para OpenRouter client | Crear cliente por request | Evita overhead de reconexión; el cliente es thread-safe |
| Últimos 10 mensajes de historial | Todo el historial | Controla tokens; 10 mensajes dan suficiente contexto sin explotar el límite |
| Truncamiento del CV como fallback | Devolver error | Mejor UX: perder detalles menores es preferible a fallar completamente |
