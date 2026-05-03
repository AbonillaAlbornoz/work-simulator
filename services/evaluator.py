import os
import json
import re
import httpx

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

DOMAIN_TERMS = {
    "banking": [
        "riesgo", "morosidad", "cartera", "crédito", "liquidez", "rentabilidad",
        "margen", "provisión", "garantía", "scoring", "automatización", "proceso",
        "eficiencia", "nps", "roi", "kpi", "métrica", "mitigación", "portafolio",
        "actúa como", "analiza", "identifica", "propón", "calcula", "entrega",
        "rol", "contexto", "estructura", "formato"
    ],
    "legal": [
        "cláusula", "contrato", "obligación", "rescisión", "incumplimiento", "penalidad",
        "jurisdicción", "arbitraje", "confidencialidad", "contingencia", "litigio",
        "responsabilidad", "indemnización", "nulidad", "negociación", "actúa como",
        "analiza", "identifica", "redacta", "evalúa", "recomienda", "rol", "contexto"
    ],
    "social_security": [
        "ibc", "cotización", "aporte", "eps", "afp", "arl", "ugpp", "incapacidad",
        "pensión", "cesantías", "liquidación", "afiliación", "fuero", "semanas",
        "base de cotización", "actúa como", "calcula", "determina", "analiza",
        "identifica", "propón", "rol", "contexto", "estructura"
    ],
    "payroll": [
        "nómina", "devengado", "deducción", "retención", "auxilio de transporte",
        "prima", "cesantías", "horas extras", "recargo", "liquidación", "smlv",
        "uvt", "comisión", "embargos", "actúa como", "calcula", "determina",
        "propón", "diseña", "analiza", "rol", "contexto", "estructura"
    ],
}

PROMPT_INDICATORS = [
    "actúa como", "actua como", "eres un", "como experto", "como especialista",
    "como analista", "como abogado", "como consultor", "como asesor", "como director",
    "analiza", "evalúa", "evalua", "calcula", "identifica", "redacta", "propón",
    "proponer", "entrega", "genera", "diseña", "considera", "basándote",
    "en formato", "estructura tu", "responde con", "el output debe",
]

DIRECT_ANSWER_PATTERNS = [
    "la solución es", "la respuesta es", "en mi opinión", "yo creo que",
    "considero que", "definitivamente", "está claro que", "obviamente",
    "el problema es simplemente", "solo hay que", "basta con",
]


def detect_prompt_structure(response: str) -> dict:
    """Detect whether the response is a prompt or a direct answer."""
    lower = response.lower()
    prompt_hits = sum(1 for p in PROMPT_INDICATORS if p in lower)
    direct_hits = sum(1 for p in DIRECT_ANSWER_PATTERNS if p in lower)
    word_count = len(response.split())

    is_prompt = prompt_hits >= 2
    is_direct = direct_hits >= 2 and prompt_hits < 2

    return {
        "is_prompt": is_prompt,
        "is_direct_answer": is_direct,
        "prompt_hits": prompt_hits,
        "direct_hits": direct_hits,
        "word_count": word_count,
    }


async def evaluate_with_ai(
    mission_title: str,
    mission_description: str,
    mission_criteria: str,
    mission_structure: str,
    user_response: str,
    profession: str = "banking",
) -> dict:
    detection = detect_prompt_structure(user_response)

    if ANTHROPIC_API_KEY:
        try:
            result = await _evaluate_with_claude(
                mission_title, mission_description,
                mission_criteria, mission_structure,
                user_response, profession, detection
            )
            result["is_direct_answer"] = detection["is_direct_answer"]
            return result
        except Exception as e:
            print(f"⚠️  Claude API failed, using heuristic: {e}")

    result = _evaluate_heuristic(
        mission_title, mission_criteria, mission_structure,
        user_response, profession, detection
    )
    result["is_direct_answer"] = detection["is_direct_answer"]
    return result


