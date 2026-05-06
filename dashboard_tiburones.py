import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
from pathlib import Path

# =============================================================================
# CONFIGURACIÓN BÁSICA DE LA PÁGINA Y ESTÉTICA (OCEAN THEME)
# =============================================================================
st.set_page_config(page_title="Radar de Tiburones", page_icon="🦈", layout="wide")

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Jura:wght@500;700&display=swap');
        
        .stApp {
            background-color: #031224; /* Azul océano profundo */
            background-image: radial-gradient(circle at top right, #004d7a 0%, transparent 40%),
                              radial-gradient(circle at bottom left, #013a63 0%, transparent 40%);
        }
        
        h1, h2, h3 { color: #48cae4 !important; font-family: 'Jura', sans-serif !important; text-shadow: 2px 2px 5px rgba(0,0,0,0.5); }
        
        [data-testid="stSidebar"] {
            background-color: #011c34 !important;
            border-right: 5px solid #00b4d8;
        }
        
        [data-testid="stMetricValue"] {
            color: #00b4d8 !important; font-size: 2.2rem;
            text-shadow: 0px 0px 8px rgba(0, 180, 216, 0.6);
            background-color: rgba(2, 62, 138, 0.5); border-left: 4px solid #48cae4; padding-left: 15px; border-radius: 4px;
        }
        
        hr { border-top: 2px solid #0077b6; }
        
        /* Ocultar enlace de GitHub arriba a la derecha por limpieza de UI */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True
)

col_logo, col_tit = st.columns([1, 8])
with col_tit:
    st.title("🦈 Radar Global de Tiburones")
    st.markdown("<p style='color: #90e0ef; font-size: 1.1em; margin-top: -15px;'>Sistema Táctico Oceanográfico | Clasificación y Mapeo de Incidentes Históricos.</p>", unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# EXTRACCIÓN, TRANSFORMACIÓN Y CARGA DE DATOS (PIPELINE ETL)
# =============================================================================
# @st.cache_data encapsula el marco de datos en RAM (Memoization). Previene colapsos 
# de I/O al evitar que Pandas relea el fichero desde el disco tras cada recarga reactiva de la UI.
@st.cache_data(show_spinner=False)
def cargar_datos_tiburones():
    ruta_csv = Path(__file__).with_name("geocoded-global-shark-attacks.csv")
    
    if not ruta_csv.exists():
        st.error(f"No se encontró {ruta_csv.name}.")
        st.stop()
        
    # pd.read_csv procesa el archivo. low_memory=False fuerza al motor de inferencia de tipos de pandas
    # a procesar la columna completa en memoria antes de asignar Dtypes previendo colapsos mixed-type.
    df = pd.read_csv(ruta_csv, low_memory=False)
    
    # 1. Renombrar columnas larguísimas
    df = df.rename(columns={
        "NEW_Latitude_Location_Area_Country": "lat",
        "NEW_Longitude_Location_Area_Country": "lon"
    })
    
    # 2. Conversiones Numéricas
    for col in ["lat", "lon", "year"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        
    # 3. Eliminar corruptos geográficos y filtrar rangos
    df = df.dropna(subset=["lat", "lon"])
    df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)]
    
    # 4. Estandarización Categórica de Strings (Data Cleaning avanzado)
    # Uniformizamos la columna booleana heterogénea transmutándola a mayúsculas strictas (.upper())
    # y eliminando espacios residuales al principio/final con .strip()
    df['fatal_y_n'] = df['fatal_y_n'].astype(str).str.upper().str.strip()
    mapeo_fatal = {
        'Y': 'Y', 'Y X 2': 'Y', 'F': 'Y', 
        'N': 'N', 'N ': 'N', 'M': 'N', 'NQ': 'N'
    }
    df['fatal_y_n'] = df['fatal_y_n'].map(mapeo_fatal).fillna('UNKNOWN')
    
    # Rellenar valores nulos de textos descriptivos
    df['country'] = df['country'].str.upper().str.strip().fillna('UNKNOWN')
    df['species'] = df['species'].fillna('No identificada')
    df['activity'] = df['activity'].fillna('Desconocida')
    
    # Estandarizar Tipos de ataque
    df['type'] = df['type'].fillna('Unknown')
    tipos_validos = ['Unprovoked', 'Provoked', 'Watercraft', 'Sea Disaster']
    df.loc[~df['type'].isin(tipos_validos), 'type'] = 'Otra / Desconocida'
    
    return df

df = cargar_datos_tiburones()

# =============================================================================
# PANEL DE CONTROL UI (SIDEBAR Y COMPONENTES DE ENTRADA)
# =============================================================================
# El bloque estático encapsulado por 'with st.sidebar' posiciona todos sus widgets descendientes fuera del canvas gráfico principal.
with st.sidebar:
    st.markdown("<h2 style='text-align: center; font-size: 2.2rem;'>🛰️ SONAR CORE</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Filtro Año
    min_year = int(df["year"].min() if df["year"].min() > 1900 else 1900)
    max_year = int(df["year"].max())
    rango_ano = st.slider("Filtro: Ventana Temporal", min_value=min_year, max_value=max_year, value=(1950, max_year))
    
    # Filtro País
    paises = sorted(df[df["country"] != "UNKNOWN"]["country"].unique().tolist())
    pais = st.selectbox("Límites Territoriales (País)", ["🌍 Océano Global"] + paises)
    
    # Filtro Fatalidad
    fatal_options = ["Ambos", "Solo Fatales (Muerte)", "No Fatales (Supervivencia)"]
    fatalidad = st.radio("Severidad del Incidente:", fatal_options)

    # Filtro Tipo de Ataque
    tipos = sorted(df["type"].unique().tolist())
    tipo_elegidos = st.multiselect("Clasificación del Incidente", options=tipos, default=tipos)
    
    # Info lateral dinámica
    st.markdown("---")
    st.info("💡 **Consejo:** El radar puede distinguir incidentes mortales pintándolos de rojo brillante en el mapa PyDeck.")

# =============================================================================
# PROCESAMIENTO ESPACIO-TEMPORAL LÓGICO (FILTROS PANDAS)
# =============================================================================
# Principio de inmutabilidad: Se ejecuta una copia en crudo de la instancia matriz para preservar
# el snapshot en memoria estático sin interferencias durante cross-filtering.
df_filtrado = df.copy()

# Filtro 1: Año
df_filtrado = df_filtrado[df_filtrado["year"].between(rango_ano[0], rango_ano[1])]

# Filtro 2: País
if pais != "🌍 Océano Global":
    df_filtrado = df_filtrado[df_filtrado["country"] == pais]

# Filtro 3: Severidad
if fatalidad == "Solo Fatales (Muerte)":
    df_filtrado = df_filtrado[df_filtrado["fatal_y_n"] == 'Y']
elif fatalidad == "No Fatales (Supervivencia)":
    df_filtrado = df_filtrado[df_filtrado["fatal_y_n"] == 'N']

# Filtro 4: Tipo
df_filtrado = df_filtrado[df_filtrado["type"].isin(tipo_elegidos)]

if df_filtrado.empty:
    st.warning("📡 El sonar no detecta incidentes bajo estos parámetros. Amplía el rango temporal o cambia de país.")
    st.stop()


# =============================================================================
# MÓDULO SUPERIOR: INDICADORES CLAVE (KPIs)
# =============================================================================
total_casos = len(df_filtrado)
paises_afectados = df_filtrado[df_filtrado["country"] != "UNKNOWN"]["country"].nunique()

try:
    actividad_top = df_filtrado[df_filtrado["activity"] != "Desconocida"]["activity"].mode().iloc[0]
except:
    actividad_top = "Indetectable"
    
fatal_percentage = (len(df_filtrado[df_filtrado['fatal_y_n'] == 'Y']) / len(df_filtrado)) * 100 if len(df_filtrado) > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros Detectados", f"{total_casos:,}")
c2.metric("Peligrosidad Promedio", f"{fatal_percentage:.1f}% FATAL")
c3.metric("Países Implicados", paises_afectados)
c4.metric("Actividad Hostil #1", actividad_top[:22])

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# TABS INTERACTIVAS (CARTOGRAFÍA Y ESTADÍSTICA)
# =============================================================================
pestanas = st.tabs(["🗺️ Océano 2D", "🔴 Radar Láser 3D", "📊 Estadísticas Críticas"])

# ~~~ PESTAÑA 1: st.map ~~~
with pestanas[0]:
    st.subheader("Ubicaciones Estáticas Detectadas")
    st.markdown("Topología 2D plana proyectada internamente vía MapBox primitivo.")
    
    # st.map compila un renderizador topológico estándar ortogonal:
    # - color: Admite hex strings puros superponiendo estéticamente los key-pairs lat/lon.
    # - zoom: Interpolado lógicamente para retroceder dinámicamente si el país de observación es el "Océano Global".
    st.map(df_filtrado, latitude="lat", longitude="lon", color="#00b4d8", zoom=4 if pais != "🌍 Océano Global" else 1)


# ~~~ PESTAÑA 2: PYDECK ~~~
with pestanas[1]:
    st.subheader("Capa de Evaluación Estratégica 3D")
    st.markdown("Los puntos <b style='color:#ff1a1a;'>Rojos</b> identifican encuentros con pérdida de vidas. Ubica áreas calientes.")
    
    df_pydeck = df_filtrado.copy()
    
    # Asignar un semáforo de colores inteligente a los vectores RGB
    def asignar_color(fatal):
        if fatal == 'Y':
            return [255, 26, 26, 200]   # Rojo Peligro
        elif fatal == 'N':
            return [0, 180, 216, 150]   # Azul Seguro
        else:
            return [255, 204, 0, 150]   # Amarillo Incógnita

    df_pydeck['color'] = df_pydeck['fatal_y_n'].apply(asignar_color)
    
    vista_marina = pdk.ViewState(
        latitude=df_pydeck["lat"].mean(), 
        longitude=df_pydeck["lon"].mean(), 
        zoom=3 if pais == "🌍 Océano Global" else 5, 
        pitch=40
    )
    
    # ScatterplotLayer renderiza dispersión volumétrica optimizada espacialmente:
    # - radius_min_pixels / radius_max_pixels: Obliga escalarmente a la vista 3D a comprimir o inflar esferas vectoriales en función del Zoom.
    # - get_fill_color: Ancla iterativa a la tupla matricial RGB "color" precalculada en el DataFrame que conformamos previamente.
    capa_tiburones = pdk.Layer(
        "ScatterplotLayer",
        data=df_pydeck,
        get_position="[lon, lat]",
        get_radius=20000, 
        radius_min_pixels=3,
        radius_max_pixels=15,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True
    )
    
    deck = pdk.Deck(
        map_style=None,
        layers=[capa_tiburones],
        initial_view_state=vista_marina,
        tooltip={
            "html": "<b>Misión: {year} | {country}</b><br/><b>Especie:</b> <span style='color:#48cae4;'>{species}</span><br/><b>Actividad:</b> {activity}<br><b>Fatal:</b> {fatal_y_n}",
            "style": {"backgroundColor": "#031224", "color": "white", "border-left": "4px solid #ff1a1a"}
        }
    )
    
    st.pydeck_chart(deck, use_container_width=True)


# ~~~ PESTAÑA 3: EDA AVANZADO MÓDULO PLOTLY ~~~
with pestanas[2]:
    st.subheader("Informes Científicos")
    
    # Vista tabular optimizada inyectada verticalmente.
    # - use_container_width: Absorbe forzosamente todo el pixelaje que proporcione la grilla de Streamlit.
    # - hide_index: Oculta la cardinalidad numérica en sucio arrastrada primigeniamente de la fase de Carga.
    st.dataframe(
        df_filtrado[['date', 'year', 'type', 'country', 'activity', 'fatal_y_n', 'species']].head(300), 
        use_container_width=True, 
        hide_index=True
    )
    st.caption("Aviso Técnico: Muestra operativa iterativamente seccionada y limitada (head=300) aislando la paginación DOM para reducir latencia.")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    cols_graficos = st.columns(2)
    
    with cols_graficos[0]:
        # px.pie dibuja segmentaciones en rosca/torta:
        # - hole: Porcentaje paramétrico (0.6 -> 60%) vacío concéntrico central.
        # - color_discrete_map: Mapea diccionariamente categorías literales ("Y", "N", "UNKNOWN") forzando el emparejamiento hexa-cromático absoluto deseado.
        fatal_counts = df_filtrado['fatal_y_n'].value_counts().reset_index()
        fig_pie = px.pie(
            fatal_counts, values='count', names='fatal_y_n', hole=0.6,
            title='Proporción de Mortalidad Global', template='plotly_dark',
            color='fatal_y_n',
            color_discrete_map={'Y': '#ff1a1a', 'N': '#00b4d8', 'UNKNOWN': '#ffcc00'}
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with cols_graficos[1]:
        # Agrupación temporal: Aislamos registros post-1950 por contornos de sesgo de reporte histórico.
        evolucion = df_filtrado[df_filtrado['year'] >= 1950]
        
        # px.histogram sobre series continuas:
        # - nbins=70: Estipula forzar al kernel estadístico a intentar rebanar la línea base del eje temporal en 70 segmentos representativos.
        # - color_discrete_sequence: Inyección en lista unitaria del color de las franjas (Cyan Neón)
        fig_line = px.histogram(
            evolucion, x='year', nbins=70, 
            title='Frecuencia Global Registrada (1950 - Presente)', 
            template='plotly_dark', 
            color_discrete_sequence=['#48cae4']
        )
        st.plotly_chart(fig_line, use_container_width=True)
