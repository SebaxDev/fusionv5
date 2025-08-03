"""
Estilos CSS optimizados para rendimiento - Versión Minimalista
"""

def get_main_styles(dark_mode=False):
    """Devuelve estilos CSS optimizados para mejor rendimiento"""
    theme_vars = """
        --primary-color: #4361ee;
        --secondary-color: #7209b7;
        --text-color: #212529;
        --bg-color: #ffffff;
        --card-bg: #ffffff;
        --border-color: #e9ecef;
    """ if not dark_mode else """
        --primary-color: #4895ef;
        --secondary-color: #b5179e;
        --text-color: #f8f9fa;
        --bg-color: #16213e;
        --card-bg: #0f3460;
        --border-color: #2d3748;
    """
    
    return f"""
    <style>
    :root {{
        {theme_vars}
        --border-radius: 8px;
    }}

    body, .block-container {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        line-height: 1.5;
    }}

    /* Layout básico */
    .block-container {{
        max-width: 1400px;
        padding: 1rem;
    }}

    /* Componentes esenciales */
    .stTextInput input, 
    .stTextArea textarea, 
    .stSelectbox select {{
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
        padding: 8px 12px;
    }}

    .stButton>button {{
        border-radius: var(--border-radius);
        background-color: var(--primary-color);
        color: white;
        padding: 8px 16px;
        border: none;
    }}

    /* Tarjetas básicas */
    .section-container {{
        background: var(--card-bg);
        border-radius: var(--border-radius);
        padding: 16px;
        margin: 16px 0;
        border: 1px solid var(--border-color);
    }}

    /* Tablas simplificadas */
    .dataframe {{
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
    }}

    .dataframe thead th {{
        background-color: var(--primary-color);
        color: white;
    }}

    /* Responsive básico */
    @media (max-width: 768px) {{
        .block-container {{
            padding: 0.5rem;
        }}
    }}
    </style>
    """

def get_loading_spinner():
    """Spinner minimalista para carga"""
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
    ">
        <div style="
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
        "></div>
    </div>
    <style>
    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}
    </style>
    """