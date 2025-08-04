"""
Componente del dashboard de métricas optimizado
Versión 2.3 - Diseño responsive mejorado
"""
import streamlit as st
import pandas as pd
from datetime import datetime

def render_metrics_dashboard(df_reclamos, is_mobile=False):
    """Renderiza el dashboard de métricas optimizado para móvil/desktop"""
    try:
        if df_reclamos.empty:
            st.warning("No hay datos de reclamos para mostrar")
            return

        df_metricas = df_reclamos.copy()

        # Procesamiento de datos
        df_activos = df_metricas[df_metricas["Estado"].isin(["Pendiente", "En curso"])]
        total_activos = len(df_activos)
        pendientes = len(df_activos[df_activos["Estado"] == "Pendiente"])
        en_curso = len(df_activos[df_activos["Estado"] == "En curso"])
        resueltos = len(df_metricas[df_metricas["Estado"] == "Resuelto"])
        desconexiones = df_metricas["Estado"].str.strip().str.lower().eq("desconexión").sum()

        # Diseño responsive basado en is_mobile
        if is_mobile:
            # Diseño para móviles (2 columnas)
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📄 Activos", f"{total_activos}/{desconexiones}")
                st.metric("🔧 En curso", en_curso)
                
            with col2:
                st.metric("🕒 Pendientes", pendientes)
                st.metric("✅ Resueltos", resueltos)
        else:
            # Diseño para desktop (4 columnas)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 Activos", f"{total_activos}/{desconexiones}")
            with col2:
                st.metric("🕒 Pendientes", pendientes)
            with col3:
                st.metric("🔧 En curso", en_curso)
            with col4:
                st.metric("✅ Resueltos", resueltos)

    except Exception as e:
        st.error(f"Error al mostrar métricas: {str(e)}")
        if st.session_state.get('DEBUG_MODE', False):
            st.exception(e)