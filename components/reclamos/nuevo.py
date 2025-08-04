# components/reclamos/nuevo.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.date_utils import ahora_argentina, format_fecha, parse_fecha
from utils.api_manager import api_manager
from utils.data_manager import batch_update_sheet
from config.settings import (
    SECTORES_DISPONIBLES,
    TIPOS_RECLAMO,
    DEBUG_MODE
)

def generar_id_unico():
    """Genera un ID único para reclamos"""
    import uuid
    return str(uuid.uuid4())[:8].upper()

def render_nuevo_reclamo(df_reclamos, df_clientes, sheet_reclamos, sheet_clientes, current_user=None):
    """
    Muestra la sección para cargar nuevos reclamos
    
    Args:
        df_reclamos (pd.DataFrame): DataFrame con los reclamos existentes
        df_clientes (pd.DataFrame): DataFrame con los clientes registrados
        sheet_reclamos: Objeto de conexión a la hoja de reclamos
        sheet_clientes: Objeto de conexión a la hoja de clientes
        current_user (str, optional): Usuario actual. Defaults to None.
    
    Returns:
        dict: Diccionario con estados de operación {
            'reclamo_guardado': bool,
            'cliente_nuevo': bool
        }
    """
    st.subheader("📝 Cargar nuevo reclamo")

    # Estado inicial
    estado = {
        'nro_cliente': '',
        'cliente_existente': None,
        'formulario_bloqueado': False,
        'reclamo_guardado': False,
        'cliente_nuevo': False,
        'actualizar_datos_cliente': False
    }

    estado['nro_cliente'] = st.text_input("🔢 N° de Cliente", placeholder="Ingresa el número de cliente").strip()

    if "Nº Cliente" in df_clientes.columns and estado['nro_cliente']:
        df_clientes["Nº Cliente"] = df_clientes["Nº Cliente"].astype(str).str.strip()
        df_reclamos["Nº Cliente"] = df_reclamos["Nº Cliente"].astype(str).str.strip()

        match = df_clientes[df_clientes["Nº Cliente"] == estado['nro_cliente']]
        df_reclamos["Fecha y hora"] = df_reclamos["Fecha y hora"].apply(parse_fecha)

        reclamos_activos = df_reclamos[
            (df_reclamos["Nº Cliente"] == estado['nro_cliente']) &
            (
                df_reclamos["Estado"].str.strip().str.lower().isin(["pendiente", "en curso"]) |
                (df_reclamos["Tipo de reclamo"].str.strip().str.lower() == "desconexion a pedido")
            )
        ]

        if not match.empty:
            estado['cliente_existente'] = match.iloc[0].to_dict()
            st.success("✅ Cliente reconocido, datos auto-cargados.")
        else:
            st.info("ℹ️ Cliente no encontrado. Se cargará como Cliente Nuevo.")

        if not reclamos_activos.empty:
            estado['formulario_bloqueado'] = True
            st.error("⚠️ Este cliente ya tiene un reclamo sin resolver o una desconexión activa. No se puede cargar uno nuevo.")

            # 🔔 Notificación por intento de duplicado
            if 'notification_manager' in st.session_state:
                ya_notificado = any(
                    reclamo_activo.get("ID Reclamo") in [
                        n.get("ID_Reclamo") for n in st.session_state.notification_manager.get_for_user("admin", unread_only=False, limit=1000)
                        if n.get("Tipo") == "duplicate_claim"
                    ]
                    for _, reclamo_activo in reclamos_activos.iterrows()
                )

                if not ya_notificado:
                    mensaje = f"Intento de reclamo duplicado para el cliente {estado['nro_cliente']}"
                    primer_reclamo = reclamos_activos.iloc[0]
                    st.session_state.notification_manager.add(
                        notification_type="duplicate_claim",
                        message=mensaje,
                        user_target="admin",
                        claim_id=primer_reclamo.get("ID Reclamo", "")
                    )

            for _, reclamo in reclamos_activos.iterrows():
                with st.expander(f"🔍 Ver reclamo activo - {format_fecha(reclamo['Fecha y hora'], '%d/%m/%Y %H:%M')}"):
                    st.markdown(f"**👤 Cliente:** {reclamo['Nombre']}")
                    st.markdown(f"**📌 Tipo de reclamo:** {reclamo['Tipo de reclamo']}")
                    st.markdown(f"**📝 Detalles:** {reclamo['Detalles'][:250]}{'...' if len(reclamo['Detalles']) > 250 else ''}")
                    st.markdown(f"**⚙️ Estado:** {reclamo['Estado'] or 'Sin estado'}")
                    st.markdown(f"**👷 Técnico asignado:** {reclamo.get('Técnico', 'No asignado') or 'No asignado'}")
                    st.markdown(f"**🙍‍♂️ Atendido por:** {reclamo.get('Atendido por', 'N/A')}")

    if not estado['formulario_bloqueado']:
        estado = _mostrar_formulario_reclamo(estado, df_clientes, sheet_reclamos, sheet_clientes, current_user)

    return estado

