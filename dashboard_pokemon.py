import streamlit as st # Streamlit es la librería principal que usamos para crear la interfaz web del dashboard interactivo.
import pandas as pd # Pandas es la librería esencial para análisis de datos. La usamos para cargar el CSV y filtrar información.
import pydeck as pdk # PyDeck pertenece a Uber y se utiliza para renderizar mapas 3D avanzados y capas espaciales (el Radar de Nivel 3).
import plotly.express as px # Plotly Express sirve para crear gráficos interactivos estupendos con muy pocas líneas de código.
from pathlib import Path # Path nos sirve para gestionar rutas de archivos de forma robusta, encontrando nuestro CSV automáticamente.

# Constante con el nombre del dataset que debe ubicarse en la misma carpeta que este script.
CSV_POKEMON = "300k.csv"

# =============================================================================
# DICCIONARIOS DE APOYO
# =============================================================================
# Un diccionario básico para traducir el identificador numérico (pokemonId) al nombre real del Pokémon.
# Extra: Si el número no está en esta lista pequeña, mostraremos "Pokemon #ID" genérico.
POKEMON_NAMES = {
    1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur", 4: "Charmander", 5: "Charmeleon", 
    6: "Charizard", 7: "Squirtle", 8: "Wartortle", 9: "Blastoise", 10: "Caterpie",
    13: "Weedle", 16: "Pidgey", 19: "Rattata", 21: "Spearow", 23: "Ekans",
    25: "Pikachu", 26: "Raichu", 27: "Sandshrew", 29: "Nidoran F", 32: "Nidoran M",
    35: "Clefairy", 37: "Vulpix", 39: "Jigglypuff", 41: "Zubat", 43: "Oddish",
    46: "Paras", 48: "Venonat", 50: "Diglett", 52: "Meowth", 54: "Psyduck",
    56: "Mankey", 58: "Growlithe", 60: "Poliwag", 63: "Abra", 66: "Machop",
    69: "Bellsprout", 72: "Tentacool", 74: "Geodude", 77: "Ponyta", 79: "Slowpoke",
    81: "Magnemite", 83: "Farfetch'd", 84: "Doduo", 86: "Seel", 88: "Grimer",
    90: "Shellder", 92: "Gastly", 95: "Onix", 96: "Drowzee", 98: "Krabby",
    100: "Voltorb", 102: "Exeggcute", 104: "Cubone", 106: "Hitmonlee", 107: "Hitmonchan",
    108: "Lickitung", 109: "Koffing", 111: "Rhyhorn", 113: "Chansey", 114: "Tangela",
    115: "Kangaskhan", 116: "Horsea", 118: "Goldeen", 120: "Staryu", 122: "Mr. Mime",
    123: "Scyther", 124: "Jynx", 125: "Electabuzz", 126: "Magmar", 127: "Pinsir",
    128: "Tauros", 129: "Magikarp", 131: "Lapras", 132: "Ditto", 133: "Eevee",
    137: "Porygon", 138: "Omanyte", 140: "Kabuto", 142: "Aerodactyl",
    143: "Snorlax", 144: "Articuno", 145: "Zapdos", 146: "Moltres",
    147: "Dratini", 148: "Dragonair", 149: "Dragonite", 150: "Mewtwo", 151: "Mew"
}

def pokemon_sprite_url(pokemon_id):
    """
    Función auxiliar genérica.
    Genera el enlace exacto (URL) a la imagen de un Pokémon alojada en la web oficial de PokeAPI.
    Recibe el número de identificación del Pokémon y devuelve el enlace en texto (string) al Sprite 2D.
    """
    return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"

# =============================================================================
# CONFIGURACIÓN BÁSICA DE LA PÁGINA (ESTILOS Y CABECERAS)
# =============================================================================
# st.set_page_config define cómo se presenta nuestra web en el navegador.
# Sólo puede llamarse una vez y DEBE ir antes de escribir elementos en la pantalla.
st.set_page_config(
    page_title="Pokemon GO | Clase Interactiva", # El texto que aparecerá en la pestaña del navegador web.
    page_icon="🔴",                              # Emoji que funcionará como favicon (el logo de la pestaña).
    layout="wide",                               # Forzamos que la aplicación se expanda a todo el ancho posible en la pantalla.
    initial_sidebar_state="expanded",            # Ordenamos que al cargar, la barra lateral aparezca desplegada.
)

