# utils/reporte_diario.py

import io
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from utils.date_utils import ahora_argentina


# ---------------------------
# Helpers internos
# ---------------------------
def _to_datetime_clean(series: pd.Series) -> pd.Series:
    """Convierte una serie a datetime de forma robusta y sin TZ."""
    s = series.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    s = s.replace({"", "nan", "NaN", "NONE": None, "None": None})
    out = pd.to_datetime(s, errors="coerce", dayfirst=True, infer_datetime_format=True)
    # Si es tz-aware, quitar TZ
    if pd.api.types.is_datetime64tz_dtype(out):
        out = out.dt.tz_localize(None)
    return out


def _prep_df(df_reclamos: pd.DataFrame):
    """Devuelve df normalizado + marcas de tiempo (ahora, hace_24h)."""
    df = df_reclamos.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Asegurar columnas clave
    for col in ["Fecha y hora", "Fecha_formateada", "Estado", "Técnico", "Tipo de reclamo"]:
        if col not in df.columns:
            df[col] = pd.NA

    # Parseo de fechas
    df["Fecha y hora"] = _to_datetime_clean(df["Fecha y hora"])          # ingreso
    df["Fecha_formateada"] = _to_datetime_clean(df["Fecha_formateada"])  # cierre

    # Normalizaciones
    df["Estado"] = df["Estado"].astype(str).str.strip().str.lower()
    df["Técnico"] = df["Técnico"].fillna("Sin técnico").astype(str).str.strip()
    df["Tipo de reclamo"] = df["Tipo de reclamo"].fillna("Sin tipo").astype(str).str.strip()

    # Ventana última 24h (naive)
    ahora_ts = pd.Timestamp(ahora_argentina()).tz_localize(None)
    hace_24h = ahora_ts - pd.Timedelta(hours=24)

    return df, ahora_ts, hace_24h


# ---------------------------
# Funciones públicas
# ---------------------------
def generar_reporte_diario_imagen(df_reclamos: pd.DataFrame) -> io.BytesIO:
    """
    Genera una imagen PNG con el reporte diario (últimas 24 h).
    - Ingresados 24h: por 'Fecha y hora'.
    - Resueltos 24h: por 'Fecha_formateada'.
    """
    df, ahora_ts, hace_24h = _prep_df(df_reclamos)

    # Ingresados últimas 24h
    mask_ing_24h = df["Fecha y hora"].notna() & (df["Fecha y hora"] >= hace_24h)
    total_ingresados_24h = int(mask_ing_24h.sum())

    # Resueltos últimas 24h
    mask_res_24h = (
        (df["Estado"] == "resuelto")
        & df["Fecha_formateada"].notna()
        & (df["Fecha_formateada"] >= hace_24h)
    )
    resueltos_24h = df.loc[mask_res_24h, ["Técnico", "Estado", "Fecha_formateada"]]

    tecnicos_resueltos = (
        resueltos_24h.groupby("Técnico")["Estado"]
        .count()
        .reset_index()
        .rename(columns={"Estado": "Cantidad"})
        .sort_values("Cantidad", ascending=False)
    )

    # Pendientes por tipo
    pendientes = df[df["Estado"] == "pendiente"]
    total_pendientes = int(len(pendientes))
    pendientes_tipo = (
        pendientes.groupby("Tipo de reclamo")["Estado"]
        .count()
        .reset_index()
        .rename(columns={"Estado": "Cantidad", "Tipo de reclamo": "Tipo"})
        .sort_values("Cantidad", ascending=False)
    )

    # ---------------- Imagen ----------------
    WIDTH, HEIGHT = 1200, 1600
    BG_COLOR = (39, 40, 34)
    TEXT_COLOR = (248, 248, 242)
    HIGHLIGHT_COLOR = (249, 38, 114)

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_sub = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        font_txt = ImageFont.truetype("DejaVuSans.ttf", 24)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_txt = ImageFont.load_default()

    y = 50
    line_h = 40

    def line(text, font, color, dy):
        nonlocal y
        draw.text((50, y), str(text), font=font, fill=color)
        y += dy

    fecha_str = ahora_ts.strftime("%d/%m/%Y")
    hora_str = ahora_ts.strftime("%H:%M")

    line(f"■ Reporte Diario - {fecha_str}", font_title, HIGHLIGHT_COLOR, line_h)
    line(f"Generado a las {hora_str}", font_sub, TEXT_COLOR, line_h)
    line("", font_txt, TEXT_COLOR, line_h // 2)

    line(f"■ Reclamos ingresados (24h): {total_ingresados_24h}", font_sub, HIGHLIGHT_COLOR, line_h)
    line("", font_txt, TEXT_COLOR, line_h // 2)

    line("■ Reporte técnico/grupo (24h):", font_sub, HIGHLIGHT_COLOR, line_h)
    if tecnicos_resueltos.empty:
        line("No hay reclamos resueltos en las últimas 24h", font_txt, TEXT_COLOR, line_h)
    else:
        for _, r in tecnicos_resueltos.iterrows():
            line(f"{r['Técnico']}: {int(r['Cantidad'])} resueltos (24h)", font_txt, TEXT_COLOR, line_h)

    line("", font_txt, TEXT_COLOR, line_h // 2)

    line(f"■ Quedan pendientes: {total_pendientes}", font_sub, HIGHLIGHT_COLOR, line_h)
    if pendientes_tipo.empty:
        line("Sin pendientes", font_txt, TEXT_COLOR, line_h)
    else:
        for _, r in pendientes_tipo.iterrows():
            line(f"{r['Tipo']}: {int(r['Cantidad'])}", font_txt, TEXT_COLOR, line_h)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def debug_fechas_cierre(df_reclamos: pd.DataFrame):
    """Vista rápida para entender por qué un cierre no entra en 24h."""
    st.subheader("🔍 Debug - Fechas de Cierre (24h)")
    df, ahora_ts, hace_24h = _prep_df(df_reclamos)

    st.write(f"Ahora: **{ahora_ts}** — Ventana desde: **{hace_24h}**")

    # Candidatos a resueltos 24h con columnas que ayudan a ver problemas
    df_dbg = df.loc[
        df["Estado"].isin(["resuelto", "pendiente", "en curso"]),
        ["ID Reclamo"] if "ID Reclamo" in df.columns else []
        + ["Estado", "Técnico", "Fecha y hora", "Fecha_formateada"]
    ].copy()

    df_dbg["entra_24h_resuelto"] = (
        (df_dbg["Estado"] == "resuelto")
        & df_dbg["Fecha_formateada"].notna()
        & (df_dbg["Fecha_formateada"] >= hace_24h)
    )

    st.write("**Muestra (50):**")
    st.dataframe(df_dbg.head(50), use_container_width=True)

    st.write("**Resueltos en 24h por técnico:**")
    tmp = df[df["Estado"] == "resuelto"]
    tmp = tmp[tmp["Fecha_formateada"].notna() & (tmp["Fecha_formateada"] >= hace_24h)]
    if tmp.empty:
        st.info("No hay resueltos en las últimas 24 horas.")
    else:
        st.dataframe(
            tmp.groupby("Técnico")["Estado"].count().reset_index().rename(columns={"Estado": "Cantidad"}),
            use_container_width=True,
        )
