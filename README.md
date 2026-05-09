# 🏦 BankSim Pro — Simulador Profesional con IA

> Plataforma de entrenamiento profesional bancario mediante simulación de casos reales, evaluación automática con IA y certificación por desempeño.

---

## 🗂 Estructura del Proyecto

```
banking-simulator/
├── backend/
│   ├── main.py                  # App FastAPI principal
│   ├── database.py              # SQLite + seed de datos
│   ├── requirements.txt
│   ├── models/
│   │   └── schemas.py           # Modelos Pydantic
│   ├── routers/
│   │   ├── missions.py          # GET /api/missions/
│   │   ├── submissions.py       # POST /api/submissions/
│   │   ├── users.py             # GET/POST /api/users/
│   │   └── certification.py    # GET /api/certification/
│   ├── services/
│   │   └── evaluator.py        # Motor de evaluación con IA
│   └── tests/
│       └── test_simulator.py   # Tests unitarios y de flujo
└── frontend/
    └── index.html              # SPA completa (HTML + CSS + JS)
```

---

## 🚀 Instalación y Ejecución

### 1. Requisitos previos

- Python 3.10 o superior
- pip

### 2. Instalar dependencias del backend

```bash
cd banking-simulator/backend
pip install -r requirements.txt
```

### 3. Configurar variables de entorno (opcional)

```bash
cp .env.example .env
# Edita .env y añade tu ANTHROPIC_API_KEY si tienes una
```

> **Sin API key:** el sistema usa evaluación heurística automáticamente.  
> **Con API key:** el sistema usa Claude Sonnet para evaluación de alta calidad.

### 4. Iniciar el servidor

```bash
cd banking-simulator/backend
uvicorn main:app --reload --port 8000
```

El servidor estará disponible en: `http://localhost:8000`

### 5. Abrir el frontend

Simplemente abre en tu navegador:

```
banking-simulator/frontend/index.html
```

O con un servidor estático:
```bash
cd banking-simulator/frontend
python -m http.server 3000
# Abre: http://localhost:3000
```

---

## 📡 API Reference

### Misiones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/missions/` | Lista todas las misiones |
| GET | `/api/missions/{id}` | Detalle de una misión |

### Envío de Respuestas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/submissions/` | Enviar respuesta y recibir evaluación |
| GET | `/api/submissions/history/{user_id}` | Historial de entregas |

### Usuarios y Progreso

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/users/` | Crear usuario |
| GET | `/api/users/{id}` | Datos del usuario |
| GET | `/api/users/{id}/progress` | Progreso completo |

### Certificación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/certification/{user_id}` | Estado de certificación |

---

## 📬 Ejemplos de uso (curl)

### Listar misiones
```bash
curl http://localhost:8000/api/missions/
```

### Enviar respuesta a una misión
```bash
curl -X POST http://localhost:8000/api/submissions/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "mission_id": 1,
    "response": "El resumen financiero del trimestre muestra ingresos por comisiones de $45,200 con gastos operativos de $32,100, generando un margen positivo. La alerta crítica es la morosidad del 3.2%, que supera el umbral estándar. Recomiendo implementar un programa de recuperación temprana de cartera y revisar los criterios de otorgamiento."
  }'
```

### Ver progreso del usuario
```bash
curl http://localhost:8000/api/users/1/progress
```

### Verificar certificación
```bash
curl http://localhost:8000/api/certification/1
```

### Crear nuevo usuario
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "maria.perez", "name": "María Pérez", "email": "m.perez@banco.com"}'
```

---

## 🧪 Ejecutar Tests

```bash
cd banking-simulator/backend
pytest tests/test_simulator.py -v
```

Tests incluidos:
- ✅ Evaluación heurística (corta, buena, excelente)
- ✅ Endpoints de misiones (listar, detalle, not found)
- ✅ Gestión de usuarios (crear, duplicado, progreso)
- ✅ Envío de respuestas (validación, retry, usuario inválido)
- ✅ Historial de entregas
- ✅ Flujo completo: 5 misiones → certificación

---

## 🧠 Motor de Evaluación

El sistema evalúa respuestas en dos modos:

### Modo IA (con `ANTHROPIC_API_KEY`)
- Usa **Claude Sonnet** para análisis semántico profundo
- Evalúa: precisión técnica, claridad, estructura, aplicabilidad
- Devuelve: score, feedback, fortalezas, áreas de mejora

### Modo Heurístico (sin API key)
- Análisis basado en longitud, estructura, terminología bancaria y accionabilidad
- Puntaje calculado en 4 dimensiones (100 puntos total)
- Funcional sin dependencias externas

---

## 🏆 Certificación

**Requisitos para obtener la certificación:**
- Completar **5 misiones** con score ≥ 70 en cada una
- Score promedio ≥ **70 puntos**

---

## 🎮 Misiones Disponibles

| # | Título | Nivel |
|---|--------|-------|
| 1 | Resumen Financiero Ejecutivo | Básico |
| 2 | Identificación de Riesgos en Cartera | Intermedio |
| 3 | Recomendaciones de Producto al Cliente | Intermedio |
| 4 | Optimización del Proceso de Apertura | Avanzado |
| 5 | Diseño de Automatización con IA | Avanzado |

---

## 🔧 Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | API key de Anthropic para evaluación IA | `""` (usa heurística) |
| `DB_PATH` | Ruta del archivo SQLite | `simulator.db` |

---

## 📚 Documentación interactiva de la API

Con el servidor corriendo, accede a:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc


prueba de ejecucion de pipeline 1
