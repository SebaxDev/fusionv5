# components/clientes/gestion.py
import streamlit as st
import pandas as pd
import uuid
from utils.date_utils import ahora_argentina, format_fecha, parse_fecha
from utils.api_manager import api_manager, batch_update_sheet
from config.settings import SECTORES_DISPONIBLES

def render_gestion_clientes(df_clientes, df_reclamos, sheet_clientes, user_role):
    """
    Muestra la sección de gestión de clientes
    
    Args:
        df_clientes (pd.DataFrame): DataFrame con los clientes
        df_reclamos (pd.DataFrame): DataFrame con los reclamos
        sheet_clientes: Objeto de conexión a la hoja de clientes
        user_role (str): Rol del usuario actual
    
    Returns:
        bool: True si se realizaron cambios que requieren recarga
    """
    st.subheader("🛠️ Gestión de Clientes")

    # Normalización de datos
    df_clientes["Nº Cliente"] = df_clientes["Nº Cliente"].astype(str).str.strip()

    if user_role == 'admin':
        cambios = False
        cambios = _mostrar_edicion_cliente(df_clientes, df_reclamos, sheet_clientes) or cambios
        st.markdown("---")
        cambios = _mostrar_nuevo_cliente(df_clientes, sheet_clientes) or cambios
    else:
        st.warning("🔒 Solo los administradores pueden editar información de clientes")

    st.markdown('</div>', unsafe_allow_html=True)
    return cambios

def _mostrar_edicion_cliente(df_clientes, df_reclamos, sheet_clientes):
    """Muestra el formulario para editar un cliente existente"""
    cambios = False

    # Selección del cliente
    clientes_lista = df_clientes["Nº Cliente"].astype(str).tolist()
    cliente_seleccionado = st.selectbox("🔍 Seleccionar cliente", clientes_lista)

    if not cliente_seleccionado:
        return cambios

    # Datos actuales del cliente
    cliente_actual = df_clientes[df_clientes["Nº Cliente"].astype(str) == str(cliente_seleccionado)].iloc[0]

    # Formulario de edición
    with st.form("form_editar_cliente"):
        col1, col2 = st.columns(2)

        with col1:
            nuevo_sector = st.selectbox(
                "🏢 Sector",
                SECTORES_DISPONIBLES,
                index=SECTORES_DISPONIBLES.index(cliente_actual.get("Sector", SECTORES_DISPONIBLES[0]))
                if cliente_actual.get("Sector") in SECTORES_DISPONIBLES else 0
            )

            nuevo_nombre = st.text_input(
                "👤 Nombre",
                value=cliente_actual.get("Nombre", "")
            )

            nueva_direccion = st.text_input(
                "📍 Dirección",
                value=cliente_actual.get("Dirección", "")
            )

        with col2:
            nuevo_telefono = st.text_input(
                "📞 Teléfono",
                value=cliente_actual.get("Teléfono", "")
            )

            nuevo_precinto = st.text_input(
                "🔒 Nº de Precinto",
                value=cliente_actual.get("N° de Precinto", "")
            )

        submitted = st.form_submit_button("💾 Guardar cambios")

    if submitted:
        # Verificar si hubo cambios
        hubo_cambios = any([
            str(nuevo_sector) != str(cliente_actual.get("Sector", "")),
            str(nuevo_nombre) != str(cliente_actual.get("Nombre", "")),
            str(nueva_direccion) != str(cliente_actual.get("Dirección", "")),
            str(nuevo_telefono) != str(cliente_actual.get("Teléfono", "")),
            str(nuevo_precinto) != str(cliente_actual.get("N° de Precinto", ""))
        ])

        if not hubo_cambios:
            st.info("ℹ️ No se detectaron cambios en los datos del cliente.")
            return cambios

        cambios = _actualizar_cliente(
            df_clientes[df_clientes["Nº Cliente"].astype(str) == str(cliente_seleccionado)],
            sheet_clientes,
            nuevo_sector,
            nuevo_nombre,
            nueva_direccion,
            nuevo_telefono,
            nuevo_precinto
        )

        if cambios:
            st.success(f"✅ Cliente {cliente_seleccionado} actualizado correctamente")

    return cambios

def _mostrar_reclamos_cliente(nro_cliente, df_reclamos):
    """Muestra los últimos reclamos del cliente"""
    df_reclamos_cliente = df_reclamos[
        df_reclamos["Nº Cliente"] == nro_cliente
    ].copy()
    
    df_reclamos_cliente["Fecha y hora"] = df_reclamos_cliente["Fecha y hora"].apply(
        parse_fecha
    )
    
    df_reclamos_cliente = df_reclamos_cliente.sort_values(
        "Fecha y hora", 
        ascending=False
    ).head(3)
    
    with st.expander("📄 Últimos reclamos"):
        for _, recl in df_reclamos_cliente.iterrows():
            st.markdown(
                f"📅 {format_fecha(recl['Fecha y hora'], '%d/%m/%Y')} | "
                f"📌 {recl['Tipo de reclamo']} | "
                f"👷 {recl.get('Técnico', 'N/A')}"
            )
    
    return False

