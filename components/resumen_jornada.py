# components/resumen_jornada.py
import pandas as pd
import pytz
from datetime import datetime
import streamlit as st

def render_resumen_jornada(df_reclamos):
    """Muestra el resumen de la jornada en el footer"""
    try:
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        st.markdown("### 📋 Resumen de la jornada")

        # Procesamiento básico de fechas
        if not df_reclamos.empty and "Fecha y hora" in df_reclamos.columns:
            df_reclamos["Fecha y hora"] = pd.to_datetime(
                df_reclamos["Fecha y hora"],
                dayfirst=True,
                errors='coerce'
            )
            
            hoy = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires")).date()
            df_hoy = df_reclamos[df_reclamos["Fecha y hora"].dt.date == hoy]
        else:
            df_hoy = pd.DataFrame()

        # Métricas básicas
        col1, col2 = st.columns(2)
        col1.metric("📌 Reclamos cargados hoy", len(df_hoy))
        
        if not df_reclamos.empty and "Estado" in df_reclamos.columns:
            en_curso = len(df_reclamos[df_reclamos["Estado"] == "En curso"])
            col2.metric("⚙️ Reclamos en curso", en_curso)
        else:
            col2.metric("⚙️ Reclamos en curso", 0)

        # Créditos
        st.markdown(f"*Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
        st.markdown("""
            <div style='text-align: center; margin-top: 20px; font-size: 0.9em; color: gray;'>
                © 2025 - Sistema de Gestión de Reclamos
            </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error al generar resumen: {str(e)}")