# st.markdown permite inyectar etiquetas y código HTML directo al motor estructural del DOM.
# Lo utilizamos para incrustar comandos <style> CSS parametrizados, reconfigurando la interfaz.
st.markdown(
    """
    <style>
        /* Importamos dos fuentes personalizadas de Google Fonts: Ubuntu para números digitales y VT323 estilo consola retro */
        @import url('https://fonts.googleapis.com/css2?family=Ubuntu+Mono:wght@700&family=VT323&display=swap');

        /* .stApp da las normas a la vista principal de la web. Pintamos un color azul noche y una retícula milimétrica con degradados lineales*/
        .stApp {
            background-color: #0b132b;
            background-image: linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
            background-size: 20px 20px;
        }

        /* H1, H2.. son los encabezados. Se sobreescriben para que usen la fuente retro "VT323" y parezca un juego de GameBoy clásico */
        h1, h2, h3, h4 { 
            color: #ffcb05 !important; 
            font-family: 'VT323', monospace !important; 
            text-shadow: 3px 3px 0px #3b4cca;  /* Da un efecto sombra en azul eléctrico */
            letter-spacing: 2px; 
        }

        /* data-testid... es el selector CSS genérico de Streamlit para apuntar a la barra lateral completa. La teñimos de Rojo Pokédex Fuerte */
        [data-testid="stSidebar"] { 
            background-color: #dc0a2d !important; 
            border-right: 15px solid #8B0000; /* Le montamos un relieve lateral a la Pokédex */
        }
        
        [data-testid="stSidebar"] p { 
            font-weight: 500;
        }

        /* Creamos una nueva clase en HTML .oak-message totalmente inventada por nosotros para los diálogos del Profesor Oak simulando un RPG retro */
        .oak-message { 
            background-color: #f8f9fa; border: 4px solid #3b4cca; border-radius: 12px; 
            padding: 15px; color: #1e1e1e; font-family: sans-serif; 
            box-shadow: 6px 6px 0px #ffcb05; margin-bottom: 25px; 
        }
        .oak-message b { color: #d32f2f; font-size: 1.3rem; }

        /* Estilizado exclusivo para apuntar a las cajitas de texto (Métricas de KPI numéricas) imitando una mini-pantalla de reloj LCD verde. */
        [data-testid="stMetricValue"] {
            color: #4ade80 !important; font-family: 'Ubuntu Mono', monospace; font-size: 2.5rem;
            text-shadow: 0 0 10px rgba(74, 222, 128, 0.5); background: #000; padding: 5px 15px;
            border-radius: 5px; border: 2px solid #333; display: inline-block; width: 100%; text-align: center;
        }
        [data-testid="stMetricLabel"] { color: #e2e8f0; font-size: 1.1rem; font-weight: bold; text-align: center;}

        /* Un ligero tuneo estético a las líneas de separación o líneas de quiebre (hr) */
        hr { border-top: 3px dashed #ffcb05; }

        /* Transformamos los aburridos botones normales de Streamlit para que simulen los botones A o START de consolas clásicas (Nintendo) */
        div.stButton > button {
            background-color: #ffcc00 !important; color: #3b4cca !important; border: 3px solid #3b4cca !important;
            border-radius: 8px !important; font-weight: 900 !important; box-shadow: 3px 3px 0px #3b4cca !important; text-transform: uppercase;
        }
        /* Y si pones el ratón por encima (hover), los sumergimos un poco (quitándole el efecto de sombra y usando translateY) */
        div.stButton > button:hover { transform: translateY(3px); box-shadow: 0px 0px 0px #3b4cca !important; }
    </style>
    """,
    unsafe_allow_html=True,  # Parámetro crítico: Inhabilita la capa de sanitización estandarizada de Streamlit, permitiendo la inyección de nuestro CSS puro en el DOM interno.
)

def oak_says(text):
    """
    Componente personalizado auxiliar. 
    Inserta un globo de texto con HTML que encajará con nuestra clase de CSS .oak-message.
    """
    st.markdown(f'<div class="oak-message"><b>👴 Profesor Oak dice:</b><br><br>{text}</div>', unsafe_allow_html=True)

# Lista limitada de columnas numéricas de interés (el CSV original tiene demasiadas y nos llenarían la RAM inútilmente)
COLUMNAS_POKEMON = [
    "pokemonId", 
    "latitude", 
    "longitude", 
    "appearedLocalTime", 
    "appearedHour",
    "appearedTimeOfDay", 
    "city", 
    "continent",
    "weather", 
    "temperature", 
    "population_density", 
    "urban", 
    "suburban", 
    "rural",
    "gymDistanceKm", 
    "pokestopDistanceKm"
]

# =============================================================================
# FUNCIONES NÚCLEO (CARGA, EXTRACCIÓN Y LIMPIEZA)
# =============================================================================

