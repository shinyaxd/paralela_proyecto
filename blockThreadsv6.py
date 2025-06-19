
# =============================================================================
# 1. IMPORTS
# =============================================================================
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from streamlit_option_menu import option_menu
from PIL import Image
from streamlit_folium import st_folium
import plotly.express as px
import matplotlib.pyplot as plt
import os
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor

# =============================================================================
# 2. CONFIGURACIÓN DE LA PÁGINA
# =============================================================================
st.set_page_config(page_title="Catálogo Sísmico del Perú", page_icon="🌍", layout="wide")

# =============================================================================
# 3. LÓGICA DE PROCESAMIENTO PARALELO EN PYTHON
# =============================================================================
def procesar_chunk(chunk_df):
    """
    Tarea que se paraleliza: convertir un trozo del DataFrame en un GeoDataFrame.
    """
    if chunk_df.empty:
        return None
    return gpd.GeoDataFrame(
        chunk_df, 
        geometry=gpd.points_from_xy(chunk_df["LONGITUD"], chunk_df["LATITUD"]),
        crs="EPSG:4326"
    )

@st.cache_data(show_spinner=False)
def cargar_y_procesar_en_paralelo():
    """
    Función principal que lee desde el CSV y usa paralelismo en Python.
    Se ejecuta una sola vez gracias a la caché.
    """
    try:
        df = pd.read_csv("Dataset_1960_2023_sismo.csv")
        departamentos_gdf = gpd.read_file("departamentos_perú.geojson")
    except FileNotFoundError as e:
        st.error(f"Error fatal: {e}. Asegúrate de tener los archivos CSV y GeoJSON.")
        st.stop()
    
    df['FECHA_UTC'] = pd.to_datetime(df['FECHA_UTC'], format='%Y%m%d', errors='coerce')
    df.dropna(subset=['FECHA_UTC', 'LATITUD', 'LONGITUD'], inplace=True)

    num_workers = os.cpu_count() or 4
    chunks = [c for c in np.array_split(df, num_workers) if not c.empty]

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        resultados_parciales = list(executor.map(procesar_chunk, chunks))
    
    gdf_sismos = pd.concat(resultados_parciales, ignore_index=True)
    gdf_analisis = gpd.sjoin(gdf_sismos, departamentos_gdf, how="inner", predicate="intersects")
    
    if 'index_right' in gdf_analisis.columns:
        gdf_analisis = gdf_analisis.drop(columns=['index_right'])
    
    gdf_analisis = gdf_analisis.rename(columns={"NOMBDEP": "DEPARTAMENTO"})
    gdf_analisis['AÑO'] = gdf_analisis['FECHA_UTC'].dt.year
    month_names_map = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    gdf_analisis['MES_NOMBRE'] = gdf_analisis['FECHA_UTC'].dt.month.map(month_names_map)
    
    return gdf_analisis, departamentos_gdf

def cargar_datos_si_no_existen():
    if "gdf_analisis" not in st.session_state or "departamentos_gdf" not in st.session_state:
        with st.spinner(f'Procesando datos en paralelo con Python... (solo la primera vez)'):
            gdf_analisis, departamentos_gdf = cargar_y_procesar_en_paralelo()
            st.session_state["gdf_analisis"] = gdf_analisis
            st.session_state["departamentos_gdf"] = departamentos_gdf

# =============================================================================
# 4. DEFINICIÓN DE PÁGINAS
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
    st.title("🗺️ Mapa Interactivo de Sismos")
    
    with st.sidebar:
        st.header("Filtros del Mapa")
        deptos = ["Todos"] + sorted(gdf["DEPARTAMENTO"].unique().tolist())
        filtro_deptos = st.multiselect("Departamento", deptos, default=["Todos"])
        años = sorted(gdf["AÑO"].dropna().unique())
        r_anos = st.slider("Rango de Años", min_value=min(años), max_value=max(años), value=(min(años), max(años)))
        r_mag = st.slider("Magnitud", float(gdf["MAGNITUD"].min()), float(gdf["MAGNITUD"].max()), (float(gdf["MAGNITUD"].min()), float(gdf["MAGNITUD"].max())))
        r_prof = st.slider("Profundidad", float(gdf["PROFUNDIDAD"].min()), float(gdf["PROFUNDIDAD"].max()), (float(gdf["PROFUNDIDAD"].min()), float(gdf["PROFUNDIDAD"].max())))

    mask = (gdf["AÑO"].between(*r_anos)) & \
           (gdf["MAGNITUD"].between(*r_mag)) & \
           (gdf["PROFUNDIDAD"].between(*r_prof))
    if "Todos" not in filtro_deptos:
        mask &= gdf["DEPARTAMENTO"].isin(filtro_deptos)

    filtered = gdf[mask]
    st.info(f"🔍 Mostrando {len(filtered)} de {len(gdf)} sismos")

    mapa = folium.Map(location=[-9.2, -75], zoom_start=5, tiles="CartoDB positron")
    folium.GeoJson(departamentos_gdf).add_to(mapa)
    cluster = MarkerCluster().add_to(mapa)

    for _, row in filtered.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=4,
            color="red",
            fill=True,
            fill_opacity=0.6,
            popup=f"{row['DEPARTAMENTO']}<br>{row['FECHA_UTC']}<br>Mag: {row['MAGNITUD']}"
        ).add_to(cluster)

    st_folium(mapa, width='100%', height=600)

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
    if "datos_cargados" not in st.session_state:
        inicio_carga = time.time()
        cargar_datos_si_no_existen()
        fin_carga = time.time()
        st.sidebar.success(f"Carga inicial completada en {fin_carga - inicio_carga:.2f} segundos.")
        st.session_state["datos_cargados"] = True  # ← marca como procesado
    else:
        cargar_datos_si_no_existen()
        st.sidebar.info("✅ Datos ya cargados (memoria caché)")

    gdf_analisis = st.session_state["gdf_analisis"]
    departamentos_gdf = st.session_state["departamentos_gdf"]
    with st.sidebar:
        st.image("img/logo_upch.png", width=150)
        selected = option_menu(
            menu_title="Menú Principal",
            options=["Inicio", "Mapa Interactivo", "Análisis Gráfico", "Conclusión", "Sobre Nosotros"],
            icons=["house", "map-fill", "bar-chart-line", "book-half", "people-fill"],
            menu_icon="cast", default_index=0
        )

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

if __name__ == "__main__":
    main()