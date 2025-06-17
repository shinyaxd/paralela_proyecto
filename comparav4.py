import streamlit as st
import pandas as pd
import geopandas as gpd
import time
import plotly.graph_objects as go
import numpy as np

try:
    import motor_sjoin_cpp
except ImportError:
    st.error("❌ No se puede importar motor_sjoin_cpp. Compílalo antes de continuar.")
    st.stop()

st.set_page_config(page_title="Comparador de rendimiento", layout="centered")
st.title("🎯 Comparador de velocidad: GeoPandas vs Motor C++")

# ---------------------------
# Cargar y multiplicar dataset en memoria
# ---------------------------
def cargar_dataset_ampliado(factor=5):
    df = pd.read_csv("Dataset_1960_2023_sismo.csv")
    df_ampliado = pd.concat([df] * factor, ignore_index=True)
    return df_ampliado

# ---------------------------
# GeoPandas puro
# ---------------------------
def usar_geopandas(factor=5):
    df = cargar_dataset_ampliado(factor)
    df.dropna(subset=["LATITUD", "LONGITUD"], inplace=True)
    departamentos = gpd.read_file("departamentos_perú.geojson").to_crs("EPSG:4326")
    sismos = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["LONGITUD"], df["LATITUD"]), crs="EPSG:4326")
    return gpd.sjoin(sismos, departamentos, how="inner", predicate="intersects")

# ---------------------------
# Motor C++ paralelo
# ---------------------------
def usar_cpp(factor=5):
    df = cargar_dataset_ampliado(factor)
    df.dropna(subset=["LATITUD", "LONGITUD"], inplace=True)
    departamentos = gpd.read_file("departamentos_perú.geojson")

    # En lugar de crear una lista de tuplas, creamos un array de NumPy.
    # Es mucho más eficiente en memoria y se pasa sin copiar.
    coords_np = df[["LATITUD", "LONGITUD"]].to_numpy(dtype=np.float64)

    wkts = departamentos["geometry"].to_wkt().tolist()
    nombres = departamentos["NOMBDEP"].tolist()
    
    # Llamamos a la función C++ pasándole el array de NumPy
    resultado = motor_sjoin_cpp.realizar_sjoin_paralelo_cpp(coords_np, wkts, nombres)
    
    df["DEPARTAMENTO"] = resultado
    df = df[df["DEPARTAMENTO"] != "Fuera de Perú"]
    return df

# ---------------------------
# Comparación principal
# ---------------------------
st.sidebar.header("⚙️ Configuración")
factor = st.sidebar.slider("Multiplicador de tamaño de datos", 1, 10, 5)

if st.button("▶️ Ejecutar comparación"):
    tiempos = {}

    with st.spinner("GeoPandas..."):
        t0 = time.time()
        usar_geopandas(factor)
        tiempos["GeoPandas"] = round(time.time() - t0, 3)

    with st.spinner("Motor C++..."):
        t0 = time.time()
        usar_cpp(factor)
        tiempos["Motor C++"] = round(time.time() - t0, 3)

    st.subheader("⏱️ Tiempos de ejecución")
    for k, v in tiempos.items():
        st.markdown(f"- **{k}**: `{v} segundos`")

    fig = go.Figure(data=[
        go.Bar(x=list(tiempos.keys()), y=list(tiempos.values()),
               text=list(tiempos.values()), textposition="outside",
               marker_color=["#636EFA", "#EF553B"])
    ])
    fig.update_layout(title="Comparación de rendimiento", yaxis_title="Tiempo (s)", height=400)
    st.plotly_chart(fig)

    geo, cpp = tiempos["GeoPandas"], tiempos["Motor C++"]
    mejora_pct = round((1 - cpp / geo) * 100, 2)
    st.subheader("🎯 Evaluación del objetivo")
    st.markdown(f"- Mejora lograda: **{mejora_pct}%**")
    if mejora_pct >= 75:
        st.success("✅ ¡Objetivo cumplido! El motor C++ fue al menos 75% más rápido.")
    else:
        st.error("❌ El objetivo NO se cumplió. La mejora fue menor al 75%.")
else:
    st.info("Haz clic en el botón para comparar. Puedes ajustar el tamaño del dataset desde la barra lateral.")
