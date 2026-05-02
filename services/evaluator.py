import os
import json
import re
import httpx

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


async def evaluate_with_ai(
    mission_title: str,
    mission_description: str,
    mission_criteria: str,
    mission_structure: str,
    user_response: str,
) -> dict:
    """Evaluate user response using Claude API, with fallback to heuristic evaluation."""
    if ANTHROPIC_API_KEY:
        try:
            return await _evaluate_with_claude(
                mission_title, mission_description,
                mission_criteria, mission_structure, user_response
            )
        except Exception as e:
            print(f"⚠️  Claude API falló, usando evaluación heurística: {e}")

    return _evaluate_heuristic(mission_title, mission_criteria, mission_structure, user_response)


async def _evaluate_with_claude(
    mission_title: str,
    mission_description: str,
    mission_criteria: str,
    mission_structure: str,
    user_response: str,
) -> dict:
    system_prompt = """Eres un coach experto en habilidades profesionales bancarias.
Evalúa la respuesta del usuario y genera un plan de mejora accionable.

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura exacta:
{
  "score": <entero 0-100>,
  "feedback": "<2-3 oraciones de feedback general constructivo>",
  "strengths": ["<fortaleza concreta 1>", "<fortaleza concreta 2>"],
  "improvements": ["<área de mejora específica 1>", "<área de mejora específica 2>"],
  "action_plan": [
    "<paso accionable 1 para mejorar en el próximo intento>",
    "<paso accionable 2>",
    "<paso accionable 3>"
  ]
}

Pesos de evaluación:
- Estructura y seguimiento del formato esperado (30%)
- Precisión técnica del contenido bancario (30%)
- Claridad y concisión del lenguaje ejecutivo (20%)
- Propuestas accionables y medibles (20%)

El action_plan debe ser específico para esta misión: qué hacer diferente en el próximo intento.
No incluyas texto antes o después del JSON."""

    user_prompt = f"""MISIÓN: {mission_title}

DATOS DEL CASO:
{mission_description}

ESTRUCTURA ESPERADA:
{mission_structure}

CRITERIOS DE EVALUACIÓN:
{mission_criteria}

RESPUESTA DEL USUARIO:
{user_response}

Evalúa y devuelve el JSON completo."""

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
        response = await client.post(ANTHROPIC_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    content = data["content"][0]["text"].strip()
    content = re.sub(r"```json\s*|\s*```", "", content).strip()
    result = json.loads(content)

    return {
        "score": max(0, min(100, int(result.get("score", 50)))),
        "feedback": result.get("feedback", "Evaluación completada."),
        "strengths": result.get("strengths", []),
        "improvements": result.get("improvements", []),
        "action_plan": result.get("action_plan", []),
    }


def _evaluate_heuristic(
    mission_title: str,
    mission_criteria: str,
    mission_structure: str,
    user_response: str,
) -> dict:
    """Heuristic evaluator — runs when AI API is unavailable."""
    response_lower = user_response.lower()
    word_count = len(user_response.split())
    score = 0
    strengths = []
    improvements = []

    # 1. Length (25 pts)
    if word_count >= 150:
        score += 25
        strengths.append("Respuesta completa y bien desarrollada")
    elif word_count >= 80:
        score += 15
        strengths.append("Extensión adecuada para el nivel de la misión")
    elif word_count >= 30:
        score += 8
        improvements.append("Amplía tu respuesta con más detalle y contexto")
    else:
        score += 2
        improvements.append("La respuesta es muy breve; desarrolla más tus ideas")

    # 2. Structure adherence (25 pts)
    structure_lines = mission_structure.lower().split("\n")
    struct_hits = 0
    for line in structure_lines:
        keywords = [w for w in line.split() if len(w) > 4]
        if any(kw in response_lower for kw in keywords):
            struct_hits += 1

    if struct_hits >= len(structure_lines):
        score += 25
        strengths.append("Siguió la estructura esperada correctamente")
    elif struct_hits >= len(structure_lines) // 2:
        score += 16
        improvements.append("Sigue más de cerca la estructura indicada en las instrucciones")
    else:
        score += 6
        improvements.append("Estructura tu respuesta exactamente como indica el formato esperado")

    # 3. Banking domain knowledge (30 pts)
    banking_terms = [
        "riesgo", "morosidad", "cartera", "crédito", "liquidez", "rentabilidad",
        "margen", "provisión", "garantía", "score", "automatización", "proceso",
        "eficiencia", "cliente", "nps", "ingresos", "gastos", "roi", "kpi",
        "métrica", "indicador", "severidad", "mitigación", "portafolio"
    ]
    domain_hits = sum(1 for t in banking_terms if t in response_lower)
    if domain_hits >= 8:
        score += 30
        strengths.append("Uso sólido de terminología técnica bancaria")
    elif domain_hits >= 5:
        score += 22
        strengths.append("Buen dominio del vocabulario del sector financiero")
    elif domain_hits >= 2:
        score += 12
        improvements.append("Incorpora más terminología técnica del sector bancario")
    else:
        score += 5
        improvements.append("Profundiza en conceptos específicos de banca y finanzas")

    # 4. Actionability (20 pts)
    action_words = [
        "implementar", "propongo", "recomiendo", "sugiero", "aplicar",
        "reducir", "aumentar", "mejorar", "optimizar", "automatizar",
        "diseñar", "establecer", "crear", "desarrollar", "ejecutar", "medir"
    ]
    action_hits = sum(1 for aw in action_words if aw in response_lower)
    if action_hits >= 4:
        score += 20
        strengths.append("Propuestas concretas y orientadas a la acción")
    elif action_hits >= 2:
        score += 12
        improvements.append("Añade más verbos de acción y propuestas medibles")
    else:
        score += 4
        improvements.append("Incluye recomendaciones concretas con pasos de implementación")

    if not strengths:
        strengths.append("Intento con algunos elementos relevantes identificados")
    if not improvements:
        improvements.append("Continúa practicando para profundizar el análisis")

    score = min(100, score)

    # Generate contextual feedback
    if score >= 85:
        feedback = (
            f"¡Excelente trabajo en '{mission_title}'! Tu respuesta demuestra dominio técnico "
            f"y capacidad analítica sólida. Puntuación: {score}/100."
        )
    elif score >= 70:
        feedback = (
            f"Buen trabajo en '{mission_title}'. Cubres los aspectos principales aunque "
            f"hay oportunidades para profundizar. Puntuación: {score}/100."
        )
    elif score >= 50:
        feedback = (
            f"Respuesta aceptable en '{mission_title}', pero puedes mejorar en estructura, "
            f"profundidad técnica y propuestas concretas. Puntuación: {score}/100."
        )
    else:
        feedback = (
            f"Tu respuesta en '{mission_title}' necesita más desarrollo. "
            f"Sigue la estructura indicada y usa terminología técnica adecuada. Puntuación: {score}/100."
        )

    # Generate action plan based on score
    action_plan = []
    if word_count < 80:
        action_plan.append("Desarrolla cada sección con al menos 2-3 oraciones de contenido")
    if domain_hits < 5:
        action_plan.append("Usa términos técnicos: morosidad, provisión, KPI, ROI, mitigación")
    if struct_hits < len(structure_lines) // 2:
        action_plan.append("Respeta el formato exacto indicado en 'Estructura esperada'")
    if action_hits < 2:
        action_plan.append("Termina cada punto con una propuesta de acción medible y concreta")
    if score < 70:
        action_plan.append("Relee el contexto del caso e identifica los datos numéricos clave")

    if not action_plan:
        action_plan.append("Intenta ser más específico con ejemplos o cifras del caso")
        action_plan.append("Refuerza la justificación de cada recomendación")

    return {
        "score": score,
        "feedback": feedback,
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "action_plan": action_plan[:4],
    }
