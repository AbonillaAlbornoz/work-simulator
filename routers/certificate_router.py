"""
Certificate router:
  GET  /api/certificate/{user_id}?profession=banking  — check & return cert data
  GET  /api/certificate/{user_id}/html?profession=    — downloadable HTML cert
"""
from fastapi import APIRouter, HTTPException, Response
from datetime import datetime
from database import get_connection

router = APIRouter()
REQUIRED_MISSIONS = 20
REQUIRED_AVG_SCORE = 70

FIELD_LABELS = {
    "banking": "Banca y Finanzas",
    "legal": "Legal y Derecho",
    "social_security": "Seguridad Social",
    "payroll": "Nómina y Compensación",
}


def _get_cert_data(user_id: int, profession: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cursor.execute("""
        SELECT r.mission_id, MAX(r.score) as best_score
        FROM results r
        JOIN missions m ON r.mission_id = m.id
        WHERE r.user_id = ? AND m.profession = ?
        GROUP BY r.mission_id
    """, (user_id, profession))
    results = cursor.fetchall()
    conn.close()

    completed = [r for r in results if r["best_score"] >= REQUIRED_AVG_SCORE]
    total_completed = len(completed)
    avg_score = (
        sum(r["best_score"] for r in results) / len(results) if results else 0
    )
    is_certified = total_completed >= REQUIRED_MISSIONS and avg_score >= REQUIRED_AVG_SCORE

    return {
        "user_id": user_id,
        "user_name": dict(user).get("name", "Usuario"),
        "user_email": dict(user).get("email", ""),
        "profession": profession,
        "field_label": FIELD_LABELS.get(profession, profession),
        "is_certified": is_certified,
        "completed_missions": total_completed,
        "average_score": round(avg_score, 1),
        "required_missions": REQUIRED_MISSIONS,
        "required_score": REQUIRED_AVG_SCORE,
        "issued_at": datetime.now().strftime("%d de %B de %Y"),
    }


@router.get("/{user_id}")
def check_certificate(user_id: int, profession: str = "banking"):
    data = _get_cert_data(user_id, profession)
    if not data["is_certified"]:
        remaining = REQUIRED_MISSIONS - data["completed_missions"]
        data["message"] = (
            f"Necesitas completar {remaining} misión(es) más con score ≥ 70."
            if remaining > 0
            else f"Sube tu promedio a {REQUIRED_AVG_SCORE} (actual: {data['average_score']})."
        )
    else:
        data["message"] = (
            f"🏆 Certificación en {data['field_label']} obtenida con "
            f"promedio {data['average_score']}/100."
        )
    return data


@router.get("/{user_id}/html")
def download_certificate_html(user_id: int, profession: str = "banking"):
    data = _get_cert_data(user_id, profession)
    if not data["is_certified"]:
        raise HTTPException(status_code=403, detail="El usuario aún no cumple los requisitos de certificación")

    cert_id = f"WSA-{user_id:04d}-{profession[:3].upper()}-2026"
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<title>Certificado WorkSim AI — {data['user_name']}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Instrument+Serif:ital@0;1&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Manrope',sans-serif;background:#f5f3ff;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:40px 20px}}
  .cert{{background:#fff;border-radius:20px;max-width:780px;width:100%;box-shadow:0 20px 60px rgba(91,76,255,.15);overflow:hidden;position:relative}}
  .cert-top{{background:linear-gradient(135deg,#5b4cff,#3d2fd6);padding:48px 52px 40px;text-align:center;color:#fff;position:relative}}
  .cert-top::after{{content:'';position:absolute;bottom:-1px;left:0;right:0;height:40px;background:#fff;border-radius:60% 60% 0 0}}
  .logo{{display:inline-flex;align-items:center;gap:10px;margin-bottom:28px}}
  .logo-mark{{width:40px;height:40px;background:rgba(255,255,255,.2);border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:20px;backdrop-filter:blur(10px)}}
  .logo-text{{font-size:20px;font-weight:800;color:#fff;letter-spacing:-.02em}}
  .logo-text span{{color:#c4b5fd}}
  .cert-label{{font-size:11px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;opacity:.7;margin-bottom:10px}}
  .cert-title{{font-family:'Instrument Serif',serif;font-size:30px;font-weight:400;line-height:1.2;margin-bottom:8px}}
  .cert-field{{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);border-radius:20px;padding:5px 16px;font-size:13px;font-weight:700;margin-top:6px;backdrop-filter:blur(8px)}}

  .cert-body{{padding:44px 52px 36px;text-align:center}}
  .cert-presents{{font-size:13px;color:#8880a6;margin-bottom:6px;font-weight:600}}
  .cert-name{{font-family:'Instrument Serif',serif;font-size:40px;font-weight:400;color:#16141f;margin-bottom:8px;letter-spacing:-.01em}}
  .cert-desc{{font-size:15px;color:#3c3950;line-height:1.65;max-width:500px;margin:0 auto 28px}}

  .cert-stats{{display:flex;justify-content:center;gap:32px;margin-bottom:32px;padding:20px;background:#f8f7fc;border-radius:14px}}
  .stat{{text-align:center}}
  .stat-val{{font-family:'Instrument Serif',serif;font-size:34px;color:#5b4cff;line-height:1}}
  .stat-lbl{{font-size:11px;color:#8880a6;font-weight:700;letter-spacing:.04em;margin-top:3px;text-transform:uppercase}}

  .cert-footer{{display:flex;justify-content:space-between;align-items:flex-end;padding:20px 0 0;border-top:1px solid #e5e2f0;margin-top:4px}}
  .footer-item{{text-align:center}}
  .footer-label{{font-size:10px;color:#8880a6;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:3px}}
  .footer-val{{font-size:13px;font-weight:700;color:#16141f}}
  .cert-id{{font-family:'Courier New',monospace;font-size:11px;color:#8880a6;letter-spacing:.08em}}

  .trophy{{font-size:52px;margin-bottom:12px;display:block}}
  .verify-badge{{display:inline-flex;align-items:center;gap:6px;background:#d1fae5;color:#059669;border:1px solid #a7f3d0;border-radius:20px;padding:5px 14px;font-size:12px;font-weight:700;margin-bottom:20px}}

  @media print{{body{{background:#fff;padding:0}}  .cert{{box-shadow:none;border-radius:0}}  .no-print{{display:none}}}}
</style>
</head>
<body>
<div class="cert">
  <div class="cert-top">
    <div class="logo">
      <div class="logo-mark">🧠</div>
      <span class="logo-text">Work<span>Sim</span> AI</span>
    </div>
    <div class="cert-label">Certificado de Competencia Profesional</div>
    <div class="cert-title">IA Aplicada en el Ámbito Profesional</div>
    <span class="cert-field">📚 {data['field_label']}</span>
  </div>

  <div class="cert-body">
    <span class="trophy">🏆</span>
    <div class="verify-badge">✓ Certificación Verificada</div>
    <div class="cert-presents">Este certificado acredita que</div>
    <div class="cert-name">{data['user_name']}</div>
    <div class="cert-desc">
      Ha completado satisfactoriamente el programa de entrenamiento en
      <strong>diseño de prompts con IA aplicados a {data['field_label']}</strong>,
      demostrando competencia en el uso de inteligencia artificial para
      resolver casos profesionales reales.
    </div>

    <div class="cert-stats">
      <div class="stat">
        <div class="stat-val">{data['completed_missions']}</div>
        <div class="stat-lbl">Misiones completadas</div>
      </div>
      <div class="stat">
        <div class="stat-val">{data['average_score']}</div>
        <div class="stat-lbl">Score promedio</div>
      </div>
      <div class="stat">
        <div class="stat-val">100%</div>
        <div class="stat-lbl">Tasa de finalización</div>
      </div>
    </div>

    <div class="cert-footer">
      <div class="footer-item">
        <div class="footer-label">Emitido por</div>
        <div class="footer-val">WorkSim AI</div>
      </div>
      <div class="footer-item">
        <div class="footer-label">Fecha de emisión</div>
        <div class="footer-val">{data['issued_at']}</div>
      </div>
      <div class="footer-item">
        <div class="footer-label">ID del certificado</div>
        <div class="cert-id">{cert_id}</div>
      </div>
    </div>
  </div>
</div>

<div class="no-print" style="margin-top:24px;text-align:center">
  <button onclick="window.print()" style="background:linear-gradient(135deg,#5b4cff,#3d2fd6);color:#fff;border:none;padding:12px 28px;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;font-family:'Manrope',sans-serif;margin-right:10px">
    🖨️ Descargar / Imprimir
  </button>
  <button onclick="window.close()" style="background:#f1f0f8;color:#3c3950;border:1px solid #e5e2f0;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;font-family:'Manrope',sans-serif">
    Cerrar
  </button>
</div>
</body>
</html>"""

    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'inline; filename="certificado-worksim-{profession}.html"'},
    )
