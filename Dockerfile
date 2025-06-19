# Dockerfile Definitivo para Desplegar en Railway

# 1. Usar una imagen base oficial de Python sobre Linux (Debian)
FROM python:3.11-slim

# 2. Instalar las dependencias del sistema operativo (OS)
#    - build-essential y g++: para compilar C++
#    - cmake: para usar tu CMakeLists.txt
#    - libgeos-dev: la librería GEOS que necesita tu código C++
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    cmake \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Establecer directorio de trabajo y copiar el archivo de requerimientos de Python
WORKDIR /app
COPY requirements.txt .

# 4. Instalar las dependencias de Python
#    El --no-cache-dir es una buena práctica en Docker para mantener la imagen ligera
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto de tu proyecto (código .py, .cpp, .csv, CMakeLists.txt, etc.)
COPY . .

# 6. ¡Paso Clave Corregido! Compilar el módulo C++ DENTRO del contenedor usando CMake
RUN mkdir build && \
    cd build && \
    cmake .. && \
    make

# 7. Variables de entorno que Railway necesita para servir la app
ENV HOST=0.0.0.0
ENV PORT=$PORT

# 8. Comando para arrancar la aplicación de Streamlit
#    Railway asignará un valor a la variable $PORT automáticamente.
#    Le decimos que busque el módulo C++ en la carpeta 'build' donde se compiló.
CMD env PYTHONPATH=/app/build streamlit run app.py --server.port $PORT --server.address $HOST