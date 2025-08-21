import io
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from utils.date_utils import ahora_argentina

def generar_reporte_diario_imagen(df_reclamos):
    """
    Genera una imagen PNG con el reporte diario (últimas 24 h).
    - Usa 'Fecha y hora' para ingresados en 24h.
    - Usa 'Fecha_formateada' para resueltos en 24h.
    - Limpia strings raros, quita TZ si existiera y normaliza 'Estado'.
    """
    # ====== Config de imagen ======
    WIDTH, HEIGHT = 1200, 1600
    BG_COLOR = (39, 40, 34)
    TEXT_COLOR = (248, 248, 242)
    HIGHLIGHT_COLOR = (249, 38, 114)

    # ====== Copia y normalización de columnas ======
    df = df_reclamos.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Asegurar columnas clave
    for col in ["Fecha y hora", "Fecha_formateada", "Estado", "Técnico", "Tipo de reclamo"]:
        if col not in df.columns:
            df[col] = pd.NA

    # --- Helper: parseo de fechas seguro ---
    def _to_datetime_clean(series):
        s = series.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
        s = s.replace({"", "nan", "NaN", "None": None})
        out = pd.to_datetime(s, errors="coerce", dayfirst=True, infer_datetime_format=True)
        # si quedó con tz, quitarla SOLO si realmente es tz-aware
        if pd.api.types.is_datetime64tz_dtype(out):
            out = out.dt.tz_localize(None)
        return out

    # Parseo ingreso/cierre
    df["Fecha y hora"] = _to_datetime_clean(df["Fecha y hora"])
    df["Fecha_formateada"] = _to_datetime_clean(df["Fecha_formateada"])

    # Normalizar estado
    df["Estado"] = df["Estado"].astype(str).str.strip().str.lower()

    # Saneos mínimos para agrupar
    df["Técnico"] = df["Técnico"].fillna("Sin técnico").astype(str).str.strip()
    df["Tipo de reclamo"] = df["Tipo de reclamo"].fillna("Sin tipo").astype(str).str.strip()

    # ====== Ventana últimas 24h ======
    ahora_ts = pd.Timestamp(ahora_argentina()).tz_localize(None)  # naive
    hace_24h = ahora_ts - pd.Timedelta(hours=24)

    # Ingresados (por fecha de ingreso)
    mask_ing_24h = df["Fecha y hora"].notna() & (df["Fecha y hora"] >= hace_24h)
    total_ingresados_24h = int(mask_ing_24h.sum())

    # Resueltos (por fecha de cierre)
    mask_res_24h = (
        (df["Estado"] == "resuelto") &
        df["Fecha_formateada"].notna() &
        (df["Fecha_formateada"] >= hace_24h)
    )
    resueltos_24h = df.loc[mask_res_24h, ["Técnico", "Estado", "Fecha_formateada"]]

    # Agrupar resueltos por técnico
    tecnicos_resueltos = (
        resueltos_24h.groupby("Técnico")["Estado"]
        .count()
        .reset_index()
        .rename(columns={"Estado": "Cantidad"})
        .sort_values("Cantidad", ascending=False)
    )

    # Pendientes por tipo
    pendientes = df[df["Estado"] == "pendiente"]
    pendientes_tipo = (
        pendientes.groupby("Tipo de reclamo")["Estado"]
        .count()
        .reset_index()
        .rename(columns={"Estado": "Cantidad", "Tipo de reclamo": "Tipo"})
        .sort_values("Cantidad", ascending=False)
    )
    total_pendientes = int(len(pendientes))

    # ====== Render de imagen ======
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_sub = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        font_txt = ImageFont.truetype("DejaVuSans.ttf", 24)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_txt = ImageFont.load_default()

    y = 50
    line_h = 40

    def line(text, font, color, dy):
        nonlocal y
        draw.text((50, y), str(text), font=font, fill=color)
        y += dy

    fecha_str = ahora_ts.strftime("%d/%m/%Y")
    hora_str = ahora_ts.strftime("%H:%M")

    line(f"■ Reporte Diario - {fecha_str}", font_title, HIGHLIGHT_COLOR, line_h)
    line(f"Generado a las {hora_str}", font_sub, TEXT_COLOR, line_h)
    line("", font_txt, TEXT_COLOR, line_h // 2)

    line(f"■ Reclamos ingresados (24h): {total_ingresados_24h}", font_sub, HIGHLIGHT_COLOR, line_h)
    line("", font_txt, TEXT_COLOR, line_h // 2)

    line("■ Reporte técnico/grupo (24h):", font_sub, HIGHLIGHT_COLOR, line_h)
    if tecnicos_resueltos.empty:
        line("No hay reclamos resueltos en las últimas 24h", font_txt, TEXT_COLOR, line_h)
    else:
        for _, r in tecnicos_resueltos.iterrows():
            line(f"{r['Técnico']}: {int(r['Cantidad'])} resueltos (24h)", font_txt, TEXT_COLOR, line_h)

    line("", font_txt, TEXT_COLOR, line_h // 2)

    line(f"■ Quedan pendientes: {total_pendientes}", font_sub, HIGHLIGHT_COLOR, line_h)
    if pendientes_tipo.empty:
        line("Sin pendientes", font_txt, TEXT_COLOR, line_h)
    else:
        for _, r in pendientes_tipo.iterrows():
            line(f"{r['Tipo']}: {int(r['Cantidad'])}", font_txt, TEXT_COLOR, line_h)

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