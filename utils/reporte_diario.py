import io
from datetime import datetime
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from utils.date_utils import ahora_argentina, format_fecha

def generar_reporte_diario_imagen(df_reclamos):
    """Genera una imagen PNG con el reporte diario."""
    # Dimensiones de la imagen
    WIDTH, HEIGHT = 1200, 1600
    BG_COLOR = (39, 40, 34)  # Monokai fondo
    TEXT_COLOR = (248, 248, 242)  # Monokai texto blanco
    HIGHLIGHT_COLOR = (249, 38, 114)  # Monokai rosa

    # Crear imagen base
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Cargar fuente (usa una genérica de sistema si no hay personalizada)
    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
        font_subtitle = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
        font_text = ImageFont.truetype("DejaVuSans.ttf", 25)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Variables para escribir texto
    y = 50
    line_height = 40

    # Fecha
    fecha_hoy = ahora_argentina().strftime("%d/%m/%Y")
    hora_gen = ahora_argentina().strftime("%H:%M")

    # Asegurar que la columna Fecha de Cierre sea datetime
    if "Fecha de Cierre" in df_reclamos.columns:
        df_reclamos["Fecha de Cierre"] = pd.to_datetime(
            df_reclamos["Fecha de Cierre"], errors="coerce", dayfirst=True
        )

    # Reclamos ingresados hoy
    hoy = ahora_argentina().date()
    reclamos_hoy = df_reclamos[df_reclamos['Fecha y hora'].dt.date == hoy]
    total_hoy = len(reclamos_hoy)

    # Reclamos resueltos por técnico/grupo basados en la fecha de cierre
    resueltos_hoy = df_reclamos[
        (df_reclamos['Fecha de Cierre'].dt.date == hoy) &
        (df_reclamos['Estado'] == 'Resuelto')
    ]

    tecnicos_resueltos = (
        resueltos_hoy.groupby('Técnico')['Estado']
        .count()
        .reset_index()
        .sort_values(by='Estado', ascending=False)
    )

    # Pendientes agrupados por tipo
    pendientes = df_reclamos[df_reclamos['Estado'] == 'Pendiente']
    pendientes_tipo = (
        pendientes.groupby('Tipo de reclamo')['Estado']
        .count()
        .reset_index()
        .sort_values(by='Estado', ascending=False)
    )
    total_pendientes = pendientes['Estado'].count()

    # --------------------------
    # Escribir contenido
    # --------------------------
    def draw_line(text, font, color, offset_y):
        nonlocal y
        draw.text((50, y), text, font=font, fill=color)
        y += offset_y

    draw_line(f"■ Reporte Diario - {fecha_hoy}", font_title, HIGHLIGHT_COLOR, line_height)
    draw_line(f"Generado a las {hora_gen}", font_subtitle, TEXT_COLOR, line_height)

    draw_line("", font_text, TEXT_COLOR, line_height // 2)

    draw_line(f"■ Reclamos ingresados hoy: {total_hoy}", font_subtitle, HIGHLIGHT_COLOR, line_height)

    draw_line("", font_text, TEXT_COLOR, line_height // 2)

    draw_line("■ Reporte técnico/grupo:", font_subtitle, HIGHLIGHT_COLOR, line_height)
    if tecnicos_resueltos.empty:
        draw_line("No hay reclamos resueltos hoy", font_text, TEXT_COLOR, line_height)
    else:
        for _, row in tecnicos_resueltos.iterrows():
            draw_line(f"{row['Técnico']}: {row['Estado']} resueltos", font_text, TEXT_COLOR, line_height)

    draw_line("", font_text, TEXT_COLOR, line_height // 2)

    draw_line(f"■ Quedan pendientes: {total_pendientes}", font_subtitle, HIGHLIGHT_COLOR, line_height)
    for _, row in pendientes_tipo.iterrows():
        draw_line(f"{row['Tipo de reclamo']}: {row['Estado']}", font_text, TEXT_COLOR, line_height)

    # Guardar a buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def render_reporte_diario(df_reclamos):
    """Renderiza en Streamlit el botón para descargar el reporte diario en PNG."""
    st.subheader("📊 Reporte Diario (Imagen PNG)")
    if df_reclamos.empty:
        st.warning("No hay datos para generar el reporte.")
        return

    buffer = generar_reporte_diario_imagen(df_reclamos)
    st.download_button(
        label="📥 Descargar Reporte Diario (PNG)",
        data=buffer,
        file_name=f"reporte_diario_{datetime.now().strftime('%Y%m%d')}.png",
        mime="image/png"
    )
