# =============================================================================
# 1. IMPORTS
# =============================================================================
import streamlit as st
import pandas as pd
import geopandas as gpd
from folium.plugins import MarkerCluster
from streamlit_option_menu import option_menu
from PIL import Image
import plotly.express as px
import matplotlib.pyplot as plt
import os
import time
import pydeck as pdk

# Importa el motor C++ compilado. Si no existe, la app se detendrá con un error claro.
try:
    # 1. Este es el primer cambio: importar el módulo directamente.
    import motor_sjoin_cpp
except ImportError:
    st.error(
        "Error Crítico: No se pudo importar el módulo 'motor_sjoin_cpp'. "
        "Asegúrate de haber compilado el proyecto con éxito usando el último comando g++ para pybind11."
    )
    st.stop()

# =============================================================================
# 2. CONFIGURACIÓN DE LA PÁGINA
# =============================================================================
st.set_page_config(page_title="Catálogo Sísmico del Perú", page_icon="🌍", layout="wide")

# =============================================================================
# 3. FUNCIÓN DE CARGA DE DATOS IMPULSADA POR C++ (CON CACHÉ)
# =============================================================================
@st.cache_data
def cargar_datos_con_motor_cpp():
    """
    Función de carga principal que delega el trabajo pesado (sjoin) al motor C++.
    Se ejecuta una sola vez gracias a la caché.
    """
    inicio_total = time.time()
    
    # 1. Cargar los datos crudos desde los archivos
    sismos_df = pd.read_csv("Dataset_1960_2023_sismo.csv")
    departamentos_gdf = gpd.read_file("departamentos_perú.geojson")
    sismos_df.dropna(subset=['LATITUD', 'LONGITUD'], inplace=True)
    
    # 2. Preparar los datos en un formato simple para C++
    coords_sismos = list(zip(sismos_df['LATITUD'], sismos_df['LONGITUD']))
    wkts_departamentos = departamentos_gdf["geometry"].to_wkt().tolist()
    nombres_departamentos = departamentos_gdf["NOMBDEP"].tolist()

    # 3. ¡Llamar al motor de C++ para hacer el trabajo pesado!
    resultados_cpp = motor_sjoin_cpp.realizar_sjoin_paralelo_cpp(
        coords_sismos, wkts_departamentos, nombres_departamentos
    )
    
    # 4. Integrar los resultados y preparar el DataFrame final para la app
    sismos_df['DEPARTAMENTO'] = resultados_cpp
    sismos_df = sismos_df[sismos_df['DEPARTAMENTO'] != "Fuera de Perú"]
    
    sismos_df['FECHA_UTC'] = pd.to_datetime(sismos_df['FECHA_UTC'], format='%Y%m%d', errors='coerce')
    sismos_df['AÑO'] = sismos_df['FECHA_UTC'].dt.year
    month_names_map = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    sismos_df['MES_NOMBRE'] = sismos_df['FECHA_UTC'].dt.month.map(month_names_map)

    # Convertimos el resultado final a un GeoDataFrame para el mapa
    gdf_final = gpd.GeoDataFrame(
        sismos_df, geometry=gpd.points_from_xy(sismos_df['LONGITUD'], sismos_df['LATITUD'])
    )
    
    fin_total = time.time()
    tiempo_total = fin_total - inicio_total
    
    return gdf_final, departamentos_gdf, tiempo_total

# =============================================================================
# 4. DEFINICIÓN DE LAS PÁGINAS DE LA APLICACIÓN
# (Aquí debes pegar el contenido de tus páginas)
# =============================================================================