# El decorador espacial @st.cache_data encapsula el retorno de la función a nivel de Memoria RAM (Memoization).
# Actúa impidiendo un sobrecosto I/O (Input/Output) de relectura de disco constante por cada mutación superficial en el DOM del Dashboard web originado por el usuario.
@st.cache_data(show_spinner=False)
def cargar_datos_pokemon():
    """
    Función inicial de transposición de datos.
    Lee el Dataset crudo dimensional, aplica un 'Rename' analítico de coordenadas forzando un casting
    matemático con la cláusula protectora errors='coerce' (Convirtiendo errores nulos a valores NaN),
    y ejecuta filtrados lógicos sobre la matriz para aislar puntos desbordados inválidamente del modelo terrícola real.
    """
    # Usamos Path(__file__) para averiguar dónde está este script (dashboard_pokemon...) dinámicamente.
    # Así podemos ejecutar la app desde cualquier carpeta sin importar dónde esté.
    ruta_csv = Path(__file__).with_name(CSV_POKEMON)

    # Si no lo encuentra, cortamos de golpe la ejecución de Python con st.stop().
    if not ruta_csv.exists():
        st.error(f"No se encontró el archivo {CSV_POKEMON} junto al dashboard.")
        st.stop()

    # Leemos el csv volcando por parámetro la lista de columnas seleccionadas (para ser rápidos y limpios), usando low_memory=False al ser gigante.
    df = pd.read_csv(ruta_csv, usecols=COLUMNAS_POKEMON, low_memory=False)

    # Las librerías de Streamlit y PyDeck adoran entender latitud con la etiqueta cruda 'lat' y longitud con 'lon', así que renombramos la cabecera.
    df = df.rename(columns={"latitude": "lat", "longitude": "lon"})

    # Aseguramos con este bucle que todos estos campos son números (convirtiendo los inconvertibles a NaNs gracias a errors="coerce")
    for columna in ["lat", "lon", "temperature", "population_density", "gymDistanceKm", "pokestopDistanceKm"]:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    # Si por algún motivo nos han entrado columnas lat/lon corruptas, no nos servirían para el mapa. Así que las borramos del juego.
    df = df.dropna(subset=["lat", "lon"])
    
    # Restringimos que nuestro espacio de coordenadas sea válido en el plano del Mundo Real. Latitudes solo van de -90 a +90, Long de -180 a +180.
    df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)]

    # Transformamos el campo texto que marcaba el tiempo de captura a tipo Datetime especializado para poder aislar si era de mañana o de tarde.
    df["appearedLocalTime"] = pd.to_datetime(df["appearedLocalTime"], errors="coerce")

    # Traducimos el ID numérico ("25") al nombre real apoyándonos en nuestro Diccionario superior POKEMON_NAMES usando un pandas `.map()`
    df["pokemon_name"] = df["pokemonId"].map(POKEMON_NAMES)
    
    # Si algún monstruo extraño que no está en la base teórica (ej. "Mewtwo") pasara el map en nulo, lo pre-rellenamos como "Pokemon #ID".
    df["pokemon_name"] = df["pokemon_name"].fillna("Pokemon #" + df["pokemonId"].astype(str))
    
    # Pulimos strings cosméticamente: reemplazamos barrabaja ("_") por espacios de forma plana para que la ciudad "New_York" se lea super bien "New York"
    df["city_label"] = df["city"].astype(str).str.replace("_", " ", regex=False)
    df["continent_label"] = df["continent"].astype(str).str.replace("_", " ", regex=False)

    # Clasificamos a nivel de zona a través de lógica manual si la captura fue en entorno urbano, rural o de extra-radio.
    df["zona"] = "Otra"
    df.loc[df["urban"], "zona"] = "Urbana"
    df.loc[df["suburban"], "zona"] = "Suburbana"
    df.loc[df["rural"], "zona"] = "Rural"

    # Retornamos el flamante DataFrame final perfectamente estructurado y formateado a Data Science puro.
    return df

def obtener_muestra(df_filtrado, max_puntos):
    """
    Función preventiva de Overloading de Memoria Gráfica. En vistas macro-espaciales globales que retornan 
    volúmenes muy extensos (ej. 150.000 nudos geográficos), el navegador del cliente es propenso a sufrir una congelación total.
    Esta función emplea df.sample para extraer exclusivamente el remanente poblacional máximo estipulado.
    """
    if len(df_filtrado) <= max_puntos: return df_filtrado
    return df_filtrado.sample(max_puntos, random_state=42)

def crear_vista_mapa(df_mapa, zoom=11, pitch=45, es_global=False):
    """
    Constructor virtual de la Cámara de Visor. 
    PyDeck requiere que le digamos dónde empieza y con qué ángulo inicial entra la cámara 3D en el plano del mapa.
    Promediamos lat y lon (_.mean) para asegurar que la cámara cae justo en el medio centroides de la ciudad solicitada!
    """
    # Retorno estructurado de ViewState (Motor Cámara de PyDeck):
    # - latitude/longitude: Fija el ancla central.
    # - zoom: Magnitud de acortamiento. Nivel 1 = Visor Global Continental, Nivel 11 = Visor Urbano.
    # - pitch: Ángulo de inclinación en grados (0 es cenital plano, >40 otorga perspectiva volumétrica).
    return pdk.ViewState(latitude=df_mapa["lat"].mean(), longitude=df_mapa["lon"].mean(), zoom=10, pitch=pitch)

