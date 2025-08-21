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

    # MEJORAR: Incluir también reclamos resueltos sin fecha pero con estado "Resuelto"
    resueltos_hoy = df_reclamos[
        (df_reclamos['Estado'] == 'Resuelto') &
        (
            # Caso 1: Tiene fecha de hoy
            ((df_reclamos['Fecha_formateada'].notna()) &
             (df_reclamos['Fecha_formateada'].dt.date == hoy)) |
            # Caso 2: No tiene fecha pero está resuelto (asumimos hoy)
            (df_reclamos['Fecha_formateada'].isna())
        )
    ]

    # Agrupar por técnico - manejar casos donde Técnico podría estar vacío
    tecnicos_resueltos = (
        resueltos_hoy.groupby('Técnico')['Estado']
        .count()
        .reset_index()
        .sort_values(by='Estado', ascending=False)
    )

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
    
    # Hacer una copia para no modificar el original
    df_debug = df_reclamos.copy()
    
    # Convertir a datetime para el análisis
    df_debug["Fecha_formateada_dt"] = pd.to_datetime(
        df_debug["Fecha_formateada"], 
        errors="coerce", 
        dayfirst=True
    )
    
    st.write("**📊 ESTADÍSTICAS COMPLETAS:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total reclamos", len(df_debug))
        st.metric("Reclamos Resueltos", (df_debug['Estado'] == 'Resuelto').sum())
    
    with col2:
        st.metric("Con Fecha_formateada", df_debug['Fecha_formateada_dt'].notna().sum())
        st.metric("Resueltos con fecha", ((df_debug['Estado'] == 'Resuelto') & 
                                        df_debug['Fecha_formateada_dt'].notna()).sum())
    
    with col3:
        hoy = ahora_argentina().date()
        resueltos_hoy = df_debug[
            (df_debug['Estado'] == 'Resuelto') &
            (df_debug['Fecha_formateada_dt'].notna()) &
            (df_debug['Fecha_formateada_dt'].dt.date == hoy)
        ]
        st.metric("Resueltos HOY", len(resueltos_hoy))
    
    st.divider()
    
    # 1. MOSTRAR TODOS LOS TÉCNICOS CON RECLAMOS RESUELTOS (cualquier fecha)
    st.write("**👷 TODOS los técnicos con reclamos resueltos (histórico):**")
    todos_tecnicos_resueltos = df_debug[df_debug['Estado'] == 'Resuelto']['Técnico'].value_counts()
    if not todos_tecnicos_resueltos.empty:
        for tecnico, count in todos_tecnicos_resueltos.items():
            st.write(f"- {tecnico}: {count} resueltos (total histórico)")
    else:
        st.write("No hay técnicos con reclamos resueltos")
    
    st.divider()
    
    # 2. MOSTRAR RECLAMOS RESUELTOS HOY CON DETALLE
    hoy = ahora_argentina().date()
    resueltos_hoy = df_debug[
        (df_debug['Estado'] == 'Resuelto') &
        (df_debug['Fecha_formateada_dt'].notna()) &
        (df_debug['Fecha_formateada_dt'].dt.date == hoy)
    ]
    
    st.write(f"**✅ RECLAMOS RESUELTOS HOY ({len(resueltos_hoy)}):**")
    if not resueltos_hoy.empty:
        # Mostrar por técnico
        st.write("**Por técnico:**")
        tecnicos_count = resueltos_hoy['Técnico'].value_counts()
        for tecnico, count in tecnicos_count.items():
            st.write(f"- {tecnico}: {count} resueltos")
        
        # Mostrar tabla detallada
        st.write("**Detalle completo:**")
        st.dataframe(resueltos_hoy[['ID Reclamo', 'Técnico', 'Fecha_formateada', 
                                  'Fecha_formateada_dt', 'Tipo de reclamo', 'Sector']])
    else:
        st.write("No hay reclamos resueltos hoy")
        
        # Mostrar los últimos resueltos de cualquier fecha para debugging
        st.write("**Últimos 10 reclamos resueltos (cualquier fecha):**")
        ultimos_resueltos = df_debug[df_debug['Estado'] == 'Resuelto'].nlargest(10, 'Fecha_formateada_dt')
        st.dataframe(ultimos_resueltos[['ID Reclamo', 'Técnico', 'Fecha_formateada', 
                                      'Fecha_formateada_dt', 'Tipo de reclamo']])
    
    st.divider()
    
    # 3. PROBLEMAS COMUNES - VERIFICAR
    st.write("**🔍 PROBLEMAS COMUNES DETECTADOS:**")
    
    # Técnicos con reclamos resueltos pero sin fecha
    tecnicos_sin_fecha = df_debug[
        (df_debug['Estado'] == 'Resuelto') & 
        (df_debug['Fecha_formateada_dt'].isna())
    ]['Técnico'].unique()
    
    if len(tecnicos_sin_fecha) > 0:
        st.warning(f"⚠️ Técnicos con reclamos resueltos pero SIN FECHA: {', '.join(tecnicos_sin_fecha)}")
    
    # Fechas que no se pudieron parsear
    fechas_invalidas = df_debug[
        (df_debug['Estado'] == 'Resuelto') & 
        (df_debug['Fecha_formateada'].notna()) &
        (df_debug['Fecha_formateada_dt'].isna())
    ]
    if len(fechas_invalidas) > 0:
        st.warning(f"⚠️ {len(fechas_invalidas)} fechas no se pudieron parsear correctamente")
        st.dataframe(fechas_invalidas[['ID Reclamo', 'Técnico', 'Fecha_formateada']].head(5))
    
    # Reclamos resueltos con fecha pero no de hoy
    resueltos_otra_fecha = df_debug[
        (df_debug['Estado'] == 'Resuelto') &
        (df_debug['Fecha_formateada_dt'].notna()) &
        (df_debug['Fecha_formateada_dt'].dt.date != hoy)
    ]
    if len(resueltos_otra_fecha) > 0:
        st.info(f"ℹ️ {len(resueltos_otra_fecha)} reclamos resueltos en otras fechas (no hoy)")
        st.dataframe(resueltos_otra_fecha[['ID Reclamo', 'Técnico', 'Fecha_formateada_dt']].head(5))


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