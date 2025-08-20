"""Componentes de UI reutilizables para una apariencia profesional"""

import streamlit as st

def card(title, content, icon=None, actions=None):
    """Componente de tarjeta elegante"""
    col1, col2 = st.columns([1, 20])
    
    if icon:
        with col1:
            st.markdown(f"<div style='font-size: 24px; color: var(--primary-color);'>{icon}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<h3 style='margin: 0;'>{title}</h3>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(content)
    
    if actions:
        col1, col2 = st.columns([3, 1])
        with col2:
            for action in actions:
                st.button(action["label"], key=action["key"])
    
    st.markdown("</div>", unsafe_allow_html=True)

def metric_card(value, label, icon, trend=None):
    """Tarjeta de métrica elegante"""
    trend_html = f"<span style='color: {trend['color']}; font-size: 0.8rem;'>{trend['value']}</span>" if trend else ""
    
    return f"""
    <div class='card' style='text-align: center;'>
        <div style='font-size: 2rem; color: var(--primary-color); margin-bottom: 0.5rem;'>{icon}</div>
        <div style='font-size: 1.5rem; font-weight: 600; color: var(--text-primary);'>{value}</div>
        <div style='color: var(--text-secondary); margin-bottom: 0.5rem;'>{label}</div>
        {trend_html}
    </div>
    """

def badge(text, type="primary"):
    """Componente de badge elegante"""
    color_map = {
        "primary": "var(--primary-color)",
        "success": "var(--success-color)",
        "warning": "var(--warning-color)",
        "danger": "var(--danger-color)",
        "info": "var(--info-color)"
    }
    
    return f"""
    <span class='badge badge-{type}' style='background-color: rgba({color_map[type]}, 0.1); color: {color_map[type]};'>
        {text}
    </span>
    """


def breadcrumb(current_page):
    """Componente de breadcrumb elegante"""
    pages = {
        "Inicio": "🏠",
        "Reclamos cargados": "📊", 
        "Gestión de clientes": "👥",
        "Imprimir reclamos": "🖨️",
        "Seguimiento técnico": "🔧",
        "Cierre de Reclamos": "✅"
    }
    
    return f"""
    <div style="
        display: flex; 
        align-items: center; 
        gap: 0.5rem; 
        margin: 1.5rem 0; 
        padding: 1rem; 
        background: var(--bg-surface); 
        border-radius: var(--radius-lg); 
        border: 1px solid var(--border-color);
        font-size: 0.95rem;
    ">
        <span style="color: var(--text-muted); display: flex; align-items: center; gap: 0.25rem;">
            <span>📋</span>
            <span>Estás en:</span>
        </span>
        <span style="color: var(--primary-color); display: flex; align-items: center; gap: 0.25rem;">
            <span>{pages.get(current_page, '📋')}</span>
            <span style="font-weight: 500;">{current_page}</span>
        </span>
    </div>
    """
