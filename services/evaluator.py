import os
import json
import re
import httpx
from typing import Optional

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"


async def evaluate_with_ai(
    mission_title: str,
    mission_description: str,
    mission_criteria: str,
    user_response: str,
) -> dict:
    """Evaluate user response using Claude API, with fallback to heuristic evaluation."""
    if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "":
        try:
            result = await _evaluate_with_claude(
                mission_title, mission_description, mission_criteria, user_response
            )
            return result
        except Exception as e:
            print(f"⚠️  Claude API falló, usando evaluación heurística: {e}")

    return _evaluate_heuristic(mission_title, mission_criteria, user_response)


async def _evaluate_with_claude(
    mission_title: str,
    mission_description: str,
    mission_criteria: str,
    user_response: str,
) -> dict:
    system_prompt = """Eres un evaluador experto en habilidades profesionales bancarias.
Evalúa la respuesta del usuario a una misión de simulación profesional.

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura exacta:
{
  "score": <número entero entre 0 y 100>,
  "feedback": "<párrafo de 2-3 oraciones con feedback constructivo>",
  "strengths": ["<fortaleza 1>", "<fortaleza 2>"],
  "improvements": ["<área de mejora 1>", "<área de mejora 2>"]
}

Criterios de evaluación:
- Precisión técnica y correctitud del contenido (35%)
- Claridad y estructura de la respuesta (30%)
- Profundidad del análisis (20%)
- Aplicabilidad práctica de las propuestas (15%)

No incluyas texto antes o después del JSON."""

    user_prompt = f"""MISIÓN: {mission_title}

CONTEXTO DE LA MISIÓN:
{mission_description}

CRITERIOS DE EVALUACIÓN:
{mission_criteria}

RESPUESTA DEL USUARIO:
{user_response}

Evalúa esta respuesta y devuelve el JSON de evaluación."""

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

    # Clean markdown fences if present
    content = re.sub(r"```json\s*|\s*```", "", content).strip()

    result = json.loads(content)

    return {
        "score": max(0, min(100, int(result.get("score", 50)))),
        "feedback": result.get("feedback", "Evaluación completada."),
        "strengths": result.get("strengths", []),
        "improvements": result.get("improvements", []),
    }


def _evaluate_heuristic(
    mission_title: str,
    mission_criteria: str,
    user_response: str,
) -> dict:
    """Fallback heuristic evaluator when AI API is unavailable."""
    response_lower = user_response.lower()
    word_count = len(user_response.split())
    score = 0
    strengths = []
    improvements = []

    # Length scoring (max 25 pts)
    if word_count >= 150:
        score += 25
        strengths.append("Respuesta completa y detallada")
    elif word_count >= 80:
        score += 15
        strengths.append("Respuesta de extensión adecuada")
    elif word_count >= 30:
        score += 8
        improvements.append("Amplía tu respuesta con más detalle y contexto")
    else:
        score += 2
        improvements.append("La respuesta es muy breve; desarrolla más tus ideas")

    # Structure scoring (max 25 pts)
    structure_keywords = ["primero", "segundo", "tercero", "1.", "2.", "3.",
                          "además", "finalmente", "conclusión", "recomendación",
                          "riesgo", "propuesta", "acción", "medida"]
    struct_hits = sum(1 for kw in structure_keywords if kw in response_lower)
    if struct_hits >= 5:
        score += 25
        strengths.append("Excelente estructura y organización de ideas")
    elif struct_hits >= 3:
        score += 18
        strengths.append("Buena organización con puntos claramente diferenciados")
    elif struct_hits >= 1:
        score += 10
        improvements.append("Organiza tu respuesta con secciones o numeración clara")
    else:
        score += 3
        improvements.append("Usa estructura numerada o con secciones para mayor claridad")

    # Domain knowledge (max 30 pts)
    banking_terms = ["riesgo", "morosidad", "cartera", "crédito", "liquidez",
                     "rentabilidad", "margen", "provisión", "garantía", "score",
                     "automatización", "proceso", "eficiencia", "cliente", "nps",
                     "ingresos", "gastos", "roi", "kpi", "métrica", "indicador"]
    domain_hits = sum(1 for term in banking_terms if term in response_lower)
    if domain_hits >= 8:
        score += 30
        strengths.append("Uso sólido de terminología y conceptos del sector bancario")
    elif domain_hits >= 5:
        score += 22
        strengths.append("Buen dominio del vocabulario técnico bancario")
    elif domain_hits >= 2:
        score += 12
        improvements.append("Incorpora más terminología técnica del sector financiero")
    else:
        score += 5
        improvements.append("Profundiza en conceptos y términos específicos de banca")

    # Actionability (max 20 pts)
    action_words = ["implementar", "propongo", "recomiendo", "sugiero", "aplicar",
                    "reducir", "aumentar", "mejorar", "optimizar", "automatizar",
                    "diseñar", "establecer", "crear", "desarrollar", "ejecutar"]
    action_hits = sum(1 for aw in action_words if aw in response_lower)
    if action_hits >= 4:
        score += 20
        strengths.append("Propuestas concretas y orientadas a la acción")
    elif action_hits >= 2:
        score += 13
        improvements.append("Añade más propuestas de acción específicas y medibles")
    else:
        score += 5
        improvements.append("Incluye recomendaciones concretas y pasos de implementación")

    # Ensure at least one entry per list
    if not strengths:
        strengths.append("Intento inicial con algunos elementos relevantes")
    if not improvements:
        improvements.append("Continúa practicando para profundizar el análisis")

    score = min(100, score)

    if score >= 85:
        feedback = (
            f"¡Excelente trabajo en '{mission_title}'! Tu respuesta demuestra "
            f"un alto nivel de dominio técnico y capacidad analítica. "
            f"Puntuación: {score}/100."
        )
    elif score >= 70:
        feedback = (
            f"Buen trabajo en '{mission_title}'. Cubres los aspectos principales, "
            f"aunque hay oportunidades para profundizar el análisis. "
            f"Puntuación: {score}/100."
        )
    elif score >= 50:
        feedback = (
            f"Respuesta aceptable para '{mission_title}', pero puedes mejorar en "
            f"estructura, profundidad técnica y propuestas concretas. "
            f"Puntuación: {score}/100."
        )
    else:
        feedback = (
            f"Tu respuesta para '{mission_title}' necesita desarrollo. "
            f"Enfócate en ampliar el análisis y usar terminología técnica adecuada. "
            f"Puntuación: {score}/100."
        )

    return {
        "score": score,
        "feedback": feedback,
        "strengths": strengths[:3],
        "improvements": improvements[:3],
    }
