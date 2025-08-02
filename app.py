# --------------------------------------------------
# Aplicación principal de gestión de reclamos optimizada
# Versión 2.0 - Con manejo robusto de API y session_state
# --------------------------------------------------

# Standard library
import io
import json
import time
from datetime import datetime

# Third-party
import pandas as pd
import pytz
import streamlit as st
from google.oauth2 import service_account
import gspread
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from streamlit_lottie import st_lottie
from tenacity import retry, wait_exponential, stop_after_attempt

# Local components
from components.auth import has_permission, check_authentication, render_login
from components.navigation import render_navigation
from components.metrics_dashboard import render_metrics_dashboard
from components.user_widget import show_user_widget

# Utils
from utils.styles import get_main_styles
from utils.data_manager import safe_get_sheet_data, safe_normalize, update_sheet_data, batch_update_sheet
from utils.api_manager import api_manager, init_api_session_state
from utils.pdf_utils import agregar_pie_pdf
from utils.date_utils import parse_fecha, es_fecha_valida, format_fecha, ahora_argentina

# Agregar aquí la nueva función
def generar_id_unico():
    """Genera un ID único para reclamos"""
    import uuid
    return str(uuid.uuid4())[:8].upper()

# Config
from config.settings import (
    SHEET_ID,
    WORKSHEET_RECLAMOS,
    WORKSHEET_CLIENTES, 
    WORKSHEET_USUARIOS,
    COLUMNAS_RECLAMOS,
    COLUMNAS_CLIENTES,
    COLUMNAS_USUARIOS,
    SECTORES_DISPONIBLES,
    TIPOS_RECLAMO,
    TECNICOS_DISPONIBLES,
    MATERIALES_POR_RECLAMO,
    ROUTER_POR_SECTOR,
    DEBUG_MODE
)


# --------------------------
# INICIALIZACIONES
# --------------------------

# Detectar dispositivo móvil
def is_mobile():
    user_agent = st.query_params.get("user_agent", [""])[0]
    mobile_keywords = ['iphone', 'android', 'mobile', 'ipad', 'tablet']
    return any(keyword in user_agent.lower() for keyword in mobile_keywords)

# Configuración de página
if is_mobile():
    st.set_page_config(
        page_title="Fusion Reclamos",
        page_icon="📋",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
else:
    st.set_page_config(
        page_title="Fusion Reclamos App",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'About': "Sistema de gestión de reclamos v2.0"
        }
    )

# Inyectar estilos CSS personalizados
st.markdown("""
<style>
    /* Estilos generales */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Estilos para móviles */
    @media screen and (max-width: 768px) {
        .stTextInput>div>div>input, 
        .stSelectbox>div>div>select,
        .stTextArea>div>textarea {
            font-size: 16px !important;
        }
        
        .stButton>button {
            width: 100% !important;
            margin: 5px 0 !important;
        }
        
        .stMarkdown h1 {
            font-size: 1.5rem !important;
        }
        
        .stMarkdown h2 {
            font-size: 1.3rem !important;
        }
        
        .stDataFrame {
            font-size: 14px !important;
        }
    }
    
    /* Header principal */
    .st-emotion-cache-10trblm {
        color: #2c3e50;
        font-weight: 600;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    /* Tarjetas y contenedores */
    .st-emotion-cache-1y4p8pa {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 1.5rem;
    }
    
    /* Botones */
    .st-emotion-cache-7ym5gk {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        transition: all 0.3s;
    }
    
    .st-emotion-cache-7ym5gk:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
    }
    
    /* Inputs y selects */
    .stTextInput>div>div>input, 
    .stSelectbox>div>div>select {
        border-radius: 8px !important;
        border: 1px solid #dfe6e9 !important;
    }
    
    /* Tablas */
    .stDataFrame {
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Títulos de sección */
    .st-emotion-cache-16txtl3 {
        color: #2c3e50;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    
    /* Modo oscuro */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #121212;
        }
        .st-emotion-cache-1y4p8pa {
            background-color: #1e1e1e;
            color: #f8f9fa;
        }
        .st-emotion-cache-10trblm {
            color: #f8f9fa;
        }
    }
</style>
""", unsafe_allow_html=True)

# Función para detectar el modo oscuro del sistema
def is_system_dark_mode():
    import platform
    if platform.system() == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
            return value == 0  # 0 = oscuro, 1 = claro
        except:
            return False
    elif platform.system() == "Darwin":
        import subprocess
        try:
            result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], capture_output=True, text=True)
            return "Dark" in result.stdout
        except:
            return False
    else:
        return False  # Linux u otros

# Inicializar modo oscuro si no está en sesión
if "modo_oscuro" not in st.session_state:
    sistema_oscuro = is_system_dark_mode()
    st.session_state.modo_oscuro = sistema_oscuro

# Sidebar con toggle para cambiar modo
with st.sidebar:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #2c3e50, #3498db);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    ">
        <h3 style="margin:0; color:white;">Panel de Control</h3>
    </div>
    """, unsafe_allow_html=True)
    
    nuevo_modo = st.toggle(
        "🌙 Modo oscuro",
        value=st.session_state.modo_oscuro,
        key="dark_mode_toggle",
        help="Cambiar entre tema claro y oscuro"
    )
    if nuevo_modo != st.session_state.modo_oscuro:
        st.session_state.modo_oscuro = nuevo_modo
        st.rerun()
    
    st.markdown("---")
    show_user_widget()
    
    # Mostrar información del sistema
    st.markdown("""
    <div style="
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        font-size: 0.8rem;
        color: #7f8c8d;
    ">
        <p style="margin:0;"><strong>Versión:</strong> 2.0.1</p>
        <p style="margin:0;"><strong>Última actualización:</strong> {}</p>
    </div>
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)

# Aplicar estilos personalizados según modo
st.markdown(get_main_styles(dark_mode=st.session_state.modo_oscuro), unsafe_allow_html=True)

