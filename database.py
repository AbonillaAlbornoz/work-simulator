import sqlite3
import os
import json

DB_PATH = os.getenv("DB_PATH", "simulator.db")

# ── Banking missions (profession='banking', ids 1-5) ─────────────────────────
BANKING_MISSIONS = [
    {
        "id": 1, "profession": "banking", "order": 1,
        "title": "Resumen Financiero Ejecutivo",
        "narrative": (
            "Eres analista junior en la sucursal Norte del banco. Tu gerente, antes de entrar "
            "a una junta con la dirección regional, te pide en 10 minutos un resumen ejecutivo "
            "con los datos del trimestre. Lo que escribas irá directo a la presentación."
        ),
        "description": (
            "Datos del trimestre: ingresos por comisiones $45,200 · gastos operativos $32,100 · "
            "morosidad 3.2% · nuevas cuentas abiertas: 87 · cuentas cerradas: 23 · NPS: 68."
        ),
        "objective": (
            "Redactar un resumen financiero ejecutivo que destaque los puntos críticos, "
            "identifique la principal alerta de riesgo y proponga una acción concreta."
        ),
        "expected_structure": (
            "1. Resumen de resultados (cifras clave en 2-3 oraciones)\n"
            "2. Alerta de riesgo identificada (cuál es y por qué es crítica)\n"
            "3. Recomendación accionable para el próximo trimestre"
        ),
        "level": "Básico",
        "criteria": "precisión de datos, identificación de riesgo, claridad ejecutiva, propuesta accionable",
        "max_score": 100,
    },
    {
        "id": 2, "profession": "banking", "order": 2,
        "title": "Identificación de Riesgos en Cartera",
        "narrative": (
            "El área de riesgo acaba de recibir la auditoría trimestral. El director te llama: "
            "'Necesito saber exactamente dónde estamos expuestos antes de que lleguen los auditores mañana.'"
        ),
        "description": (
            "Cartera de créditos personales: 30% con score < 600 · tasa de impago subió de 1.8% a 4.1% · "
            "concentración en construcción: 38% · 15% de créditos con garantías vencidas."
        ),
        "objective": (
            "Identificar los 3 riesgos más críticos, clasificarlos por severidad "
            "y proponer una medida de mitigación concreta para cada uno."
        ),
        "expected_structure": (
            "1. Riesgo #1: [nombre] · Severidad: Alta/Media/Baja · Mitigación\n"
            "2. Riesgo #2: [nombre] · Severidad: Alta/Media/Baja · Mitigación\n"
            "3. Riesgo #3: [nombre] · Severidad: Alta/Media/Baja · Mitigación"
        ),
        "level": "Intermedio",
        "criteria": "identificación de riesgos, clasificación por severidad, medidas de mitigación viables",
        "max_score": 100,
    },
    {
        "id": 3, "profession": "banking", "order": 3,
        "title": "Recomendaciones de Producto al Cliente",
        "narrative": (
            "Cliente VIP en sala de espera. Carlos Méndez, empresario, lleva 8 años con el banco "
            "y recibió un bono de $50,000. El asesor titular está de vacaciones y tú lo atenderás."
        ),
        "description": (
            "Perfil: empresario, 45 años, ingresos $12,000/mes, hipoteca al 60%, sin inversiones activas, "
            "viajero frecuente, 2 hijos en universidad. Bono disponible: $50,000."
        ),
        "objective": (
            "Diseñar 3 recomendaciones priorizadas de productos bancarios con justificación "
            "y beneficios concretos para este perfil específico."
        ),
        "expected_structure": (
            "1. Recomendación principal: [producto] · Por qué le conviene · Beneficio concreto\n"
            "2. Recomendación secundaria: [producto] · Por qué le conviene · Beneficio concreto\n"
            "3. Recomendación complementaria: [producto] · Por qué le conviene · Beneficio concreto"
        ),
        "level": "Intermedio",
        "criteria": "adecuación al perfil, justificación técnica, beneficios concretos, orden lógico",
        "max_score": 100,
    },
    {
        "id": 4, "profession": "banking", "order": 4,
        "title": "Optimización del Proceso de Apertura de Cuentas",
        "narrative": (
            "El banco perdió 3 clientes esta semana. El proceso tarda 47 minutos. "
            "El gerente te convoca: 'Quiero un plan antes de las 5pm. Debemos bajar a 20 minutos.'"
        ),
        "description": (
            "Proceso actual: 47 min total · validación de documentos: 18 min · captura: 12 min · "
            "aprobación supervisor: 10 min · entrega kit: 7 min. Problemas: 23% rechazos, "
            "supervisores disponibles 70% del tiempo, 8% errores de captura."
        ),
        "objective": (
            "Proponer un plan que reduzca el proceso a menos de 20 minutos indicando qué "
            "eliminar, automatizar o rediseñar, con métricas de éxito medibles."
        ),
        "expected_structure": (
            "1. Diagnóstico: cuello de botella principal\n"
            "2. Propuestas de mejora por etapa (eliminar/automatizar/rediseñar)\n"
            "3. Tiempo proyectado por etapa\n"
            "4. Métricas de éxito"
        ),
        "level": "Avanzado",
        "criteria": "análisis del cuello de botella, propuestas concretas, viabilidad, métricas claras",
        "max_score": 100,
    },
    {
        "id": 5, "profession": "banking", "order": 5,
        "title": "Diseño de Automatización con IA",
        "narrative": (
            "850 llamadas diarias, agentes agotados, tasa de éxito del 38%. El director de tecnología "
            "te pide la propuesta de IA para el comité ejecutivo del lunes."
        ),
        "description": (
            "Operación: 850 llamadas/día · 65% casos simples · costo por llamada: $4.20 · "
            "tasa de éxito: 38% · costo mensual estimado: $107,100."
        ),
        "objective": (
            "Diseñar una propuesta de automatización con IA: qué automatizar, qué tecnología, "
            "cómo medir el ROI y cómo gestionar los riesgos."
        ),
        "expected_structure": (
            "1. Alcance: qué se automatiza y qué queda con humanos\n"
            "2. Tecnología propuesta y justificación\n"
            "3. ROI esperado y métricas de éxito\n"
            "4. Riesgos y plan de mitigación"
        ),
        "level": "Avanzado",
        "criteria": "selección de casos, justificación técnica de IA, métricas de ROI, gestión de riesgos",
        "max_score": 100,
    },
]