def crear_densidad_grid(df_mapa, tamano_celda=0.003, max_celdas=600):
    """
    Este es el núcleo matemático del motor de bloques 3D (para que en vez de ver 1 millón de esferas apelotonadas en Nueva-York,
    dibujemos altos rascacielos sumando las apariciones que comparten calle o barrio).
    Agrupamos y redondeamos las coordenadas geográficas lat/lon en recuadros (celdas) reduciendo el tamaño a 0.003.
    """
    df_grid = df_mapa.copy()
    
    # Redondear y cuadricular latitud y longitud. Todos los puntos muy cercanos convergerán al mismo eje "ficticio" y misma baldosa.
    df_grid["lat_grid"] = (df_grid["lat"] / tamano_celda).round() * tamano_celda
    df_grid["lon_grid"] = (df_grid["lon"] / tamano_celda).round() * tamano_celda

    # Con este `agg` resumimos cuántas apariciones han ocurrido en cada "baldosa cuadriculada" y qué pokémon en específico reinó esa zona.
    densidad = (
        df_grid.groupby(["lat_grid", "lon_grid"])
        .agg(apariciones=("pokemonId", "count"), pokemon_distintos=("pokemon_name", "nunique"), pokemon_top=("pokemon_name", lambda valores: valores.mode().iloc[0]))
        .reset_index().sort_values("apariciones", ascending=False).head(max_celdas) # Obtenemos solo el Top X hexágonos de rascacielos.
    )

    # Escalamiento geométrico del modelo espacial. Mutamos cardinalidades de densidad para proyectarlas dimensionalmente sobre el eje Y Vertical Volumétrico (Eje Z nativo de Altitud 3D).
    max_apariciones = densidad["apariciones"].max()
    densidad["elevation"] = densidad["apariciones"] * 45
    
    # Computación transicional de Color: Procesamos canales RGB iterables estáticos usando interpolación matemática sobre 255.
    densidad["color_intensity"] = ((densidad["apariciones"] / max_apariciones) * 155 + 100).round().astype(int)
    densidad["color_r"] = 255
    densidad["color_g"] = densidad["color_intensity"]
    densidad["color_b"] = 5
    densidad["color_a"] = 190  # Canal estructurado "Alpha". Transforma la opacidad renderizada, otorgando la volumetría de cristal semitransparente requerida.

    return densidad


# =============================================================================
# PUNTO DE ENTRADA PRINCIPAL - EJECUCIÓN LINEAL DE REACTIVIDAD (STREAMLIT)
# =============================================================================
# Streamlit en su modelo asíncrono implementa evaluación descendente Top-to-Bottom. En cada state change (interacción),
# el script se reprocesa íntegramente. Las funciones atadas mediante @st.cache_data son consultadas instantáneamente de la RAM acortando el retardo (Latency).
df = cargar_datos_pokemon()

# =============================================================================
# HEADER Y NAVEGACIÓN PASO A PASO
# =============================================================================
# Creación de dos columnas para alinear estructuralmente la cabecera, dándole muchísimo tamaño extra (proporción 1 a 6 de peso) al título principal.
col_logo, col_tit = st.columns([1, 6])
with col_logo:
    # Mostramos un Sprite nativo de una Pokeball clásica.
    st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png", width=70)
with col_tit:
    st.title("Laboratorio Pokémon: Mapas Interactivos")

