# components/notification_bell.py

import streamlit as st
from utils.date_utils import format_fecha
from config.settings import NOTIFICATION_TYPES

def render_notification_bell():
    """Muestra el ícono de notificaciones y el panel"""
    if 'notification_manager' not in st.session_state:
        return
        
    user = st.session_state.auth.get('user_info', {}).get('username')
    if not user:
        return
        
    notifications = st.session_state.notification_manager.get_for_user(user, unread_only=True)
    
    unread_count = len(notifications)
    
    # Ícono en el sidebar
    with st.sidebar:
        col1, col2 = st.columns([1, 3])
        col1.markdown(f"🔔 **{unread_count}**" if unread_count > 0 else "🔔")
        
        if col2.button("Ver notificaciones"):
            st.session_state.show_notifications = not st.session_state.get('show_notifications', False)
            
        if st.session_state.get('show_notifications'):
            with st.expander("Notificaciones", expanded=True):
                if not notifications:
                    st.info("No tienes notificaciones nuevas")
                    return
                    
                for notification in notifications[:10]:  # Mostrar las 10 más recientes
                    icon = NOTIFICATION_TYPES.get(notification['Tipo'], {}).get('icon', '✉️')
                    
                    with st.container():
                        cols = st.columns([1, 10])
                        cols[0].markdown(f"**{icon}**")
                        
                        with cols[1]:
                            st.markdown(f"**{notification['Mensaje']}**")
                            st.caption(format_fecha(notification['Fecha_Hora']))
                            
                            # Botón para marcar como leída
                            if st.button("Marcar como leída", key=f"read_{notification['ID']}"):
                                st.session_state.notification_manager.mark_as_read([notification['ID']])
                                st.rerun()
                                
                        st.divider()