def _mostrar_formulario_reclamo(estado, df_clientes, sheet_reclamos, sheet_clientes, current_user):
    """Muestra y procesa el formulario de nuevo reclamo"""
    with st.form("reclamo_formulario", clear_on_submit=True):
        col1, col2 = st.columns(2)

        if estado['cliente_existente']:
            with col1:
                nombre = st.text_input(
                    "👤 Nombre del Cliente",
                    value=estado['cliente_existente'].get("Nombre", "")
                )
                direccion = st.text_input(
                    "📍 Dirección",
                    value=estado['cliente_existente'].get("Dirección", "")
                )

            with col2:
                telefono = st.text_input(
                    "📞 Teléfono",
                    value=estado['cliente_existente'].get("Teléfono", "")
                )

                # ✅ Sector cargado como en gestión de clientes
                try:
                    sector_raw = estado['cliente_existente'].get("Sector", "1")
                    sector_int = int(float(sector_raw))  # Acepta "13", "13.0", etc.
                    sector_index = SECTORES_DISPONIBLES.index(str(sector_int)) if str(sector_int) in SECTORES_DISPONIBLES else 0
                except:
                    sector_index = 0

                sector = st.text_input(
                    "🔢 Sector (1-17)",
                    value=str(sector_index + 1),
                    placeholder="Ingrese el sector numérico (1-17)"
                )


        else:
            with col1:
                nombre = st.text_input("👤 Nombre del Cliente", placeholder="Nombre completo")
                direccion = st.text_input("📍 Dirección", placeholder="Dirección completa")
            with col2:
                telefono = st.text_input("📞 Teléfono", placeholder="Número de contacto")
                sector = st.text_input(
                    "🔢 Sector (1-17)",
                    placeholder="Ingrese el sector numérico (1-17)",
                    key="input_sector_new"
                )


        tipo_reclamo = st.selectbox("📌 Tipo de Reclamo", TIPOS_RECLAMO)
        detalles = st.text_area("📝 Detalles del Reclamo", placeholder="Describe el problema o solicitud...", height=100)

        col3, col4 = st.columns(2)
        with col3:
            precinto = st.text_input("🔒 N° de Precinto (opcional)",
                                   value=estado['cliente_existente'].get("N° de Precinto", "").strip() if estado['cliente_existente'] else "",
                                   placeholder="Número de precinto")
        with col4:
            atendido_por = st.text_input("👤 Atendido por", placeholder="Nombre de quien atiende", value=current_user or "")

        enviado = st.form_submit_button("✅ Guardar Reclamo", use_container_width=True)

    if enviado:
        estado = _procesar_envio_formulario(
            estado, nombre, direccion, telefono, sector, 
            tipo_reclamo, detalles, precinto, atendido_por,
            df_clientes, sheet_reclamos, sheet_clientes
        )
    
    return estado

