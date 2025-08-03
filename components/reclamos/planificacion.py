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

def inicializar_estado_grupos():
    """Inicializa el estado de los grupos en session_state"""
    defaults = {
        "asignaciones_grupos": {
            "Grupo A": [], "Grupo B": [], "Grupo C": [], "Grupo D": []
        },
        "tecnicos_grupos": {
            "Grupo A": [], "Grupo B": [], "Grupo C": [], "Grupo D": []
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def _limpiar_asignaciones(df_reclamos):
    """Limpia asignaciones de reclamos que ya no existen"""
    ids_validos = set(df_reclamos["ID Reclamo"].astype(str).unique())
    for grupo in st.session_state.asignaciones_grupos:
        st.session_state.asignaciones_grupos[grupo] = [
            id for id in st.session_state.asignaciones_grupos[grupo] 
            if str(id) in ids_validos
        ]

def render_planificacion_grupos(df_reclamos, sheet_reclamos, user):
    """
    Muestra la sección de planificación de grupos de trabajo
    
    Args:
        df_reclamos (pd.DataFrame): DataFrame con los reclamos
        sheet_reclamos: Objeto de conexión a la hoja de reclamos
        user (dict): Información del usuario actual
    
    Returns:
        dict: Diccionario con flags de estado (needs_refresh)
    """
    if user.get('rol') != 'admin':
        st.warning("⚠️ Solo los administradores pueden acceder a esta sección")
        return {'needs_refresh': False}

    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("📋 Asignación de reclamos a grupos de trabajo")

    try:
        inicializar_estado_grupos()
        _limpiar_asignaciones(df_reclamos)
        
        if st.button("🔄 Refrescar reclamos"):
            st.cache_data.clear()
            return {'needs_refresh': True}

        grupos_activos = st.slider(
            "🔢 Cantidad de grupos de trabajo activos", 
            1, 4, 2
        )

        _mostrar_asignacion_tecnicos(grupos_activos)
        df_pendientes = _mostrar_reclamos_disponibles(df_reclamos, grupos_activos)
        
        if df_pendientes is not None:
            materiales_por_grupo = _mostrar_reclamos_asignados(df_pendientes, grupos_activos)
            cambios = _mostrar_acciones_finales(
                df_reclamos, sheet_reclamos, 
                grupos_activos, materiales_por_grupo
            )
            
            return {'needs_refresh': cambios}

        return {'needs_refresh': False}

    except Exception as e:
        st.error(f"❌ Error en la planificación: {str(e)}")
        if DEBUG_MODE:
            st.exception(e)
        return {'needs_refresh': False}
    finally:
        st.markdown('</div>', unsafe_allow_html=True)

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

def _mostrar_reclamos_disponibles(df_reclamos, grupos_activos):
    """Muestra reclamos disponibles para asignar"""
    st.markdown("---")
    st.markdown("### 📋 Reclamos pendientes para asignar")

    # Preparar datos
    df_reclamos.columns = df_reclamos.columns.str.strip()
    df_reclamos["ID Reclamo"] = df_reclamos["ID Reclamo"].astype(str).str.strip()
    df_reclamos["Fecha y hora"] = pd.to_datetime(
        df_reclamos["Fecha y hora"], 
        dayfirst=True, 
        errors='coerce'
    )

    # Asegurar que no haya IDs vacíos
    df_reclamos["ID Reclamo"] = df_reclamos["ID Reclamo"].replace('', pd.NA)
    df_reclamos["ID Reclamo"] = df_reclamos["ID Reclamo"].fillna(
        "temp_" + pd.Series(range(len(df_reclamos))).astype(str))
    
    df_pendientes = df_reclamos[df_reclamos["Estado"] == "Pendiente"].copy()

    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        filtro_sector = st.selectbox(
            "Filtrar por sector", 
            ["Todos"] + sorted(SECTORES_DISPONIBLES),
            format_func=lambda x: f"Sector {x}" if x != "Todos" else x
        )
    with col2:
        filtro_tipo = st.selectbox(
            "Filtrar por tipo de reclamo", 
            ["Todos"] + sorted(df_pendientes["Tipo de reclamo"].dropna().unique())
        )

    # Aplicar filtros
    if filtro_sector != "Todos":
        df_pendientes = df_pendientes[df_pendientes["Sector"] == str(filtro_sector)]
    if filtro_tipo != "Todos":
        df_pendientes = df_pendientes[df_pendientes["Tipo de reclamo"] == filtro_tipo]

    # Ordenamiento
    orden = st.selectbox(
        "🔃 Ordenar reclamos por:", 
        ["Fecha más reciente", "Sector", "Tipo de reclamo"]
    )
    
    if orden == "Fecha más reciente":
        df_pendientes = df_pendientes.sort_values("Fecha y hora", ascending=False)
    elif orden == "Sector":
        df_pendientes = df_pendientes.sort_values("Sector")
    elif orden == "Tipo de reclamo":
        df_pendientes = df_pendientes.sort_values("Tipo de reclamo")

    # Mostrar reclamos disponibles
    asignados = [
        r for reclamos in st.session_state.asignaciones_grupos.values() 
        for r in reclamos
    ]
    df_disponibles = df_pendientes[~df_pendientes["ID Reclamo"].isin(asignados)]

    for idx, row in df_disponibles.iterrows():
        with st.container():
            col1, *cols_grupo = st.columns([4] + [1]*grupos_activos)
            fecha_formateada = _format_fecha_reclamo(row["Fecha y hora"])
            resumen = f"📍 Sector {row['Sector']} - {row['Tipo de reclamo'].capitalize()} - {fecha_formateada}"
            col1.markdown(f"**{resumen}**")

            for i, grupo in enumerate(["Grupo A", "Grupo B", "Grupo C", "Grupo D"][:grupos_activos]):
                tecnicos = st.session_state.tecnicos_grupos[grupo]
                tecnicos_str = ", ".join(tecnicos[:2]) + ("..." if len(tecnicos) > 2 else "") if tecnicos else "Sin técnicos"
                
                # Clave única para cada botón
                button_key = f"asignar_{grupo}_{row['ID Reclamo']}_{idx}"
                
                if cols_grupo[i].button(
                    f"➡️{grupo[-1]} ({tecnicos_str})", 
                    key=button_key
                ):
                    if row["ID Reclamo"] not in asignados:
                        st.session_state.asignaciones_grupos[grupo].append(row["ID Reclamo"])
                        st.rerun()

            with col1.expander("🔍 Ver detalles"):
                _mostrar_detalles_reclamo(row)

        st.divider()

    return df_pendientes

def _format_fecha_reclamo(fecha):
    """Formatea la fecha del reclamo para visualización"""
    if pd.isna(fecha): 
        return "Sin fecha"
    try: 
        return fecha.strftime('%d/%m/%Y')
    except: 
        return "Fecha inválida"

def _mostrar_detalles_reclamo(reclamo):
    """Muestra los detalles de un reclamo"""
    st.markdown(f"""
    **🔢 Nº Cliente:** {reclamo['Nº Cliente']}  
    **👤 Nombre:** {reclamo['Nombre']}  
    **📍 Dirección:** {reclamo['Dirección']}  
    **📞 Teléfono:** {reclamo['Teléfono']}  
    **📅 Fecha completa:** {reclamo['Fecha y hora'].strftime('%d/%m/%Y %H:%M') if not pd.isna(reclamo['Fecha y hora']) else 'Sin fecha'}  
    """)
    if reclamo.get("Detalles"):
        st.markdown(f"**📝 Detalles:** {reclamo['Detalles'][:250]}{'...' if len(reclamo['Detalles']) > 250 else ''}")

def _mostrar_reclamos_asignados(df_pendientes, grupos_activos):
    """Muestra los reclamos asignados por grupo"""
    st.markdown("---")
    st.markdown("### 📌 Reclamos asignados por grupo")

    materiales_por_grupo = {}

    for grupo in ["Grupo A", "Grupo B", "Grupo C", "Grupo D"][:grupos_activos]:
        reclamos_ids = st.session_state.asignaciones_grupos[grupo]
        tecnicos = st.session_state.tecnicos_grupos[grupo]
        
        st.markdown(f"#### 🔢 {grupo} - Técnicos: {', '.join(tecnicos) if tecnicos else 'Sin asignar'} ({len(reclamos_ids)} reclamos)")

        reclamos_grupo = df_pendientes[df_pendientes["ID Reclamo"].isin(reclamos_ids)]

        # Resumen de tipos y sectores
        if not reclamos_grupo.empty:
            resumen_tipos = " - ".join([f"{v} {k}" for k, v in reclamos_grupo["Tipo de reclamo"].value_counts().items()])
            sectores = ", ".join(sorted(set(reclamos_grupo["Sector"].astype(str))))
            st.markdown(resumen_tipos)
            st.markdown(f"Sectores: {sectores}")

        # Calcular materiales necesarios
        materiales_total = _calcular_materiales_grupo(reclamos_grupo)
        materiales_por_grupo[grupo] = materiales_total

        if materiales_total:
            st.markdown("🛠️ **Materiales mínimos estimados:**")
            for mat, cant in materiales_total.items():
                st.markdown(f"- {cant} {mat.replace('_', ' ').title()}")

        # Mostrar reclamos asignados
        for idx, reclamo_id in enumerate(reclamos_ids):
            reclamo_data = df_pendientes[df_pendientes["ID Reclamo"] == reclamo_id]
            col1, col2 = st.columns([5, 1])
            
            if not reclamo_data.empty:
                row = reclamo_data.iloc[0]
                fecha_formateada = _format_fecha_reclamo(row["Fecha y hora"])
                resumen = f"📍 Sector {row['Sector']} - {row['Tipo de reclamo'].capitalize()} - {fecha_formateada}"
                col1.markdown(f"**{resumen}**")
            else:
                col1.markdown(f"**Reclamo ID: {reclamo_id} (ya no está pendiente)**")

            # Clave única para el botón de quitar
            if col2.button("❌ Quitar", key=f"quitar_{grupo}_{reclamo_id}_{idx}"):
                st.session_state.asignaciones_grupos[grupo].remove(reclamo_id)
                st.rerun()
            
            st.divider()

    return materiales_por_grupo

def _calcular_materiales_grupo(reclamos_grupo):
    """Calcula los materiales necesarios para un grupo de trabajo"""
    materiales_total = {}
    
    for _, row in reclamos_grupo.iterrows():
        tipo = row["Tipo de reclamo"]
        sector = str(row["Sector"])
        materiales_tipo = MATERIALES_POR_RECLAMO.get(tipo, {})
        
        for mat, cant in materiales_tipo.items():
            key = mat
            if "router" in mat:
                marca = ROUTER_POR_SECTOR.get(sector, "vsol")
                key = f"router_{marca}"
            materiales_total[key] = materiales_total.get(key, 0) + cant
    
    return materiales_total

def _mostrar_acciones_finales(df_reclamos, sheet_reclamos, grupos_activos, materiales_por_grupo):
    """Muestra botones de acción final y maneja su lógica"""
    st.markdown("---")
    cambios = False
    
    col1, col2 = st.columns(2)
    
    if col1.button("💾 Guardar cambios y pasar a 'En curso'", use_container_width=True):
        cambios = _guardar_cambios(df_reclamos, sheet_reclamos, grupos_activos)
    
    if col2.button("📄 Generar PDF de asignaciones por grupo", use_container_width=True):
        _generar_pdf_asignaciones(grupos_activos, materiales_por_grupo, df_pendientes)
    
    return cambios

def _guardar_cambios(df_reclamos, sheet_reclamos, grupos_activos):
    """Guarda los cambios en la hoja de cálculo"""
    errores = []
    for grupo in ["Grupo A", "Grupo B", "Grupo C", "Grupo D"][:grupos_activos]:
        if (st.session_state.asignaciones_grupos[grupo] and 
            not st.session_state.tecnicos_grupos[grupo]):
            errores.append(grupo)

    if errores:
        st.warning(f"⚠️ Los siguientes grupos tienen reclamos asignados pero sin técnicos: {', '.join(errores)}")
        return False

    with st.spinner("Actualizando reclamos..."):
        updates = []
        for grupo in ["Grupo A", "Grupo B", "Grupo C", "Grupo D"][:grupos_activos]:
            tecnicos = st.session_state.tecnicos_grupos[grupo]
            tecnicos_str = ", ".join(tecnicos).upper() if tecnicos else ""
            
            for reclamo_id in st.session_state.asignaciones_grupos[grupo]:
                fila = df_reclamos[df_reclamos["ID Reclamo"] == reclamo_id]
                
                if not fila.empty:
                    index = fila.index[0] + 2
                    updates.append({"range": f"I{index}", "values": [["En curso"]]})
                    updates.append({"range": f"J{index}", "values": [[tecnicos_str]]})
                else:
                    st.warning(f"⚠️ Reclamo con ID {reclamo_id} no encontrado en la hoja.")

        if updates:
            success, error = api_manager.safe_sheet_operation(
                batch_update_sheet, 
                sheet_reclamos, 
                updates, 
                is_batch=True
            )
            
            if success:
                st.success("✅ Reclamos actualizados correctamente en la hoja.")
                return True
            else:
                st.error("❌ Error al actualizar: " + str(error))
    
    return False

def _generar_pdf_asignaciones(grupos_activos, materiales_por_grupo, df_pendientes):
    """Genera un PDF con las asignaciones de grupos"""
    with st.spinner("Generando PDF..."):
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 40
        hoy = datetime.now().strftime('%d/%m/%Y')

        for grupo in ["Grupo A", "Grupo B", "Grupo C", "Grupo D"][:grupos_activos]:
            reclamos_ids = st.session_state.asignaciones_grupos[grupo]
            
            if not reclamos_ids:
                continue

            tecnicos = st.session_state.tecnicos_grupos[grupo]
            agregar_pie_pdf(c, width, height)
            c.showPage()
            y = height - 40

            # Encabezado del grupo
            tipos = df_pendientes[df_pendientes["ID Reclamo"].isin(reclamos_ids)]["Tipo de reclamo"].value_counts()
            resumen_tipos = " - ".join([f"{v} {k}" for k, v in tipos.items()])

            c.setFont("Helvetica-Bold", 16)
            c.drawString(40, y, f"{grupo} - Técnicos: {', '.join(tecnicos)} (Asignado el {hoy})")
            y -= 20
            c.setFont("Helvetica", 12)
            c.drawString(40, y, resumen_tipos)
            y -= 25

            # Detalles de cada reclamo
            for reclamo_id in reclamos_ids:
                reclamo_data = df_pendientes[df_pendientes["ID Reclamo"] == reclamo_id]
                
                if not reclamo_data.empty:
                    reclamo = reclamo_data.iloc[0]
                    c.setFont("Helvetica-Bold", 14)
                    c.drawString(40, y, f"{reclamo['Nº Cliente']} - {reclamo['Nombre']}")
                    y -= 15
                    c.setFont("Helvetica", 11)

                    fecha_pdf = _format_fecha_pdf(reclamo["Fecha y hora"])
                    lineas = [
                        f"Fecha: {fecha_pdf}",
                        f"Dirección: {reclamo['Dirección']} - Tel: {reclamo['Teléfono']}",
                        f"Sector: {reclamo['Sector']} - Precinto: {reclamo.get('Nº de Precinto', 'N/A')}",
                        f"Tipo: {reclamo['Tipo de reclamo']}",
                        f"Detalles: {reclamo['Detalles'][:100]}..." if len(reclamo['Detalles']) > 100 
                        else f"Detalles: {reclamo['Detalles']}",
                    ]
                    
                    for linea in lineas:
                        c.drawString(40, y, linea)
                        y -= 12

                    y -= 8
                    c.line(40, y, width - 40, y)
                    y -= 15

                    if y < 100:
                        agregar_pie_pdf(c, width, height)
                        c.showPage()
                        y = height - 40
                        c.setFont("Helvetica-Bold", 16)
                        c.drawString(40, y, f"{grupo} (cont.)")
                        y -= 25

            # Materiales necesarios
            materiales = materiales_por_grupo.get(grupo, {})
            if materiales:
                y -= 10
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y, "Materiales mínimos estimados:")
                y -= 15
                c.setFont("Helvetica", 11)
                
                for mat, cant in materiales.items():
                    c.drawString(40, y, f"- {cant} {mat.replace('_', ' ').title()}")
                    y -= 12

            y -= 20

        agregar_pie_pdf(c, width, height)
        c.save()
        buffer.seek(0)

        st.download_button(
            label="📄 Descargar PDF de asignaciones",
            data=buffer,
            file_name="asignaciones_grupos.pdf",
            mime="application/pdf"
        )

def _format_fecha_pdf(fecha):
    """Formatea la fecha para el PDF"""
    if pd.isna(fecha):
        return "Sin fecha"
    return fecha.strftime('%d/%m/%Y %H:%M')