# ── Legal missions (profession='legal', ids 11-15) ────────────────────────────
LEGAL_MISSIONS = [
    {
        "id": 11, "profession": "legal", "order": 1,
        "title": "Análisis de Contrato de Arrendamiento",
        "narrative": (
            "Eres abogado junior en un despacho. Tu socio te envía un contrato de arrendamiento "
            "comercial firmado hace 3 años. El cliente quiere saber si está protegido antes de "
            "renovar. Tienes 30 minutos para el análisis previo a la reunión."
        ),
        "description": (
            "Contrato de arrendamiento comercial con las siguientes cláusulas: renta mensual $8,500 "
            "con incremento anual del 8% · plazo 5 años sin opción de prórroga automática · "
            "arrendatario responde por daños estructurales · cláusula penal del 3 meses de renta "
            "por terminación anticipada · sin cláusula de caso fortuito o fuerza mayor · "
            "jurisdicción exclusiva en ciudad del arrendador."
        ),
        "objective": (
            "Identificar las cláusulas de mayor riesgo para el arrendatario, clasificarlas "
            "por nivel de riesgo y proponer una negociación para cada una."
        ),
        "expected_structure": (
            "1. Cláusula de riesgo #1: [nombre] · Riesgo: Alto/Medio/Bajo · Propuesta de negociación\n"
            "2. Cláusula de riesgo #2: [nombre] · Riesgo: Alto/Medio/Bajo · Propuesta de negociación\n"
            "3. Cláusula de riesgo #3: [nombre] · Riesgo: Alto/Medio/Bajo · Propuesta de negociación\n"
            "4. Recomendación general al cliente"
        ),
        "level": "Básico",
        "criteria": "precisión jurídica, identificación de riesgos contractuales, propuestas de negociación viables, claridad al cliente",
        "max_score": 100,
    },
    {
        "id": 12, "profession": "legal", "order": 2,
        "title": "Redacción de Cláusula de Confidencialidad",
        "narrative": (
            "Una startup tecnológica contrata tu despacho para una fusión. El socio te pide "
            "redactar una cláusula NDA robusta antes de la reunión de due diligence mañana. "
            "'Que sea sólida pero no ahuyente al comprador', te dice."
        ),
        "description": (
            "Contexto: empresa de software con valuación de $2M en proceso de adquisición. "
            "Información sensible a proteger: código fuente, base de clientes (340 empresas), "
            "contratos con 5 proveedores clave, proyecciones financieras a 3 años, "
            "tecnología patentada pendiente de registro. Partes: empresa vendedora (México) "
            "y comprador potencial (EEUU). Duración deseada: protección post-negociación."
        ),
        "objective": (
            "Redactar una cláusula de confidencialidad completa que proteja los activos "
            "de la empresa sin ser excesivamente restrictiva para el proceso de negociación."
        ),
        "expected_structure": (
            "1. Definición de información confidencial (qué queda incluido y excluido)\n"
            "2. Obligaciones de las partes (qué pueden y no pueden hacer con la información)\n"
            "3. Plazo de vigencia y condiciones de terminación\n"
            "4. Consecuencias del incumplimiento (penalidades y remedios)"
        ),
        "level": "Intermedio",
        "criteria": "precisión jurídica, completitud de la cláusula, equilibrio entre protección y viabilidad, lenguaje técnico apropiado",
        "max_score": 100,
    },
    {
        "id": 13, "profession": "legal", "order": 3,
        "title": "Resumen Jurídico Ejecutivo",
        "narrative": (
            "El CEO de tu cliente corporativo tiene reunión con inversionistas en 2 horas. "
            "Te llama: 'Necesito que me expliques en términos simples qué significa esta "
            "resolución judicial y qué riesgo tenemos. Sin jerga legal, que lo entiendan todos.'"
        ),
        "description": (
            "Resolución judicial en proceso laboral colectivo: el tribunal determinó que la empresa "
            "incurrió en prácticas de contratación irregular (outsourcing no permitido) durante "
            "2019-2022 afectando a 47 trabajadores. Se ordena: reinstalación de 12 trabajadores "
            "o pago de liquidación equivalente a $340,000 total · pago de salarios caídos "
            "desde la fecha de despido · multa administrativa de $45,000 · recurso de apelación "
            "disponible con plazo de 15 días hábiles · riesgo de demanda colectiva adicional "
            "de los 35 trabajadores restantes estimado en $850,000."
        ),
        "objective": (
            "Redactar un resumen ejecutivo claro, sin jerga legal, que explique la situación, "
            "los montos en riesgo, las opciones disponibles y la recomendación estratégica."
        ),
        "expected_structure": (
            "1. Qué pasó (en lenguaje claro, máximo 3 oraciones)\n"
            "2. Qué significa para la empresa (impacto económico total)\n"
            "3. Opciones disponibles con pros y contras de cada una\n"
            "4. Recomendación del despacho con justificación"
        ),
        "level": "Intermedio",
        "criteria": "claridad para no abogados, precisión de los hechos, análisis completo de opciones, recomendación fundamentada",
        "max_score": 100,
    },
    {
        "id": 14, "profession": "legal", "order": 4,
        "title": "Evaluación de Riesgos en Contrato Comercial",
        "narrative": (
            "Tu cliente está a punto de firmar un contrato de distribución exclusiva con una "
            "empresa extranjera. Es su mayor acuerdo hasta la fecha. Te pide: "
            "'Dime si debo firmar esto o no, y por qué.' Tienes una hora."
        ),
        "description": (
            "Contrato de distribución exclusiva internacional: exclusividad en territorio nacional "
            "por 10 años irrevocables · mínimo de compra mensual de $50,000 o penalidad del 20% · "
            "proveedor puede terminar el contrato con 30 días de aviso por 'incumplimiento a su "
            "discreción' · todos los conflictos se resuelven en arbitraje en Ginebra bajo reglas ICC · "
            "ley aplicable: Suiza · cláusula de no competencia por 3 años post-terminación en "
            "todo Latinoamérica · el distribuidor asume todos los costos de marketing y certificaciones."
        ),
        "objective": (
            "Realizar una evaluación completa de riesgos del contrato, clasificarlos por "
            "nivel de exposición y emitir una recomendación clara sobre si firmar o negociar."
        ),
        "expected_structure": (
            "1. Semáforo de riesgos: lista de cláusulas problemáticas con nivel (Rojo/Amarillo/Verde)\n"
            "2. Top 3 riesgos críticos con análisis de impacto\n"
            "3. Propuestas de modificación para cada riesgo crítico\n"
            "4. Recomendación final: firmar / negociar primero / no firmar — con justificación"
        ),
        "level": "Avanzado",
        "criteria": "completitud del análisis, identificación de riesgos ocultos, propuestas viables, claridad de la recomendación",
        "max_score": 100,
    },
    {
        "id": 15, "profession": "legal", "order": 5,
        "title": "Respuesta Profesional a Cliente en Crisis",
        "narrative": (
            "Son las 8pm del viernes. Un cliente importante te escribe en pánico: acaba de recibir "
            "una carta de requerimiento de $1.2M de un ex-socio alegando apropiación indebida. "
            "El lunes hay reunión de consejo. Necesita tu respuesta esta noche."
        ),
        "description": (
            "Situación: carta de requerimiento por $1.2M alegando que tu cliente se apropió de "
            "oportunidad de negocio del ex-socio (contrato con empresa gobierno por $3M). "
            "Hechos disponibles: el ex-socio salió de la empresa hace 8 meses por acuerdo mutuo · "
            "el contrato con gobierno se firmó 6 meses después de su salida · existe acuerdo de "
            "separación firmado con cláusula de finiquito · el ex-socio no tenía rol activo en "
            "las negociaciones con el gobierno según registros internos · plazo para responder: "
            "10 días hábiles según la carta."
        ),
        "objective": (
            "Redactar una respuesta profesional al cliente que: calme la situación con base en los "
            "hechos, explique la posición legal, defina los pasos inmediatos y genere confianza."
        ),
        "expected_structure": (
            "1. Evaluación inicial de la situación (fortalezas y debilidades de tu posición)\n"
            "2. Análisis de la carta de requerimiento (validez, fundamentos, riesgos)\n"
            "3. Plan de acción inmediato (próximas 72 horas)\n"
            "4. Respuesta recomendada al ex-socio (estrategia de negociación o defensa)"
        ),
        "level": "Avanzado",
        "criteria": "manejo de crisis, precisión jurídica, comunicación clara con cliente, estrategia legal sólida",
        "max_score": 100,
    },
]

