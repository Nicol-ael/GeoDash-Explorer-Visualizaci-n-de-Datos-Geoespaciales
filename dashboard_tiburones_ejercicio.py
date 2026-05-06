import streamlit as st
import pandas as pd
from pathlib import Path

# =============================================================================
# CONFIGURACIÓN BÁSICA DE LA PÁGINA
# =============================================================================
st.set_page_config(page_title="Radar de Tiburones", page_icon="🦈", layout="wide")

st.title("🦈 Base de Datos Global: Ataques de Tiburón")
st.markdown("Sistema Táctico Oceanográfico | Demostrador de Clasificación Cartográfica de Incidentes Históricos.")

# =============================================================================
# CARGA Y LIMPIEZA DE DATOS
# =============================================================================

@st.cache_data
def cargar_datos_tiburones():
    df = pd.read_csv("geocoded-global-shark-attacks.csv")

    # Renombrar columnas
    df = df.rename(columns={
        "NEW_Latitude_Location_Area_Country": "lat",
        "NEW_Longitude_Location_Area_Country": "lon"
    })

    # Convertir a numérico
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    # Eliminar nulos
    df = df.dropna(subset=["lat", "lon"])

    # Filtrar rangos válidos
    df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)]

    return df


# Cargar datos
df = cargar_datos_tiburones()

with st.sidebar:
    st.header("Filtros")

    # País
    paises = ["Todos"] + sorted(df["country"].dropna().unique().tolist())
    pais = st.selectbox("Selecciona un país", paises)

    # Tipo de ataque
    tipos = df["type"].dropna().unique().tolist()
    tipo_seleccionado = st.multiselect("Tipo de ataque", tipos)

# Aplicar filtros
df_filtrado = df.copy()

if pais != "Todos":
    df_filtrado = df_filtrado[df_filtrado["country"] == pais]

if tipo_seleccionado:
    df_filtrado = df_filtrado[df_filtrado["type"].isin(tipo_seleccionado)]



# =============================================================================
# MÉTRICAS ESTÁTICAS SUPERIORES (KPIs)
# =============================================================================

col1, col2, col3 = st.columns(3)

# KPI 1: total de casos
col1.metric("Total ataques", len(df_filtrado))

# KPI 2: países afectados
col2.metric("Países afectados", df_filtrado["country"].nunique())

# KPI 3: actividad más peligrosa
if not df_filtrado.empty and not df_filtrado["activity"].dropna().empty:
    actividad = df_filtrado["activity"].mode()[0]
else:
    actividad = "N/A"



st.markdown("---")

# =============================================================================
# PINTANDO EL MAPA CARTOGRÁFICO
# =============================================================================
st.header("🗺️ Sonar Submarino")


st.map(df_filtrado.rename(columns={"lat": "latitude", "lon": "longitude"}))

# =============================================================================
# TABLA DE CONSULTA FINAL
# =============================================================================
st.subheader("Expedientes de los Incidentes")
st.dataframe(
    df_filtrado[["date", "year", "country", "location", "activity"]]
)

