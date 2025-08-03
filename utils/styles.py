"""
Estilos CSS optimizados - Versión Mejorada con márgenes y diseño refinado
"""

def get_main_styles(dark_mode=False):
    """Devuelve estilos CSS con márgenes y diseño mejorado"""
    theme_vars = """
        --primary-color: #4361ee;
        --secondary-color: #7209b7;
        --accent-color: #3a0ca3;
        --text-color: #212529;
        --bg-color: #f8f9fa;
        --card-bg: #ffffff;
        --border-color: #e9ecef;
        --shadow: 0 2px 8px rgba(0,0,0,0.1);
    """ if not dark_mode else """
        --primary-color: #4895ef;
        --secondary-color: #b5179e;
        --accent-color: #560bad;
        --text-color: #f8f9fa;
        --bg-color: #121212;
        --card-bg: #1e1e1e;
        --border-color: #2d3748;
        --shadow: 0 2px 8px rgba(0,0,0,0.3);
    """
    
    return f"""
    <style>
    :root {{
        {theme_vars}
        --border-radius: 10px;
        --side-margin: 5%;
        --top-margin: 2rem;
    }}

    /* Estructura principal */
    body, .block-container {{
        font-family: 'Segoe UI', Roboto, -apple-system, sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        line-height: 1.6;
        margin: 0;
        padding: 0;
    }}

    .block-container {{
        max-width: 90%;
        margin: var(--top-margin) var(--side-margin);
        padding: 0;
    }}

    /* Encabezados */
    h1, h2, h3, h4, h5, h6 {{
        color: var(--primary-color);
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }}

    /* Componentes de formulario */
    .stTextInput input, 
    .stTextArea textarea, 
    .stSelectbox select,
    .stDateInput input {{
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        padding: 10px 14px;
        background-color: var(--card-bg);
        color: var(--text-color);
        transition: all 0.2s ease;
    }}

    .stTextInput input:focus, 
    .stTextArea textarea:focus, 
    .stSelectbox select:focus {{
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.2);
        outline: none;
    }}

    /* Botones */
    .stButton>button {{
        border-radius: var(--border-radius);
        background-color: var(--primary-color);
        color: white;
        padding: 10px 20px;
        border: none;
        font-weight: 500;
        transition: all 0.2s ease;
    }}

    .stButton>button:hover {{
        background-color: var(--accent-color);
        transform: translateY(-1px);
        box-shadow: var(--shadow);
    }}

    /* Tarjetas y contenedores */
    .section-container {{
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: 20px;
        margin: 20px 0;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow);
    }}

    /* Tablas */
    .dataframe {{
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow);
        overflow: hidden;
    }}

    .dataframe thead th {{
        background-color: var(--primary-color);
        color: white;
        font-weight: 600;
    }}

    /* Barra lateral */
    .css-1d391kg {{
        padding: 1.5rem;
        background-color: var(--card-bg) !important;
        border-right: 1px solid var(--border-color);
    }}

    /* Efectos hover para elementos interactivos */
    .element-container:has(button):hover,
    .stCheckbox:hover,
    .stRadio:hover {{
        transform: translateY(-2px);
        transition: all 0.2s ease;
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
            padding: 15px;
        }}
    }}
    </style>
    """

def get_loading_spinner():
    """Spinner mejorado con diseño más moderno"""
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
        background-color: rgba(0,0,0,0.5);
        z-index: 9999;
        backdrop-filter: blur(2px);
    ">
        <div style="
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255,255,255,0.2);
            border-radius: 50%;
            border-top-color: var(--primary-color);
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
                border-top-color: var(--secondary-color);
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