def _verificar_cambios_desde_reclamos(nro_cliente, df_reclamos, nueva_direccion, nuevo_telefono, nuevo_precinto):
    """Verifica si hay diferencias entre datos actuales y reclamos recientes"""
    df_reclamos_cliente = df_reclamos[
        df_reclamos["Nº Cliente"] == nro_cliente
    ].copy()
    
    cambios_detectados = False
    
    for campo, nuevo_valor in zip(
        ["Dirección", "Teléfono", "N° de Precinto"], 
        [nueva_direccion, nuevo_telefono, nuevo_precinto]
    ):
        reclamos_valor = df_reclamos_cliente[campo].dropna().astype(str).str.strip().unique()
        if len(reclamos_valor) > 0 and nuevo_valor.strip() not in reclamos_valor:
            cambios_detectados = True

    if cambios_detectados:
        st.info("📌 Se detectaron datos nuevos distintos a los reclamos recientes. Podés actualizarlos si es necesario.")
    
    return cambios_detectados

def _actualizar_cliente(cliente_row, sheet_clientes, nuevo_sector, nuevo_nombre, 
                       nueva_direccion, nuevo_telefono, nuevo_precinto):
    """Actualiza los datos del cliente en la hoja de cálculo"""
    with st.spinner("Actualizando cliente..."):
        try:
            # Nos aseguramos que el índice sea numérico y válido para Google Sheets
            index = int(cliente_row.index[0]) + 2

            # Convertimos todos los valores a string para evitar problemas
            updates = [
                {"range": f"B{index}", "values": [[str(nuevo_sector)]]},
                {"range": f"C{index}", "values": [[str(nuevo_nombre).upper()]]},
                {"range": f"D{index}", "values": [[str(nueva_direccion).upper()]]},
                {"range": f"E{index}", "values": [[str(nuevo_telefono)]]},
                {"range": f"F{index}", "values": [[str(nuevo_precinto)]]},
                {"range": f"H{index}", "values": [[format_fecha(ahora_argentina())]]}
            ]

            success, error = api_manager.safe_sheet_operation(
                batch_update_sheet,
                sheet_clientes,
                updates,
                is_batch=True
            )

            if success:
                st.success("✅ Cliente actualizado correctamente.")
                
                if 'notification_manager' in st.session_state:
                    num_cliente = str(cliente_row.iloc[0]['Nº Cliente'])
                    nombre_cliente = str(nuevo_nombre).upper()
                    mensaje = f"✏️ Se actualizaron los datos del cliente N° {num_cliente} - {nombre_cliente}."
                    st.session_state.notification_manager.add(
                        notification_type="cliente_actualizado",
                        message=mensaje,
                        user_target="all"
                    )
                return True
            else:
                st.error(f"❌ Error al actualizar: {error}")
                return False

        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            return False

def _mostrar_nuevo_cliente(df_clientes, sheet_clientes):
    """Muestra el formulario para crear nuevo cliente"""
    st.subheader("🆕 Cargar nuevo cliente")
    cambios = False

    with st.form("form_nuevo_cliente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_nro = st.text_input(
                "🔢 N° de Cliente (nuevo)", 
                placeholder="Número único"
            ).strip()
            
            nuevo_sector = st.selectbox(
                "🔢 Sector (1-17)",
                options=SECTORES_DISPONIBLES,
                index=0,
                key="new_sector"
            )
        
        with col2:
            nuevo_nombre = st.text_input(
                "👤 Nombre", 
                placeholder="Nombre completo"
            )
            
            nueva_direccion = st.text_input(
                "📍 Dirección", 
                placeholder="Dirección completa"
            )

        nuevo_telefono = st.text_input(
            "📞 Teléfono", 
            placeholder="Número de contacto"
        )
        
        nuevo_precinto = st.text_input(
            "🔒 N° de Precinto (opcional)", 
            placeholder="Número de precinto"
        )

        guardar_cliente = st.form_submit_button(
            "💾 Guardar nuevo cliente", 
            use_container_width=True
        )

    if guardar_cliente:
        cambios = _guardar_nuevo_cliente(
            df_clientes, sheet_clientes,
            nuevo_nro, nuevo_sector, nuevo_nombre,
            nueva_direccion, nuevo_telefono, nuevo_precinto
        )

    return cambios

def _guardar_nuevo_cliente(df_clientes, sheet_clientes, nuevo_nro, nuevo_sector, 
                          nuevo_nombre, nueva_direccion, nuevo_telefono, nuevo_precinto):
    """Guarda un nuevo cliente en la hoja de cálculo"""
    if not nuevo_nombre.strip() or not nueva_direccion.strip():
        st.error("⚠️ Debés ingresar nombre y dirección.")
        return False
    
    if nuevo_nro and str(nuevo_nro) in df_clientes["Nº Cliente"].astype(str).values:
        st.warning("⚠️ Este cliente ya existe.")
        return False

    with st.spinner("Guardando nuevo cliente..."):
        try:
            nuevo_id = str(uuid.uuid4())

            nueva_fila = [
                nuevo_nro, 
                str(nuevo_sector),
                nuevo_nombre.upper(),
                nueva_direccion.upper(), 
                nuevo_telefono, 
                nuevo_precinto, 
                nuevo_id,
                format_fecha(ahora_argentina())
            ]

            success, error = api_manager.safe_sheet_operation(
                sheet_clientes.append_row,
                nueva_fila
            )

            if success:
                st.success("✅ Nuevo cliente agregado correctamente.")

                if 'notification_manager' in st.session_state:
                    mensaje = f"🆕 Se agregó el cliente N° {nuevo_nro} - {nuevo_nombre.upper()} al sistema."
                    st.session_state.notification_manager.add(
                        notification_type="cliente_nuevo",
                        message=mensaje,
                        user_target="all"
                    )

                return True
            else:
                st.error(f"❌ Error al guardar: {error}")
                return False

        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            return False
