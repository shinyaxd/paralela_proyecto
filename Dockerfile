# Imagen base más completa con soporte para compilación C++
FROM python:3.10

# Instalar compiladores y librerías necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    python3-dev \
    libgeos-dev \
    libgeos++-dev \
    libproj-dev \
    libgdal-dev \
    curl \
    git \
    && apt-get clean

# Evitar warnings de PROJ
ENV PROJ_LIB=/usr/share/proj

# Crear directorio de trabajo
WORKDIR /app

# Copiar todos los archivos del proyecto
COPY . /app

# Instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Compilar módulo C++ con pybind11
RUN g++ -O3 -Wall -shared -std=c++11 -fPIC \
    bindings.cpp procesador_sjoin.cpp \
    -I/usr/include/geos \
    -I/usr/local/include/python3.10 \
    -I/usr/local/lib/python3.10/site-packages/pybind11/include \
    -o motor_sjoin_cpp$(python3-config --extension-suffix) \
    -lgeos++

# Exponer el puerto de Streamlit
EXPOSE 10000

# Comando para ejecutar la app
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
