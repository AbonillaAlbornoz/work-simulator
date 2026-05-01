import sqlite3
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "simulator.db")

MISSIONS_DATA = [
    {
        "id": 1,
        "title": "Resumen Financiero Ejecutivo",
        "description": (
            "El gerente de una sucursal te entrega los siguientes datos del trimestre: "
            "ingresos por comisiones $45,200, gastos operativos $32,100, morosidad 3.2%, "
            "nuevas cuentas abiertas: 87, cuentas cerradas: 23, NPS del cliente: 68. "
            "Tu misión: redactar un resumen financiero ejecutivo de máximo 200 palabras "
            "que destaque los puntos críticos, identifique una alerta de riesgo y proponga "
            "una acción concreta para el siguiente trimestre."
        ),
        "level": "Básico",
        "criteria": "precisión de datos, identificación de riesgo, claridad ejecutiva, propuesta accionable",
        "max_score": 100,
    },
    {
        "id": 2,
        "title": "Identificación de Riesgos en Cartera",
        "description": (
            "Eres analista de riesgo. La cartera de créditos personales muestra: "
            "30% de clientes con score crediticio < 600, tasa de impago últimos 6 meses subió "
            "de 1.8% a 4.1%, concentración en sector construcción (38% de la cartera), "
            "y 15% de créditos con garantías vencidas. "
            "Tu misión: identificar los 3 riesgos más críticos, clasificarlos por severidad "
            "(alto/medio/bajo) y proponer una medida de mitigación para cada uno."
        ),
        "level": "Intermedio",
        "criteria": "identificación correcta de riesgos, clasificación adecuada, medidas de mitigación viables",
        "max_score": 100,
    },
    {
        "id": 3,
        "title": "Recomendaciones de Producto al Cliente",
        "description": (
            "Un cliente premium lleva 8 años en el banco. Perfil: empresario, 45 años, "
            "ingresos mensuales $12,000, tiene cuenta corriente, hipoteca pagada al 60%, "
            "sin inversiones activas, viaja frecuentemente al exterior, tiene 2 hijos en universidad. "
            "Acaba de recibir un bono de $50,000 y quiere 'hacer algo inteligente con ese dinero'. "
            "Tu misión: diseñar 3 recomendaciones de productos/servicios bancarios priorizadas, "
            "con justificación para cada una y los beneficios concretos para este cliente."
        ),
        "level": "Intermedio",
        "criteria": "adecuación al perfil, justificación técnica, beneficios concretos, orden lógico",
        "max_score": 100,
    },
    {
        "id": 4,
        "title": "Optimización del Proceso de Apertura de Cuentas",
        "description": (
            "El proceso actual de apertura de cuenta tarda 47 minutos promedio. "
            "Desglose: validación de documentos (18 min), captura de datos (12 min), "
            "aprobación del supervisor (10 min), entrega de kit (7 min). "
            "Problemas reportados: 23% de rechazos por documentación incompleta, "
            "supervisores disponibles solo 70% del tiempo, errores de captura en 8% de casos. "
            "Tu misión: proponer un plan de optimización que reduzca el tiempo a menos de 20 minutos, "
            "indicando qué pasos eliminar, automatizar o rediseñar, con métricas de éxito."
        ),
        "level": "Avanzado",
        "criteria": "análisis del cuello de botella, propuestas concretas, viabilidad, métricas claras",
        "max_score": 100,
    },
    {
        "id": 5,
        "title": "Diseño de Automatización con IA",
        "description": (
            "El área de cobranza atiende 850 llamadas diarias para gestionar pagos vencidos. "
            "El 65% son casos simples (recordatorio de pago, acuerdo de plazo). "
            "Costo por llamada: $4.20. Tasa de éxito actual: 38%. "
            "El banco quiere implementar IA para automatizar parte del proceso. "
            "Tu misión: diseñar una propuesta de automatización que incluya: "
            "qué casos automatizar y cuáles no, qué tipo de IA usar (y por qué), "
            "cómo medir el éxito, y los riesgos del proyecto con su mitigación."
        ),
        "level": "Avanzado",
        "criteria": "selección de casos apropiados, justificación técnica de IA, métricas de ROI, gestión de riesgos",
        "max_score": 100,
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
            description TEXT NOT NULL,
            level TEXT NOT NULL,
            criteria TEXT NOT NULL,
            max_score INTEGER DEFAULT 100
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mission_id INTEGER NOT NULL,
            response TEXT NOT NULL,
            score INTEGER NOT NULL,
            feedback TEXT NOT NULL,
            attempt INTEGER DEFAULT 1,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (mission_id) REFERENCES missions(id)
        )
    """)

    # Seed missions
    for mission in MISSIONS_DATA:
        cursor.execute("""
            INSERT OR IGNORE INTO missions (id, title, description, level, criteria, max_score)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (mission["id"], mission["title"], mission["description"],
              mission["level"], mission["criteria"], mission["max_score"]))

    # Default demo user
    cursor.execute("""
        INSERT OR IGNORE INTO users (id, username, name, email)
        VALUES (1, 'demo', 'Analista Demo', 'demo@banco.com')
    """)

    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")
