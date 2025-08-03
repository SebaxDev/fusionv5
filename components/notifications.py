# components/notifications.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.date_utils import ahora_argentina, format_fecha
from utils.api_manager import api_manager
from utils.data_manager import safe_get_sheet_data, batch_update_sheet
from config.settings import NOTIFICATION_TYPES, COLUMNAS_NOTIFICACIONES, MAX_NOTIFICATIONS

class NotificationManager:
    def __init__(self, sheet_notifications):
        self.sheet = sheet_notifications
        self.max_retries = 3
        
    def _get_next_id(self):
        """Obtiene el próximo ID disponible con manejo robusto de errores"""
        for _ in range(self.max_retries):
            try:
                df = safe_get_sheet_data(self.sheet, COLUMNAS_NOTIFICACIONES)
                return 1 if df.empty else int(df['ID'].max()) + 1
            except Exception as e:
                st.error(f"Error al obtener ID: {str(e)}")
                time.sleep(1)
        return None
        
    def add(self, notification_type, message, user_target='all', claim_id=None, action=None):
        """
        Agrega una nueva notificación con validación de tipos
        
        Args:
            notification_type (str): Tipo de notificación definido en settings
            message (str): Mensaje descriptivo
            user_target (str): Usuario destino o 'all' para todos
            claim_id (str): ID relacionado (opcional)
            action (str): Acción asociada (opcional)
        
        Returns:
            bool: True si fue exitoso
        """
        if notification_type not in NOTIFICATION_TYPES:
            raise ValueError(f"Tipo de notificación no válido: {notification_type}. Opciones: {list(NOTIFICATION_TYPES.keys())}")
            
        new_id = self._get_next_id()
        if new_id is None:
            return False
            
        new_notification = [
            new_id,
            notification_type,
            NOTIFICATION_TYPES[notification_type]['priority'],
            message,
            str(user_target),
            str(claim_id) if claim_id else "",
            format_fecha(ahora_argentina()),
            False,  # Leída
            action or ""
        ]
        
        # Intento con retry
        for attempt in range(self.max_retries):
            success, error = api_manager.safe_sheet_operation(
                self.sheet.append_row,
                new_notification
            )
            if success:
                return True
            time.sleep(1)
            
        st.error(f"Fallo al agregar notificación después de {self.max_retries} intentos")
        return False
        
    def get_for_user(self, username, unread_only=True, limit=MAX_NOTIFICATIONS):
        """
        Obtiene notificaciones para un usuario con caché local
        """
        try:
            df = safe_get_sheet_data(self.sheet, COLUMNAS_NOTIFICACIONES)

            if df.empty:
                return []

            # Parseo robusto de fechas
            df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'], errors='coerce')

            # FIX: convertir texto en booleanos
            df['Leída'] = df['Leída'].astype(str).str.strip().str.upper().map({'FALSE': False, 'TRUE': True}).fillna(False)

            # Filtro por usuario y estado
            mask = df['Usuario_Destino'].isin([username, 'all'])
            if unread_only:
                mask &= (df['Leída'] == False)

            notifications = (
                df[mask]
                .sort_values('Fecha_Hora', ascending=False)
                .head(limit)
            )

            return notifications.to_dict('records')

        except Exception as e:
            st.error(f"Error al obtener notificaciones: {str(e)}")
            return []
     
    def get_unread_count(self, username):
        """Cuenta rápidamente notificaciones no leídas"""
        notifications = self.get_for_user(username, unread_only=True)
        return len(notifications)
        
    def mark_as_read(self, notification_ids):
        """
        Marca notificaciones como leídas en batch
        
        Args:
            notification_ids (list): Lista de IDs a marcar
        
        Returns:
            bool: True si fue exitoso
        """
        if not notification_ids:
            return False
            
        try:
            updates = [{
                'range': f"H{int(row['ID'])+1}",  # Columna 'Leída'
                'values': [[True]]
            } for row in safe_get_sheet_data(self.sheet, COLUMNAS_NOTIFICACIONES) 
              if row['ID'] in notification_ids]
            
            if not updates:
                return False
                
            success, error = api_manager.safe_sheet_operation(
                batch_update_sheet,
                self.sheet,
                updates,
                is_batch=True
            )
            return success
            
        except Exception as e:
            st.error(f"Error al marcar como leídas: {str(e)}")
            return False
            
    def clear_old(self, days=30):
        """
        Limpia notificaciones antiguas
        """
        try:
            df = safe_get_sheet_data(self.sheet, COLUMNAS_NOTIFICACIONES)
            if df.empty:
                return True

            # Conversión robusta a datetime
            df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'], errors='coerce')

            # Solo des-localizar si la columna tiene zona horaria
            if pd.api.types.is_datetime64tz_dtype(df['Fecha_Hora']):
                df['Fecha_Hora'] = df['Fecha_Hora'].dt.tz_convert(None)

            # Eliminar NaT para evitar errores de comparación
            df_validas = df[df['Fecha_Hora'].notna()].copy()

            # Comparación con corte
            cutoff_date = ahora_argentina().replace(tzinfo=None) - timedelta(days=days)

            old_ids = df_validas[df_validas['Fecha_Hora'] < cutoff_date]['ID'].tolist()

            if not old_ids:
                return True

            return self._delete_rows(old_ids)

        except Exception as e:
            st.error(f"Error al limpiar notificaciones: {str(e)}")
            return False

            
    def _delete_rows(self, row_ids):
        """Método interno para eliminar filas (implementar según API)"""
        # Esto depende de cómo permita tu API eliminar filas
        # Ejemplo conceptual:
        updates = [{
            'delete_dimension': {
                'range': {
                    'sheetId': self.sheet.id,
                    'dimension': 'ROWS',
                    'startIndex': int(row_id),
                    'endIndex': int(row_id)+1
                }
            }
        } for row_id in row_ids]
        
        success, _ = api_manager.safe_sheet_operation(
            self.sheet.batch_update,
            {'requests': updates}
        )
        return success

def init_notification_manager(sheet_notifications):
    """Inicializa el manager de notificaciones con estado persistente"""
    if 'notification_manager' not in st.session_state:
        st.session_state.notification_manager = NotificationManager(sheet_notifications)

        # Verificamos si el usuario ya inició sesión antes de limpiar
        user = st.session_state.get('auth', {}).get('user_info', {}).get('username', '')
        if user and st.session_state.get('clear_notifications_job') is None:
            if st.session_state.notification_manager.clear_old():
                st.session_state.clear_notifications_job = True