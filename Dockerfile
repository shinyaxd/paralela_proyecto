# Imagen base con soporte para geospatial y compiladores
FROM python:3.10-slim

# Instalar dependencias del sistema necesarias para geopandas, folium, pybind11 y compilación C++
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    python3-dev \
    libgeos-dev \
    libproj-dev \
    libgdal-dev \
    curl \
    git \
    && apt-get clean

# Establecer variable para evitar el warning de GDAL
ENV PROJ_LIB=/usr/share/proj

# Crear directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto al contenedor
COPY . /app

# Instalar las dependencias de Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Compilar el módulo C++
RUN g++ -O3 -Wall -shared -std=c++11 -fPIC \
    bindings.cpp procesador_sjoin.cpp \
    -I/usr/local/include/python3.10 \
    -I/usr/local/lib/python3.10/site-packages/pybind11/include \
    -o motor_sjoin_cpp$(python3-config --extension-suffix)

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
