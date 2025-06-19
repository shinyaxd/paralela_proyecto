# Imagen base completa para soportar compilación C++ y librerías geoespaciales
FROM python:3.10

# Evitar warning de pip root
ENV PIP_ROOT_USER_ACTION=ignore

# Instalar compiladores y librerías necesarias para C++ y GEOS C API
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

# Crear directorio de trabajo
WORKDIR /app

# Copiar todos los archivos del proyecto al contenedor
COPY . /app

# Instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Compilar el módulo C++ con pybind11 y la API geos_c
RUN g++ -O3 -Wall -shared -std=c++11 -fPIC \
    bindings.cpp procesador_sjoin.cpp \
    -I/usr/include \
    -I/usr/local/include/python3.10 \
    -I/usr/local/lib/python3.10/site-packages/pybind11/include \
    -o motor_sjoin_cpp$(python3-config --extension-suffix) \
    -lgeos_c -fopenmp

# Exponer el puerto de Streamlit (Render usará este puerto)
EXPOSE 10000

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
