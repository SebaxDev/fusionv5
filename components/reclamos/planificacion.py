# components/reclamos/planificacion.py

import io
import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from utils.date_utils import parse_fecha, format_fecha
from utils.api_manager import api_manager, batch_update_sheet
from utils.pdf_utils import agregar_pie_pdf
from config.settings import (
    SECTORES_DISPONIBLES,
    TECNICOS_DISPONIBLES,
    MATERIALES_POR_RECLAMO,
    ROUTER_POR_SECTOR
)

GRUPOS_POSIBLES = [f"Grupo {letra}" for letra in "ABCDE"]

def inicializar_estado_grupos():
    if "asignaciones_grupos" not in st.session_state:
        st.session_state.asignaciones_grupos = {g: [] for g in GRUPOS_POSIBLES}
    if "tecnicos_grupos" not in st.session_state:
        st.session_state.tecnicos_grupos = {g: [] for g in GRUPOS_POSIBLES}
    if "vista_simulacion" not in st.session_state:
        st.session_state.vista_simulacion = False
    if "simulacion_asignaciones" not in st.session_state:
        st.session_state.simulacion_asignaciones = {}

def distribuir_por_sector(df_reclamos, grupos_activos):
    grupos = GRUPOS_POSIBLES[:grupos_activos]
    asignaciones = {g: [] for g in grupos}
    sectores = [str(s) for s in range(1, 18)]
    sector_grupo_map = {s: grupos[i % grupos_activos] for i, s in enumerate(sectores)}
    for _, r in df_reclamos.iterrows():
        sector = str(r.get("Sector", "")).strip()
        grupo = sector_grupo_map.get(sector)
        if grupo:
            asignaciones[grupo].append(r["ID Reclamo"])
    return asignaciones

def _mostrar_asignacion_tecnicos(grupos_activos):
    """Muestra la interfaz para asignar técnicos a grupos"""
    st.markdown("### 👷 Asignar técnicos a cada grupo")
    for grupo in list(st.session_state.tecnicos_grupos.keys())[:grupos_activos]:
        st.session_state.tecnicos_grupos[grupo] = st.multiselect(
            f"{grupo} - Técnicos asignados",
            TECNICOS_DISPONIBLES,
            default=st.session_state.tecnicos_grupos[grupo],
            key=f"tecnicos_{grupo}"
        )

def distribuir_por_tipo(df_reclamos, grupos_activos):
    grupos = GRUPOS_POSIBLES[:grupos_activos]
    asignaciones = {g: [] for g in grupos}
    reclamos = df_reclamos.to_dict("records")
    reclamos_por_tipo = {}
    for r in reclamos:
        tipo = r.get("Tipo de reclamo", "Otro")
        reclamos_por_tipo.setdefault(tipo, []).append(r["ID Reclamo"])
    i = 0
    for tipo, ids in reclamos_por_tipo.items():
        for rid in ids:
            grupo = grupos[i % grupos_activos]
            asignaciones[grupo].append(rid)
            i += 1
    return asignaciones

def _limpiar_asignaciones(df_reclamos):
    ids_validos = set(df_reclamos["ID Reclamo"].astype(str).unique())
    for grupo in st.session_state.asignaciones_grupos:
        st.session_state.asignaciones_grupos[grupo] = [
            id for id in st.session_state.asignaciones_grupos[grupo] 
            if str(id) in ids_validos
        ]

def render_planificacion_grupos(df_reclamos, sheet_reclamos, user):
    if user.get('rol') != 'admin':
        st.warning("⚠️ Solo los administradores pueden acceder a esta sección")
        return {'needs_refresh': False}

    st.subheader("📋 Asignación de reclamos a grupos de trabajo")

    try:
        inicializar_estado_grupos()
        _limpiar_asignaciones(df_reclamos)

        grupos_activos = st.slider("🔢 Cantidad de grupos de trabajo activos", 1, 5, 2)

        modo_distribucion = st.selectbox(
            "📊 Elegí el modo de distribución",
            ["Manual", "Automática por sector", "Automática por tipo de reclamo"],
            index=0
        )

        if modo_distribucion != "Manual":
            if st.button("⚙️ Distribuir reclamos ahora"):
                if modo_distribucion == "Automática por sector":
                    st.session_state.simulacion_asignaciones = distribuir_por_sector(df_reclamos, grupos_activos)
                else:
                    st.session_state.simulacion_asignaciones = distribuir_por_tipo(df_reclamos, grupos_activos)

                st.session_state.vista_simulacion = True
                st.success("✅ Distribución previa generada. Revisala antes de guardar.")
                st.experimental_rerun()

        if st.session_state.get("vista_simulacion"):
            st.subheader("🗂️ Distribución previa de reclamos")
            for grupo, reclamos in st.session_state.simulacion_asignaciones.items():
                st.markdown(f"### 📦 {grupo} - {len(reclamos)} reclamos")
                for rid in reclamos:
                    row = df_reclamos[df_reclamos["ID Reclamo"] == rid]
                    if not row.empty:
                        r = row.iloc[0]
                        st.markdown(f"- {r['Nº Cliente']} | {r['Tipo de reclamo']} | Sector {r['Sector']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Generar PDF de esta distribución"):
                    _generar_pdf_asignaciones(
                        grupos_activos,
                        {},
                        df_reclamos[df_reclamos["ID Reclamo"].isin(
                            sum(st.session_state.simulacion_asignaciones.values(), [])
                        )]
                    )
            with col2:
                if st.button("💾 Confirmar y guardar esta asignación"):
                    st.session_state.asignaciones_grupos = st.session_state.simulacion_asignaciones
                    st.session_state.vista_simulacion = False
                    st.success("✅ Asignaciones aplicadas.")
                    st.experimental_rerun()

        if st.button("🔄 Refrescar reclamos"):
            st.cache_data.clear()
            return {'needs_refresh': True}

        _mostrar_asignacion_tecnicos(grupos_activos)
        df_pendientes = _mostrar_reclamos_disponibles(df_reclamos, grupos_activos)

        if df_pendientes is not None:
            materiales_por_grupo = _mostrar_reclamos_asignados(df_pendientes, grupos_activos)
            cambios = _mostrar_acciones_finales(
                df_reclamos, sheet_reclamos, 
                grupos_activos, materiales_por_grupo, df_pendientes
            )
            return {'needs_refresh': cambios}

        return {'needs_refresh': False}

    except Exception as e:
        st.error(f"❌ Error en la planificación: {str(e)}")
        if 'DEBUG_MODE' in globals() and DEBUG_MODE:
            st.exception(e)
        return {'needs_refresh': False}
