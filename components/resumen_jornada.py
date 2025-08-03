# components/resumen_jornada.py
import pandas as pd
import pytz
from datetime import datetime
import streamlit as st

def render_resumen_jornada(df_reclamos):
    """Muestra el resumen de la jornada en el footer"""
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown("### 📋 Resumen de la jornada")

    # Procesamiento de fechas
    df_reclamos["Fecha y hora"] = pd.to_datetime(
        df_reclamos["Fecha y hora"],
        dayfirst=True,
        format='mixed',
        errors='coerce'
    )

    argentina = pytz.timezone("America/Argentina/Buenos_Aires")
    hoy = datetime.now(argentina).date()

    df_hoy = df_reclamos[
        df_reclamos["Fecha y hora"].dt.tz_localize(None).dt.date == hoy
    ].copy()

    df_en_curso = df_reclamos[df_reclamos["Estado"] == "En curso"].copy()

    # Métricas del día
    col1, col2 = st.columns(2)
    col1.metric("📌 Reclamos cargados hoy", len(df_hoy))
    col2.metric("⚙️ Reclamos en curso", len(df_en_curso))

    # Distribución de trabajo
    _mostrar_distribucion_trabajo(df_en_curso)
    
    # Créditos
    _mostrar_creditos(argentina)

    st.markdown('</div>', unsafe_allow_html=True)

def _mostrar_distribucion_trabajo(df_en_curso):
    """Muestra la distribución de trabajo por técnico"""
    if not df_en_curso.empty and "Técnico" in df_en_curso.columns:
        df_en_curso["Técnico"] = df_en_curso["Técnico"].fillna("").astype(str)
        df_en_curso = df_en_curso[df_en_curso["Técnico"].str.strip() != ""]

        # CORRECCIÓN: Añadí el paréntesis que faltaba en esta línea
        df_en_curso["tecnicos_set"] = df_en_curso["Técnico"].apply(
            lambda x: tuple(sorted([t.strip().upper() for t in x.split(",") if t.strip()]))
        
        conteo_grupos = df_en_curso.groupby("tecnicos_set").size().reset_index(name="Cantidad")

        if not conteo_grupos.empty:
            st.markdown("#### 👷 Distribución por técnicos:")
            for fila in conteo_grupos.itertuples():
                tecnicos = ", ".join(fila.tecnicos_set)
                st.markdown(f"- **{tecnicos}**: {fila.Cantidad} reclamos")

def _mostrar_creditos(argentina):
    """Muestra los créditos y última actualización"""
    st.markdown(f"*Última actualización: {datetime.now(argentina).strftime('%d/%m/%Y %H:%M')}*")
    st.markdown("""
        <div style='text-align: center; margin-top: 20px; font-size: 0.9em; color: gray;'>
            © 2025 - Hecho con amor por: 
            <a href="https://instagram.com/mellamansebax" target="_blank" 
               style="text-decoration: none; color: inherit; font-weight: bold;">
                Sebastián Andrés
            </a> 💜
        </div>
    """, unsafe_allow_html=True)