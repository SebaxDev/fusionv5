"""
Estilos CSS refinados - Tema Monokai Classic
Aplicado como modo oscuro por defecto
"""

def get_main_styles(dark_mode=False):
    """Devuelve estilos CSS refinados con paleta Monokai"""
    # Ignoramos el parámetro dark_mode y forzamos Monokai como base
    theme_vars = """
        --primary-color: #66D9EF;     /* Azul verdoso */
        --secondary-color: #F92672;   /* Magenta */
        --accent-color: #E6DB74;      /* Amarillo */
        --text-color: #F8F8F2;        /* Blanco cálido */
        --bg-color: #272822;          /* Fondo principal */
        --card-bg: #3E3D32;           /* Fondo de tarjetas */
        --border-color: #49483E;      /* Bordes */
        --shadow: 0 2px 8px rgba(0,0,0,0.4);
        --green-color: #A6E22E;
        --orange-color: #FD971F;
    """
    
    return f"""
    <style>
    :root {{
        {theme_vars}
        --border-radius: 8px;
        --side-margin: 3%;
        --top-margin: 1.5rem;
    }}

    /* Fuente global */
    body, .block-container {{
        font-family: 'Fira Code', 'Segoe UI', Roboto, -apple-system, sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }}

    .block-container {{
        max-width: 1000px;
        margin: var(--top-margin) auto;
        padding: 0 10px;
    }}

    /* Títulos */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--primary-color);
        margin-top: 1.2rem;
        margin-bottom: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }}

    /* Formularios */
    .stTextInput input, 
    .stTextArea textarea, 
    .stSelectbox select,
    .stDateInput input {{
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        padding: 8px 12px;
        background-color: var(--card-bg);
        color: var(--text-color);
        transition: all 0.2s ease;
    }}

    .stTextInput input:focus, 
    .stTextArea textarea:focus, 
    .stSelectbox select:focus {{
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(102, 217, 239, 0.25);
        outline: none;
    }}

    /* Botones */
    .stButton>button {{
        border-radius: var(--border-radius);
        background-color: var(--secondary-color);
        color: var(--text-color);
        padding: 8px 16px;
        border: none;
        font-weight: 500;
        transition: all 0.2s ease;
        cursor: pointer;
    }}

    .stButton>button:hover {{
        background-color: var(--primary-color);
        color: #272822;
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }}

    /* Secciones y tarjetas */
    .section-container {{
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: 16px 20px;
        margin: 16px 0;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow);
    }}

    /* Tablas */
    .dataframe {{
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow);
        overflow: hidden;
        margin-bottom: 1rem;
    }}

    .dataframe thead th {{
        background-color: var(--secondary-color);
        color: white;
        font-weight: 600;
    }}

    .dataframe tbody td {{
        background-color: var(--card-bg);
        color: var(--text-color);
    }}

    .dataframe tbody tr:hover td {{
        background-color: #4E4C3A;
    }}

    /* Sidebar */
    .css-1d391kg {{
        padding: 1.2rem;
        background-color: var(--card-bg) !important;
        border-right: 1px solid var(--border-color);
    }}

    /* Links */
    a {{
        color: var(--primary-color);
        text-decoration: none;
    }}
    a:hover {{
        color: var(--accent-color);
    }}

    /* Hover general */
    .element-container:has(button):hover,
    .stCheckbox:hover,
    .stRadio:hover {{
        transform: translateY(-1px);
        transition: all 0.2s ease;
    }}

    /* Colores especiales para avisos */
    .stAlert div[data-baseweb="notification"] {{
        background-color: var(--card-bg);
        border-left: 5px solid var(--secondary-color);
        color: var(--text-color);
    }}
    .stAlert[data-baseweb="notification"][role="alert"] {{
        border-left-color: var(--orange-color);
    }}
    .stAlert[data-baseweb="notification"][role="status"] {{
        border-left-color: var(--green-color);
    }}

    /* Responsive */
    @media (max-width: 768px) {{
        :root {{
            --side-margin: 2%;
            --top-margin: 1rem;
        }}
        
        .block-container {{
            max-width: 96%;
        }}

        .section-container {{
            padding: 14px 16px;
        }}
    }}
    </style>
    """

def get_loading_spinner():
    """Spinner con colores Monokai"""
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
        background-color: rgba(0,0,0,0.4);
        z-index: 9999;
        backdrop-filter: blur(2px);
    ">
        <div style="
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255,255,255,0.2);
            border-radius: 50%;
            border-top-color: var(--secondary-color);
            animation: spin 1s ease-in-out infinite;
            position: relative;
        ">
            <div style="
                content: '';
                position: absolute;
                top: -4px;
                left: -4px;
                right: -4px;
                bottom: -4px;
                border: 4px solid transparent;
                border-radius: 50%;
                border-top-color: var(--primary-color);
                animation: spin 1.5s ease infinite;
                opacity: 0.7;
            "></div>
        </div>
    </div>
    <style>
    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}
    </style>
    """
