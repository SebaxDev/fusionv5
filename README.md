# README - Fusion Reclamos App

## 📌 Descripción General

**Fusion Reclamos App** es una aplicación robusta y optimizada para la gestión integral de reclamos, diseñada para mejorar la eficiencia en el seguimiento, asignación y resolución de incidencias. Desarrollada con Streamlit y conectada a Google Sheets, ofrece una interfaz intuitiva con funcionalidades avanzadas para usuarios con distintos niveles de permisos.

---

## 🚀 Características Principales

### 🔐 Autenticación y Roles
- **Sistema de login seguro** con validación de credenciales.
- **Roles diferenciados**: `admin` y `user`, con permisos específicos para cada sección.
- **Modo oscuro/claro** adaptable al sistema del usuario.

### 📋 Gestión de Reclamos
- **Carga de nuevos reclamos** con validación de clientes existentes.
- **Detección automática** de reclamos duplicados o activos.
- **Tipos de reclamo configurables** (ej: "Desconexión a pedido").
- **Validación robusta** de datos y fechas.

### 📊 Visualización y Filtrado
- **Dashboard de métricas** con resumen de reclamos.
- **Filtros avanzados** por estado, sector y tipo de reclamo.
- **Historial completo** por cliente.

### 🛠️ Asignación y Seguimiento
- **Asignación a grupos de trabajo** (hasta 4 grupos configurables).
- **Distribución por técnicos** con visualización de carga laboral.
- **Seguimiento en tiempo real** de reclamos "Pendientes" y "En curso".

### 📄 Generación de Reportes
- **PDFs personalizados** para reclamos, desconexiones y asignaciones.
- **Exportación a CSV** del historial de clientes.
- **Formato técnico compacto** para impresión.

### 🔄 Sincronización con Google Sheets
- **Conexión segura** mediante Service Account.
- **Manejo optimizado** de operaciones de lectura/escritura.
- **Actualización en tiempo real** con caché inteligente.

---

## 🛠️ Tecnologías Utilizadas

- **Frontend**: Streamlit (Python)
- **Backend**: Python 3.9+
- **Base de datos**: Google Sheets (como backend)
- **Librerías clave**:
  - `pandas` para manejo de datos
  - `gspread` para conexión con Sheets
  - `reportlab` para generación de PDFs
  - `pytz` para manejo de zonas horarias

---

## 📈 Funcionalidades por Sección

### 1. **Inicio - Nuevo Reclamo**
- Carga rápida con autocompletado para clientes existentes.
- Validación de campos obligatorios.
- Creación automática de nuevos clientes.

### 2. **Reclamos Cargados**
- Edición masiva o individual de reclamos.
- Gestión especial de "Desconexiones a pedido".
- Cambio de estados (Pendiente/En curso/Resuelto).

### 3. **Gestión de Clientes**
- Búsqueda avanzada por número de cliente.
- Edición de información (solo para admins).
- Visualización del historial completo.

### 4. **Imprimir Reclamos**
- Selección manual o por filtros.
- Generación de PDFs optimizados para campo.
- Exportación de reclamos activos.

### 5. **Seguimiento Técnico (Admin)**
- Asignación a grupos de trabajo.
- Distribución equitativa entre técnicos.
- Generación de órdenes de trabajo en PDF.

### 6. **Cierre de Reclamos (Admin)**
- Marcado de reclamos como resueltos.
- Actualización de precintos.
- Reasignación rápida de técnicos.

---

## 🌟 Beneficios Clave

✅ **Reducción de tiempos** en gestión de reclamos  
✅ **Seguimiento preciso** del estado de cada incidencia  
✅ **Optimización** de recursos técnicos  
✅ **Reportes profesionales** listos para imprimir  
✅ **Acceso multi-dispositivo** (web + móvil)  
✅ **Sin necesidad de servidores** (usa Google Sheets como backend)  

---

## 🔧 Requisitos de Instalación

1. Python 3.9+
2. Librerías listadas en `requirements.txt`
3. Credenciales de Google Service Account (en `st.secrets`)
4. Acceso a una hoja de Google Sheets configurada con:
   - 3 hojas: Reclamos, Clientes, Usuarios
   - Columnas definidas en `config/settings.py`

---

## 📜 Notas de Versión (2.0)

- **Mejoras en estabilidad**: Manejo robusto de errores en conexión con Sheets.
- **Optimización de caché**: Recarga inteligente de datos.
- **Nuevo sistema de permisos**: Más granularidad en accesos.
- **Mejoras en PDFs**: Diseño profesional con pie de página.
- **Soporte para zonas horarias**: Correcto manejo de fechas en Argentina.

---

## 🚧 Próximas Mejoras

- Integración con WhatsApp para notificaciones
- Panel de estadísticas históricas
- Mapa interactivo de sectores
- Soporte para imágenes en reclamos

---

**Desarrollado por** [Sebastian Andres]  
📅 Julio 2025  
📧 sebaxfusion@gmail.com