async def _evaluate_with_claude(
    mission_title, mission_description, mission_criteria,
    mission_structure, user_response, profession, detection
) -> dict:
    domain_labels = {
        "banking": "bancaria y financiera",
        "legal": "legal y jurídica",
        "social_security": "seguridad social y recursos humanos",
        "payroll": "nómina y compensación laboral",
    }
    domain = domain_labels.get(profession, "profesional")

    is_prompt_note = ""
    if detection["is_direct_answer"]:
        is_prompt_note = (
            "\n⚠️ NOTA IMPORTANTE: El usuario parece haber respondido el problema directamente "
            "en lugar de escribir un PROMPT. Penaliza significativamente el score (máximo 45 puntos) "
            "y explica en el feedback que debe escribir un prompt, no resolver el caso directamente."
        )

    system_prompt = f"""Eres un coach experto en habilidades profesionales del área {domain}.
La tarea del usuario NO es resolver el caso directamente.
Su tarea es escribir un PROMPT efectivo que le daría a una IA para que resuelva el caso.
Evalúa qué tan bien diseñado está el prompt.{is_prompt_note}

Responde ÚNICAMENTE con JSON válido:
{{
  "score": <entero 0-100>,
  "feedback": "<2-3 oraciones de feedback>",
  "strengths": ["<fortaleza del prompt 1>", "<fortaleza 2>"],
  "improvements": ["<mejora específica 1>", "<mejora 2>"],
  "action_plan": ["<paso accionable 1>", "<paso 2>", "<paso 3>"]
}}

Criterios de evaluación del PROMPT:
- ¿Define un rol claro para la IA? (25%)
- ¿Incluye el contexto/datos relevantes del caso? (25%)
- ¿Especifica la estructura del output esperado? (25%)
- ¿Usa terminología técnica {domain}? (25%)

El action_plan debe decir exactamente qué mejorar en el PROMPT."""

    user_prompt = f"""MISIÓN: {mission_title}
CASO: {mission_description}
ESTRUCTURA DE PROMPT ESPERADA: {mission_structure}
CRITERIOS: {mission_criteria}
PROMPT ESCRITO POR EL USUARIO: {user_response}

Evalúa el prompt y devuelve el JSON."""

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": user_prompt}],
        "system": system_prompt,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    content = re.sub(r"```json\s*|\s*```", "", data["content"][0]["text"].strip()).strip()
    result = json.loads(content)
    return {
        "score": max(0, min(100, int(result.get("score", 50)))),
        "feedback": result.get("feedback", "Evaluación completada."),
        "strengths": result.get("strengths", []),
        "improvements": result.get("improvements", []),
        "action_plan": result.get("action_plan", []),
    }


