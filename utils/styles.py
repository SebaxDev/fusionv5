# styles.py - Versión renovada
"""Estilos CSS profesionales tipo CRM"""

def get_main_styles(dark_mode=True):
    """Devuelve estilos CSS profesionales para modo claro/oscuro"""
    
    if dark_mode:
        theme_vars = """
            --primary-color: #4361EE;
            --primary-light: #4895EF;
            --secondary-color: #7209B7;
            --success-color: #06D6A0;
            --warning-color: #FFD166;
            --danger-color: #EF476F;
            --info-color: #118AB2;
            
            --bg-primary: #0F172A;
            --bg-secondary: #1E293B;
            --bg-surface: #1E293B;
            --bg-card: #334155;
            
            --text-primary: #F8FAFC;
            --text-secondary: #CBD5E1;
            --text-muted: #94A3B8;
            
            --border-color: #334155;
            --border-light: #475569;
            
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
            
            --radius-sm: 0.25rem;
            --radius-md: 0.375rem;
            --radius-lg: 0.5rem;
            --radius-xl: 0.75rem;
        """
    else:
        theme_vars = """
            --primary-color: #3B82F6;
            --primary-light: #60A5FA;
            --secondary-color: #8B5CF6;
            --success-color: #10B981;
            --warning-color: #F59E0B;
            --danger-color: #EF4444;
            --info-color: #06B6D4;
            
            --bg-primary: #FFFFFF;
            --bg-secondary: #F8FAFC;
            --bg-surface: #F1F5F9;
            --bg-card: #FFFFFF;
            
            --text-primary: #1E293B;
            --text-secondary: #475569;
            --text-muted: #64748B;
            
            --border-color: #E2E8F0;
            --border-light: #F1F5F9;
            
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
            
            --radius-sm: 0.25rem;
            --radius-md: 0.375rem;
            --radius-lg: 0.5rem;
            --radius-xl: 0.75rem;
        """
    
    return f"""
    <style>
    :root {{
        {theme_vars}
    }}
    
    /* Fuentes modernas */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    body, .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: var(--bg-primary);
        color: var(--text-primary);
        line-height: 1.6;
    }}
    
    /* Mejoras para contenedores principales */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    
    /* HEADERS MODERNOS */
    h1, h2, h3, h4, h5, h6 {{
        font-weight: 600;
        margin-bottom: 0.75rem;
        color: var(--text-primary);
        letter-spacing: -0.025em;
    }}
    
    h1 {{
        font-size: 2.25rem;
        line-height: 2.5rem;
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
    }}
    
    h2 {{
        font-size: 1.875rem;
        line-height: 2.25rem;
        color: var(--text-primary);
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--border-color);
        margin-top: 2rem;
    }}
    
    h3 {{
        font-size: 1.5rem;
        line-height: 2rem;
        color: var(--text-primary);
    }}
    
    /* BOTONES MODERNOS */
    .stButton > button {{
        border: none;
        border-radius: var(--radius-lg);
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        cursor: pointer;
        box-shadow: var(--shadow-md);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }}
    
    .stButton > button:focus {{
        outline: none;
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
    }}
    
    /* Botón primario */
    .stButton > button:first-child {{
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
        color: white;
    }}
    
    .stButton > button:first-child:hover {{
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary-color) 100%);
    }}
    
    /* Botón secundario */
    .stButton > button:not(:first-child) {{
        background: transparent;
        color: var(--primary-color);
        border: 1px solid var(--primary-color);
    }}
    
    .stButton > button:not(:first-child):hover {{
        background: var(--primary-color);
        color: white;
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }}
    
    /* TARJETAS Y CONTENEDORES ELEGANTES */
    .card {{
        background: var(--bg-card);
        border-radius: var(--radius-xl);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;
    }}
    
    .card:hover {{
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
    }}
    
    .card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-color);
    }}
    
    .card-title {{
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }}
    
    /* FORMULARIOS ELEGANTES */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {{
        background-color: var(--bg-surface);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-md);
        padding: 0.75rem;
        color: var(--text-primary);
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus,
    .stNumberInput > div > div > input:focus,
    .stDateInput > div > div > input:focus {{
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
        outline: none;
    }}
    
    /* LABELS MEJORADOS */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stNumberInput label,
    .stDateInput label {{
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        display: block;
    }}
    
    /* SIDEBAR PROFESIONAL */
    .css-1d391kg {{
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color);
    }}
    
    .css-1d391kg .stButton > button {{
        width: 100%;
        justify-content: flex-start;
        margin-bottom: 0.5rem;
        border-radius: var(--radius-md);
    }}
    
    /* MEJORAS PARA TABLAS */
    .dataframe {{
        border-radius: var(--radius-lg);
        overflow: hidden;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border-color);
    }}
    
    .dataframe thead th {{
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-light) 100%);
        color: white;
        font-weight: 600;
        padding: 0.75rem;
        text-align: left;
    }}
    
    .dataframe tbody td {{
        padding: 0.75rem;
        border-bottom: 1px solid var(--border-color);
        background-color: var(--bg-surface);
        color: var(--text-primary);
    }}
    
    .dataframe tbody tr:hover td {{
        background-color: var(--bg-secondary);
    }}
    
    /* NOTIFICACIONES Y ALERTAS MEJORADAS */
    .stAlert {{
        border-radius: var(--radius-lg);
        border: none;
        box-shadow: var(--shadow-md);
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
    }}
    
    .stAlert[data-baseweb="notification"] {{
        background-color: var(--bg-surface);
        border-left: 4px solid var(--info-color);
    }}
    
    .stAlert[data-baseweb="notification"].success {{
        border-left-color: var(--success-color);
    }}
    
    .stAlert[data-baseweb="notification"].warning {{
        border-left-color: var(--warning-color);
    }}
    
    .stAlert[data-baseweb="notification"].error {{
        border-left-color: var(--danger-color);
    }}
    
    /* BADGES Y ETIQUETAS */
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }}
    
    .badge-primary {{
        background-color: rgba(67, 97, 238, 0.1);
        color: var(--primary-color);
    }}
    
    .badge-success {{
        background-color: rgba(6, 214, 160, 0.1);
        color: var(--success-color);
    }}
    
    .badge-warning {{
        background-color: rgba(255, 209, 102, 0.1);
        color: var(--warning-color);
    }}
    
    .badge-danger {{
        background-color: rgba(239, 71, 111, 0.1);
        color: var(--danger-color);
    }}
    
    /* GRID SYSTEM MEJORADO */
    .stHorizontalBlock > div {{
        gap: 1rem;
    }}
    
    /* SCROLLBAR PERSONALIZADO */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: var(--bg-surface);
        border-radius: var(--radius-md);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: var(--border-color);
        border-radius: var(--radius-md);
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-muted);
    }}
    
    /* RESPONSIVE DESIGN */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding: 1rem;
        }}
        
        .card {{
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        
        h1 {{
            font-size: 1.875rem;
            line-height: 2.25rem;
        }}
        
        h2 {{
            font-size: 1.5rem;
            line-height: 2rem;
        }}
    }}
    </style>
    """

def get_loading_spinner():
    """Spinner de carga moderno"""
    return """
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: rgba(15, 23, 42, 0.8);
        z-index: 9999;
        backdrop-filter: blur(4px);
    ">
        <div style="
            width: 60px;
            height: 60px;
            border: 3px solid rgba(255,255,255,0.1);
            border-radius: 50%;
            border-top-color: #4361EE;
            animation: spin 1s ease-in-out infinite;
            position: relative;
        ">
            <div style="
                content: '';
                position: absolute;
                top: -3px;
                left: -3px;
                right: -3px;
                bottom: -3px;
                border: 3px solid transparent;
                border-radius: 50%;
                border-top-color: #7209B7;
                animation: spin 1.5s ease infinite;
                opacity: 0.7;
            "></div>
        </div>
        <style>
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        </style>
    </div>
    """