# --------------------------------------------------
# INICIALIZACIÓN GARANTIZADA
# --------------------------------------------------
class AppState:
    def __init__(self):
        self._init_state()
        
    def _init_state(self):
        """Inicializa todos los estados necesarios"""
        defaults = {
            'app_initialized': False,
            'df_reclamos': pd.DataFrame(),
            'df_clientes': pd.DataFrame(),
            'last_update': None,
            'modo_oscuro': is_system_dark_mode()
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

# Uso:
app_state = AppState()

# --------------------------
# CONEXIÓN CON GOOGLE SHEETS
# --------------------------

@st.cache_resource(ttl=3600)  # Cache por 1 hora
def init_google_sheets():
    """Conexión optimizada a Google Sheets con retry automático"""
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    def _connect():
        creds = service_account.Credentials.from_service_account_info(
            {**st.secrets["gcp_service_account"], "private_key": st.secrets["gcp_service_account"]["private_key"].replace("\\n", "\n")},
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        return (
            client.open_by_key(SHEET_ID).worksheet(WORKSHEET_RECLAMOS),
            client.open_by_key(SHEET_ID).worksheet(WORKSHEET_CLIENTES),
            client.open_by_key(SHEET_ID).worksheet(WORKSHEET_USUARIOS)
        )
    
    try:
        return _connect()
    except Exception as e:
        st.error(f"🔴 Error de conexión: {str(e)}")
        st.stop()

# Inicializar conexión con Google Sheets
with st.spinner("Conectando con Google Sheets..."):
    sheet_reclamos, sheet_clientes, sheet_usuarios = init_google_sheets()
    if not all([sheet_reclamos, sheet_clientes, sheet_usuarios]):
        st.stop()

# Verificar autenticación
if not check_authentication():
    render_login(sheet_usuarios)
    st.stop()

# Obtener información del usuario actual
user_info = st.session_state.auth.get('user_info', {})
user_role = user_info.get('rol', '')

# --------------------------
# CARGA DE DATOS
# --------------------------

@st.cache_data(ttl=30, show_spinner="Cargando datos...")
def cargar_datos():
    """
    Carga datos de Google Sheets con manejo robusto de fechas y validaciones
    Utiliza funciones centralizadas de date_utils para el manejo de fechas
    """
    try:
        # Cargar datos de las hojas
        with st.spinner("Obteniendo datos de Google Sheets..."):
            df_reclamos = safe_get_sheet_data(sheet_reclamos, COLUMNAS_RECLAMOS)
            df_clientes = safe_get_sheet_data(sheet_clientes, COLUMNAS_CLIENTES)
            df_usuarios = safe_get_sheet_data(sheet_usuarios, COLUMNAS_USUARIOS)
        
        # Validación de datos básica
        if df_reclamos.empty:
            st.error("⚠️ La hoja de reclamos está vacía o no se pudo cargar")
        if df_clientes.empty:
            st.error("⚠️ La hoja de clientes está vacía o no se pudo cargar")
        if df_reclamos.empty or df_clientes.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Normalización de columnas clave
        with st.spinner("Normalizando datos..."):
            for col in ["Nº Cliente", "N° de Precinto"]:
                if col in df_clientes.columns:
                    df_clientes[col] = df_clientes[col].astype(str).str.strip()
                if col in df_reclamos.columns:
                    df_reclamos[col] = df_reclamos[col].astype(str).str.strip()

        # Procesamiento de fechas con manejo de errores
        with st.spinner("Procesando fechas..."):
            if 'Fecha y hora' in df_reclamos.columns:
                # Guardar una copia del formato original para diagnóstico
                df_reclamos['Fecha_original'] = df_reclamos['Fecha y hora'].copy()
                
                # Convertir fechas usando la función centralizada
                df_reclamos['Fecha y hora'] = df_reclamos['Fecha y hora'].apply(
                    lambda x: parse_fecha(x) if not pd.isna(x) else pd.NaT
                )
                
                # Verificación de fechas inválidas con función centralizada
                fechas_invalidas = ~df_reclamos['Fecha y hora'].apply(es_fecha_valida)
                if fechas_invalidas.any():
                    num_fechas_invalidas = fechas_invalidas.sum()
                    st.warning(f"⚠️ Advertencia: {num_fechas_invalidas} reclamos tienen fechas inválidas o faltantes")
                    
                    if DEBUG_MODE:
                        invalid_data = df_reclamos[fechas_invalidas].copy()
                        st.write("Filas con fechas inválidas:", 
                                invalid_data[['Nº Cliente', 'Nombre', 'Fecha_original']].head(10))
                
                # Crear columna adicional con fecha formateada usando función centralizada
                df_reclamos['Fecha_formateada'] = df_reclamos['Fecha y hora'].apply(
                    lambda x: format_fecha(x, '%d/%m/%Y %H:%M', 'Fecha inválida')
                )
                
                # Eliminar columna temporal de diagnóstico
                df_reclamos.drop('Fecha_original', axis=1, inplace=True, errors='ignore')
            else:
                st.error("❌ No se encontró la columna 'Fecha y hora' en los datos de reclamos")
                df_reclamos['Fecha y hora'] = pd.NaT
                df_reclamos['Fecha_formateada'] = 'Columna no encontrada'
            
        # Validación adicional de datos importantes
        required_cols = ['Nº Cliente', 'Nombre', 'Sector']
        missing_cols = [col for col in required_cols if col not in df_reclamos.columns]
        
        if missing_cols:
            st.error(f"❌ Columnas requeridas faltantes en reclamos: {', '.join(missing_cols)}")
            
        for col in required_cols:
            if col in df_clientes.columns and df_clientes[col].isnull().all():
                st.warning(f"⚠️ Columna '{col}' en clientes está completamente vacía")

        # Validar consistencia entre clientes y reclamos
        clientes_sin_reclamos = set(df_clientes['Nº Cliente']) - set(df_reclamos['Nº Cliente'])
        if clientes_sin_reclamos and DEBUG_MODE:
            st.info(f"ℹ️ {len(clientes_sin_reclamos)} clientes registrados sin reclamos")

        return df_reclamos, df_clientes, df_usuarios
        
    except Exception as e:
        st.error(f"❌ Error crítico al cargar datos: {str(e)}")
        if DEBUG_MODE:
            st.exception(e)
        
        # En caso de error, devolver dataframes vacíos para evitar problemas en otras partes
        empty_df = pd.DataFrame(columns=COLUMNAS_RECLAMOS) if 'COLUMNAS_RECLAMOS' in globals() else pd.DataFrame()
        return empty_df.copy(), empty_df.copy(), empty_df.copy()

# Cargar datos y guardar en session_state
df_reclamos, df_clientes, df_usuarios = cargar_datos()
st.session_state.df_reclamos = df_reclamos
st.session_state.df_clientes = df_clientes

# --------------------------
# MIGRACIÓN DE UUID PARA REGISTROS EXISTENTES
# --------------------------

def migrar_uuids_existentes():
    """Genera UUIDs para registros existentes que no los tengan"""
    try:
        # Para Reclamos
        if 'ID Reclamo' in df_reclamos.columns:
            reclamos_sin_uuid = df_reclamos[df_reclamos['ID Reclamo'].isna() | (df_reclamos['ID Reclamo'] == '')]
            if not reclamos_sin_uuid.empty:
                st.warning(f"⚠️ Hay {len(reclamos_sin_uuid)} reclamos sin UUID. Generando IDs...")
                
                updates_reclamos = []
                for idx, row in reclamos_sin_uuid.iterrows():
                    nuevo_uuid = generar_id_unico()
                    updates_reclamos.append({
                        "range": f"P{idx + 2}",  # Asumiendo que la columna UUID es la P
                        "values": [[nuevo_uuid]]
                    })
                
                # Actualizar en lotes de 50 para evitar timeout
                batch_size = 50
                for i in range(0, len(updates_reclamos), batch_size):
                    batch = updates_reclamos[i:i + batch_size]
                    success, error = api_manager.safe_sheet_operation(
                        batch_update_sheet,
                        sheet_reclamos,
                        batch,
                        is_batch=True
                    )
                    if not success:
                        st.error(f"Error al actualizar lote de reclamos: {error}")
                        return False
                
                st.success("✅ UUIDs generados para reclamos existentes")
                st.cache_data.clear()
                return True

        # Para Clientes
        if 'ID Cliente' in df_clientes.columns:
            clientes_sin_uuid = df_clientes[df_clientes['ID Cliente'].isna() | (df_clientes['ID Cliente'] == '')]
            if not clientes_sin_uuid.empty:
                st.warning(f"⚠️ Hay {len(clientes_sin_uuid)} clientes sin UUID. Generando IDs...")
                
                updates_clientes = []
                for idx, row in clientes_sin_uuid.iterrows():
                    nuevo_uuid = generar_id_unico()
                    updates_clientes.append({
                        "range": f"G{idx + 2}",  # Asumiendo que la columna UUID es la G
                        "values": [[nuevo_uuid]]
                    })
                
                # Actualizar en lotes
                batch_size = 50
                for i in range(0, len(updates_clientes), batch_size):
                    batch = updates_clientes[i:i + batch_size]
                    success, error = api_manager.safe_sheet_operation(
                        batch_update_sheet,
                        sheet_clientes,
                        batch,
                        is_batch=True
                    )
                    if not success:
                        st.error(f"Error al actualizar lote de clientes: {error}")
                        return False
                
                st.success("✅ UUIDs generados para clientes existentes")
                st.cache_data.clear()
                return True

    except Exception as e:
        st.error(f"❌ Error en la migración de UUIDs: {str(e)}")
        if DEBUG_MODE:
            st.exception(e)
        return False

# Ejecutar la migración solo si el usuario es admin y hay registros sin UUID
if user_role == 'admin':
    with st.expander("🔧 Herramientas de administrador", expanded=False):
        if st.button("🆔 Generar UUIDs para registros existentes"):
            if migrar_uuids_existentes():
                st.rerun()

# --------------------------
# INTERFAZ PRINCIPAL
# --------------------------
st.markdown("---")
# Header simplificado para móviles
if is_mobile():
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #3498db, #2c3e50);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    ">
        <h2 style="margin:0; color:white;">📋 Fusion Reclamos</h2>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #3498db, #2c3e50);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    ">
        <h1 style="margin:0; color:#ffffff;">📋 Fusion Reclamos App</h1>
        <p style="margin:0; opacity:0.9;">Sistema integral de gestión de reclamos técnicos</p>
    </div>
    """, unsafe_allow_html=True)

# Dashboard simplificado para móviles
if is_mobile():
    cols = st.columns(2)
    reclamos_hoy = len(df_reclamos[df_reclamos["Fecha y hora"].dt.date == datetime.now().date()])
    desconexiones = len(df_reclamos[df_reclamos["Tipo de reclamo"].str.strip().str.lower() == "desconexion a pedido"])
    
    with cols[0]:
        st.metric("📅 Hoy", reclamos_hoy)
    with cols[1]:
        st.metric("🔌 Desconexiones", desconexiones)
else:
    with st.container():
        cols = st.columns(4)
        reclamos_hoy = len(df_reclamos[df_reclamos["Fecha y hora"].dt.date == datetime.now().date()])
        pendientes = len(df_reclamos[df_reclamos["Estado"] == "Pendiente"])
        en_curso = len(df_reclamos[df_reclamos["Estado"] == "En curso"])
        desconexiones = len(df_reclamos[df_reclamos["Tipo de reclamo"].str.strip().str.lower() == "desconexion a pedido"])
        
        with cols[0]:
            st.metric("📅 Hoy", reclamos_hoy, help="Reclamos cargados hoy")
        with cols[1]:
            st.metric("⏳ Pendientes", pendientes, help="Reclamos pendientes de atención")
        with cols[2]:
            st.metric("⚙️ En Curso", en_curso, help="Reclamos siendo atendidos")
        with cols[3]:
            st.metric("🔌 Desconexiones", desconexiones, help="Desconexiones a pedido")
        
        st.markdown("---")

# Navegación simplificada para móviles
if is_mobile():
    opcion = st.selectbox(
        "Menú principal",
        options=["Inicio", "Reclamos cargados", "Cierre de Reclamos"],
        index=0,
        key="mobile_nav"
    )
else:
    opcion = render_navigation()

# --------------------------
# SECCIÓN 1: INICIO - NUEVO RECLAMO
# --------------------------

if opcion == "Inicio" and has_permission('inicio'):
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("📝 Cargar nuevo reclamo")

    nro_cliente = st.text_input("🔢 N° de Cliente", placeholder="Ingresa el número de cliente").strip()
    cliente_existente = None
    formulario_bloqueado = False
    reclamo_guardado = False
    cliente_nuevo = False
    actualizar_datos_cliente = False

    if "Nº Cliente" in df_clientes.columns and nro_cliente:
        df_clientes["Nº Cliente"] = df_clientes["Nº Cliente"].astype(str).str.strip()
        df_reclamos["Nº Cliente"] = df_reclamos["Nº Cliente"].astype(str).str.strip()

        match = df_clientes[df_clientes["Nº Cliente"] == nro_cliente]
        df_reclamos["Fecha y hora"] = df_reclamos["Fecha y hora"].apply(parse_fecha)

        reclamos_activos = df_reclamos[
            (df_reclamos["Nº Cliente"] == nro_cliente) &
            (
                df_reclamos["Estado"].str.strip().str.lower().isin(["pendiente", "en curso"]) |
                (df_reclamos["Tipo de reclamo"].str.strip().str.lower() == "desconexion a pedido")
            )
        ]

        if not match.empty:
            cliente_existente = match.iloc[0].to_dict()
            st.success("✅ Cliente reconocido, datos auto-cargados.")
        else:
            st.info("ℹ️ Cliente no encontrado. Se cargará como Cliente Nuevo.")

        if not reclamos_activos.empty:
            formulario_bloqueado = True
            st.error("⚠️ Este cliente ya tiene un reclamo sin resolver o una desconexión activa. No se puede cargar uno nuevo.")

            for _, reclamo in reclamos_activos.iterrows():
                with st.expander(f"🔍 Ver reclamo activo - {format_fecha(reclamo['Fecha y hora'], '%d/%m/%Y %H:%M')}"):
                    st.markdown(f"**👤 Cliente:** {reclamo['Nombre']}")
                    st.markdown(f"**📌 Tipo de reclamo:** {reclamo['Tipo de reclamo']}")
                    st.markdown(f"**📝 Detalles:** {reclamo['Detalles'][:250]}{'...' if len(reclamo['Detalles']) > 250 else ''}")
                    st.markdown(f"**⚙️ Estado:** {reclamo['Estado'] or 'Sin estado'}")
                    st.markdown(f"**👷 Técnico asignado:** {reclamo.get('Técnico', 'No asignado') or 'No asignado'}")
                    st.markdown(f"**🙍‍♂️ Atendido por:** {reclamo.get('Atendido por', 'N/A')}")

    if not formulario_bloqueado:
        with st.form("reclamo_formulario", clear_on_submit=True):
            col1, col2 = st.columns(2)

            if cliente_existente:
                with col1:
                    nombre = st.text_input("👤 Nombre del Cliente", value=cliente_existente.get("Nombre", ""))
                    direccion = st.text_input("📍 Dirección", value=cliente_existente.get("Dirección", ""))
                with col2:
                    telefono = st.text_input("📞 Teléfono", value=cliente_existente.get("Teléfono", ""))
                    # Cambiamos el text_input por selectbox para sector
                    sector = st.selectbox(
                        "🔢 Sector (1-17)",
                        options=SECTORES_DISPONIBLES,
                        index=0,
                        key="select_sector"
                    )
            else:
                with col1:
                    nombre = st.text_input("👤 Nombre del Cliente", placeholder="Nombre completo")
                    direccion = st.text_input("📍 Dirección", placeholder="Dirección completa")
                with col2:
                    telefono = st.text_input("📞 Teléfono", placeholder="Número de contacto")
                    # Cambiamos el text_input por selectbox para sector
                    sector = st.selectbox(
                        "🔢 Sector (1-17)",
                        options=SECTORES_DISPONIBLES,
                        index=0,
                        key="select_sector_new"
                    )

            tipo_reclamo = st.selectbox("📌 Tipo de Reclamo", TIPOS_RECLAMO)
            detalles = st.text_area("📝 Detalles del Reclamo", placeholder="Describe el problema o solicitud...", height=100)

            col3, col4 = st.columns(2)
            with col3:
                precinto = st.text_input("🔒 N° de Precinto (opcional)",
                                       value=cliente_existente.get("N° de Precinto", "").strip() if cliente_existente else "",
                                       placeholder="Número de precinto")
            with col4:
                atendido_por = st.text_input("👤 Atendido por", placeholder="Nombre de quien atiende", value=st.session_state.get("current_user", ""))

            enviado = st.form_submit_button("✅ Guardar Reclamo", use_container_width=True)

        if enviado:
            campos_obligatorios = {
                "Nombre": nombre.strip(),
                "Dirección": direccion.strip(),
                "Sector": str(sector).strip(),  # Convertimos a string por si acaso
                "Tipo de reclamo": tipo_reclamo.strip(),
                "Atendido por": atendido_por.strip()
            }
            campos_vacios = [campo for campo, valor in campos_obligatorios.items() if not valor]

            if not nro_cliente:
                st.error("⚠️ Debes ingresar un número de cliente.")
            elif campos_vacios:
                st.error(f"⚠️ Los siguientes campos están vacíos: {', '.join(campos_vacios)}.")
            else:
                with st.spinner("Guardando reclamo..."):
                    try:
                        fecha_hora_obj = ahora_argentina()
                        fecha_hora_str = format_fecha(fecha_hora_obj)
                        estado_reclamo = "" if tipo_reclamo.strip().lower() == "desconexion a pedido" else "Pendiente"
                        id_reclamo = generar_id_unico()

                        fila_reclamo = [
                            fecha_hora_str,
                            nro_cliente,
                            str(sector),  # Aseguramos que sea string
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
                            reclamo_guardado = True
                            st.success(f"✅ Reclamo cargado para el cliente {nro_cliente} - {tipo_reclamo.upper()}")

                            if tipo_reclamo.strip().lower() == "desconexion a pedido":
                                st.warning("📄 Este reclamo es una Desconexión a Pedido. **Y NO CUENTA como reclamo activo.**")

                            cliente_row_idx = df_clientes[df_clientes["Nº Cliente"] == nro_cliente].index

                            if cliente_row_idx.empty:
                                fila_cliente = [nro_cliente, str(sector), nombre.upper(), direccion.upper(), telefono, precinto]
                                success_cliente, _ = api_manager.safe_sheet_operation(sheet_clientes.append_row, fila_cliente)
                                if success_cliente:
                                    cliente_nuevo = True
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
                                    success_update, _ = api_manager.safe_sheet_operation(batch_update_sheet, sheet_clientes, updates_cliente, is_batch=True)
                                    if success_update:
                                        st.info("🔁 Datos del cliente actualizados.")

                            st.cache_data.clear()
                            time.sleep(3)
                            st.rerun()
                        else:
                            st.error(f"❌ Error al guardar: {error}")
                            if DEBUG_MODE:
                                st.write("Detalles del error:", error)
                    except Exception as e:
                        st.error(f"❌ Error inesperado: {str(e)}")
                        if DEBUG_MODE:
                            st.exception(e)

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# SECCIÓN 2: RECLAMOS CARGADOS
# ----------------------------

elif opcion == "Reclamos cargados" and has_permission('reclamos_cargados'):
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("📊 Gestión de reclamos cargados")

    try:
        df = df_reclamos.copy()

        df_clientes["Nº Cliente"] = df_clientes["Nº Cliente"].astype(str).str.strip()
        df["Nº Cliente"] = df["Nº Cliente"].astype(str).str.strip()
        df["ID Reclamo"] = df["ID Reclamo"].astype(str).str.strip()

        df = pd.merge(df, df_clientes[["Nº Cliente", "N° de Precinto", "Teléfono"]],
                      on="Nº Cliente", how="left", suffixes=("", "_cliente"))

        df["Fecha y hora"] = df["Fecha y hora"].apply(parse_fecha)
        df["Fecha_formateada"] = df["Fecha y hora"].apply(lambda x: format_fecha(x, '%d/%m/%Y %H:%M'))

        if df["Fecha y hora"].isna().any():
            num_fechas_invalidas = df["Fecha y hora"].isna().sum()
            st.warning(f"⚠️ {num_fechas_invalidas} reclamos tienen fechas inválidas o faltantes")

        df = df.sort_values("Fecha y hora", ascending=False)

        # === Detectar múltiples reclamos activos por cliente ===
        df_activos = df[df["Estado"].isin(["Pendiente", "En curso"])]
        duplicados = df_activos.duplicated(subset="Nº Cliente", keep=False)
        df_activos["Duplicado"] = duplicados

        # === Estadísticas visuales ===
        if not df_activos.empty:
            conteo_por_tipo = df_activos["Tipo de reclamo"].value_counts().sort_index()
            st.markdown("#### 📊 Distribución de reclamos activos por tipo")
            tipos, cantidad = list(conteo_por_tipo.index), list(conteo_por_tipo.values)
            for i in range(0, len(tipos), 4):
                cols = st.columns(4)
                for j, col in enumerate(cols):
                    if i + j < len(tipos):
                        tipo, cant = tipos[i + j], cantidad[i + j]
                        color = "#dc3545" if cant > 10 else "#0d6efd"
                        col.markdown(f"""
                        <div style='text-align:center;background:#f8f9fa;padding:5px;border-radius:8px;'>
                            <h5 style='margin:0;color:#6c757d;font-size:0.7rem'>{tipo}</h5>
                            <h4 style='margin:0;color:{color};font-size:1.2rem'>{cant}</h4>
                        </div>""", unsafe_allow_html=True)

        # === Filtros ===
        st.markdown("#### 🔍 Filtros de búsqueda")
        col1, col2, col3 = st.columns(3)
        estado = col1.selectbox("Estado", ["Todos"] + sorted(df["Estado"].dropna().unique()))
        # Cambiamos a selectbox con SECTORES_DISPONIBLES
        sector = col2.selectbox("Sector", ["Todos"] + sorted(SECTORES_DISPONIBLES))
        tipo = col3.selectbox("Tipo de reclamo", ["Todos"] + sorted(df["Tipo de reclamo"].dropna().unique()))

        df_filtrado = df.copy()
        if estado != "Todos": df_filtrado = df_filtrado[df_filtrado["Estado"] == estado]
        if sector != "Todos": df_filtrado = df_filtrado[df_filtrado["Sector"] == str(sector)]  # Convertimos a string para comparar
        if tipo != "Todos": df_filtrado = df_filtrado[df_filtrado["Tipo de reclamo"] == tipo]

        st.markdown(f"**Mostrando {len(df_filtrado)} reclamos**")

        columnas = ["Fecha_formateada", "Nº Cliente", "Nombre", "Sector", "Tipo de reclamo", "Teléfono", "Estado"]
        df_mostrar = df_filtrado[columnas].copy().rename(columns={"Fecha_formateada": "Fecha y hora"})
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

        # === Edición ===
        st.markdown("---")
        st.markdown("### ✏️ Editar un reclamo puntual")
        df_filtrado["selector"] = df_filtrado["ID Reclamo"] + " - " + df_filtrado["Nombre"]
        seleccion = st.selectbox("Seleccioná un reclamo por ID y nombre", [""] + df_filtrado["selector"].tolist())

        if seleccion:
            reclamo_id = seleccion.split(" - ")[0]
            reclamo_actual = df[df["ID Reclamo"] == reclamo_id].iloc[0]

            st.markdown(f"**Estado actual:** {reclamo_actual['Estado']}")
            st.markdown(f"**Fecha:** {format_fecha(reclamo_actual.get('Fecha y hora'))}")

            direccion = st.text_input("Dirección", value=reclamo_actual.get("Dirección", ""))
            telefono = st.text_input("Teléfono", value=reclamo_actual.get("Teléfono", ""))
            tipo_reclamo = st.selectbox("Tipo de reclamo", sorted(df["Tipo de reclamo"].unique()),
                index=sorted(df["Tipo de reclamo"].unique()).index(reclamo_actual["Tipo de reclamo"]))
            detalles = st.text_area("Detalles", value=reclamo_actual.get("Detalles", ""), height=100)
            precinto = st.text_input("N° de Precinto", value=reclamo_actual.get("N° de Precinto", ""))
            # Cambiamos a selectbox para sector en la edición
            sector_edit = st.selectbox(
                "Sector",
                options=SECTORES_DISPONIBLES,
                index=SECTORES_DISPONIBLES.index(int(reclamo_actual["Sector"])) if reclamo_actual["Sector"] in [str(s) for s in SECTORES_DISPONIBLES] else 0
            )

            estado_nuevo = st.selectbox("Nuevo estado", ["Pendiente", "En curso", "Resuelto"],
                index=["Pendiente", "En curso", "Resuelto"].index(reclamo_actual["Estado"]) if reclamo_actual["Estado"] in ["Pendiente", "En curso", "Resuelto"] else 0)

            col1, col2 = st.columns(2)

            if col1.button("💾 Guardar cambios", use_container_width=True):
                if not direccion.strip() or not detalles.strip():
                    st.warning("⚠️ Dirección y detalles no pueden estar vacíos.")
                else:
                    with st.spinner("Actualizando reclamo..."):
                        fila = df[df["ID Reclamo"] == reclamo_id].index[0] + 2
                        updates = [
                            {"range": f"D{fila}", "values": [[direccion]]},
                            {"range": f"E{fila}", "values": [[telefono]]},
                            {"range": f"G{fila}", "values": [[tipo_reclamo]]},
                            {"range": f"H{fila}", "values": [[detalles]]},
                            {"range": f"I{fila}", "values": [[estado_nuevo]]},
                            {"range": f"K{fila}", "values": [[precinto]]},
                            {"range": f"C{fila}", "values": [[str(sector_edit)]]},  # Convertimos a string
                        ]
                        if estado_nuevo == "Pendiente":
                            updates.append({"range": f"J{fila}", "values": [[""]]})

                        success, error = api_manager.safe_sheet_operation(batch_update_sheet, sheet_reclamos, updates, is_batch=True)
                        if success:
                            st.success("✅ Reclamo actualizado.")
                            st.cache_data.clear()
                            time.sleep(3)
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {error}")

            if col2.button("🔄 Cambiar solo estado", use_container_width=True):
                with st.spinner("Actualizando estado..."):
                    fila = df[df["ID Reclamo"] == reclamo_id].index[0] + 2
                    updates = [
                        {"range": f"I{fila}", "values": [[estado_nuevo]]}
                    ]
                    if estado_nuevo == "Pendiente":
                        updates.append({"range": f"J{fila}", "values": [[""]]})
                    success, error = api_manager.safe_sheet_operation(batch_update_sheet, sheet_reclamos, updates, is_batch=True)
                    if success:
                        st.success(f"☑️ Estado cambiado a {estado_nuevo}.")
                        st.cache_data.clear()
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {error}")

        # === Desconexiones a pedido ===
        st.markdown("---")
        st.markdown("### 🔌 Gestión de Desconexiones a Pedido")

        desconexiones = df[
            (df["Tipo de reclamo"].str.strip().str.lower() == "desconexion a pedido") &
            ((df["Estado"].isna()) | (df["Estado"] == ""))
        ]

        st.info(f"📄 {len(desconexiones)} desconexiones sin estado cargadas")

        for i, row in desconexiones.iterrows():
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"**{row['Nº Cliente']} - {row['Nombre']} - {format_fecha(row['Fecha y hora'])} - Sector {row['Sector']}**")
            if col2.button("Resuelto", key=f"resuelto_{i}"):
                fila = i + 2
                success, error = api_manager.safe_sheet_operation(sheet_reclamos.update, f"I{fila}", [["Resuelto"]])
                if success:
                    st.success("✅ Marcado como resuelto.")
                    st.cache_data.clear()
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error(f"❌ Error al actualizar: {error}")

    except Exception as e:
        st.error(f"⚠️ Error en la gestión de reclamos: {str(e)}")
        if DEBUG_MODE:
            st.exception(e)

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# SECCIÓN 3: GESTIÓN DE CLIENTES
# --------------------------

elif opcion == "Gestión de clientes" and has_permission('gestion_clientes'):
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("🛠️ Gestión de Clientes")

    df_clientes["Nº Cliente"] = df_clientes["Nº Cliente"].astype(str).str.strip()

    if user_role == 'admin':
        st.markdown("### ✏️ Editar datos de un cliente")

        df_clientes["label"] = df_clientes.apply(
            lambda row: f"{row['Nº Cliente']} - {row['Nombre']} - Sector {row.get('Sector', '')}",
            axis=1
        )
        seleccion_cliente = st.selectbox(
            "🔎 Seleccioná un cliente para editar",
            options=[""] + df_clientes["label"].tolist(),
            index=0
        )

        if seleccion_cliente:
            nro_cliente = seleccion_cliente.split(" - ")[0].strip()
            cliente_row = df_clientes[df_clientes["Nº Cliente"] == nro_cliente]

            if not cliente_row.empty:
                cliente_actual = cliente_row.iloc[0]

                with st.form("editar_cliente_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        # Cambiamos a selectbox para sector
                        nuevo_sector = st.selectbox(
                            "🔢 Sector (1-17)",
                            options=SECTORES_DISPONIBLES,
                            index=SECTORES_DISPONIBLES.index(int(cliente_actual["Sector"])) if cliente_actual["Sector"] in [str(s) for s in SECTORES_DISPONIBLES] else 0,
                            key="edit_sector"
                        )
                        nuevo_nombre = st.text_input("👤 Nombre", value=cliente_actual.get("Nombre", ""))
                    with col2:
                        nueva_direccion = st.text_input("📍 Dirección", value=cliente_actual.get("Dirección", ""))
                        nuevo_telefono = st.text_input("📞 Teléfono", value=cliente_actual.get("Teléfono", ""))

                    nuevo_precinto = st.text_input("🔒 N° de Precinto", 
                        value=cliente_actual.get("N° de Precinto", ""),
                        help="Número de precinto del medidor"
                    )

                    st.text_input("🆔 ID Cliente", value=cliente_actual.get("ID Cliente", "N/A"), disabled=True)

                    # Mostrar últimos 3 reclamos
                    df_reclamos_cliente = df_reclamos[df_reclamos["Nº Cliente"] == nro_cliente].copy()
                    df_reclamos_cliente["Fecha y hora"] = df_reclamos_cliente["Fecha y hora"].apply(parse_fecha)
                    df_reclamos_cliente = df_reclamos_cliente.sort_values("Fecha y hora", ascending=False).head(3)
                    with st.expander("📄 Últimos reclamos"):
                        for _, recl in df_reclamos_cliente.iterrows():
                            st.markdown(f"📅 {format_fecha(recl['Fecha y hora'], '%d/%m/%Y')} | 📌 {recl['Tipo de reclamo']} | 👷 {recl.get('Técnico', 'N/A')}")

                    # Verificar si hay cambios desde reclamos
                    cambios_detectados = False
                    for campo, nuevo_valor in zip(["Dirección", "Teléfono", "N° de Precinto"], [nueva_direccion, nuevo_telefono, nuevo_precinto]):
                        reclamos_valor = df_reclamos_cliente[campo].dropna().astype(str).str.strip().unique()
                        if len(reclamos_valor) > 0 and nuevo_valor.strip() not in reclamos_valor:
                            cambios_detectados = True

                    if cambios_detectados:
                        st.info("📌 Se detectaron datos nuevos distintos a los reclamos recientes. Podés actualizarlos si es necesario.")

                    actualizar = st.form_submit_button("💾 Actualizar datos del cliente", use_container_width=True)

                if actualizar:
                    with st.spinner("Actualizando cliente..."):
                        try:
                            index = cliente_row.index[0] + 2

                            updates = [
                                {"range": f"B{index}", "values": [[str(nuevo_sector)]]},  # Convertimos a string
                                {"range": f"C{index}", "values": [[nuevo_nombre.upper()]]},
                                {"range": f"D{index}", "values": [[nueva_direccion.upper()]]},
                                {"range": f"E{index}", "values": [[nuevo_telefono]]},
                                {"range": f"F{index}", "values": [[nuevo_precinto]]},
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
                                st.cache_data.clear()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ Error al actualizar: {error}")

                        except Exception as e:
                            st.error(f"❌ Error inesperado: {str(e)}")

        st.markdown("---")
        st.subheader("🆕 Cargar nuevo cliente")

        with st.form("form_nuevo_cliente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_nro = st.text_input("🔢 N° de Cliente (nuevo)", placeholder="Número único").strip()
                # Cambiamos a selectbox para sector en nuevo cliente
                nuevo_sector = st.selectbox(
                    "🔢 Sector (1-17)",
                    options=SECTORES_DISPONIBLES,
                    index=0,
                    key="new_sector"
                )
            with col2:
                nuevo_nombre = st.text_input("👤 Nombre", placeholder="Nombre completo")
                nueva_direccion = st.text_input("📍 Dirección", placeholder="Dirección completa")

            nuevo_telefono = st.text_input("📞 Teléfono", placeholder="Número de contacto")
            nuevo_precinto = st.text_input("🔒 N° de Precinto (opcional)", placeholder="Número de precinto")

            guardar_cliente = st.form_submit_button("💾 Guardar nuevo cliente", use_container_width=True)

            if guardar_cliente:
                if not nuevo_nombre.strip() or not nueva_direccion.strip():
                    st.error("⚠️ Debés ingresar nombre y dirección.")
                elif nuevo_nro and nuevo_nro in df_clientes["Nº Cliente"].values:
                    st.warning("⚠️ Este cliente ya existe.")
                else:
                    with st.spinner("Guardando nuevo cliente..."):
                        try:
                            import uuid
                            nuevo_id = str(uuid.uuid4())

                            nueva_fila = [
                                nuevo_nro, 
                                str(nuevo_sector),  # Convertimos a string
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
                                st.cache_data.clear()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ Error al guardar: {error}")

                        except Exception as e:
                            st.error(f"❌ Error inesperado: {str(e)}")
    else:
        st.warning("🔒 Solo los administradores pueden editar información de clientes")

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# SECCIÓN 4: IMPRIMIR RECLAMOS
# --------------------------

elif opcion == "Imprimir reclamos" and has_permission('imprimir_reclamos'):
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("🖨️ Seleccionar reclamos para imprimir (formato técnico compacto)")

    try:
        # Preparar datos con manejo robusto de fechas
        df_pdf = df_reclamos.copy()

        # Convertir fechas y manejar posibles errores
        df_pdf["Fecha y hora"] = pd.to_datetime(
            df_pdf["Fecha y hora"],
            dayfirst=True,
            errors='coerce'
        )

        df_merged = pd.merge(
            df_pdf,
            df_clientes[["Nº Cliente", "N° de Precinto"]],
            on="Nº Cliente",
            how="left",
            suffixes=("", "_cliente")
        )

        # Filtrar por sectores disponibles
        df_merged = df_merged[df_merged["Sector"].isin(SECTORES_DISPONIBLES)]

        with st.expander("🕒 Reclamos pendientes de resolución", expanded=True):
            df_pendientes = df_merged[df_merged["Estado"] == "Pendiente"]
            if not df_pendientes.empty:
                df_pendientes_display = df_pendientes.copy()
                df_pendientes_display["Fecha y hora"] = df_pendientes_display["Fecha y hora"].apply(lambda f: format_fecha(f, '%d/%m/%Y %H:%M'))

                st.dataframe(
                    df_pendientes_display[["Fecha y hora", "Nº Cliente", "Nombre", "Dirección", "Sector", "Tipo de reclamo"]],
                    use_container_width=True
                )
            else:
                st.success("✅ No hay reclamos pendientes actualmente.")

        solo_pendientes = st.checkbox("🧾 Mostrar solo reclamos pendientes para imprimir", value=True)

        st.markdown("### � Imprimir reclamos por tipo")
        tipos_disponibles = sorted(df_merged["Tipo de reclamo"].unique())
        tipos_seleccionados = st.multiselect(
            "Seleccioná tipos de reclamo a imprimir",
            tipos_disponibles,
            default=tipos_disponibles[0] if tipos_disponibles else None
        )

        if tipos_seleccionados:
            reclamos_filtrados = df_merged[
                (df_merged["Estado"] == "Pendiente") &
                (df_merged["Tipo de reclamo"].isin(tipos_seleccionados)) &
                (df_merged["Sector"].isin(SECTORES_DISPONIBLES))
            ]

            if not reclamos_filtrados.empty:
                st.success(f"Se encontraron {len(reclamos_filtrados)} reclamos pendientes de los tipos seleccionados.")

                if st.button("📄 Generar PDF de reclamos por tipo", key="pdf_tipo"):
                    with st.spinner("Generando PDF..."):
                        buffer = io.BytesIO()
                        c = canvas.Canvas(buffer, pagesize=A4)
                        width, height = A4
                        y = height - 40

                        c.setFont("Helvetica-Bold", 18)
                        c.drawString(40, y, f"RECLAMOS PENDIENTES - {datetime.now().strftime('%d/%m/%Y')}")
                        y -= 30

                        for i, (_, reclamo) in enumerate(reclamos_filtrados.iterrows()):
                            c.setFont("Helvetica-Bold", 16)
                            c.drawString(40, y, f"#{reclamo['Nº Cliente']} - {reclamo['Nombre']} ({reclamo['Sector']})")
                            y -= 15
                            c.setFont("Helvetica", 13)

                            fecha_pdf = format_fecha(reclamo['Fecha y hora'], '%d/%m/%Y %H:%M')

                            lineas = [
                                f"Fecha: {fecha_pdf}",
                                f"Dirección: {reclamo['Dirección']} - Tel: {reclamo['Teléfono']}",
                                f"Sector: {reclamo['Sector']} - Precinto: {reclamo.get('N° de Precinto', 'N/A')}",
                                f"Tipo: {reclamo['Tipo de reclamo']}",
                                f"Detalles: {reclamo['Detalles'][:100]}..." if len(reclamo['Detalles']) > 100 else f"Detalles: {reclamo['Detalles']}",
                            ]

                            for linea in lineas:
                                c.drawString(40, y, linea)
                                y -= 12

                            y -= 8
                            c.line(40, y, width-40, y)
                            y -= 15

                            if y < 100 and i < len(reclamos_filtrados) - 1:
                                agregar_pie_pdf(c, width, height)
                                c.showPage()
                                y = height - 40
                                c.setFont("Helvetica-Bold", 18)
                                c.drawString(40, y, f"RECLAMOS PENDIENTES (cont.) - {datetime.now().strftime('%d/%m/%Y')}")
                                y -= 30

                        agregar_pie_pdf(c, width, height)
                        c.save()
                        buffer.seek(0)

                        st.download_button(
                            label="📥 Descargar PDF filtrado por tipo",
                            data=buffer,
                            file_name=f"reclamos_{'_'.join(tipos_seleccionados)}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.info("No hay reclamos pendientes para los tipos seleccionados en tus sectores asignados.")

        st.markdown("### 📋 Selección manual de reclamos")

        if solo_pendientes:
            df_merged = df_merged[df_merged["Estado"] == "Pendiente"]

        # Asegurarse de mostrar solo los sectores disponibles
        df_merged = df_merged[df_merged["Sector"].isin(SECTORES_DISPONIBLES)]

        selected = st.multiselect(
            "Seleccioná los reclamos a imprimir:",
            df_merged.index,
            format_func=lambda x: f"{df_merged.at[x, 'Nº Cliente']} - {df_merged.at[x, 'Nombre']} ({df_merged.at[x, 'Sector']})",
            key="multiselect_reclamos"
        )

        if st.button("📄 Generar PDF con seleccionados", key="pdf_manual") and selected:
            with st.spinner("Generando PDF..."):
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                width, height = A4
                y = height - 40

                c.setFont("Helvetica-Bold", 18)
                c.drawString(40, y, f"RECLAMOS SELECCIONADOS - {datetime.now().strftime('%d/%m/%Y')}")
                y -= 30

                for i, idx in enumerate(selected):
                    reclamo = df_merged.loc[idx]
                    c.setFont("Helvetica-Bold", 16)
                    c.drawString(40, y, f"#{reclamo['Nº Cliente']} - {reclamo['Nombre']} ({reclamo['Sector']})")
                    y -= 15
                    c.setFont("Helvetica", 13)

                    fecha_pdf = format_fecha(reclamo['Fecha y hora'], '%d/%m/%Y %H:%M')

                    lineas = [
                        f"Fecha: {fecha_pdf}",
                        f"Dirección: {reclamo['Dirección']} - Tel: {reclamo['Teléfono']}",
                        f"Sector: {reclamo['Sector']} - Precinto: {reclamo.get('N° de Precinto', 'N/A')}",
                        f"Tipo: {reclamo['Tipo de reclamo']}",
                        f"Detalles: {reclamo['Detalles'][:100]}..." if len(reclamo['Detalles']) > 100 else f"Detalles: {reclamo['Detalles']}",
                    ]

                    for linea in lineas:
                        c.drawString(40, y, linea)
                        y -= 12

                    y -= 8
                    c.line(40, y, width-40, y)
                    y -= 15

                    if y < 100 and i < len(selected) - 1:
                        agregar_pie_pdf(c, width, height)
                        c.showPage()
                        y = height - 40
                        c.setFont("Helvetica-Bold", 18)
                        c.drawString(40, y, f"RECLAMOS SELECCIONADOS (cont.) - {datetime.now().strftime('%d/%m/%Y')}")
                        y -= 30

                agregar_pie_pdf(c, width, height)
                c.save()
                buffer.seek(0)

                st.download_button(
                    label="📥 Descargar PDF seleccionados",
                    data=buffer,
                    file_name="reclamos_seleccionados.pdf",
                    mime="application/pdf"
                )

        elif not selected:
            st.info("Seleccioná al menos un reclamo para generar el PDF.")

        st.markdown("### 📦 Exportar todos los reclamos 'Pendiente' y 'En curso'")
        todos_filtrados = df_merged[df_merged["Estado"].isin(["Pendiente", "En curso"])].copy()

        if not todos_filtrados.empty:
            if st.button("📄 Generar PDF de todos los reclamos activos", key="pdf_todos"):
                with st.spinner("Generando PDF completo..."):
                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer, pagesize=A4)
                    width, height = A4
                    y = height - 40

                    c.setFont("Helvetica-Bold", 18)
                    c.drawString(40, y, f"TODOS LOS RECLAMOS ACTIVOS - {datetime.now().strftime('%d/%m/%Y')}")
                    y -= 30

                    for i, (_, reclamo) in enumerate(todos_filtrados.iterrows()):
                        c.setFont("Helvetica-Bold", 16)
                        c.drawString(40, y, f"#{reclamo['Nº Cliente']} - {reclamo['Nombre']} ({reclamo['Sector']})")
                        y -= 15
                        c.setFont("Helvetica", 13)

                        fecha_pdf = format_fecha(reclamo['Fecha y hora'], '%d/%m/%Y %H:%M')

                        lineas = [
                            f"Fecha: {fecha_pdf}",
                            f"Dirección: {reclamo['Dirección']} - Tel: {reclamo['Teléfono']}",
                            f"Sector: {reclamo['Sector']} - Precinto: {reclamo.get('N° de Precinto', 'N/A')}",
                            f"Tipo: {reclamo['Tipo de reclamo']}",
                            f"Detalles: {reclamo['Detalles'][:100]}..." if len(reclamo['Detalles']) > 100 else f"Detalles: {reclamo['Detalles']}",
                        ]
                        for linea in lineas:
                            c.drawString(40, y, linea)
                            y -= 12

                        y -= 10
                        c.line(40, y, width-40, y)
                        y -= 15

                        if y < 100:
                            agregar_pie_pdf(c, width, height)
                            c.showPage()
                            y = height - 40
                            c.setFont("Helvetica-Bold", 18)
                            c.drawString(40, y, f"RECLAMOS ACTIVOS (cont.) - {datetime.now().strftime('%d/%m/%Y')}")
                            y -= 30

                    agregar_pie_pdf(c, width, height)
                    c.save()
                    buffer.seek(0)

                    st.download_button(
                        label="📥 Descargar TODOS los reclamos activos en PDF",
                        data=buffer,
                        file_name="reclamos_activos_completo.pdf",
                        mime="application/pdf"
                    )
        else:
            st.info("🎉 No hay reclamos activos actualmente en tus sectores asignados.")

    except Exception as e:
        st.error(f"❌ Error al generar PDF: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# SECCIÓN 5: PLANIFICACIÓN DE GRUPOS DE TRABAJO
# --------------------------

elif opcion == "Seguimiento técnico" and user_role == 'admin':
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("🧭 Asignación de reclamos a grupos de trabajo")

    if "asignaciones_grupos" not in st.session_state:
        st.session_state.asignaciones_grupos = {
            "Grupo A": [], "Grupo B": [], "Grupo C": [], "Grupo D": []
        }

    if "tecnicos_grupos" not in st.session_state:
        st.session_state.tecnicos_grupos = {
            "Grupo A": [], "Grupo B": [], "Grupo C": [], "Grupo D": []
        }

    if st.button("🔄 Refrescar reclamos"):
        df_reclamos = cargar_reclamos()
        st.cache_data.clear()
        st.rerun()

    grupos_activos = st.slider("🛠️ Cantidad de grupos de trabajo activos", 1, 4, 2)

    st.markdown("### 👥 Asignar técnicos a cada grupo")
    for grupo in list(st.session_state.tecnicos_grupos.keys())[:grupos_activos]:
        st.session_state.tecnicos_grupos[grupo] = st.multiselect(
            f"{grupo} - Técnicos asignados",
            TECNICOS_DISPONIBLES,
            default=st.session_state.tecnicos_grupos[grupo],
            key=f"tecnicos_{grupo}"
        )

    st.markdown("---")
    st.markdown("### 📋 Reclamos pendientes para asignar")

    df_reclamos.columns = df_reclamos.columns.str.strip()
    df_reclamos["ID Temporal"] = df_reclamos["ID Reclamo"].astype(str).str.strip()
    df_reclamos["Fecha y hora"] = pd.to_datetime(df_reclamos["Fecha y hora"], dayfirst=True, errors='coerce')

    df_pendientes = df_reclamos[df_reclamos["Estado"] == "Pendiente"].copy()

    # Cambiamos el filtro de sector para usar SECTORES_DISPONIBLES
    filtro_sector = st.selectbox(
        "Filtrar por sector", 
        ["Todos"] + sorted(SECTORES_DISPONIBLES),
        format_func=lambda x: f"Sector {x}" if x != "Todos" else x
    )
    
    filtro_tipo = st.selectbox(
        "Filtrar por tipo de reclamo", 
        ["Todos"] + sorted(df_pendientes["Tipo de reclamo"].dropna().unique())
    )

    if filtro_sector != "Todos":
        df_pendientes = df_pendientes[df_pendientes["Sector"] == str(filtro_sector)]  # Convertimos a string para comparar
    if filtro_tipo != "Todos":
        df_pendientes = df_pendientes[df_pendientes["Tipo de reclamo"] == filtro_tipo]

    def format_fecha(fecha):
        if pd.isna(fecha): return "Sin fecha"
        try: return fecha.strftime('%d/%m/%Y')
        except: return "Fecha inválida"

    orden = st.selectbox("📊 Ordenar reclamos por:", ["Fecha más reciente", "Sector", "Tipo de reclamo"])
    if orden == "Fecha más reciente":
        df_pendientes = df_pendientes.sort_values("Fecha y hora", ascending=False)
    elif orden == "Sector":
        df_pendientes = df_pendientes.sort_values("Sector")
    elif orden == "Tipo de reclamo":
        df_pendientes = df_pendientes.sort_values("Tipo de reclamo")

    asignados = [r for reclamos in st.session_state.asignaciones_grupos.values() for r in reclamos]
    df_disponibles = df_pendientes[~df_pendientes["ID Reclamo"].isin(asignados)]

    for idx, row in df_disponibles.iterrows():
        with st.container():
            col1, *cols_grupo = st.columns([4] + [1]*grupos_activos)
            fecha_formateada = format_fecha(row["Fecha y hora"])
            resumen = f"📍 Sector {row['Sector']} - {row['Tipo de reclamo'].capitalize()} - {fecha_formateada}"
            col1.markdown(f"**{resumen}**")

            for i, grupo in enumerate(["Grupo A", "Grupo B", "Grupo C", "Grupo D"][:grupos_activos]):
                tecnicos = st.session_state.tecnicos_grupos[grupo]
                tecnicos_str = ", ".join(tecnicos[:2]) + ("..." if len(tecnicos) > 2 else "") if tecnicos else "Sin técnicos"
                if cols_grupo[i].button(f"➕ {grupo[-1]} ({tecnicos_str})", key=f"asignar_{grupo}_{row['ID Reclamo']}"):
                    if row["id"] not in asignados:
                        st.session_state.asignaciones_grupos[grupo].append(row["id"])
                        st.rerun()

            with col1.expander("ℹ️ Ver detalles"):
                st.markdown(f"""
                **📟 Nº Cliente:** {row['Nº Cliente']}  
                **👤 Nombre:** {row['Nombre']}  
                **📍 Dirección:** {row['Dirección']}  
                **📞 Teléfono:** {row['Teléfono']}  
                **📅 Fecha completa:** {row['Fecha y hora'].strftime('%d/%m/%Y %H:%M') if not pd.isna(row['Fecha y hora']) else 'Sin fecha'}  
                """)
                if row.get("Detalles"):
                    st.markdown(f"**📝 Detalles:** {row['Detalles'][:250]}{'...' if len(row['Detalles']) > 250 else ''}")
        st.divider()

    st.markdown("---")
    st.markdown("### 🧺 Reclamos asignados por grupo")

    materiales_por_grupo = {}

    for grupo in ["Grupo A", "Grupo B", "Grupo C", "Grupo D"][:grupos_activos]:
        reclamos_ids = st.session_state.asignaciones_grupos[grupo]
        tecnicos = st.session_state.tecnicos_grupos[grupo]
        st.markdown(f"#### 🛠️ {grupo} - Técnicos: {', '.join(tecnicos) if tecnicos else 'Sin asignar'} ({len(reclamos_ids)} reclamos)")

        reclamos_grupo = df_pendientes[df_pendientes["ID Reclamo"].isin(reclamos_ids)]

        resumen_tipos = " - ".join([f"{v} {k}" for k, v in reclamos_grupo["Tipo de reclamo"].value_counts().items()])
        sectores = ", ".join(sorted(set(reclamos_grupo["Sector"].astype(str))))
        st.markdown(resumen_tipos)
        st.markdown(f"Sectores: {sectores}")

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

        materiales_por_grupo[grupo] = materiales_total

        if materiales_total:
            st.markdown("📦 **Materiales mínimos estimados:**")
            for mat, cant in materiales_total.items():
                st.markdown(f"- {cant} {mat.replace('_', ' ').title()}")

        if reclamos_ids:
            for reclamo_id in reclamos_ids:
                reclamo_data = df_pendientes[df_pendientes["ID Reclamo"] == reclamo_id]
                col1, col2 = st.columns([5, 1])
                if not reclamo_data.empty:
                    row = reclamo_data.iloc[0]
                    fecha_formateada = format_fecha(row["Fecha y hora"])
                    resumen = f"📍 Sector {row['Sector']} - {row['Tipo de reclamo'].capitalize()} - {fecha_formateada}"
                    col1.markdown(f"**{resumen}**")
                else:
                    col1.markdown(f"**Reclamo ID: {reclamo_id} (ya no está pendiente)**")

                if col2.button("❌ Quitar", key=f"quitar_{grupo}_{reclamo_id}"):
                    st.session_state.asignaciones_grupos[grupo].remove(reclamo_id)
                    st.rerun()
                st.divider()
        else:
            st.info("Este grupo no tiene reclamos asignados.")

    st.markdown("---")

    if st.button("💾 Guardar cambios y pasar a 'En curso'", use_container_width=True):
        errores = []
        for grupo, reclamos in st.session_state.asignaciones_grupos.items():
            if reclamos and not st.session_state.tecnicos_grupos[grupo]:
                errores.append(grupo)

        if errores:
            st.warning(f"⚠️ Los siguientes grupos tienen reclamos asignados pero sin técnicos: {', '.join(errores)}")
        else:
            with st.spinner("Actualizando reclamos..."):
                updates = []
                for grupo, ids in st.session_state.asignaciones_grupos.items():
                    tecnicos = st.session_state.tecnicos_grupos[grupo]
                    tecnicos_str = ", ".join(tecnicos).upper() if tecnicos else ""
                    for reclamo_id in ids:
                        fila = df_reclamos[df_reclamos["UUID"] == reclamo_id]
                        if not fila.empty:
                            index = fila.index[0] + 2
                            updates.append({"range": f"I{index}", "values": [["En curso"]]})
                            updates.append({"range": f"J{index}", "values": [[tecnicos_str]]})
                        else:
                            st.warning(f"⚠️ Reclamo con ID {reclamo_id} no encontrado en la hoja.")

                if updates:
                    success, error = api_manager.safe_sheet_operation(batch_update_sheet, sheet_reclamos, updates, is_batch=True)
                    if success:
                        st.success("✅ Reclamos actualizados correctamente en la hoja.")
                        st.cache_data.clear()
                        df_reclamos = cargar_reclamos()
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error("❌ Error al actualizar: " + str(error))

    if st.button("📅 Generar PDF de asignaciones por grupo", use_container_width=True):
        with st.spinner("Generando PDF..."):
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            y = height - 40
            hoy = datetime.now().strftime('%d/%m/%Y')

            for grupo in ["Grupo A", "Grupo B", "Grupo C", "Grupo D"][:grupos_activos]:
                reclamos_ids = st.session_state.asignaciones_grupos[grupo]
                tecnicos = st.session_state.tecnicos_grupos[grupo]

                if not reclamos_ids:
                    continue

                agregar_pie_pdf(c, width, height)
                c.showPage()
                y = height - 40

                tipos = df_pendientes[df_pendientes["ID Reclamo"].isin(reclamos_ids)]["Tipo de reclamo"].value_counts()
                resumen_tipos = " - ".join([f"{v} {k}" for k, v in tipos.items()])

                c.setFont("Helvetica-Bold", 16)
                c.drawString(40, y, f"{grupo} - Técnicos: {', '.join(tecnicos)} (Asignado el {hoy})")
                y -= 20
                c.setFont("Helvetica", 12)
                c.drawString(40, y, resumen_tipos)
                y -= 25

                for reclamo_id in reclamos_ids:
                    reclamo_data = df_pendientes[df_pendientes["ID Reclamo"] == reclamo_id]
                    if not reclamo_data.empty:
                        reclamo = reclamo_data.iloc[0]
                        c.setFont("Helvetica-Bold", 14)
                        c.drawString(40, y, f"{reclamo['Nº Cliente']} - {reclamo['Nombre']}")
                        y -= 15
                        c.setFont("Helvetica", 11)

                        fecha_pdf = format_fecha(reclamo["Fecha y hora"]) if pd.isna(reclamo["Fecha y hora"]) else reclamo["Fecha y hora"].strftime('%d/%m/%Y %H:%M')
                        lineas = [
                            f"Fecha: {fecha_pdf}",
                            f"Dirección: {reclamo['Dirección']} - Tel: {reclamo['Teléfono']}",
                            f"Sector: {reclamo['Sector']} - Precinto: {reclamo.get('N° de Precinto', 'N/A')}",
                            f"Tipo: {reclamo['Tipo de reclamo']}",
                            f"Detalles: {reclamo['Detalles'][:100]}..." if len(reclamo['Detalles']) > 100 else f"Detalles: {reclamo['Detalles']}",
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
                label="📅 Descargar PDF de asignaciones",
                data=buffer,
                file_name="asignaciones_grupos.pdf",
                mime="application/pdf"
            )

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# SECCIÓN 6: CIERRE DE RECLAMOS
# --------------------------
elif opcion == "Cierre de Reclamos" and has_permission('cierre_reclamos'):
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.subheader("✅ Cierre de reclamos en curso")

    # Normalización de datos
    df_reclamos["ID Reclamo"] = df_reclamos["ID Reclamo"].astype(str).str.strip()
    df_reclamos["Nº Cliente"] = df_reclamos["Nº Cliente"].astype(str).str.strip()
    df_reclamos["Técnico"] = df_reclamos["Técnico"].astype(str).fillna("")
    df_reclamos["Fecha y hora"] = df_reclamos["Fecha y hora"].apply(parse_fecha)

    st.markdown("### 🔄 Reasignar técnico por N° de cliente")
    cliente_busqueda = st.text_input("🔢 Ingresá el N° de Cliente para buscar", key="buscar_cliente_tecnico").strip()
    if cliente_busqueda:
        reclamos_filtrados = df_reclamos[
            (df_reclamos["Nº Cliente"] == cliente_busqueda) &
            (df_reclamos["Estado"].isin(["Pendiente", "En curso"]))
        ]

        if not reclamos_filtrados.empty:
            reclamo = reclamos_filtrados.iloc[0]
            st.markdown(f"📌 **Reclamo encontrado:** {reclamo['Tipo de reclamo']} - Estado: {reclamo['Estado']}")
            st.markdown(f"👷 Técnico actual: `{reclamo['Técnico'] or 'No asignado'}`")
            st.markdown(f"📅 Fecha del reclamo: `{format_fecha(reclamo['Fecha y hora'])}`")
            st.markdown(f"📍 Sector: `{reclamo.get('Sector', 'No especificado')}`")  # Mostrar sector del reclamo

            tecnicos_actuales_raw = [t.strip().lower() for t in reclamo["Técnico"].split(",") if t.strip()]
            tecnicos_actuales = [tecnico for tecnico in TECNICOS_DISPONIBLES if tecnico.lower() in tecnicos_actuales_raw]
            nuevo_tecnico_multiselect = st.multiselect(
                "👷 Nuevo técnico asignado",
                options=TECNICOS_DISPONIBLES,
                default=tecnicos_actuales,
                key="nuevo_tecnico_input"
            )

            if st.button("💾 Guardar nuevo técnico", key="guardar_tecnico"):
                with st.spinner("Actualizando técnico..."):
                    try:
                        fila_index = reclamo.name + 2
                        nuevo_tecnico = ", ".join(nuevo_tecnico_multiselect).upper()
                        updates = [{"range": f"J{fila_index}", "values": [[nuevo_tecnico]]}]
                        if reclamo['Estado'] == "Pendiente":
                            updates.append({"range": f"I{fila_index}", "values": [["En curso"]]})
                        success, error = api_manager.safe_sheet_operation(
                            batch_update_sheet,
                            sheet_reclamos,
                            updates,
                            is_batch=True
                        )
                        if success:
                            st.success("✅ Técnico actualizado correctamente.")
                            st.cache_data.clear()
                            time.sleep(3)
                            st.rerun()
                        else:
                            st.error(f"❌ Error al actualizar: {error}")
                            if DEBUG_MODE:
                                st.write("Detalles del error:", error)
                    except Exception as e:
                        st.error(f"❌ Error inesperado: {str(e)}")
                        if DEBUG_MODE:
                            st.exception(e)
        else:
            st.warning("⚠️ No se encontró un reclamo pendiente o en curso para ese cliente.")

    # Filtro de sector para reclamos en curso
    en_curso = df_reclamos[df_reclamos["Estado"] == "En curso"].copy()
    
    # Agregar filtro por sector usando SECTORES_DISPONIBLES
    filtro_sector = st.selectbox(
        "🔢 Filtrar por sector", 
        ["Todos"] + sorted(SECTORES_DISPONIBLES),
        key="filtro_sector_cierre",
        format_func=lambda x: f"Sector {x}" if x != "Todos" else x
    )
    
    if filtro_sector != "Todos":
        en_curso = en_curso[en_curso["Sector"] == str(filtro_sector)]  # Convertir a string para comparación

    if en_curso.empty:
        st.info("📭 No hay reclamos en curso en este momento.")
    else:
        tecnicos_unicos = sorted(set(
            tecnico.strip().upper()
            for t in en_curso["Técnico"]
            for tecnico in t.split(",")
            if tecnico.strip()
        ))

        tecnicos_seleccionados = st.multiselect("👷 Filtrar por técnico asignado", tecnicos_unicos, key="filtro_tecnicos")

        if tecnicos_seleccionados:
            en_curso = en_curso[
                en_curso["Técnico"].apply(lambda t: any(tecnico.strip().upper() in t.upper() for tecnico in tecnicos_seleccionados))
            ]

        st.write("### 📋 Reclamos en curso:")
        df_mostrar = en_curso[["Fecha_formateada", "Nº Cliente", "Nombre", "Sector", "Tipo de reclamo", "Técnico"]].copy()
        df_mostrar = df_mostrar.rename(columns={"Fecha_formateada": "Fecha y hora"})

        st.dataframe(df_mostrar, use_container_width=True, height=400,
                    column_config={
                        "Fecha y hora": st.column_config.TextColumn(
                            "Fecha y hora",
                            help="Fecha del reclamo en formato DD/MM/YYYY HH:MM"
                        ),
                        "Sector": st.column_config.TextColumn(
                            "Sector",
                            help="Número de sector asignado"
                        )
                    })

        st.markdown("### ✏️ Acciones por reclamo:")

        for i, row in en_curso.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**#{row['Nº Cliente']} - {row['Nombre']}**")
                    st.markdown(f"📅 {format_fecha(row['Fecha y hora'])}")
                    st.markdown(f"📍 Sector: {row.get('Sector', 'N/A')}")  # Mostrar sector
                    st.markdown(f"📌 {row['Tipo de reclamo']}")
                    st.markdown(f"👷 {row['Técnico']}")

                    cliente_id = str(row["Nº Cliente"]).strip()
                    cliente_info = df_clientes[df_clientes["Nº Cliente"] == cliente_id]
                    precinto_actual = cliente_info["N° de Precinto"].values[0] if not cliente_info.empty else ""

                    nuevo_precinto = st.text_input("🔒 Precinto", value=precinto_actual, key=f"precinto_{i}")

                with col2:
                    if st.button("✅ Resuelto", key=f"resolver_{row['ID Reclamo']}", use_container_width=True):
                        with st.spinner("Cerrando reclamo..."):
                            try:
                                fila_index = row.name + 2
                                updates = [{"range": f"I{fila_index}", "values": [["Resuelto"]]}]
                                if len(COLUMNAS_RECLAMOS) > 12:
                                    fecha_resolucion = format_fecha(ahora_argentina())
                                    updates.append({"range": f"M{fila_index}", "values": [[fecha_resolucion]]})
                                if nuevo_precinto.strip() and nuevo_precinto != precinto_actual:
                                    updates.append({"range": f"F{fila_index}", "values": [[nuevo_precinto.strip()]]})
                                success, error = api_manager.safe_sheet_operation(
                                    batch_update_sheet,
                                    sheet_reclamos,
                                    updates,
                                    is_batch=True
                                )
                                if success:
                                    if nuevo_precinto.strip() and nuevo_precinto != precinto_actual and not cliente_info.empty:
                                        index_cliente_en_clientes = cliente_info.index[0] + 2
                                        success_precinto, error_precinto = api_manager.safe_sheet_operation(
                                            sheet_clientes.update,
                                            f"F{index_cliente_en_clientes}",
                                            [[nuevo_precinto.strip()]]
                                        )
                                        if not success_precinto:
                                            st.warning(f"⚠️ Precinto guardado en reclamo pero no en hoja de clientes: {error_precinto}")
                                    st.success(f"🟢 Reclamo de {row['Nombre']} cerrado correctamente.")
                                    st.cache_data.clear()
                                    time.sleep(3)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error al actualizar: {error}")
                                    if DEBUG_MODE:
                                        st.write("Detalles del error:", error)
                            except Exception as e:
                                st.error(f"❌ Error inesperado: {str(e)}")
                                if DEBUG_MODE:
                                    st.exception(e)

                with col3:
                    if st.button("↩️ Pendiente", key=f"volver_{row['ID Reclamo']}", use_container_width=True):
                        with st.spinner("Cambiando estado..."):
                            try:
                                fila_index = row.name + 2
                                updates = [
                                    {"range": f"I{fila_index}", "values": [["Pendiente"]]},
                                    {"range": f"J{fila_index}", "values": [[""]]}
                                ]
                                success, error = api_manager.safe_sheet_operation(
                                    batch_update_sheet,
                                    sheet_reclamos,
                                    updates,
                                    is_batch=True
                                )
                                if success:
                                    st.success(f"🔄 Reclamo de {row['Nombre']} vuelto a PENDIENTE.")
                                    st.cache_data.clear()
                                    time.sleep(3)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error al actualizar: {error}")
                                    if DEBUG_MODE:
                                        st.write("Detalles del error:", error)
                            except Exception as e:
                                st.error(f"❌ Error inesperado: {str(e)}")
                                if DEBUG_MODE:
                                    st.exception(e)
                st.divider()

    st.markdown("---")
    st.markdown("### 🗑️ Limpieza de reclamos antiguos")

    tz_argentina = pytz.timezone("America/Argentina/Buenos_Aires")
    df_resueltos = df_reclamos[df_reclamos["Estado"] == "Resuelto"].copy()
    df_resueltos["Fecha y hora"] = pd.to_datetime(df_resueltos["Fecha y hora"])
    if df_resueltos["Fecha y hora"].dt.tz is None:
        df_resueltos["Fecha y hora"] = df_resueltos["Fecha y hora"].dt.tz_localize(tz_argentina)
    else:
        df_resueltos["Fecha y hora"] = df_resueltos["Fecha y hora"].dt.tz_convert(tz_argentina)
    df_resueltos["Dias_resuelto"] = (datetime.now(tz_argentina) - df_resueltos["Fecha y hora"]).dt.days
    df_antiguos = df_resueltos[df_resueltos["Dias_resuelto"] > 10]

    st.markdown(f"📅 **Reclamos resueltos con más de 10 días:** {len(df_antiguos)}")

    if len(df_antiguos) > 0:
        if st.button("🔍 Ver reclamos antiguos", key="ver_antiguos"):
            st.dataframe(df_antiguos[["Fecha y hora", "Nº Cliente", "Nombre", "Sector", "Tipo de reclamo", "Dias_resuelto"]])
        if st.button("🗑️ Eliminar reclamos antiguos", key="eliminar_antiguos"):
            with st.spinner("Eliminando reclamos antiguos..."):
                try:
                    filas_a_eliminar = [idx + 2 for idx in df_antiguos.index]
                    batch_size = 50
                    for i in range(0, len(filas_a_eliminar), batch_size):
                        batch = filas_a_eliminar[i:i + batch_size]
                        requests = [{
                            "deleteDimension": {
                                "range": {
                                    "sheetId": sheet_reclamos.id,
                                    "dimension": "ROWS",
                                    "startIndex": fila - 1,
                                    "endIndex": fila
                                }
                            }
                        } for fila in batch]
                        success, error = api_manager.safe_sheet_operation(
                            sheet_reclamos.spreadsheet.batch_update,
                            {"requests": requests}
                        )
                        if not success:
                            st.error(f"Error al eliminar lote {i//batch_size + 1}: {error}")
                            break
                    if success:
                        st.success(f"✅ Se eliminaron {len(df_antiguos)} reclamos antiguos correctamente.")
                        st.cache_data.clear()
                        time.sleep(3)
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error al eliminar reclamos: {str(e)}")
                    if DEBUG_MODE:
                        st.exception(e)

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------
# NUEVO FOOTER - RESUMEN DE LA JORNADA
# --------------------------
st.markdown("---")
st.markdown('<div class="section-container">', unsafe_allow_html=True)
st.markdown("### 📋 Resumen de la jornada")

# Función auxiliar para formatear fechas
def format_fecha(fecha, formato='%d/%m/%Y %H:%M'):
    """Formatea una fecha para visualización consistente"""
    if pd.isna(fecha) or fecha is None:
        return "Fecha no disponible"
    try:
        if isinstance(fecha, str):
            fecha = pd.to_datetime(fecha, dayfirst=True, format='mixed')
        return fecha.strftime(formato)
    except:
        return "Fecha inválida"

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

    # Crear un set inmutable de técnicos asignados por reclamo (para detectar duplicados)
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

st.markdown("""
    <div style='text-align: center; margin-top: 20px; font-size: 0.9em; color: gray;'>
        © 2025 - Hecho con amor por: 
        <a href="https://instagram.com/mellamansebax" target="_blank" style="text-decoration: none; color: inherit; font-weight: bold;">
            Sebastián Andrés
        </a> 💜
    </div>
""", unsafe_allow_html=True)
