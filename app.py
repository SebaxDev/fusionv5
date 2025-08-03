# --------------------------------------------------
# Aplicación principal de gestión de reclamos optimizada
# Versión 2.3 - Diseño optimizado para rendimiento
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
from components.reclamos.nuevo import render_nuevo_reclamo
from components.reclamos.gestion import render_gestion_reclamos
from components.clientes.gestion import render_gestion_clientes
from components.reclamos.impresion import render_impresion_reclamos
from components.reclamos.planificacion import render_planificacion_grupos
from components.reclamos.cierre import render_cierre_reclamos
from components.resumen_jornada import render_resumen_jornada

from components.auth import has_permission, check_authentication, render_login
from components.navigation import render_navigation
from components.metrics_dashboard import render_metrics_dashboard
from components.user_widget import render_user_widget

# Utils
from utils.styles import get_main_styles, get_loading_spinner
from utils.data_manager import safe_get_sheet_data, safe_normalize, update_sheet_data, batch_update_sheet
from utils.api_manager import api_manager, init_api_session_state
from utils.pdf_utils import agregar_pie_pdf
from utils.date_utils import parse_fecha, es_fecha_valida, format_fecha, ahora_argentina

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
# FUNCIONES AUXILIARES OPTIMIZADAS
# --------------------------

def generar_id_unico():
    """Genera un ID único para reclamos"""
    import uuid
    return str(uuid.uuid4())[:8].upper()

def is_mobile():
    """Detecta si el dispositivo es móvil"""
    user_agent = st.query_params.get("user_agent", [""])[0]
    mobile_keywords = ['iphone', 'android', 'mobile', 'ipad', 'tablet']
    return any(keyword in user_agent.lower() for keyword in mobile_keywords)

def is_system_dark_mode():
    """Detecta el modo oscuro del sistema"""
    import platform
    if platform.system() == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
            return value == 0
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
        return False

def show_error(message):
    """Muestra un mensaje de error optimizado"""
    st.error(message)

def show_success(message):
    """Muestra un mensaje de éxito optimizado"""
    st.success(message)

def show_warning(message):
    """Muestra un mensaje de advertencia optimizado"""
    st.warning(message)

# --------------------------
# CONFIGURACIÓN DE PÁGINA
# --------------------------

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
            'About': "Sistema de gestión de reclamos v2.3"
        }
    )

# Inyectar estilos CSS optimizados
if "modo_oscuro" not in st.session_state:
    st.session_state.modo_oscuro = is_system_dark_mode()

st.markdown(get_main_styles(dark_mode=st.session_state.modo_oscuro), unsafe_allow_html=True)

# --------------------------
# SIDEBAR OPTIMIZADO
# --------------------------

with st.sidebar:
    st.markdown("### Panel de Control")
    
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
    render_user_widget()
    
    st.markdown(f"""
    <div style="margin-top: 20px;">
        <p style="margin:0;"><strong>Versión:</strong> 2.3.0</p>
        <p style="margin:0;"><strong>Última actualización:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
    </div>
    """, unsafe_allow_html=True)

# --------------------------
# INICIALIZACIÓN
# --------------------------

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

app_state = AppState()

# --------------------------
# CONEXIÓN CON GOOGLE SHEETS
# --------------------------

@st.cache_resource(ttl=3600)
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
        show_error(f"Error de conexión: {str(e)}")
        st.stop()

# Carga con spinner optimizado
loading_placeholder = st.empty()
loading_placeholder.markdown(get_loading_spinner(), unsafe_allow_html=True)
try:
    sheet_reclamos, sheet_clientes, sheet_usuarios = init_google_sheets()
    if not all([sheet_reclamos, sheet_clientes, sheet_usuarios]):
        st.stop()
finally:
    loading_placeholder.empty()

# --------------------------
# AUTENTICACIÓN
# --------------------------

if not check_authentication():
    render_login(sheet_usuarios)
    st.stop()

user_info = st.session_state.auth.get('user_info', {})
user_role = user_info.get('rol', '')

# --------------------------
# CARGA DE DATOS OPTIMIZADA
# --------------------------

