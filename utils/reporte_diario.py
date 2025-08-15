import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from utils.date_utils import ahora_argentina

def generar_reporte_diario(df_reclamos):
    """Genera un PDF con el reporte diario de reclamos"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    fecha_hoy = ahora_argentina().strftime("%d/%m/%Y")
    hora_actual = ahora_argentina().strftime("%H:%M")

    # ===========================
    # Título
    # ===========================
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"Reporte Diario - {fecha_hoy}")

    c.setFont("Helvetica", 10)
    c.drawString(50, height - 65, f"Generado a las {hora_actual}")

    # ===========================
    # Reclamos ingresados hoy
    # ===========================
    ingresados_hoy = df_reclamos[
        df_reclamos["Fecha_formateada"].str.startswith(fecha_hoy)
    ]
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 100, f"Reclamos ingresados hoy: {len(ingresados_hoy)}")

    # ===========================
    # Resueltos por técnico
    # ===========================
    resueltos_hoy = ingresados_hoy[ingresados_hoy["Estado"] == "Resuelto"]
    y_pos = height - 130
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, "Reporte técnico/grupo:")
    y_pos -= 20
    c.setFont("Helvetica", 10)

    if not resueltos_hoy.empty:
        for tecnico, grupo in resueltos_hoy.groupby("Técnico"):
            c.drawString(60, y_pos, f"{tecnico}: {len(grupo)} resueltos")
            y_pos -= 15
    else:
        c.drawString(60, y_pos, "No hay reclamos resueltos hoy")
        y_pos -= 15

    # ===========================
    # Pendientes por tipo
    # ===========================
    pendientes = df_reclamos[df_reclamos["Estado"] == "Pendiente"]
    y_pos -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, "Quedan pendientes:")
    y_pos -= 20
    c.setFont("Helvetica", 10)

    if not pendientes.empty:
        for tipo, grupo in pendientes.groupby("Tipo de reclamo"):
            c.drawString(60, y_pos, f"{tipo}: {len(grupo)}")
            y_pos -= 15
    else:
        c.drawString(60, y_pos, "No hay reclamos pendientes")

    # ===========================
    # Pie de página
    # ===========================
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 30, "Generado automáticamente por Fusion Reclamos App")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
