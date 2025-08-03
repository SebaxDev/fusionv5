# --------------------------------------------------
# Aplicación principal de gestión de reclamos optimizada
# Versión 2.2 - Con diseño profesional mejorado
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
# FUNCIONES AUXILIARES MEJORADAS
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
    """Muestra un mensaje de error con estilo mejorado"""
    st.markdown(f"""
    <div class="stAlert">
        <p style="color:var(--danger-color);">❌ {message}</p>
    </div>
    """, unsafe_allow_html=True)

def show_success(message):
    """Muestra un mensaje de éxito con estilo mejorado"""
    st.markdown(f"""
    <div class="stAlert">
        <p style="color:var(--success-color);">✅ {message}</p>
    </div>
    """, unsafe_allow_html=True)

def show_warning(message):
    """Muestra un mensaje de advertencia con estilo mejorado"""
    st.markdown(f"""
    <div class="stAlert">
        <p style="color:var(--warning-color);">⚠️ {message}</p>
    </div>
    """, unsafe_allow_html=True)

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
            'About': "Sistema de gestión de reclamos v2.2"
        }
    )

# Inyectar estilos CSS personalizados
if "modo_oscuro" not in st.session_state:
    st.session_state.modo_oscuro = is_system_dark_mode()

st.markdown(get_main_styles(dark_mode=st.session_state.modo_oscuro), unsafe_allow_html=True)

# --------------------------
# SIDEBAR MEJORADO
# --------------------------

with st.sidebar:
    st.markdown("""
    <div class="neumorphic">
        <h3 style="margin:0; color:var(--primary-color);">Panel de Control</h3>
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
    render_user_widget()
    
    st.markdown(f"""
    <div class="neumorphic">
        <p style="margin:0; color:var(--secondary-color);"><strong>Versión:</strong> 2.2.0</p>
        <p style="margin:0; color:var(--text-color); opacity:0.8;"><strong>Última actualización:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
    </div>
    """, unsafe_allow_html=True)

# --------------------------
# INICIALIZACIÓN GARANTIZADA
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
# CONEXIÓN CON GOOGLE SHEETS (MEJORADA)
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

# Carga con spinner mejorado
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
# CARGA DE DATOS (MEJORADA)
# --------------------------

@st.cache_data(ttl=30, show_spinner=False)
def cargar_datos():
    """Carga datos de Google Sheets con manejo robusto de fechas y validaciones"""
    try:
        # Mostrar spinner personalizado
        loading_placeholder = st.empty()
        loading_placeholder.markdown(get_loading_spinner(), unsafe_allow_html=True)
        
        # Cargar datos
        df_reclamos = safe_get_sheet_data(sheet_reclamos, COLUMNAS_RECLAMOS)
        df_clientes = safe_get_sheet_data(sheet_clientes, COLUMNAS_CLIENTES)
        df_usuarios = safe_get_sheet_data(sheet_usuarios, COLUMNAS_USUARIOS)
        
        # Validación de datos
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

        # Procesamiento de fechas
        if 'Fecha y hora' in df_reclamos.columns:
            df_reclamos['Fecha y hora'] = df_reclamos['Fecha y hora'].apply(
                lambda x: parse_fecha(x) if not pd.isna(x) else pd.NaT
            )
            df_reclamos['Fecha_formateada'] = df_reclamos['Fecha y hora'].apply(
                lambda x: format_fecha(x, '%d/%m/%Y %H:%M', 'Fecha inválida')
            )
        else:
            show_error("No se encontró la columna 'Fecha y hora' en los datos de reclamos")
            df_reclamos['Fecha y hora'] = pd.NaT
            df_reclamos['Fecha_formateada'] = 'Columna no encontrada'
            
        return df_reclamos, df_clientes, df_usuarios
        
    except Exception as e:
        show_error(f"Error crítico al cargar datos: {str(e)}")
        if DEBUG_MODE:
            st.exception(e)
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    finally:
        loading_placeholder.empty()

# Cargar datos
df_reclamos, df_clientes, df_usuarios = cargar_datos()
st.session_state.df_reclamos = df_reclamos
st.session_state.df_clientes = df_clientes

# --------------------------
# MIGRACIÓN DE UUID (MEJORADA)
# --------------------------

def migrar_uuids_existentes():
    """Genera UUIDs para registros existentes que no los tengan"""
    try:
        updates = []
        
        # Para Reclamos
        if 'ID Reclamo' in df_reclamos.columns:
            reclamos_sin_uuid = df_reclamos[df_reclamos['ID Reclamo'].isna() | (df_reclamos['ID Reclamo'] == '')]
            if not reclamos_sin_uuid.empty:
                show_warning(f"Hay {len(reclamos_sin_uuid)} reclamos sin UUID. Generando IDs...")
                
                for idx, row in reclamos_sin_uuid.iterrows():
                    updates.append({
                        "range": f"P{idx + 2}",
                        "values": [[generar_id_unico()]]
                    })

        # Para Clientes
        if 'ID Cliente' in df_clientes.columns:
            clientes_sin_uuid = df_clientes[df_clientes['ID Cliente'].isna() | (df_clientes['ID Cliente'] == '')]
            if not clientes_sin_uuid.empty:
                show_warning(f"Hay {len(clientes_sin_uuid)} clientes sin UUID. Generando IDs...")
                
                for idx, row in clientes_sin_uuid.iterrows():
                    updates.append({
                        "range": f"G{idx + 2}",
                        "values": [[generar_id_unico()]]
                    })

        # Procesar actualizaciones por lotes
        if updates:
            batch_size = 50
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i + batch_size]
                success, error = api_manager.safe_sheet_operation(
                    batch_update_sheet,
                    sheet_reclamos if i < len(reclamos_sin_uuid) else sheet_clientes,
                    batch,
                    is_batch=True
                )
                if not success:
                    show_error(f"Error al actualizar lote: {error}")
                    return False
            
            show_success("UUIDs generados para registros existentes")
            st.cache_data.clear()
            return True
            
        return False

    except Exception as e:
        show_error(f"Error en la migración de UUIDs: {str(e)}")
        if DEBUG_MODE:
            st.exception(e)
        return False

# --------------------------
# INTERFAZ PRINCIPAL (MEJORADA)
# --------------------------

# Header moderno
st.markdown("""
<div class="neumorphic">
    <div style="text-align: center;">
        <h1 style="margin:0; margin-bottom:0.5rem; background:linear-gradient(90deg, var(--primary-color), var(--secondary-color)); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            📋 Fusion Reclamos App
        </h1>
        <p style="margin:0; font-size:1.1rem; color:var(--text-color); opacity:0.9;">
            Sistema integral de gestión de reclamos técnicos
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Dashboard de métricas
render_metrics_dashboard(df_reclamos, is_mobile=is_mobile())

# Navegación
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
            "user": user_info
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
        st.markdown('<div class="section-container dark-transition">', unsafe_allow_html=True)
        resultado = COMPONENTES[opcion]["render"](**COMPONENTES[opcion]["params"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        if resultado and resultado.get('needs_refresh'):
            st.cache_data.clear()
            time.sleep(2)
            st.rerun()

# --------------------------
# RESUMEN DE JORNADA (MEJORADO)
# --------------------------
st.markdown("---")
with st.container():
    st.markdown('<div class="section-container dark-transition">', unsafe_allow_html=True)
    render_resumen_jornada(df_reclamos)
    st.markdown('</div>', unsafe_allow_html=True)