def pagina_inicio():
    st.title("Catálogo Sísmico 1960 - 2023")
    st.markdown("<h1 style='color:blue; text-align:center;'>BIENVENIDO A LA APLICACIÓN DE ANÁLISIS DE SISMOS</h1>", unsafe_allow_html=True)
    # Introducción al tema
    st.markdown("""
    ### ¿Qué es un sismo?
    Un sismo es una sacudida brusca y pasajera de la corteza terrestre que se produce por diversas causas, siendo las más comunes la actividad de fallas geológicas. También puede originarse por la fricción en el borde de placas tectónicas, procesos volcánicos, impactos de asteroides o explosiones nucleares subterráneas realizadas por el ser humano.

    El punto donde inicia el movimiento dentro de la Tierra se llama hipocentro o foco, y el lugar de la superficie terrestre directamente encima de este punto se denomina epicentro. Los sismos generan ondas sísmicas que se propagan desde el hipocentro y pueden causar fenómenos como desplazamientos de la corteza terrestre, tsunamis, corrimientos de tierras o actividad volcánica, dependiendo de su magnitud y origen.

    Se clasifican en varios tipos, como tectónicos, volcánicos, superficiales, y pueden medirse mediante escalas como la de Richter o la de magnitud de momento.

    ### Importancia del monitoreo de sismos
    - **Prevención**: El análisis de los datos sísmicos ayuda a entender las zonas de riesgo y diseñar construcciones más seguras.
    - **Ciencia**: Proporciona información clave sobre la dinámica del planeta Tierra.
    - **Educación**: Incrementa la conciencia pública sobre cómo actuar en caso de sismos.

    En esta aplicación, puedes explorar datos sísmicos registrados desde 1960 hasta 2023. Usa las opciones del menú para visualizar mapas, gráficos y aplicar filtros personalizados según tus intereses.
    """)
    img = Image.open("img/sismoportada.jpeg")
    img = img.resize((250, 300))  # Ajusta el valor de la altura según lo necesario
    
    # Mostrar la imagen redimensionada
    st.image(img)
    st.markdown("https://sinia.minam.gob.pe/sites/default/files/sial-sialtrujillo/archivos/public/docs/328.pdf")
    # st.image(
    #     "img/sismo.png",  # Ruta relativa a la imagen
    #     caption="El movimiento de la tierra nos impulsa a ser más conscientes y a valorar cada instante",
    #     use_container_width=True
    # )
    
    col1, col2 = st.columns([4,1])
    st.markdown("<h3>Componentes<h3>", unsafe_allow_html=True)
    # Conclusión  al tema
    with col1:
        st.markdown("""
        <p>
        El Perú, ubicado en el Cinturón de Fuego del Pacífico, es una región altamente sísmica. Esta actividad, combinada con un alto porcentaje de viviendas construidas mediante autoconstrucción o de antigüedad considerable, incrementa significativamente la vulnerabilidad de su población frente a eventos sísmicos. En este contexto, la plataforma de catálogo sísmico (1960-2023) que hemos desarrollado se convierte en una herramienta fundamental para informar a los usuarios sobre los sismos históricos en el país, facilitar la investigación sismológica con una base de datos homogénea y concientizar a la población sobre la recurrencia de estos eventos y la importancia de estar preparados [1].
        Nuestra plataforma cuenta con funcionalidades clave diseñadas para mejorar la comprensión de los usuarios. A través de mapas interactivos, es posible visualizar la distribución espacial de los sismos, diferenciados por colores según su magnitud o profundidad [2]. Los filtros dinámicos permiten realizar búsquedas específicas por magnitud, profundidad, fecha y departamento, mientras que gráficos como histogramas y dispersión ofrecen análisis detallados sobre la frecuencia de los sismos y la relación entre sus parámetros. Además, cada evento cuenta con información detallada sobre su fecha, hora, magnitud, profundidad, ubicación y, cuando sea posible, datos sobre daños ocasionados.
        El diseño intuitivo de la interfaz y la inclusión de recursos educativos sobre la sismología en Perú contribuyen a que esta herramienta sea accesible tanto para investigadores como para el público en general. Asimismo, se considera crucial mantener la base de datos actualizada con los últimos eventos sísmicos para garantizar la relevancia y efectividad de la plataforma [3].
        Con esta plataforma, buscamos no solo aumentar el conocimiento sobre la actividad sísmica en el Perú, sino también contribuir a la toma de decisiones informadas para la prevención y mitigación de desastres, fortaleciendo así la resiliencia de nuestras
        comunidades ante futuros eventos. sísmicos.</p>""", unsafe_allow_html=True)
    with col2: 
        st.image(
            "img/sismo_intro.png",  # Ruta relativa a la imagen
            caption="El movimiento de la tierra nos impulsa a ser más conscientes y a valorar cada instante",  use_container_width=True
        )
    col1, col2 = st.columns([1,4])
    with col1:
        img = Image.open("img/informesismo.png")
        img = img.resize((250, 300))  # Ajusta el valor de la altura según lo necesario
        # Mostrar la imagen redimensionada
        st.image(img)
    with col2:
        st.markdown("""
        <h5 style="color:blue; font-weight:bold; margin-bottom:5px;">Sismotectónica del sismo de Yauca del 28 de junio 2024 (M7.0) y niveles de sacudimiento del suelo - Informe Técnico N° 023-2024/IGP Ciencias de la Tierra Sólida</h5>
        
        <p style="font-size:1.2rem;">El 28 de junio de 2024, un sismo de magnitud 7.0 ocurrió a 54 km al SO de Yauca, Arequipa, con sacudidas percibidas hasta 500 km. Fue causado por la fricción entre las placas de Nazca y Sudamericana, generando 16 réplicas en 48 horas. El área de ruptura fue de 55 x 70 km. Aceleraciones de 150 cm/seg² en Yauca, Chala, Atiquipa y Bella Unión provocaron daños en viviendas de adobe y concreto, además de deslizamientos en la Panamericana Sur y vías secundarias.</p>
        
        """, unsafe_allow_html=True)

        st.markdown("""https://sigrid.cenepred.gob.pe/sigridv3/documento/17731.""")
    col1, col2 = st.columns([1,4])
    with col1:
        img = Image.open("img/mapasismico.png")
        img = img.resize((250, 300))  # Ajusta el valor de la altura según lo necesario
        # Mostrar la imagen redimensionada
        st.image(img)

    with col2:
        st.markdown("""
        <h5 style="color:blue; font-weight:bold; margin-bottom:5px;">MAPAS SÍSMICOS</h5>
        
        <p style="font-size:1rem;">El 19 de septiembre de 2013, el Instituto Geofísico del Perú (IGP) presentó el Mapa Sísmico del Perú en el Ministerio del Ambiente (MINAM), resultado de un trabajo de cuatro años concluido en 2012. Este documento detalla la distribución de eventos sísmicos entre 1960 y 2011, clasificados por profundidad, y permite identificar las zonas más afectadas por sismos en el país. Hernando Tavera, responsable del área de Sismología del IGP, destacó que las ciudades de la Costa son las más impactadas por sismos de intensidad regular y alta. En la sierra y la selva, las regiones con mayor actividad sísmica incluyen Moyobamba, Rioja, Ayacucho, Huancayo, Cusco y el Cañón del Colca, en Arequipa. Los mapas fueron entregados a direcciones del MINAM, como la Dirección de Investigación e Información Ambiental y la de Ordenamiento Territorial, para apoyar la gestión del riesgo y la preparación de la población ante sismos. La ceremonia contó con la participación de autoridades del IGP, MINAM, INDECI, RedPeIA, SOS Emergencias, la Municipalidad de Lima y otros organismos. </p>
        
        """, unsafe_allow_html=True)

        st.markdown("""https://sinia.minam.gob.pe/novedades/sismos-son-mas-frecuentes-fuertes-costa-pais""")
    col1, col2 = st.columns([1,4])
    with col1:
        img = Image.open("img/simulaciones.png")
        img = img.resize((250, 300))  # Ajusta el valor de la altura según lo necesario
        # Mostrar la imagen redimensionada
        st.image(img)
    with col2:
        st.markdown("""
        <h5 style="color:blue; font-weight:bold; margin-bottom:5px; ">Aprueban la Ejecución de Simulacros y Simulaciones y la Directiva “Ejecución de Simulacros y Simulaciones Ante Peligros Asociados a Fenómenos de Origen Natural”</h5>
        
        <p style="font-size:1.2rem;">reaccionar ante diversos escenarios (por bajas temperaturas; sismos seguido de tsunami; sismos seguido de fenómenos de geodinámica externa y por intensas precipitaciones pluviales) y la ejecución de las simulaciones tiene por objeto poner a prueba los Planes de Gestión Reactiva de los sectores, gobiernos regionales y locales, entidades públicas y privadas. .</p>
        
        """, unsafe_allow_html=True)

        st.markdown("""https://sinia.minam.gob.pe/sites/default/files/sinia/archivos/public/docs/rm_080-2016-pcm.pdf""")
    col1, col2 = st.columns([1,4])
    with col1:
        img = Image.open("img/frecuentes.png")
        img = img.resize((250, 300))  # Ajusta el valor de la altura según lo necesario
        # Mostrar la imagen redimensionada
        st.image(img)
    with col2:
        st.markdown("""
        <h5 style="color:blue; font-weight:bold; margin-bottom:5px;">Sismos son más frecuentes y fuertes en la costa del país</h5>
        
        <p style="font-size:1.2rem;">El Mapa Sísmico del Perú muestra sismos de magnitud ≥M4.0 desde 1960, según datos del IGP y Engdahl & Villaseñor. Clasifica eventos como superficiales, intermedios y profundos, según la profundidad de sus focos. Los sismos se originan en tres fuentes: contacto entre placas (como el terremoto de Pisco 2007, 8.0Mw), deformación continental (Moyobamba 1991, M6.0), y deformación oceánica (2011, M7.0). Predomina la actividad sísmica en el Centro y Sur. Este mapa es clave para delimitar zonas sismogénicas y prevenir riesgos.</p>
        
        """, unsafe_allow_html=True)

        st.markdown("""https://ultimosismo.igp.gob.pe/mapas-sismicos""")

    st.markdown("""
    ### Recursos adicionales
    - [El sitio web oficial de los registros administrativos del riesgo de desastres](https://sigrid.cenepred.gob.pe/sigridv3/documento/17731)
    - [El Sistema Nacional de Información Ambiental](https://sinia.minam.gob.pe/normas/aprueban-ejecucion-simulacros-simulaciones-directiva-ejecucion)
    """)

    st.info("🙌La naturaleza puede ser poderosa, pero la valentía y la solidaridad de las personas son indestructibles.🥰")

