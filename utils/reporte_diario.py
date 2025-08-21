def generar_reporte_diario_imagen(df_reclamos):
    """Genera una imagen PNG con el reporte diario (últimas 24 h)."""
    import io
    from PIL import Image, ImageDraw, ImageFont
    import pandas as pd
    from utils.date_utils import ahora_argentina

    # ==== Copia segura y normalización de columnas ====
    df = df_reclamos.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Columnas clave (alias por si cambian mayúsculas/espacios)
    COL_INGRESO = next((c for c in df.columns if c.lower() == "fecha y hora"), "Fecha y hora")
    COL_CIERRE  = next((c for c in df.columns if c.lower() == "fecha_formateada"), "Fecha_formateada")
    COL_ESTADO  = next((c for c in df.columns if c.lower() == "estado"), "Estado")
    COL_TECNICO = next((c for c in df.columns if c.lower() == "técnico"), "Técnico")
    COL_TIPO    = next((c for c in df.columns if c.lower() == "tipo de reclamo"), "Tipo de reclamo")

    # Asegurar columnas presentes
    for col in (COL_INGRESO, COL_CIERRE, COL_ESTADO, COL_TECNICO, COL_TIPO):
        if col not in df.columns:
            df[col] = pd.NA

    # ==== Parseo de fechas (ingreso y cierre) ====
    # Ingreso (puede venir con strings varios)
    df[COL_INGRESO] = (
        df[COL_INGRESO]
        .astype(str).str.strip().replace({"", "nan", "NaN", "None": None})
    )
    df[COL_INGRESO] = pd.to_datetime(
        df[COL_INGRESO], errors="coerce", dayfirst=True, infer_datetime_format=True
    )
    # Si quedó con tz, la quitamos de forma segura
    if pd.api.types.is_datetime64tz_dtype(df[COL_INGRESO]):
        df[COL_INGRESO] = df[COL_INGRESO].dt.tz_localize(None)

    # Cierre (fecha de resolución)
    df[COL_CIERRE] = (
        df[COL_CIERRE]
        .astype(str).str.replace(r"\s+", " ", regex=True)  # colapsar dobles espacios
        .str.strip().replace({"", "nan", "NaN", "None": None})
    )
    df[COL_CIERRE] = pd.to_datetime(
        df[COL_CIERRE], errors="coerce", dayfirst=True, infer_datetime_format=True
    )
    if pd.api.types.is_datetime64tz_dtype(df[COL_CIERRE]):
        df[COL_CIERRE] = df[COL_CIERRE].dt.tz_localize(None)

    # Estado normalizado
    df[COL_ESTADO] = df[COL_ESTADO].astype(str).str.strip().str.lower()

    # Técnico / Tipo saneados para agrupar
    df[COL_TECNICO] = df[COL_TECNICO].fillna("Sin técnico").astype(str).str.strip()
    df[COL_TIPO] = df[COL_TIPO].fillna("Sin tipo").astype(str).str.strip()

    # ==== Ventana últimas 24 h ====
    ahora_ts = pd.Timestamp(ahora_argentina()).tz_localize(None)
    hace_24h = ahora_ts - pd.Timedelta(hours=24)

    # Ingresados últimas 24 h (por fecha de ingreso)
    mask_ing_24h = df[COL_INGRESO].notna() & (df[COL_INGRESO] >= hace_24h)
    total_ingresados_24h = int(mask_ing_24h.sum())

    # Resueltos últimas 24 h (por fecha de cierre)
    mask_res_24h = (
        (df[COL_ESTADO] == "resuelto")
        & df[COL_CIERRE].notna()
        & (df[COL_CIERRE] >= hace_24h)
    )
    resueltos_24h = df.loc[mask_res_24h, [COL_TECNICO, COL_ESTADO, COL_CIERRE]]

    # Agrupar resueltos por técnico
    tecnicos_resueltos = (
        resueltos_24h.groupby(COL_TECNICO)[COL_ESTADO]
        .count()
        .reset_index()
        .rename(columns={COL_ESTADO: "Cantidad"})
        .sort_values("Cantidad", ascending=False)
    )

    # Pendientes por tipo (estado == Pendiente)
    pendientes = df[df[COL_ESTADO] == "pendiente"]
    pendientes_tipo = (
        pendientes.groupby(COL_TIPO)[COL_ESTADO]
        .count()
        .reset_index()
        .rename(columns={COL_ESTADO: "Cantidad", COL_TIPO: "Tipo"})
        .sort_values("Cantidad", ascending=False)
    )
    total_pendientes = int(len(pendientes))

    # ==== Render de imagen ====
    WIDTH, HEIGHT = 1200, 1600
    BG_COLOR = (39, 40, 34)
    TEXT_COLOR = (248, 248, 242)
    HIGHLIGHT_COLOR = (249, 38, 114)

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
            line(f"{r[COL_TECNICO]}: {int(r['Cantidad'])} resueltos (24h)", font_txt, TEXT_COLOR, line_h)

    line("", font_txt, TEXT_COLOR, line_h // 2)

    line(f"■ Quedan pendientes: {total_pendientes}", font_sub, HIGHLIGHT_COLOR, line_h)
    if pendientes_tipo.empty:
        line("Sin pendientes", font_txt, TEXT_COLOR, line_h)
    else:
        for _, r in pendientes_tipo.iterrows():
            line(f"{r['Tipo']}: {int(r['Cantidad'])}", font_txt, TEXT_COLOR, line_h)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

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