import os
import json
import re
import httpx

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

BANKING_TERMS = [
    "riesgo", "morosidad", "cartera", "crédito", "liquidez", "rentabilidad",
    "margen", "provisión", "garantía", "score", "automatización", "proceso",
    "eficiencia", "cliente", "nps", "ingresos", "gastos", "roi", "kpi",
    "métrica", "indicador", "severidad", "mitigación", "portafolio"
]

LEGAL_TERMS = [
    "cláusula", "contrato", "obligación", "rescisión", "incumplimiento", "penalidad",
    "jurisdicción", "arbitraje", "confidencialidad", "nda", "riesgo legal", "contingencia",
    "litigio", "demanda", "sentencia", "apelación", "finiquito", "due diligence",
    "responsabilidad", "indemnización", "prescripción", "nulidad", "acuerdo", "negociación"
]


async def evaluate_with_ai(
    mission_title: str,
    mission_description: str,
    mission_criteria: str,
    mission_structure: str,
    user_response: str,
    profession: str = "banking",
) -> dict:
    if ANTHROPIC_API_KEY:
        try:
            return await _evaluate_with_claude(
                mission_title, mission_description,
                mission_criteria, mission_structure,
                user_response, profession
            )
        except Exception as e:
            print(f"⚠️  Claude API failed, using heuristic: {e}")

    return _evaluate_heuristic(
        mission_title, mission_criteria, mission_structure, user_response, profession
    )


async def _evaluate_with_claude(
    mission_title, mission_description, mission_criteria,
    mission_structure, user_response, profession
) -> dict:
    domain = "bancaria" if profession == "banking" else "legal / jurídica"
    system_prompt = f"""Eres un coach experto en habilidades profesionales del área {domain}.
Evalúa la respuesta del usuario a una simulación profesional.

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura exacta:
{{
  "score": <entero 0-100>,
  "feedback": "<2-3 oraciones de feedback constructivo>",
  "strengths": ["<fortaleza 1>", "<fortaleza 2>"],
  "improvements": ["<mejora específica 1>", "<mejora específica 2>"],
  "action_plan": ["<paso accionable 1>", "<paso accionable 2>", "<paso accionable 3>"]
}}

Pesos: estructura (30%) · precisión técnica {domain} (30%) · claridad ejecutiva (20%) · propuestas accionables (20%).
El action_plan debe indicar exactamente qué cambiar en el próximo intento.
No incluyas texto antes o después del JSON."""

    user_prompt = f"""MISIÓN: {mission_title}
DATOS: {mission_description}
ESTRUCTURA ESPERADA: {mission_structure}
CRITERIOS: {mission_criteria}
RESPUESTA: {user_response}

Evalúa y devuelve el JSON."""

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
    mission_title, mission_criteria, mission_structure, user_response, profession="banking"
) -> dict:
    response_lower = user_response.lower()
    word_count = len(user_response.split())
    score = 0
    strengths = []
    improvements = []

    # 1. Length (25 pts)
    if word_count >= 150:
        score += 25; strengths.append("Respuesta completa y bien desarrollada")
    elif word_count >= 80:
        score += 15; strengths.append("Extensión adecuada para el nivel de la misión")
    elif word_count >= 30:
        score += 8; improvements.append("Amplía tu respuesta con más detalle y argumentación")
    else:
        score += 2; improvements.append("La respuesta es muy breve — desarrolla cada sección")

    # 2. Structure adherence (25 pts)
    struct_lines = [l for l in mission_structure.lower().split("\n") if l.strip()]
    hits = sum(
        1 for line in struct_lines
        if any(w in response_lower for w in line.split() if len(w) > 4)
    )
    ratio = hits / max(len(struct_lines), 1)
    if ratio >= 0.8:
        score += 25; strengths.append("Siguió la estructura esperada correctamente")
    elif ratio >= 0.5:
        score += 16; improvements.append("Sigue más de cerca la estructura indicada en el briefing")
    else:
        score += 6; improvements.append("Estructura tu respuesta exactamente como indica el formato")

    # 3. Domain knowledge (30 pts)
    terms = LEGAL_TERMS if profession == "legal" else BANKING_TERMS
    domain_hits = sum(1 for t in terms if t in response_lower)
    if domain_hits >= 7:
        score += 30; strengths.append("Uso sólido de terminología técnica del área")
    elif domain_hits >= 4:
        score += 22; strengths.append("Buen dominio del vocabulario especializado")
    elif domain_hits >= 2:
        score += 12; improvements.append("Incorpora más terminología técnica del área")
    else:
        score += 5; improvements.append("Usa términos específicos del campo profesional")

    # 4. Actionability (20 pts)
    action_words = [
        "propongo", "recomiendo", "sugiero", "implementar", "establecer",
        "redactar", "negociar", "modificar", "incluir", "eliminar",
        "identificar", "analizar", "revisar", "diseñar", "ejecutar"
    ]
    action_hits = sum(1 for aw in action_words if aw in response_lower)
    if action_hits >= 4:
        score += 20; strengths.append("Propuestas concretas y orientadas a la acción")
    elif action_hits >= 2:
        score += 12; improvements.append("Añade más propuestas de acción específicas")
    else:
        score += 4; improvements.append("Incluye recomendaciones concretas con pasos claros")

    if not strengths:
        strengths.append("Intento inicial con elementos relevantes identificados")
    if not improvements:
        improvements.append("Continúa practicando para profundizar el análisis")

    score = min(100, score)
    domain_label = "legal" if profession == "legal" else "bancaria"

    if score >= 85:
        feedback = f"¡Excelente análisis en '{mission_title}'! Tu respuesta demuestra dominio técnico {domain_label} sólido. Puntuación: {score}/100."
    elif score >= 70:
        feedback = f"Buen trabajo en '{mission_title}'. Cubres los aspectos principales aunque hay oportunidades de profundizar. Puntuación: {score}/100."
    elif score >= 50:
        feedback = f"Respuesta aceptable en '{mission_title}', pero puedes mejorar en estructura y profundidad técnica {domain_label}. Puntuación: {score}/100."
    else:
        feedback = f"Tu respuesta en '{mission_title}' necesita más desarrollo. Sigue la estructura indicada y usa terminología técnica. Puntuación: {score}/100."

    action_plan = []
    if word_count < 80:
        action_plan.append("Desarrolla cada sección con al menos 2-3 oraciones de contenido")
    if domain_hits < 4:
        lbl = "cláusula, riesgo legal, jurisdicción, indemnización" if profession == "legal" else "morosidad, provisión, KPI, ROI, mitigación"
        action_plan.append(f"Incorpora términos técnicos: {lbl}")
    if ratio < 0.5:
        action_plan.append("Respeta el formato exacto indicado en 'Qué debe tener tu respuesta'")
    if action_hits < 2:
        action_plan.append("Termina cada punto con una propuesta concreta y medible")
    if score < 70:
        action_plan.append("Relee el contexto del caso e identifica los datos clave antes de responder")

    if not action_plan:
        action_plan = ["Sé más específico con ejemplos del caso", "Refuerza la justificación de cada recomendación"]

    return {
        "score": score,
        "feedback": feedback,
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "action_plan": action_plan[:4],
    }
