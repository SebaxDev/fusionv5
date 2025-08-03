# components/resumen_jornada.py

import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
from utils.date_utils import format_fecha

def render_resumen_jornada(df_reclamos):
    """Muestra el resumen de la jornada en el footer (versión mejorada)"""
    st.markdown("---")
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown("### 📋 Resumen de la jornada")

    try:
        # Procesamiento mejorado de fechas
        df_reclamos["Fecha y hora"] = pd.to_datetime(
            df_reclamos["Fecha y hora"],
            dayfirst=True,
            format='mixed',
            errors='coerce'
        )

        # Obtener fecha actual con zona horaria
        argentina = pytz.timezone("America/Argentina/Buenos_Aires")
        hoy = datetime.now(argentina).date()

        # Filtrar reclamos de hoy (comparando solo la parte de fecha)
        df_hoy = df_reclamos[
            df_reclamos["Fecha y hora"].dt.tz_localize(None).dt.date == hoy
        ].copy()

        # Reclamos en curso
        df_en_curso = df_reclamos[df_reclamos["Estado"] == "En curso"].copy()

        # Mostrar métricas
        col1, col2 = st.columns(2)
        col1.metric("📌 Reclamos cargados hoy", len(df_hoy))
        col2.metric("⚙️ Reclamos en curso", len(df_en_curso))

        # Técnicos por reclamo
        st.markdown("### 👷 Reclamos en curso por técnicos")

        if not df_en_curso.empty and "Técnico" in df_en_curso.columns:
            # Normalizar nombres y filtrar no vacíos
            df_en_curso["Técnico"] = df_en_curso["Técnico"].fillna("").astype(str)
            df_en_curso = df_en_curso[df_en_curso["Técnico"].str.strip() != ""]

            # Crear un set inmutable de técnicos asignados por reclamo
            df_en_curso["tecnicos_set"] = df_en_curso["Técnico"].apply(
                lambda x: tuple(sorted([t.strip().upper() for t in x.split(",") if t.strip()]))
            )

            # Agrupar por ese conjunto de técnicos
            conteo_grupos = df_en_curso.groupby("tecnicos_set").size().reset_index(name="Cantidad")

            # Mostrar estadísticas
            if not conteo_grupos.empty:
                st.markdown("#### Distribución de trabajo:")
                for fila in conteo_grupos.itertuples():
                    tecnicos = ", ".join(fila.tecnicos_set)
                    st.markdown(f"- 👥 **{tecnicos}**: {fila.Cantidad} reclamos")
                
                # Mostrar reclamos más antiguos pendientes
                reclamos_antiguos = df_en_curso.sort_values("Fecha y hora").head(3)
                if not reclamos_antiguos.empty:
                    st.markdown("#### ⏳ Reclamos más antiguos aún en curso:")
                    for _, row in reclamos_antiguos.iterrows():
                        fecha_formateada = format_fecha(row["Fecha y hora"])
                        st.markdown(
                            f"- **{row['Nombre']}** ({row['Nº Cliente']}) - " 
                            f"Desde: {fecha_formateada} - "
                            f"Técnicos: {row['Técnico']}"
                        )
            else:
                st.info("No hay técnicos asignados actualmente a reclamos en curso.")
        else:
            st.info("No hay reclamos en curso en este momento.")

        # Mostrar fecha y hora actual del sistema
        st.markdown(f"*Última actualización: {datetime.now(argentina).strftime('%d/%m/%Y %H:%M')}*")
        
        # Créditos (opcional)
        st.markdown("""
            <div style='text-align: center; margin-top: 20px; font-size: 0.9em; color: gray;'>
                © 2025 - Sistema de Gestión de Reclamos
            </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error al generar resumen: {str(e)}")
        if DEBUG_MODE:
            st.exception(e)
    finally:
        st.markdown('</div>', unsafe_allow_html=True)