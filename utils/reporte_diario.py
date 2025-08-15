import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from utils.date_utils import ahora_argentina

def generar_reporte_diario(df_reclamos):
    """Genera un PDF con el reporte diario de reclamos"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    fecha_hoy = ahora_argentina().strftime("%d/%m/%Y")
    hora_actual = ahora_argentina().strftime("%H:%M")

    # Filtrar reclamos
    reclamos_hoy = df_reclamos[df_reclamos['Fecha_formateada'].str.startswith(fecha_hoy)]
    reclamos_resueltos = (
        reclamos_hoy[reclamos_hoy['Estado'] == 'Resuelto']['Técnico']
        .value_counts()
        .to_dict()
    )
    pendientes_por_tipo = (
        df_reclamos[df_reclamos['Estado'] == 'Pendiente']['Tipo de reclamo']
        .value_counts()
        .to_dict()
    )
    total_pendientes = sum(pendientes_por_tipo.values())

    # Título principal
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"■ Reporte Diario - {fecha_hoy}")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Generado a las {hora_actual}")
    y -= 40

    # Reclamos ingresados hoy
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"■ Reclamos ingresados hoy: {len(reclamos_hoy)}")
    y -= 30

    # Reporte técnico/grupo
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "■ Reporte técnico/grupo:")
    y -= 20
    if reclamos_resueltos:
        for tecnico, cantidad in reclamos_resueltos.items():
            c.drawString(70, y, f"{tecnico}: {cantidad} resueltos")
            y -= 20
    else:
        c.drawString(70, y, "No hay reclamos resueltos hoy")
        y -= 20
    y -= 10

    # Pendientes por tipo
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"■ Quedan pendientes: {total_pendientes}")
    y -= 20
    for tipo, cantidad in pendientes_por_tipo.items():
        c.drawString(70, y, f"{tipo}: {cantidad}")
        y -= 20

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer
