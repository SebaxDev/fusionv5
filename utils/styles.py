"""
Estilos CSS centralizados para la aplicación con diseño profesional y moderno
"""

def get_main_styles(dark_mode=False):
    theme_vars = """
        --primary-color: #4361ee;
        --primary-hover: #3a56d4;
        --secondary-color: #7209b7;
        --success-color: #4cc9f0;
        --warning-color: #f8961e;
        --danger-color: #f72585;
        --light-bg: #f8f9fa;
        --text-color: #212529;
        --bg-color: #ffffff;
        --card-bg: #ffffff;
        --border-color: #e9ecef;
        --hover-bg: #f1f3ff;
    """ if not dark_mode else """
        --primary-color: #4895ef;
        --primary-hover: #3a7bc8;
        --secondary-color: #b5179e;
        --success-color: #4cc9f0;
        --warning-color: #f8961e;
        --danger-color: #f72585;
        --light-bg: #1a1a2e;
        --text-color: #f8f9fa;
        --bg-color: #16213e;
        --card-bg: #0f3460;
        --border-color: #2d3748;
        --hover-bg: #2d3748;
    """
    
    return f"""
    <style>
    :root {{
        {theme_vars}
        --border-radius: 12px;
        --border-radius-sm: 8px;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }}

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    body, .block-container {{
        font-family: var(--font-sans) !important;
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
        line-height: 1.6;
    }}

    /* Tipografía mejorada */
    h1 {{
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        margin-bottom: 1.5rem !important;
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2 !important;
    }}

    h2 {{
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        margin: 2rem 0 1rem 0 !important;
        color: var(--primary-color) !important;
    }}

    h3 {{
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin: 1.5rem 0 0.75rem 0 !important;
    }}

    .block-container {{
        max-width: 1400px !important;
        padding: 2rem 3rem !important;
        animation: fadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Componentes de formulario mejorados */
    .stTextInput input, .stTextArea textarea, .stSelectbox select, .stDateInput input, .stTimeInput input {{
        border-radius: var(--border-radius-sm) !important;
        border: 2px solid var(--border-color) !important;
        padding: 12px 16px !important;
        transition: var(--transition) !important;
        font-size: 15px !important;
        color: var(--text-color) !important;
        background-color: var(--card-bg) !important;
        box-shadow: var(--shadow) !important;
    }}

    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus, 
    .stDateInput input:focus, .stTimeInput input:focus {{
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.2) !important;
        outline: none !important;
    }}

    /* Botones modernos */
    .stButton>button {{
        border-radius: var(--border-radius-sm) !important;
        border: none !important;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
        color: white !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: var(--transition) !important;
        box-shadow: var(--shadow) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        font-size: 14px !important;
    }}

    .stButton>button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-md) !important;
        opacity: 0.9 !important;
    }}

    .stButton>button:active {{
        transform: translateY(0) !important;
        box-shadow: var(--shadow) !important;
    }}

    /* Tarjetas y contenedores */
    .metric-container {{
        background: var(--card-bg) !important;
        border-radius: var(--border-radius) !important;
        padding: 24px !important;
        box-shadow: var(--shadow) !important;
        margin-bottom: 20px !important;
        transition: var(--transition) !important;
        border: 1px solid var(--border-color) !important;
    }}

    .metric-container:hover {{
        transform: translateY(-5px) !important;
        box-shadow: var(--shadow-lg) !important;
        border-color: var(--primary-color) !important;
    }}

    .metric-title {{
        font-size: 14px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        color: var(--secondary-color) !important;
        margin-bottom: 8px !important;
    }}

    .metric-value {{
        font-size: 28px !important;
        font-weight: 700 !important;
        color: var(--primary-color) !important;
    }}

    /* Tablas mejoradas */
    .dataframe {{
        border-radius: var(--border-radius) !important;
        box-shadow: var(--shadow) !important;
        border: 1px solid var(--border-color) !important;
        overflow: hidden !important;
    }}

    .dataframe thead th {{
        background-color: var(--primary-color) !important;
        color: white !important;
        font-weight: 600 !important;
    }}

    /* Radio buttons y checkboxes */
    .stRadio > div, .stCheckbox > div {{
        background: var(--card-bg) !important;
        border-radius: var(--border-radius) !important;
        padding: 16px !important;
        box-shadow: var(--shadow) !important;
        border: 1px solid var(--border-color) !important;
    }}

    .stRadio [role=radiogroup] {{
        gap: 1rem !important;
        align-items: center !important;
    }}

    /* Alertas y notificaciones */
    .stAlert {{
        border-radius: var(--border-radius) !important;
        animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: var(--shadow) !important;
        border-left: 4px solid var(--primary-color) !important;
    }}

    @keyframes slideIn {{
        from {{ transform: translateX(-30px); opacity: 0; }}
        to {{ transform: translateX(0); opacity: 1; }}
    }}

    /* Efecto de carga */
    .loading-overlay {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        background: rgba(22, 33, 62, 0.8) !important;
        z-index: 9999 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        backdrop-filter: blur(5px) !important;
    }}

    .spinner {{
        width: 50px !important;
        height: 50px !important;
        border: 4px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 50% !important;
        border-top-color: var(--primary-color) !important;
        animation: spin 1s ease-in-out infinite !important;
    }}

    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}

    /* Secciones y contenedores */
    .section-container {{
        background: var(--card-bg) !important;
        border-radius: var(--border-radius) !important;
        padding: 32px !important;
        margin: 24px 0 !important;
        box-shadow: var(--shadow) !important;
        border: 1px solid var(--border-color) !important;
        transition: var(--transition) !important;
    }}

    .section-container:hover {{
        box-shadow: var(--shadow-md) !important;
    }}

    /* Efectos hover */
    .hover-card {{
        transition: var(--transition) !important;
        cursor: pointer !important;
    }}

    .hover-card:hover {{
        transform: scale(1.02) !important;
        box-shadow: var(--shadow-lg) !important;
        background-color: var(--hover-bg) !important;
    }}

    /* Badges modernos */
    .status-badge {{
        padding: 6px 14px !important;
        border-radius: 20px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        box-shadow: var(--shadow) !important;
    }}

    .status-pendiente {{
        background: linear-gradient(135deg, #fff3cd, #ffe69c) !important;
        color: #856404 !important;
    }}

    .status-en-curso {{
        background: linear-gradient(135deg, #d1ecf1, #a8e6f0) !important;
        color: #0c5460 !important;
    }}

    .status-resuelto {{
        background: linear-gradient(135deg, #d4edda, #b8e6c4) !important;
        color: #155724 !important;
    }}

    /* Scrollbar personalizada */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background: var(--light-bg);
    }}

    ::-webkit-scrollbar-thumb {{
        background: var(--primary-color);
        border-radius: 4px;
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: var(--primary-hover);
    }}

    /* Tooltips */
    .tooltip {{
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted var(--primary-color);
    }}

    .tooltip .tooltiptext {{
        visibility: hidden;
        width: 200px;
        background-color: var(--card-bg);
        color: var(--text-color);
        text-align: center;
        border-radius: var(--border-radius-sm);
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
    }}

    .tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
    }}

    /* Responsive design */
    @media (max-width: 768px) {{
        .block-container {{
            padding: 1.5rem !important;
        }}
        
        h1 {{
            font-size: 2rem !important;
        }}
        
        h2 {{
            font-size: 1.5rem !important;
        }}
        
        .metric-container {{
            padding: 20px !important;
        }}
        
        .section-container {{
            padding: 24px !important;
        }}
    }}

    /* Efecto neumorfismo para modo claro */
    .neumorphic {{
        border-radius: var(--border-radius) !important;
        background: var(--card-bg) !important;
        box-shadow:  8px 8px 16px #d9d9d9, 
                    -8px -8px 16px #ffffff !important;
    }}

    /* Transiciones para modo oscuro */
    .dark-transition * {{
        transition: background-color 0.3s ease, color 0.3s ease;
    }}
    </style>
    """

def get_loading_spinner():
    return """
    <div class="loading-overlay dark-transition">
        <div class="spinner"></div>
        <p style="color: white; margin-top: 20px; font-weight: 500;">Cargando...</p>
    </div>
    """