ALL_MISSIONS = BANKING_MISSIONS + LEGAL_MISSIONS


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
            profession TEXT NOT NULL DEFAULT 'banking',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN profession TEXT NOT NULL DEFAULT 'banking'")
    except Exception:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS missions (
            id INTEGER PRIMARY KEY,
            profession TEXT NOT NULL DEFAULT 'banking',
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
    for col, default in [
        ("profession", "'banking'"), ("narrative", "''"),
        ("objective", "''"), ("expected_structure", "''"), ('"order"', "0"),
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

    # Upsert all missions
    for m in ALL_MISSIONS:
        cursor.execute("""
            INSERT INTO missions (id, profession, title, narrative, description, objective,
                                  expected_structure, level, criteria, max_score, "order")
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                profession=excluded.profession, title=excluded.title,
                narrative=excluded.narrative, description=excluded.description,
                objective=excluded.objective, expected_structure=excluded.expected_structure,
                level=excluded.level, criteria=excluded.criteria,
                max_score=excluded.max_score, "order"=excluded."order"
        """, (
            m["id"], m["profession"], m["title"], m["narrative"], m["description"],
            m["objective"], m["expected_structure"], m["level"], m["criteria"],
            m["max_score"], m["order"]
        ))

    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, name, email, profession)
        VALUES (1, 'demo', 'Profesional Demo', 'demo@worksim.ai', 'banking')
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada — banking + legal missions ready")