def pagina_mapa(gdf, departamentos_gdf):
    st.title("🗺️ Mapa Interactivo de Sismos - Degradado Oscuro y Círculos Grandes")

    # --- Filtros ---
    with st.sidebar:
        st.header("Filtros del Mapa")
        deptos = ["Todos"] + sorted(gdf["DEPARTAMENTO"].unique())
        filtro_deptos = st.multiselect("Departamento", deptos, default=["Todos"])

        años = sorted(gdf["AÑO"].dropna().unique())
        r_anos = st.slider("Rango de Años", int(min(años)), int(max(años)), (int(min(años)), int(max(años))))

        r_mag = st.slider("Magnitud", float(gdf["MAGNITUD"].min()), float(gdf["MAGNITUD"].max()), 
                          (float(gdf["MAGNITUD"].min()), float(gdf["MAGNITUD"].max())))

        r_prof = st.slider("Profundidad (km)", float(gdf["PROFUNDIDAD"].min()), float(gdf["PROFUNDIDAD"].max()), 
                          (float(gdf["PROFUNDIDAD"].min()), float(gdf["PROFUNDIDAD"].max())))

    # --- Filtros aplicados ---
    mask = (gdf["AÑO"].between(*r_anos)) & \
           (gdf["MAGNITUD"].between(*r_mag)) & \
           (gdf["PROFUNDIDAD"].between(*r_prof))
    if "Todos" not in filtro_deptos:
        mask &= gdf["DEPARTAMENTO"].isin(filtro_deptos)
    filtered_gdf = gdf[mask]
    st.info(f"🔍 Mostrando {len(filtered_gdf)} de {len(gdf)} sismos")

    # --- Agrupación por departamento ---
    grouped = filtered_gdf.groupby("DEPARTAMENTO").agg({
        "LATITUD": "mean",
        "LONGITUD": "mean",
        "MAGNITUD": "mean",
        "FECHA_UTC": "count"
    }).reset_index().rename(columns={"FECHA_UTC": "CANTIDAD_SISMOS"})

    max_sismos = grouped["CANTIDAD_SISMOS"].max()
    min_sismos = grouped["CANTIDAD_SISMOS"].min()

    # --- Degradado verde oscuro → amarillo fuerte → rojo oscuro
    def color_degradado(cantidad):
        ratio = (cantidad - min_sismos) / (max_sismos - min_sismos + 1e-9)
        if ratio <= 0.5:
            # Verde oscuro (0,128,0) → Amarillo fuerte (255,215,0)
            r = int(ratio * 2 * (255 - 0))
            g = int(128 + ratio * 2 * (215 - 128))
            b = 0
        else:
            # Amarillo fuerte (255,215,0) → Rojo oscuro (200,0,0)
            r = int(255 - (ratio - 0.5) * 2 * (255 - 200))
            g = int(215 - (ratio - 0.5) * 2 * 215)
            b = 0
        return [r, g, b, 220]

    grouped["color"] = grouped["CANTIDAD_SISMOS"].apply(color_degradado)
    grouped["radius"] = grouped["CANTIDAD_SISMOS"] / max_sismos * 100000  # aún más grandes

    # --- Círculos (Scatterplot) ---
    circle_layer = pdk.Layer(
        "ScatterplotLayer",
        data=grouped,
        get_position='[LONGITUD, LATITUD]',
        get_radius="radius",
        get_fill_color="color",
        pickable=True,
        auto_highlight=True
    )

    # --- Texto con número de sismos ---
    text_layer = pdk.Layer(
        "TextLayer",
        data=grouped,
        get_position='[LONGITUD, LATITUD]',
        get_text="CANTIDAD_SISMOS",
        get_size=18,
        get_color=[255, 255, 255],
        get_alignment_baseline="'center'",
    )

    # --- Bordes departamentales ---
    deptos_layer = pdk.Layer(
        "GeoJsonLayer",
        data=departamentos_gdf.__geo_interface__,
        stroked=True,
        filled=False,
        get_line_color=[0, 100, 255],
        line_width_min_pixels=2,
    )

    # --- Vista inicial ---
    view_state = pdk.ViewState(
        latitude=-9.2,
        longitude=-75,
        zoom=5,
        pitch=0
    )

    # --- Tooltip al pasar el mouse ---
    tooltip = {
        "html": "<b>Departamento:</b> {DEPARTAMENTO} <br>"
                "<b>Sismos:</b> {CANTIDAD_SISMOS} <br>"
                "<b>Magnitud Promedio:</b> {MAGNITUD:.2f}",
        "style": {"color": "white", "backgroundColor": "steelblue"}
    }

    # --- Renderizar mapa final ---
    st.pydeck_chart(pdk.Deck(
        layers=[deptos_layer, circle_layer, text_layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/light-v10"
    ))

def pagina_graficos(df):
    st.title("📊 Análisis Gráfico de Sismos")
    
    # Menús de selección en la barra lateral para una mejor experiencia
    with st.sidebar:
        st.header("Opciones de Gráficos")
        selected_graph = st.radio(
            "Analizar por:",
            ["Año", "Magnitud", "Profundidad"]
        )
        tipo_grafico = st.selectbox(
            "Tipo de Gráfico:",
            ["Barras", "Sector Circular", "Líneas"]
        )
    
    st.markdown("---")

    if selected_graph == "Año":
        visualizacion_anos(df, tipo_grafico)
    elif selected_graph == "Magnitud":
        visualizacion_magnitud(df, tipo_grafico)
    elif selected_graph == "Profundidad":
        visualizacion_profundidad(df, tipo_grafico)


def pagina_conclusion():
    st.title("Conclusión del Proyecto")
    
    st.markdown(""" 
    <h2>Análisis de Riesgos Sísmicos en Perú y el Desarrollo de una Plataforma de Catálogo Sísmico<h2>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    # Conclusión  al tema
    with col1:
        st.markdown("""
        <p style='font-size: 1.4rem;'>
        En conclusión, nuestro proyecto consiste en el desarrollo de un dashboard interactivo para visualizar y analizar datos sísmicos de Perú entre 1960 y 2023, utilizando un dataset en formato CSV. Realizamos un procesamiento de datos para asignar los sismos a departamentos específicos y ajustamos el formato de fecha y hora para mayor legibilidad. El dashboard, construido con Streamlit, ofrece funcionalidades como filtros de selección, gráficos de barras y un mapa interactivo. La interfaz incluye un menú de navegación para facilitar la interacción del usuario, y destacamos la importancia de una guía de usuario que explique el uso del dashboard con imágenes ilustrativas.
        Consideramos que el proyecto tiene un alto potencial para la evaluación de riesgos sísmicos, la investigación geológica y la educación pública. Sin embargo, es fundamental asegurar la implementación completa del código, tener en cuenta la precisión de la geolocalización y mantener el dataset actualizado.
        </p>""", unsafe_allow_html=True)

    with col2:
        st.image(
            "img/sismo_conclusion.png",  # Ruta relativa a la imagen
            caption="El movimiento de la tierra nos impulsa a ser más conscientes y a valorar cada instante", use_container_width=True
        )

    st.markdown("""
    ### Recursos adicionales
    - [El sitio web oficial de los registros administrativos del riesgo de desastres](https://sigrid.cenepred.gob.pe/sigridv3/documento/17731)
    - [El Sistema Nacional de Información Ambiental](https://sinia.minam.gob.pe/normas/aprueban-ejecucion-simulacros-simulaciones-directiva-ejecucion)
    """)
    st.info("🙌La naturaleza puede ser poderosa, pero la valentía y la solidaridad de las personas son indestructibles.🥰")

def pagina_sobre_nosotros():
    st.title("¡Sobre Nosotros!")   
    st.markdown("### 🧑‍💻 Equipo del Proyecto")
    st.divider()

    personas = [
        {"nombre": "", "info": "", "imagen": "img/noemi.png"},
        {"nombre": "", "info": "", "imagen": "img/ruben.png"},
        {"nombre": "", "info": "", "imagen": "img/sebastian.png"},
        {"nombre": "", "info": "", "imagen": "img/valery.png"},
        {"nombre": "", "info": "", "imagen": "img/milagros.png"}
    ]

    # Iteramos sobre la lista de personas de dos en dos para crear las filas
    for i in range(0, len(personas), 2):
        
        # Creamos una nueva fila con dos columnas en cada iteración
        col1, col2 = st.columns(2)
        
        # Procesamos la primera persona de la fila (la de la izquierda)
        with col1:
            try:
                # Usamos el ancho fijo de 450 que preferías
                st.image(personas[i]["imagen"], width=450)
            except FileNotFoundError:
                st.error(f"Error: No se encontró la imagen '{personas[i]['imagen']}'")
        
        # Verificamos si existe una segunda persona para esta fila (para evitar errores con números impares)
        if (i + 1) < len(personas):
            # Si existe, la procesamos en la columna de la derecha
            with col2:
                try:
                    # Usamos el ancho fijo de 450 que preferías
                    st.image(personas[i+1]["imagen"], width=450)
                except FileNotFoundError:
                    st.error(f"Error: No se encontró la imagen '{personas[i+1]['imagen']}'")

# --- Funciones de visualización para la página de gráficos ---
def visualizacion_anos(df, tipo_grafico):
    st.subheader(f"Análisis de Sismos por Año - Gráfico de {tipo_grafico}")
    conteo = df['AÑO'].value_counts().sort_index()
    if tipo_grafico == "Barras":
        fig = px.bar(conteo, x=conteo.index, y=conteo.values, labels={"x": "Año", "y": "Cantidad de Sismos"}, title="Cantidad de Sismos por Año")
    elif tipo_grafico == "Sector Circular":
        fig = px.pie(values=conteo.values, names=conteo.index, title="Distribución Porcentual de Sismos por Año")
    else:
        fig = px.line(conteo, x=conteo.index, y=conteo.values, markers=True, labels={"x": "Año", "y": "Cantidad de Sismos"}, title="Tendencia de Sismos a lo Largo de los Años")
    st.plotly_chart(fig, use_container_width=True)

def visualizacion_magnitud(df, tipo_grafico):
    st.subheader(f"Análisis de Sismos por Magnitud - Gráfico de {tipo_grafico}")
    df_temp = df.copy()
    df_temp['MAGNITUD_ROUND'] = df_temp['MAGNITUD'].round(0)
    conteo = df_temp['MAGNITUD_ROUND'].value_counts().sort_index()
    if tipo_grafico == "Barras":
        fig = px.bar(conteo, x=conteo.index, y=conteo.values, labels={"x": "Magnitud (redondeada)", "y": "Cantidad de Sismos"}, title="Distribución de Sismos por Magnitud")
    elif tipo_grafico == "Sector Circular":
        fig = px.pie(values=conteo.values, names=conteo.index, title="Distribución Porcentual de Sismos por Magnitud")
    else:
        fig = px.line(conteo, x=conteo.index, y=conteo.values, markers=True, labels={"x": "Magnitud (redondeada)", "y": "Cantidad de Sismos"}, title="Frecuencia de Sismos por Nivel de Magnitud")
    st.plotly_chart(fig, use_container_width=True)

def visualizacion_profundidad(df, tipo_grafico):
    st.subheader(f"Análisis de Sismos por Profundidad - Gráfico de {tipo_grafico}")
    bins = [0, 70, 300, 1000]
    labels = ['Superficial (0-70 km)', 'Intermedia (70-300 km)', 'Profunda (>300 km)']
    df_temp = df.copy()
    df_temp['PROFUNDIDAD_CAT'] = pd.cut(df['PROFUNDIDAD'], bins=bins, labels=labels, right=False)
    conteo = df_temp['PROFUNDIDAD_CAT'].value_counts().reindex(labels).fillna(0)
    if tipo_grafico == "Barras":
        fig = px.bar(conteo, x=conteo.index, y=conteo.values, labels={"x": "Categoría de Profundidad", "y": "Cantidad de Sismos"}, title="Distribución de Sismos por Categoría de Profundidad")
    elif tipo_grafico == "Sector Circular":
        fig = px.pie(values=conteo.values, names=conteo.index, title="Distribución Porcentual de Sismos por Profundidad")
    else:
        fig = px.line(conteo, x=conteo.index, y=conteo.values, markers=True, labels={"x": "Categoría de Profundidad", "y": "Cantidad de Sismos"}, title="Frecuencia de Sismos por Profundidad")
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 5. ESTRUCTURA PRINCIPAL DE LA APLICACIÓN
# =============================================================================
def main():
    # Usamos el estado de sesión para evitar recargar los datos dos veces
    if "gdf_analisis" not in st.session_state:
        with st.spinner(f'Procesando datos con el motor C++... (solo la primera vez)'):
            gdf_analisis, departamentos_gdf, tiempo_total = cargar_datos_con_motor_cpp()
            st.session_state["gdf_analisis"] = gdf_analisis
            st.session_state["departamentos_gdf"] = departamentos_gdf
            st.session_state["tiempo_total"] = tiempo_total
    else:
        gdf_analisis = st.session_state["gdf_analisis"]
        departamentos_gdf = st.session_state["departamentos_gdf"]
        tiempo_total = st.session_state["tiempo_total"]

    # Mostrar tiempo de carga solo cuando ya está listo
    st.sidebar.success(f"Carga completada en {tiempo_total:.2f} segundos.")

    # Menú de navegación
    with st.sidebar:
        st.image("img/logo_upch.png", width=150)
        selected = option_menu(
            menu_title="Menú Principal",
            options=["Inicio", "Mapa Interactivo", "Análisis Gráfico", "Conclusión", "Sobre Nosotros"],
            icons=["house", "map-fill", "bar-chart-line", "book-half", "people-fill"],
            menu_icon="cast", default_index=0
        )

    # Navegación por páginas
    if selected == "Inicio":
        pagina_inicio()
    elif selected == "Mapa Interactivo":
        pagina_mapa(gdf_analisis, departamentos_gdf)
    elif selected == "Análisis Gráfico":
        pagina_graficos(gdf_analisis)
    elif selected == "Conclusión":
        pagina_conclusion()
    elif selected == "Sobre Nosotros":
        pagina_sobre_nosotros()

# Llamada principal
if __name__ == "__main__":
    main()