def _evaluate_heuristic(
    mission_title, mission_criteria, mission_structure,
    user_response, profession, detection
) -> dict:
    response_lower = user_response.lower()
    word_count = detection["word_count"]
    score = 0
    strengths = []
    improvements = []

    # Penalize direct answers
    if detection["is_direct_answer"]:
        return {
            "score": 30,
            "feedback": (
                f"⚠️ Parece que estás respondiendo el problema directamente. "
                f"Recuerda: tu tarea es escribir el PROMPT que le darías a la IA para resolver '{mission_title}', "
                f"no resolver el caso tú mismo. Empieza con 'Actúa como [rol]...' y define qué debe hacer la IA."
            ),
            "strengths": ["Conoces el tema del caso"],
            "improvements": [
                "Escribe un PROMPT en lugar de resolver el caso directamente",
                "Empieza con 'Actúa como [especialista en...]'",
                "Define la estructura del output que esperas de la IA",
            ],
            "action_plan": [
                "Cambia 'La solución es...' por 'Actúa como [rol] y analiza...'",
                "Incluye el contexto del caso en el prompt",
                "Especifica el formato de respuesta que quieres de la IA",
                "Termina con 'Entrega: [estructura esperada]'",
            ],
        }

    # 1. Role definition (25 pts)
    role_words = ["actúa como", "actua como", "eres un", "como experto", "como especialista",
                  "como analista", "como abogado", "como consultor", "como asesor"]
    role_hits = sum(1 for w in role_words if w in response_lower)
    if role_hits >= 1:
        score += 25
        strengths.append("Define claramente el rol que debe asumir la IA")
    else:
        score += 5
        improvements.append("Empieza definiendo el rol: 'Actúa como [especialista en...]'")

    # 2. Context/data inclusion (25 pts)
    terms = DOMAIN_TERMS.get(profession, DOMAIN_TERMS["banking"])
    domain_hits = sum(1 for t in terms if t in response_lower)
    if domain_hits >= 6:
        score += 25
        strengths.append("Incluye contexto técnico y datos relevantes del caso")
    elif domain_hits >= 3:
        score += 16
        improvements.append("Añade más datos concretos del caso en el prompt")
    else:
        score += 6
        improvements.append("Incluye los datos clave del caso en tu prompt")

    # 3. Output structure specification (25 pts)
    struct_words = ["entrega", "genera", "propón", "formato", "estructura", "lista",
                    "incluye", "presenta", "redacta", "calcula", "identifica"]
    struct_hits = sum(1 for w in struct_words if w in response_lower)
    struct_lines = [l for l in mission_structure.lower().split("\n") if l.strip()]
    struct_match = sum(
        1 for line in struct_lines
        if any(w in response_lower for w in line.split() if len(w) > 4)
    )
    if struct_hits >= 3 and struct_match >= 2:
        score += 25
        strengths.append("Especifica bien la estructura y el output esperado de la IA")
    elif struct_hits >= 2:
        score += 16
        improvements.append("Sé más específico sobre qué debe entregar la IA (formato y secciones)")
    else:
        score += 6
        improvements.append("Define el formato de output: 'Entrega: 1. resumen 2. análisis 3. recomendación'")

    # 4. Length and quality (25 pts)
    if word_count >= 100:
        score += 25
        strengths.append("Prompt completo y bien desarrollado")
    elif word_count >= 50:
        score += 16
        improvements.append("Amplía el prompt con más contexto y especificaciones")
    elif word_count >= 20:
        score += 8
        improvements.append("El prompt es demasiado corto — añade rol, contexto y estructura")
    else:
        score += 2
        improvements.append("Desarrolla mucho más el prompt")

    if not strengths:
        strengths.append("Intento inicial con algunos elementos de prompt identificados")
    if not improvements:
        improvements.append("Refina la especificación del output esperado")

    score = min(100, score)

    if score >= 85:
        feedback = f"¡Excelente prompt para '{mission_title}'! Tiene rol claro, contexto relevante y output bien definido. La IA podría resolver el caso con este prompt."
    elif score >= 70:
        feedback = f"Buen prompt para '{mission_title}'. Cubre los elementos principales aunque puedes mejorar la especificación del output esperado."
    elif score >= 50:
        feedback = f"Tu prompt para '{mission_title}' tiene algunos elementos correctos pero necesita más contexto y estructura. Recuerda: defines el trabajo de la IA, no lo resuelves tú."
    else:
        feedback = f"Tu prompt para '{mission_title}' necesita desarrollo. Asegúrate de incluir: rol de la IA, datos del caso y formato de respuesta esperado."

    action_plan = []
    if role_hits == 0:
        action_plan.append("Comienza con: 'Actúa como [especialista en...] y...'")
    if domain_hits < 3:
        action_plan.append("Copia los datos clave del caso directamente en tu prompt")
    if struct_hits < 2:
        action_plan.append("Termina el prompt con: 'Entrega en este formato: 1... 2... 3...'")
    if word_count < 50:
        action_plan.append("Un buen prompt tiene al menos 60-80 palabras — desarrolla más")
    if not action_plan:
        action_plan = [
            "Añade el contexto numérico del caso dentro del prompt",
            "Especifica más el formato exacto del output que necesitas",
        ]

    return {
        "score": score,
        "feedback": feedback,
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "action_plan": action_plan[:4],
    }