@st.cache_data(ttl=30, show_spinner=False)
def cargar_datos():
    """Carga datos de Google Sheets con manejo robusto de fechas"""
    try:
        loading_placeholder = st.empty()
        loading_placeholder.markdown(get_loading_spinner(), unsafe_allow_html=True)
        
        df_reclamos = safe_get_sheet_data(sheet_reclamos, COLUMNAS_RECLAMOS)
        df_clientes = safe_get_sheet_data(sheet_clientes, COLUMNAS_CLIENTES)
        df_usuarios = safe_get_sheet_data(sheet_usuarios, COLUMNAS_USUARIOS)
        
        if df_reclamos.empty:
            show_warning("La hoja de reclamos está vacía o no se pudo cargar")
        if df_clientes.empty:
            show_warning("La hoja de clientes está vacía o no se pudo cargar")
        if df_reclamos.empty or df_clientes.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Normalización de datos
        for col in ["Nº Cliente", "N° de Precinto"]:
            if col in df_clientes.columns:
                df_clientes[col] = df_clientes[col].astype(str).str.strip()
            if col in df_reclamos.columns:
                df_reclamos[col] = df_reclamos[col].astype(str).str.strip()

        if 'Fecha y hora' in df_reclamos.columns:
            df_reclamos['Fecha y hora'] = df_reclamos['Fecha y hora'].apply(
                lambda x: parse_fecha(x) if not pd.isna(x) else pd.NaT
            )
            df_reclamos['Fecha_formateada'] = df_reclamos['Fecha y hora'].apply(
                lambda x: format_fecha(x, '%d/%m/%Y %H:%M', 'Fecha inválida')
            )
            
        return df_reclamos, df_clientes, df_usuarios
        
    except Exception as e:
        show_error(f"Error al cargar datos: {str(e)}")
        if DEBUG_MODE:
            st.exception(e)
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    finally:
        loading_placeholder.empty()

df_reclamos, df_clientes, df_usuarios = cargar_datos()
st.session_state.df_reclamos = df_reclamos
st.session_state.df_clientes = df_clientes

# --------------------------
# INTERFAZ PRINCIPAL OPTIMIZADA
# --------------------------

st.markdown("""
<div style="text-align: center;">
    <h1 style="margin:0; margin-bottom:0.5rem;">
        📋 Fusion Reclamos App
    </h1>
    <p style="margin:0;">
        Sistema integral de gestión de reclamos técnicos
    </p>
</div>
""", unsafe_allow_html=True)

# Dashboard de métricas
render_metrics_dashboard(df_reclamos, is_mobile=is_mobile())

# Navegación optimizada
opcion = render_navigation() if not is_mobile() else st.selectbox(
    "Menú principal",
    options=["Inicio", "Reclamos cargados", "Cierre de Reclamos"],
    index=0,
    key="mobile_nav"
)

# --------------------------
# RUTEO DE COMPONENTES
# --------------------------

COMPONENTES = {
    "Inicio": {
        "render": render_nuevo_reclamo,
        "permiso": "inicio",
        "params": {
            "df_reclamos": df_reclamos,
            "df_clientes": df_clientes,
            "sheet_reclamos": sheet_reclamos,
            "sheet_clientes": sheet_clientes,
            "current_user": user_info.get('nombre', '')
        }
    },
    "Reclamos cargados": {
        "render": render_gestion_reclamos,
        "permiso": "reclamos_cargados",
        "params": {
            "df_reclamos": df_reclamos,
            "df_clientes": df_clientes,
            "sheet_reclamos": sheet_reclamos,
            "user": user_info
        }
    },
    "Gestión de clientes": {
        "render": render_gestion_clientes,
        "permiso": "gestion_clientes",
        "params": {
            "df_clientes": df_clientes,
            "df_reclamos": df_reclamos,
            "sheet_clientes": sheet_clientes,
            "user": user_info
        }
    },
    "Imprimir reclamos": {
        "render": render_impresion_reclamos,
        "permiso": "imprimir_reclamos",
        "params": {
            "df_reclamos": df_reclamos,
            "df_clientes": df_clientes
        }
    },
    "Seguimiento técnico": {
        "render": render_planificacion_grupos,
        "permiso": "seguimiento_tecnico",
        "params": {
            "df_reclamos": df_reclamos,
            "sheet_reclamos": sheet_reclamos,
            "user": user_info
        }
    },
    "Cierre de Reclamos": {
        "render": render_cierre_reclamos,
        "permiso": "cierre_reclamos",
        "params": {
            "df_reclamos": df_reclamos,
            "df_clientes": df_clientes,
            "sheet_reclamos": sheet_reclamos,
            "sheet_clientes": sheet_clientes,
            "user": user_info
        }
    }
}

# Renderizar componente seleccionado
if opcion in COMPONENTES and has_permission(COMPONENTES[opcion]["permiso"]):
    with st.container():
        st.markdown('<div class="section-container">', unsafe_allow_html=True)
        resultado = COMPONENTES[opcion]["render"](**COMPONENTES[opcion]["params"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        if resultado and resultado.get('needs_refresh'):
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()

# --------------------------
# RESUMEN DE JORNADA OPTIMIZADO
# --------------------------
st.markdown("---")
with st.container():
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    render_resumen_jornada(df_reclamos)
    st.markdown('</div>', unsafe_allow_html=True)