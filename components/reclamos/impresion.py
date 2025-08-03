# components/reclamos/impresion.py

import io
import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from utils.date_utils import format_fecha, parse_fecha
from utils.pdf_utils import agregar_pie_pdf

def render_impresion_reclamos(df_reclamos, df_clientes, user):
    """
    Muestra la sección para imprimir reclamos en formato PDF
    
    Args:
        df_reclamos (pd.DataFrame): DataFrame con los reclamos
        df_clientes (pd.DataFrame): DataFrame con los clientes
        user (dict): Información del usuario actual
        
    Returns:
        dict: {
            'needs_refresh': bool,  # Siempre False para este módulo
            'message': str,         # Mensaje sobre la operación realizada
            'data_updated': bool    # Siempre False para este módulo
        }
    """
    result = {
        'needs_refresh': False,
        'message': None,
        'data_updated': False
    }
    
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("📨️ Seleccionar reclamos para imprimir (formato técnico compacto)")

    try:
        # Preparar datos con información del usuario
        df_merged = _preparar_datos(df_reclamos, df_clientes, user)
        
        # Mostrar reclamos pendientes
        _mostrar_reclamos_pendientes(df_merged)
        
        # Configuración de filtros
        with st.expander("⚙️ Configuración de impresión", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                solo_pendientes = st.checkbox(
                    "📜 Mostrar solo reclamos pendientes", 
                    value=True
                )
            with col2:
                incluir_usuario = st.checkbox(
                    "👤 Incluir mi nombre en el PDF",
                    value=True
                )

        # Impresión por tipo
        mensaje_tipo = _generar_pdf_por_tipo(df_merged, solo_pendientes, user if incluir_usuario else None)
        if mensaje_tipo:
            result['message'] = mensaje_tipo
        
        # Impresión manual
        mensaje_manual = _generar_pdf_manual(df_merged, solo_pendientes, user if incluir_usuario else None)
        if mensaje_manual:
            result['message'] = mensaje_manual

    except Exception as e:
        st.error(f"❌ Error al generar PDF: {str(e)}")
        result['message'] = f"Error al generar PDF: {str(e)}"
        if DEBUG_MODE:
            st.exception(e)
    finally:
        st.markdown('</div>', unsafe_allow_html=True)
    
    return result

def _preparar_datos(df_reclamos, df_clientes, user):
    """Prepara y combina los datos para impresión incluyendo info de usuario"""
    df_pdf = df_reclamos.copy()
    
    # Procesamiento de fechas
    df_pdf["Fecha y hora"] = pd.to_datetime(
        df_pdf["Fecha y hora"], 
        dayfirst=True, 
        errors='coerce'
    )
    
    # Agregar información del usuario a los datos
    df_pdf["Usuario_impresion"] = user.get('nombre', 'Sistema')
    
    # Merge con clientes (optimizado)
    return pd.merge(
        df_pdf,
        df_clientes[["Nº Cliente", "N° de Precinto"]].drop_duplicates(),
        on="Nº Cliente",
        how="left",
        suffixes=("", "_cliente")
    )

def _mostrar_reclamos_pendientes(df_merged):
    """Muestra tabla de reclamos pendientes con mejor formato"""
    with st.expander("🕒 Reclamos pendientes de resolución", expanded=True):
        df_pendientes = df_merged[
            df_merged["Estado"].astype(str).str.strip().str.lower() == "pendiente"
        ]
        
        if not df_pendientes.empty:
            # Formatear datos para visualización
            df_pendientes_display = df_pendientes.copy()
            df_pendientes_display["Fecha y hora"] = df_pendientes_display["Fecha y hora"].apply(
                lambda f: format_fecha(f, '%d/%m/%Y %H:%M') if not pd.isna(f) else 'Sin fecha'
            )
            
            # Mostrar tabla con configuración mejorada
            st.dataframe(
                df_pendientes_display[[
                    "Fecha y hora", "Nº Cliente", "Nombre", 
                    "Dirección", "Sector", "Tipo de reclamo"
                ]],
                use_container_width=True,
                column_config={
                    "Fecha y hora": st.column_config.DatetimeColumn(
                        "Fecha y hora",
                        format="DD/MM/YYYY HH:mm"
                    ),
                    "Nº Cliente": st.column_config.TextColumn(
                        "N° Cliente",
                        help="Número de cliente"
                    ),
                    "Sector": st.column_config.NumberColumn(
                        "Sector",
                        format="%d"
                    )
                },
                height=400
            )
        else:
            st.success("✅ No hay reclamos pendientes actualmente.")

def _generar_pdf_por_tipo(df_merged, solo_pendientes, usuario=None):
    """Genera PDF filtrado por tipos de reclamo"""
    st.markdown("### 📋 Imprimir reclamos por tipo")
    
    tipos_disponibles = sorted(df_merged["Tipo de reclamo"].dropna().unique())
    tipos_seleccionados = st.multiselect(
        "Seleccioná tipos de reclamo a imprimir",
        tipos_disponibles,
        default=tipos_disponibles[0] if tipos_disponibles else None,
        key="select_tipos_pdf"
    )

    if not tipos_seleccionados:
        return None

    # Aplicar filtros
    df_filtrado = df_merged.copy()
    if solo_pendientes:
        df_filtrado = df_filtrado[
            df_filtrado["Estado"].str.strip().str.lower() == "pendiente"
        ]
    
    reclamos_filtrados = df_filtrado[
        df_filtrado["Tipo de reclamo"].isin(tipos_seleccionados)
    ]

    if reclamos_filtrados.empty:
        st.info("No hay reclamos pendientes para los tipos seleccionados.")
        return None

    st.success(f"📋 Se encontraron {len(reclamos_filtrados)} reclamos de los tipos seleccionados.")

    if st.button("📄 Generar PDF de reclamos por tipo", key="pdf_tipo"):
        buffer = _crear_pdf_reclamos(
            reclamos_filtrados, 
            f"RECLAMOS - {', '.join(tipos_seleccionados)}",
            usuario
        )
        
        nombre_archivo = f"reclamos_{'_'.join(t.lower().replace(' ', '_') for t in tipos_seleccionados)}.pdf"
        
        st.download_button(
            label="⬇️ Descargar PDF filtrado por tipo",
            data=buffer,
            file_name=nombre_archivo,
            mime="application/pdf",
            help=f"Descargar {len(reclamos_filtrados)} reclamos de tipo {', '.join(tipos_seleccionados)}"
        )
        
        return f"PDF generado con {len(reclamos_filtrados)} reclamos de tipo {', '.join(tipos_seleccionados)}"
    
    return None

def _generar_pdf_manual(df_merged, solo_pendientes, usuario=None):
    """Genera PDF con selección manual de reclamos"""
    st.markdown("### 📋 Selección manual de reclamos")

    df_filtrado = df_merged.copy()
    if solo_pendientes:
        df_filtrado = df_filtrado[
            df_filtrado["Estado"].astype(str).str.strip().str.lower() == "pendiente"
        ]

    # Selector mejorado con más información
    selected = st.multiselect(
        "Seleccioná los reclamos a imprimir:",
        df_filtrado.index,
        format_func=lambda x: (
            f"{df_filtrado.at[x, 'Nº Cliente']} - "
            f"{df_filtrado.at[x, 'Nombre']} - "
            f"Sector {df_filtrado.at[x, 'Sector']} - "
            f"{df_filtrado.at[x, 'Tipo de reclamo']}"
        ),
        key="multiselect_reclamos"
    )

    if not selected:
        st.info("ℹ️ Seleccioná al menos un reclamo para generar el PDF.")
        return None

    if st.button("📄 Generar PDF con seleccionados", key="pdf_manual"):
        buffer = _crear_pdf_reclamos(
            df_filtrado.loc[selected],
            f"RECLAMOS SELECCIONADOS",
            usuario
        )
        
        st.download_button(
            label="⬇️ Descargar PDF seleccionados",
            data=buffer,
            file_name="reclamos_seleccionados.pdf",
            mime="application/pdf",
            help=f"Descargar {len(selected)} reclamos seleccionados"
        )
        
        return f"PDF generado con {len(selected)} reclamos seleccionados"
    
    return None

def _crear_pdf_reclamos(df_reclamos, titulo, usuario=None):
    """
    Crea un PDF con los reclamos seleccionados
    
    Args:
        df_reclamos (pd.DataFrame): DataFrame con los reclamos a imprimir
        titulo (str): Título principal del documento
        usuario (dict, optional): Información del usuario que genera el PDF
        
    Returns:
        io.BytesIO: Buffer con el PDF generado
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40
    hoy = datetime.now().strftime('%d/%m/%Y %H:%M')

    # Encabezado del documento
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, titulo)
    y -= 20
    
    c.setFont("Helvetica", 12)
    c.drawString(40, y, f"Generado el: {hoy}")
    if usuario:
        c.drawString(width - 150, y, f"Por: {usuario.get('nombre', 'Sistema')}")
    y -= 30

    # Contenido de los reclamos
    for i, (_, reclamo) in enumerate(df_reclamos.iterrows()):
        # Encabezado del reclamo
        c.setFont("Helvetica-Bold", 14)
        cliente_line = f"#{reclamo['Nº Cliente']} - {reclamo['Nombre']} (Sector {reclamo['Sector']})"
        c.drawString(40, y, cliente_line)
        y -= 18
        
        # Detalles del reclamo
        c.setFont("Helvetica", 11)
        
        fecha_pdf = format_fecha(reclamo['Fecha y hora'], '%d/%m/%Y %H:%M') if not pd.isna(reclamo['Fecha y hora']) else 'Sin fecha'
        lineas = [
            f"Fecha: {fecha_pdf}",
            f"Dirección: {reclamo['Dirección']}",
            f"Contacto: {reclamo['Teléfono']}",
            f"Precinto: {reclamo.get('N° de Precinto', 'N/A')}",
            f"Tipo: {reclamo['Tipo de reclamo']}",
        ]
        
        # Detalles con manejo de texto largo
        detalles = reclamo['Detalles']
        if len(detalles) > 150:
            lineas.append(f"Detalles: {detalles[:150]}...")
        else:
            lineas.append(f"Detalles: {detalles}")

        # Dibujar cada línea
        for linea in lineas:
            if y < 100:  # Salto de página si queda poco espacio
                agregar_pie_pdf(c, width, height)
                c.showPage()
                y = height - 40
                c.setFont("Helvetica-Bold", 14)
                c.drawString(40, y, f"{titulo} (cont.)")
                y -= 30
                c.setFont("Helvetica", 11)
            
            c.drawString(40, y, linea)
            y -= 14

        # Separador entre reclamos
        y -= 10
        c.line(40, y, width-40, y)
        y -= 15

    # Pie de página final
    agregar_pie_pdf(c, width, height)
    c.save()
    buffer.seek(0)
    return buffer