def _procesar_envio_formulario(estado, nombre, direccion, telefono, sector, tipo_reclamo, 
                              detalles, precinto, atendido_por, df_clientes, sheet_reclamos, sheet_clientes):
    """Procesa el envío del formulario y guarda los datos"""
    campos_obligatorios = {
        "Nombre": nombre.strip(),
        "Dirección": direccion.strip(),
        "Sector": str(sector).strip(),
        "Tipo de reclamo": tipo_reclamo.strip(),
        "Atendido por": atendido_por.strip()
    }
    campos_vacios = [campo for campo, valor in campos_obligatorios.items() if not valor]

    # ✅ Validación del sector antes de guardar
    if str(sector).strip() not in SECTORES_DISPONIBLES:
        st.error(f"⚠️ El sector ingresado ({sector}) no es válido. Debe ser un número entre 1 y 17.")
        return estado

    if not estado['nro_cliente']:
        st.error("⚠️ Debes ingresar un número de cliente.")
    elif campos_vacios:
        st.error(f"⚠️ Los siguientes campos están vacíos: {', '.join(campos_vacios)}.")
    else:
        with st.spinner("Guardando reclamo..."):
            try:
                fecha_hora_obj = ahora_argentina()
                fecha_hora_str = format_fecha(fecha_hora_obj)
                estado_reclamo = "Desconexión" if tipo_reclamo.strip().lower() == "desconexion a pedido" else "Pendiente"
                id_reclamo = generar_id_unico()

                fila_reclamo = [
                    fecha_hora_str,
                    estado['nro_cliente'],
                    str(sector),
                    nombre.upper(),
                    direccion.upper(),
                    telefono,
                    tipo_reclamo,
                    detalles.upper(),
                    estado_reclamo,
                    "",
                    precinto,
                    atendido_por.upper(),
                    "",
                    "",
                    "",
                    id_reclamo
                ]

                success, error = api_manager.safe_sheet_operation(
                    sheet_reclamos.append_row,
                    fila_reclamo
                )

                if success:
                    estado['reclamo_guardado'] = True
                    st.success(f"✅ Reclamo cargado para el cliente {estado['nro_cliente']} - {tipo_reclamo.upper()}")

                    # 🔔 Notificación por nuevo reclamo
                    if 'notification_manager' in st.session_state:
                        mensaje = f"📝 Se generó un nuevo reclamo para el cliente N° {estado['nro_cliente']} - {nombre.upper()} ({tipo_reclamo})."
                        st.session_state.notification_manager.add(
                            notification_type="nuevo_reclamo",
                            message=mensaje,
                            user_target="all",
                            claim_id=id_reclamo
                        )

                    if tipo_reclamo.strip().lower() == "desconexion a pedido":
                        st.warning("📄 Este reclamo es una Desconexión a Pedido. **Y NO CUENTA como reclamo activo.**")

                    cliente_row_idx = df_clientes[df_clientes["Nº Cliente"] == estado['nro_cliente']].index

                    if cliente_row_idx.empty:
                        fila_cliente = [
                            estado['nro_cliente'], 
                            str(sector), 
                            nombre.upper(), 
                            direccion.upper(), 
                            telefono, 
                            precinto
                        ]
                        success_cliente, _ = api_manager.safe_sheet_operation(
                            sheet_clientes.append_row, 
                            fila_cliente
                        )
                        if success_cliente:
                            estado['cliente_nuevo'] = True
                            st.info("ℹ️ Se ha creado un nuevo registro de cliente.")
                    else:
                        idx = cliente_row_idx[0] + 2
                        updates_cliente = []
                        if str(df_clientes.at[cliente_row_idx[0], "Nombre"]).strip().upper() != nombre.strip().upper():
                            updates_cliente.append({"range": f"C{idx}", "values": [[nombre.upper()]]})
                        if str(df_clientes.at[cliente_row_idx[0], "Dirección"]).strip().upper() != direccion.strip().upper():
                            updates_cliente.append({"range": f"D{idx}", "values": [[direccion.upper()]]})
                        if str(df_clientes.at[cliente_row_idx[0], "Teléfono"]).strip() != telefono.strip():
                            updates_cliente.append({"range": f"E{idx}", "values": [[telefono.strip()]]})
                        if str(df_clientes.at[cliente_row_idx[0], "Sector"]).strip() != str(sector).strip():
                            updates_cliente.append({"range": f"B{idx}", "values": [[str(sector).strip()]]})
                        if str(df_clientes.at[cliente_row_idx[0], "N° de Precinto"]).strip() != precinto.strip():
                            updates_cliente.append({"range": f"F{idx}", "values": [[precinto.strip()]]})
                        if updates_cliente:
                            success_update, _ = api_manager.safe_sheet_operation(
                                batch_update_sheet, 
                                sheet_clientes, 
                                updates_cliente, 
                                is_batch=True
                            )
                            if success_update:
                                st.info("🔁 Datos del cliente actualizados.")

                    st.cache_data.clear()
                else:
                    st.error(f"❌ Error al guardar: {error}")
                    if DEBUG_MODE:
                        st.write("Detalles del error:", error)
            except Exception as e:
                st.error(f"❌ Error inesperado: {str(e)}")
                if DEBUG_MODE:
                    st.exception(e)
    
    return estado