# =============================================================================
# DEFINICIÓN ARQUITECTÓNICA DE BARRA LATERAL (SIDEBAR) Y PARÁMETROS GEOGRÁFICOS
# =============================================================================
# La sintaxis de apuntado condicional 'with' encapsula las variables resultantes y widgets anidados dentro de una sección virtual estática delimitada por el DOM lateral provisto.
with st.sidebar:
    # Imprimo mi logotipo de texto estético personalizado saltándome streamlit e inyectándolo desde HTML
    st.markdown("<h1 style='text-align: center; color: white; text-shadow: 2px 2px 0px #000;'>🔴 POKÉDEX OS</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.header("🎯 Misiones de la Clase")
    
    # Construímos el switch en forma interactiva. Elegir uno de los 4 pasos recargará toda la vista main y esconderá o mostrará lo que debe ver el alumno
    paso = st.radio(
        "Niveles paso a paso:",
        [
            "Nivel 1: La Pokédex de Datos", 
            "Nivel 2: Nuestro Primer Mapa", 
            "Nivel 3: El Radar 3D (PyDeck)", 
            "Nivel 4: Investigación Completa"
        ]
    )
    
    st.markdown("---")
    st.header("🎛️ Terminal del Pokégear")
    st.markdown("<p style='color: #b8c7dd; font-size: 0.9em; margin-top:-10px;'>Configura el entorno de búsqueda</p>", unsafe_allow_html=True)

    # st.expander() envuelve el código en una caja colapsable (Panel Desplegable) súper intuitiva para ahorrar espacio si no se le necesita.
    with st.expander("🌍 Región Geográfica", expanded=True):
        st.markdown("<p style='font-size: 0.82em; color: #ffcb05;'>⚠️ <b>Tip de Data Science:</b> Tu dataset agrupa la localización usando la <b>Zona Horaria continental</b>. (Ej: 'Berlin' ilumina toda la región centro-europea).</p>", unsafe_allow_html=True)
        
        # Con value_counts contabilizamos internamente las aglomeraciones. Con esto en el selectbox a continuación mostramos métricas en vivo.
        conteo_ciudades = df["city_label"].value_counts().to_dict()
        ciudades = sorted(df["city_label"].dropna().unique().tolist())
        
        opciones_ciudades = ["🌎 Global (Todas)"] + ciudades
        
        def format_ciudad(c):
            # Formateador de texto que inyecta en el desplegable el texto 'x avistamientos' para aportar puro músculo analítico si c no es Global.
            if c == "🌎 Global (Todas)":
                return c
            return f"{c} ({conteo_ciudades.get(c, 0)} avistamientos)"
            
        ciudad_default = "New York" if "New York" in ciudades else opciones_ciudades[0]
        
        # st.selectbox es una lista desplegable única.
        ciudad = st.selectbox(
            "Macro-Región (Timezone)", 
            options=opciones_ciudades, 
            index=opciones_ciudades.index(ciudad_default),
            format_func=format_ciudad
        )

    with st.expander("🌤️ Simulador Atmosférico", expanded=True):
        # A diferencia del selectbox arriba, un campo multiselect permite a los usuarios seleccionar más de 1 categoría a su antojo
        momentos = sorted(df["appearedTimeOfDay"].dropna().unique().tolist())
        momentos_elegidos = st.multiselect("Ciclo Solar (Día/Noche)", options=momentos, default=momentos)

        climas = sorted(df["weather"].dropna().unique().tolist())
        climas_elegidos = st.multiselect("Patrón Meteorológico", options=climas, default=climas)

        temp_min = float(df["temperature"].min())
        temp_max = float(df["temperature"].max())
        
        # .slider invoca una barra bidireccional continua:
        # - min_value / max_value: Determinan los extremos operativos extrayendo el techo y suelo flotante de la base.
        # - value: Al proporcionarle una tupla (x,y), habilita automáticamente el modo de "rango entre dos valores".
        # - step: Salto condicional de incremento al deslizar (en saltos de 0.5 grados Celsius).
        rango_temp = st.slider(
            "Temperatura Exterior (ºC)",
            min_value=round(temp_min, 1), max_value=round(temp_max, 1),
            value=(round(temp_min, 1), round(temp_max, 1)), step=0.5,
        )
    
    with st.expander("🔋 Motor del Radar", expanded=False):
        # select_slider engañará a la vista en diseño permitiendo deslizar visualmente pero anclándose estéticamente solo a 3 textos permitidos.
        potencia = st.select_slider(
            "Capacidad de procesamiento Visual",
            options=["Ahorro Batería 🪫", "Rendimiento Normal 🔋", "Silph Scope Extremo ⚡"],
            value="Rendimiento Normal 🔋",
            help="Limita cuántos Pokémon dibuja la pantalla en los mapas para que no se congele el ordenador de la clase."
        )
        
        # Procesamos la regla artificial que hemos establecido para 'la carga pesada del navegador web' que afectará a obtener_muestra(df)
        if potencia == "Ahorro Batería 🪫":
            max_puntos = 500
        elif potencia == "Rendimiento Normal 🔋":
            max_puntos = 3000
        else:
            max_puntos = 10000


# =============================================================================
# FILTRADO ESTRUCTURAL DEL MODELO DATASET MEDIANTE SERIES BOOLEANAS
# =============================================================================
# Para sostener principios de mutabilidad y seguridad de variable global en Pandas, se efectúa 
# una copia dura sobre el origen primario con .copy(). Evitamos colisiones cross-sessions en tiempo de ejecución
df_filtrado = df.copy()

# A continuación, agregación en escalera de máscaras booleanas condicionales limitando y depurando los segmentos de datos solicitados:
if ciudad != "🌎 Global (Todas)":
    df_filtrado = df_filtrado[df_filtrado["city_label"] == ciudad]
    
df_filtrado = df_filtrado[df_filtrado["appearedTimeOfDay"].isin(momentos_elegidos)]
df_filtrado = df_filtrado[df_filtrado["weather"].isin(climas_elegidos)]

# El comando 'between' le indica directamente a pandas que queremos filas cuyo número fluctua entre un mínimo y un máximo matemático dado.
df_filtrado = df_filtrado[df_filtrado["temperature"].between(rango_temp[0], rango_temp[1])]

# Manejanza de errores UI: Si pides que haya Dragones apareciendo en clima helado a veces ocurren imposibles, y evitamos que python pete abruptamente
if df_filtrado.empty:
    st.warning("⚠️ El radar no encontró Pokémon con estas condiciones. ¡Cambia los filtros!")
    st.stop() # Mata explícitamente el hilo de recarga de Streamlit para que no pinte mapas vacíos ni de Error Crítico rojo.

# Llamamos a nuestro guardián anti-congelamiento 'obtener_muestra'. Solo enviamos al mapa lo que el navegador aguante bien gráficamente.
df_mapa = obtener_muestra(df_filtrado, max_puntos)


# =============================================================================
# CUADRO DE MANDO SUPERIOR (KPIs CONSTANTES EN EJE Y)
# =============================================================================
# Calcular en caliente el conteo global y especies de nuestra sub-muestra resultante para asombrar de resultados al vuelo.
total_apariciones = len(df_filtrado)
pokemon_unicos = df_filtrado["pokemon_name"].nunique()

try:
    # Intentamos obtener la fila campeona y su moda estadística (el texto más frecuente matemáticamente repetido de nuestra columna)
    # EXPLICACIÓN Pandas: 
    # .mode() busca el valor que más se repite (la moda estadística).
    # Como puede haber un empate estadístico, Pandas siempre devuelve una Lista/Serie.
    # Con .iloc[0] forzamos a extraer estrictamente el primer ganador de esa lista de empates.
    pokemon_top_id = df_filtrado["pokemonId"].mode().iloc[0]
    pokemon_top_name = df_filtrado["pokemon_name"].mode().iloc[0]
except:
    # Excepción por defecto de error, si el DataFrame se corrompió al cruzar valores, ponemos al abanderado.
    pokemon_top_id = 25 
    pokemon_top_name = "Pikachu"

# Pintamos 4 columnas para posicionar 4 elementos muy llamativos ordenados estigmatizando nuestro marco temporal superior.
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    st.metric("Total Detectados", f"{total_apariciones:,}") # st.metric es un bloque de "cifra" muy grande. Los "}" formatean a millares automáticos.
with col2:
    st.metric("Especies Únicas", pokemon_unicos)
with col3:
    st.metric("Más Frecuente", pokemon_top_name)
with col4:
    # Petición GET síncrona para recuperar la representación del PNG crudo ubicada en el alojamiento de origen remoto PokeAPI
    st.image(pokemon_sprite_url(pokemon_top_id), width=70)
    
    # Inserción estructurada del widget de audio mediante inserción binaria del string al DOM permitiendo un streaming OGG por defecto
    st.audio(f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/{pokemon_top_id}.ogg", format="audio/ogg")

st.markdown("---") # Pintará en la pantalla del usuario esa línea rota amarilla para crear espacios temáticos formales.


# =============================================================================
# LOGICA DE VISUALIZACION SECUENCIAL CONDICIONADA (NÚCLEO PRINCIPAL DE RENDER)
# =============================================================================

# ---------------------------------------------------------
# NIVEL 1
# ---------------------------------------------------------
# Condicional Switch fundamental que interviene según lo seleccionado previamente en la UI del profesor (el widget se guardó en `paso`)
if paso == "Nivel 1: La Pokédex de Datos":
    st.header("🗂️ Nivel 1: Analizando el DataFrame")
    oak_says(
        "¡Hola futuro científico de datos! Antes de crear un mapa, siempre debemos mirar qué datos tenemos en nuestro CSV.<br><br>"
        "Fíjate especialmente en que tenemos una columna <code>lat</code> (latitud) y una <code>lon</code> (longitud). "
        "Si tienes esas dos maravillas... <b>¡tienes un mapa en potencia!</b>"
    )
    
    # Enseña cómo pintar datos limpios estilo DataFrame como una tabla incrustada en tu interfaz web con `st.dataframe`
    st.dataframe(
        df_filtrado[["pokemonId", "pokemon_name", "lat", "lon", "city_label", "weather", "temperature", "appearedTimeOfDay"]].head(800), 
        use_container_width=True,
        hide_index=True 
    )

# ---------------------------------------------------------
# NIVEL 2
# ---------------------------------------------------------
elif paso == "Nivel 2: Nuestro Primer Mapa":
    st.header("🗺️ Nivel 2: El mapa más rápido usando `st.map`")
    oak_says(
        "¿Viendo datos en crudo te aburres? ¡Mapealos en 1 línea de código!<br><br>"
        "La orden <code>st.map</code> es estupenda para ver rápidamente si nuestras coordenadas caen en el lugar correcto o si tenemos "
        "Pokémon perdidos en medio del océano por un fallo de formato."
    )
    
    # Permite emular cómo se vería el texto de Python nativo codificado como un trozo educativo resaltado en la app web del alumno.
    st.code('st.map(df_mapa, latitude="lat", longitude="lon", color="#ffcb05")', language="python")
    
    es_global = (ciudad == "🌎 Global (Todas)")
    zoom_mapa = 1 if es_global else 11

    # st.map instancía nativamente MapBox con una carga cognitiva mínima:
    # - latitude / longitude: Mapeo de diccionarios de coordenadas en Pandas.
    # - zoom: Set manual para aislar el contenedor.
    # - height: Define en píxeles el tamaño vertical del bloque renderizado en el front-end.
    # - color / size: Parámetros semánticos que unifican el estilo hexadecimal de los radio-points.
    st.map(
        df_mapa,
        latitude="lat",
        longitude="lon",
        zoom=zoom_mapa,
        height=450,
        color="#ffcb05", 
        size=15
    )

# ---------------------------------------------------------
# NIVEL 3
# ---------------------------------------------------------
elif paso == "Nivel 3: El Radar 3D (PyDeck)":
    st.header("✨ Nivel 3: Construyendo un Radar con PyDeck")
    oak_says(
        "<code>st.map</code> está bien para empezar, pero para impresionar necesitamos algo espectacular.<br><br>"
        "La librería <b>PyDeck</b> nos permite crear capas sobre un mapa en 3D, añadir tooltips interactivos (prueba a pasar el ratón por los puntos) "
        "e inclinar la cámara para darle dramatismo."
    )
    
    # Estructurador dinámico interno. Puedes encadenar botones radios para crear mini-misiones dentro de las misiones principales sin problema.
    estilo_mapa = st.radio("Alternar Visor del Radar:", ["🔴 Puntos Individuales", "📶 Bloques de Densidad 3D"], horizontal=True)
    
    if estilo_mapa == "🔴 Puntos Individuales":
        st.markdown("Cada círculo brillante representa el lugar de aparición exacto de un Pokémon.")
        es_global = (ciudad == "🌎 Global (Todas)")
        vista = crear_vista_mapa(df_mapa, zoom=11, pitch=35, es_global=es_global)
        
        # Una capa Pydeck de 'Puntos' (Scatterplot). Necesita decirle qué columna maneja las ubicaciones espaciales en una lista vectorial.
        capa_puntos = pdk.Layer(
            "ScatterplotLayer",
            data=df_mapa,
            get_position="[lon, lat]",
            get_radius=800, radius_min_pixels=3, radius_max_pixels=25, # Área a teñir referida explícitamente en metros a la redonda
            get_fill_color=[239, 83, 80, 220], # Tono RGB incluyendo Alfa (Transparencia) 
            pickable=True, # Elemento mandatorio en booleano para interactuar y saltar Tooltips
            auto_highlight=True,
        )
        
        # LÓGICA DE INYECCIÓN DE TOOLTIP CON PARSEO HTML DIRECTO:
        # PyDeck y Streamlit permiten incrustar cadenas con sintaxis HTML en las etiquetas pop-up.
        # El motor JS implícitamente busca y evalúa el mapeo de toda variable contenida entre llaves {},
        # igualándola contra las métricas exactas del DataFrame que conforma ese nodo puntual de la capa.
        # Así podemos rellenar atributos estáticos como 'src' cargando imágenes bajo demanda externa usando el pokemonId propio asincrónicamente.
        tooltip_html = '''
        <div style="text-align: center; font-family: sans-serif;">
            <b style="color: #ffcb05; font-size: 1.1em;">{pokemon_name}</b> (ID: {pokemonId})<br>
            <img src='https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemonId}.png' width='80' /><br>
            <b>Hora local:</b> {appearedLocalTime}<br>
            <b>Clima:</b> {weather}<br>
            <b>Población:</b> {population_density} hab/km²
        </div>
        '''
        
        # Compilando la vista o cámara 'ViewState' y emparedando el array de capaz (en este caso una sola capa) conseguimos la unidad real del Motor Render ('pd.Deck')
        deck_puntos = pdk.Deck(
            layers=[capa_puntos],
            initial_view_state=vista,
            tooltip={"html": tooltip_html, "style": {"backgroundColor": "#1e1e1e", "color": "white"}},
        )
        
        st.pydeck_chart(deck_puntos, width="stretch") # Streamlit incrusta el gráfico nativamente pasándole la cubierta configurada deck_puntos
        
    else:
        st.markdown("Los puntos se han agrupado. Cuanto más alto es el bloque, más Pokémon aparecieron en esa esquina.")
        tamano_celda = 0.003

        # Llamamos al recálculo de pre-rendering matemático espacial que preparamos en `crear_densidad_grid`
        df_densidad = crear_densidad_grid(df_mapa, tamano_celda=tamano_celda)
        es_global = (ciudad == "🌎 Global (Todas)")
        vista_3d = crear_vista_mapa(df_mapa, zoom=11, pitch=55, es_global=es_global)
        
        # La ColumnLayer (A veces HexagonLayer funciona parecido) usa el Eje de elevación 3D nativo, creando un modelo volumétrico súper visual
        capa_columnas = pdk.Layer(
            "ColumnLayer",
            data=df_densidad,
            get_position="[lon_grid, lat_grid]",
            get_elevation="elevation",
            get_fill_color="[color_r, color_g, color_b, color_a]",
            radius=150,
            extruded=True, # Parámetro crucial que obliga a "Levantar" el eje del hexágono transformándolo a 3D puro
            pickable=True,
            elevation_scale=1,
            disk_resolution=6 # Cuántas esquinas forman una columna (resolución de 6 crea un hexágono)
        )
        
        deck_columnas = pdk.Deck(
            layers=[capa_columnas], 
            initial_view_state=vista_3d, 
            tooltip={"html": "<b>Apariciones: {apariciones}</b><br/>Rey de la zona: {pokemon_top}", "style": {"backgroundColor": "#081629", "color": "white"}}
        )
        st.pydeck_chart(deck_columnas, width="stretch")


# ---------------------------------------------------------
# NIVEL 4
# ---------------------------------------------------------
elif paso == "Nivel 4: Investigación Completa":
    st.header("📊 Nivel 4: Cuadro de Entrenador (EDA Finito)")
    oak_says(
        "Al final del día, los mapas cuentan dónde suceden las cosas, pero <b>los gráficos nos cuentan por qué</b>.<br><br>"
        "Investiga la estadística oficial de las criaturas detectadas. ¡Habrás completado la clase de hoy con maestría!"
    )
    
    col_eda1, col_eda2 = st.columns(2)

    with col_eda1:
        # Extraer velozmente a un dataframe resumido y nuevo de los 12 Pokémon con mayor conteo matemático global.
        top_pokemon_df = df_filtrado["pokemon_name"].value_counts().head(12).reset_index()
        
        # px.bar construye gráficos de barras:
        # - orientation="h": Fuerza barras horizontales para facilitar la lectura de categorías textuales (nombres de especies largas).
        # - template="plotly_dark": Carga una hoja de estilos base optimizada para fondos oscuros.
        # - color_continuous_scale: Proyección de la rampa de calor; en este caso 'Plasma' va de púrpura profundo a amarillo radiactivo.
        # - labels: Sobreescribe los feos identificadores de columnas por alias formales para ejes y leyendas.
        fig_top = px.bar(
            top_pokemon_df, x="count", y="pokemon_name", orientation="h",
            template="plotly_dark", color="count", color_continuous_scale="Plasma",
            labels={"pokemon_name": "", "count": "Apariciones"},
            title="Top 12 Especies Recolectadas",
        )
        # Fuerza que en Plotly los gráficos Horizontales cuenten de menor a mayor para ser más legibles estadísticamente.
        fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_top, use_container_width=True)

    with col_eda2:
        # px.histogram mapea la distribución volumétrica:
        # - nbins: Agrupación en contenedores. Forzamos 24 contenedores fijos (representando las 24 horas del día).
        # - color: Al asignar segmentación binaria por "appearedTimeOfDay" (Día/Noche), el histograma se colorea e interpola automáticamente creando Stacked Bars (Barras apiladas).
        fig_hora = px.histogram(
            df_filtrado, x="appearedHour", nbins=24,
            template="plotly_dark", color="appearedTimeOfDay",
            labels={"appearedHour": "Hora del día", "appearedTimeOfDay": "Momento"},
            title="Distribución Nocturna vs Diurna",
        )
        st.plotly_chart(fig_hora, use_container_width=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    cols = st.columns([1,1,1])
    with cols[1]: # Hack estético para utilizar la columna central, logrando posicionar y centrar el botón en medio visual de la pantalla.
        # st.button captura el booleano 'has_clickado == True'. Solo reacciona un milisegundo disparando lo contenido
        if st.button("🏆 HAZ CLIC PARA TERMINAR EL DÍA", use_container_width=True):
            st.balloons() # Lanza globos rebotantes como mecánica de retención festiva en navegadores del alumno.
            st.success("¡Felicidades Entrenador! Has completado el módulo y ya dominas Streamlit y Pandas.")

# =============================================================================
# EXTRA: EXPORTACIÓN DE DATOS (FUNCIONALIDAD DATA SCIENCE FUNDAMENTAL)
# =============================================================================
# Unimos la sección que exporta por sí misma a CSV todo lo que el dataframe dinámico df_filtrado contiene, dejándolo estáticamente visible inferiormente 
st.sidebar.markdown("---")
st.sidebar.header("💾 Exportar Datos")
st.sidebar.markdown("<p style='font-size: 0.85em; color: white;'>Descarga el resultado de tu radar en CSV.</p>", unsafe_allow_html=True)

# Precalcular el formateo lógico .to_csv con una decorador de memoria previene una sobreescritura 
# masiva innecesaria limitando el estrangulamiento de hardware computacional interno.
@st.cache_data
def convertir_df(df_a_guardar):
    return df_a_guardar.to_csv(index=False).encode('utf-8')

csv_data = convertir_df(df_filtrado)

# Widget final nativo descargador. Envuelve el CSV estatico y al pulsarlo ofrece la clásica ventana en Google Chrome de "Descargar En..."
if st.sidebar.download_button(
    label="📥 Extraer CSV del Radar",
    data=csv_data,
    file_name='pokemon_radar_export.csv',
    mime='text/csv'
):
    st.sidebar.snow() # Un easter-egg jugable final para demostrar la flexibilidad. Emitirá nieve solo encima de tu capa lateral.
