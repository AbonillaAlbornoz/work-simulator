import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "simulator.db")

MISSIONS_DATA = [
    {
        "id": 1,
        "title": "Resumen Financiero Ejecutivo",
        "narrative": (
            "Eres analista junior en la sucursal Norte del banco. "
            "Tu gerente, antes de entrar a una junta con la dirección regional, "
            "te pide en 10 minutos un resumen ejecutivo con los datos del trimestre. "
            "No hay tiempo para errores: lo que escribas irá directo a la presentación."
        ),
        "description": (
            "Datos del trimestre: ingresos por comisiones $45,200 · gastos operativos $32,100 · "
            "morosidad 3.2% · nuevas cuentas abiertas: 87 · cuentas cerradas: 23 · NPS del cliente: 68."
        ),
        "objective": (
            "Redactar un resumen financiero ejecutivo que destaque los puntos críticos del trimestre, "
            "identifique la principal alerta de riesgo y proponga una acción concreta para el siguiente período."
        ),
        "expected_structure": (
            "1. Resumen de resultados (cifras clave en 2-3 oraciones)\n"
            "2. Alerta de riesgo identificada (cuál es y por qué es crítica)\n"
            "3. Recomendación accionable para el próximo trimestre"
        ),
        "level": "Básico",
        "criteria": "precisión de datos, identificación de riesgo, claridad ejecutiva, propuesta accionable",
        "max_score": 100,
        "order": 1,
    },
    {
        "id": 2,
        "title": "Identificación de Riesgos en Cartera",
        "narrative": (
            "El área de riesgo acaba de recibir la auditoría trimestral de la cartera de créditos. "
            "El director de riesgo te llama a su oficina: 'Necesito que me digas exactamente dónde estamos "
            "expuestos antes de que lleguen los auditores externos mañana.' "
            "Tienes los datos. Es el momento de demostrar tu criterio analítico."
        ),
        "description": (
            "Cartera de créditos personales: 30% de clientes con score crediticio < 600 · "
            "tasa de impago subió de 1.8% a 4.1% en 6 meses · concentración en sector construcción: 38% · "
            "15% de créditos con garantías vencidas."
        ),
        "objective": (
            "Identificar los 3 riesgos más críticos de la cartera, clasificarlos por severidad "
            "y proponer una medida de mitigación concreta para cada uno."
        ),
        "expected_structure": (
            "1. Riesgo #1: [nombre] · Severidad: Alta/Media/Baja · Mitigación propuesta\n"
            "2. Riesgo #2: [nombre] · Severidad: Alta/Media/Baja · Mitigación propuesta\n"
            "3. Riesgo #3: [nombre] · Severidad: Alta/Media/Baja · Mitigación propuesta"
        ),
        "level": "Intermedio",
        "criteria": "identificación correcta de riesgos, clasificación adecuada, medidas de mitigación viables",
        "max_score": 100,
        "order": 2,
    },
    {
        "id": 3,
        "title": "Recomendaciones de Producto al Cliente",
        "narrative": (
            "Cliente VIP en sala de espera. Carlos Méndez, empresario, lleva 8 años con el banco "
            "y acaba de recibir un bono de $50,000. El asesor titular está de vacaciones y tú lo vas a atender. "
            "Esta es tu oportunidad de mostrar que conoces los productos y que piensas en el cliente, no en la comisión."
        ),
        "description": (
            "Perfil del cliente: empresario · 45 años · ingresos $12,000/mes · cuenta corriente activa · "
            "hipoteca al 60% de pago · sin inversiones activas · viajero frecuente al exterior · "
            "2 hijos en universidad. Bono disponible: $50,000."
        ),
        "objective": (
            "Diseñar 3 recomendaciones de productos o servicios bancarios, priorizadas por relevancia "
            "para este cliente específico, con justificación y beneficios concretos para cada una."
        ),
        "expected_structure": (
            "1. Recomendación principal: [producto] · Por qué le conviene · Beneficio concreto\n"
            "2. Recomendación secundaria: [producto] · Por qué le conviene · Beneficio concreto\n"
            "3. Recomendación complementaria: [producto] · Por qué le conviene · Beneficio concreto"
        ),
        "level": "Intermedio",
        "criteria": "adecuación al perfil, justificación técnica, beneficios concretos, orden lógico",
        "max_score": 100,
        "order": 3,
    },
    {
        "id": 4,
        "title": "Optimización del Proceso de Apertura de Cuentas",
        "narrative": (
            "El banco perdió 3 clientes esta semana porque el proceso de apertura de cuenta tardó casi una hora. "
            "El gerente de operaciones te convoca: 'Quiero un plan en mi escritorio antes de las 5pm. "
            "Necesitamos bajar ese tiempo a menos de 20 minutos o vamos a seguir perdiendo clientes frente a los neobancos.'"
        ),
        "description": (
            "Proceso actual: duración promedio 47 min · validación de documentos: 18 min · "
            "captura de datos: 12 min · aprobación del supervisor: 10 min · entrega de kit: 7 min. "
            "Problemas: 23% de rechazos por documentación incompleta · supervisores disponibles solo 70% del tiempo · "
            "errores de captura en 8% de casos."
        ),
        "objective": (
            "Proponer un plan de optimización que reduzca el proceso a menos de 20 minutos, "
            "indicando qué pasos eliminar, automatizar o rediseñar, con métricas de éxito medibles."
        ),
        "expected_structure": (
            "1. Diagnóstico: cuello de botella principal identificado\n"
            "2. Propuestas de mejora: qué cambiar en cada etapa (eliminar / automatizar / rediseñar)\n"
            "3. Tiempo proyectado por etapa tras la mejora\n"
            "4. Métricas de éxito para medir el impacto"
        ),
        "level": "Avanzado",
        "criteria": "análisis del cuello de botella, propuestas concretas, viabilidad, métricas claras",
        "max_score": 100,
        "order": 4,
    },
    {
        "id": 5,
        "title": "Diseño de Automatización con IA",
        "narrative": (
            "El área de cobranza está colapsada. 850 llamadas diarias, agentes agotados y una tasa de éxito "
            "del 38% que no mejora. El director de tecnología te pide que lideres la propuesta de IA "
            "para el comité ejecutivo del próximo lunes. 'Necesito saber qué automatizamos, con qué, "
            "cuánto nos ahorra y qué puede salir mal.'"
        ),
        "description": (
            "Operación actual: 850 llamadas diarias · 65% casos simples (recordatorio de pago, acuerdo de plazo) · "
            "costo por llamada: $4.20 · tasa de éxito: 38% · costo mensual estimado: $107,100."
        ),
        "objective": (
            "Diseñar una propuesta de automatización con IA para el área de cobranza: "
            "qué automatizar, qué tecnología usar, cómo medir el ROI y cómo gestionar los riesgos del proyecto."
        ),
        "expected_structure": (
            "1. Alcance: qué casos se automatizan y cuáles quedan con humanos (con criterios)\n"
            "2. Tecnología propuesta: tipo de IA · justificación de la elección\n"
            "3. ROI esperado: ahorro proyectado · métricas de éxito\n"
            "4. Riesgos del proyecto y plan de mitigación"
        ),
        "level": "Avanzado",
        "criteria": "selección de casos apropiados, justificación técnica de IA, métricas de ROI, gestión de riesgos",
        "max_score": 100,
        "order": 5,
    },
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS missions (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            narrative TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL,
            objective TEXT NOT NULL DEFAULT '',
            expected_structure TEXT NOT NULL DEFAULT '',
            level TEXT NOT NULL,
            criteria TEXT NOT NULL,
            max_score INTEGER DEFAULT 100,
            "order" INTEGER DEFAULT 0
        )
    """)

    # Safe migration: add new columns if they don't exist
    for col, default in [
        ("narrative", "''"),
        ("objective", "''"),
        ("expected_structure", "''"),
        ('"order"', "0"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE missions ADD COLUMN {col} TEXT NOT NULL DEFAULT {default}")
        except Exception:
            pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mission_id INTEGER NOT NULL,
            response TEXT NOT NULL,
            score INTEGER NOT NULL,
            feedback TEXT NOT NULL,
            action_plan TEXT NOT NULL DEFAULT '[]',
            attempt INTEGER DEFAULT 1,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (mission_id) REFERENCES missions(id)
        )
    """)

    try:
        cursor.execute("ALTER TABLE results ADD COLUMN action_plan TEXT NOT NULL DEFAULT '[]'")
    except Exception:
        pass

    # Upsert missions
    for m in MISSIONS_DATA:
        cursor.execute("""
            INSERT INTO missions (id, title, narrative, description, objective, expected_structure,
                                  level, criteria, max_score, "order")
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                narrative=excluded.narrative,
                description=excluded.description,
                objective=excluded.objective,
                expected_structure=excluded.expected_structure,
                level=excluded.level,
                criteria=excluded.criteria,
                max_score=excluded.max_score,
                "order"=excluded."order"
        """, (
            m["id"], m["title"], m["narrative"], m["description"],
            m["objective"], m["expected_structure"],
            m["level"], m["criteria"], m["max_score"], m["order"]
        ))

    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, name, email)
        VALUES (1, 'demo', 'Analista Demo', 'demo@banco.com')
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")
