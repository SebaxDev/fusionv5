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
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_subtitle = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        font_text = ImageFont.truetype("DejaVuSans.ttf", 24)
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

    # Asegurar que la columna Fecha_formateada (columna M) sea datetime
    if "Fecha_formateada" in df_reclamos.columns:
        df_reclamos["Fecha_formateada"] = pd.to_datetime(
            df_reclamos["Fecha_formateada"], 
            errors="coerce", 
            dayfirst=True
        )
    else:
        # Si no existe la columna, crear una vacía
        df_reclamos["Fecha_formateada"] = pd.NaT

    # Reclamos ingresados hoy
    hoy = ahora_argentina().date()
    reclamos_hoy = df_reclamos[df_reclamos['Fecha y hora'].dt.date == hoy]
    total_hoy = len(reclamos_hoy)

    # Reclamos resueltos por técnico/grupo basados en la fecha de cierre HOY
    # Obtener el inicio y fin del día en Argentina timezone
    inicio_dia = ahora_argentina().replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia = inicio_dia.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    resueltos_hoy = df_reclamos[
        (df_reclamos['Fecha_formateada'].notna()) &
        (df_reclamos['Fecha_formateada'].dt.date == hoy) &
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


def debug_fechas_cierre(df_reclamos):
    """Función para debuggear problemas con fechas de cierre"""
    st.subheader("🔍 Debug - Fechas de Cierre (Fecha_formateada)")
    
    if "Fecha_formateada" not in df_reclamos.columns:
        st.warning("No existe la columna 'Fecha_formateada'")
        return
    
    # Convertir a datetime para el análisis
    df_reclamos["Fecha_formateada_dt"] = pd.to_datetime(
        df_reclamos["Fecha_formateada"], 
        errors="coerce", 
        dayfirst=True
    )
    
    st.write("**Muestra de fechas de cierre:**")
    st.dataframe(df_reclamos[['ID Reclamo', 'Estado', 'Técnico', 'Fecha_formateada', 'Fecha_formateada_dt']].head(10))
    
    st.write("**Estadísticas:**")
    st.write(f"Total reclamos: {len(df_reclamos)}")
    st.write(f"Reclamos con Fecha_formateada no nula: {df_reclamos['Fecha_formateada_dt'].notna().sum()}")
    st.write(f"Reclamos Resueltos: {(df_reclamos['Estado'] == 'Resuelto').sum()}")
    
    # Reclamos resueltos hoy
    hoy = ahora_argentina().date()
    resueltos_hoy = df_reclamos[
        (df_reclamos['Estado'] == 'Resuelto') &
        (df_reclamos['Fecha_formateada_dt'].notna()) &
        (df_reclamos['Fecha_formateada_dt'].dt.date == hoy)
    ]
    
    st.write(f"Reclamos resueltos hoy: {len(resueltos_hoy)}")
    if not resueltos_hoy.empty:
        st.dataframe(resueltos_hoy[['ID Reclamo', 'Técnico', 'Fecha_formateada', 'Fecha_formateada_dt']])
        
        # Mostrar por técnico
        st.write("**Resueltos por técnico hoy:**")
        tecnicos_count = resueltos_hoy['Técnico'].value_counts()
        for tecnico, count in tecnicos_count.items():
            st.write(f"- {tecnico}: {count} resueltos")
    else:
        st.write("**Últimos 5 reclamos resueltos (de cualquier fecha):**")
        ultimos_resueltos = df_reclamos[df_reclamos['Estado'] == 'Resuelto'].nlargest(5, 'Fecha_formateada_dt')
        st.dataframe(ultimos_resueltos[['ID Reclamo', 'Técnico', 'Fecha_formateada', 'Fecha_formateada_dt']])


def render_reporte_diario(df_reclamos):
    """Renderiza en Streamlit el botón para descargar el reporte diario en PNG."""
    st.subheader("📊 Reporte Diario (Imagen PNG)")
    
    # Botón de debug
    if st.button("🔍 Debug Fechas Cierre"):
        debug_fechas_cierre(df_reclamos)
    
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