# Dockerfile Definitivo y Corregido para Desplegar en Railway

# 1. Usar una imagen base oficial de Python sobre Linux
FROM python:3.11-slim

# 2. Instalar todas las dependencias del sistema operativo (OS)
#    - build-essential y g++: para compilar C++
#    - cmake: para usar tu CMakeLists.txt (el método profesional)
#    - libgeos-dev: la librería GEOS que necesita tu código C++
#    - pkg-config: la herramienta que CMake necesita para encontrar GEOS
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    cmake \
    libgeos-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 3. Establecer directorio de trabajo
WORKDIR /app

# 4. Copiar e instalar las dependencias de Python
#    Asegúrate de que tu archivo se llame 'requirements.txt' y no 'requeriments.txt'
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto de tu proyecto al contenedor
COPY . .

# 6. ¡Paso Clave! Compilar el módulo C++ en pasos separados para mejor depuración
RUN mkdir build
WORKDIR /app/build

# 6a. Ejecutar CMake. Si esto falla, el error nos dirá por qué.
RUN cmake ..

# 6b. Ejecutar Make. Si esto falla, veremos el error de compilación de C++.
RUN make

# 7. Regresar al directorio principal de la aplicación
WORKDIR /app

# 8. Variables de entorno que Railway necesita para servir la app
ENV HOST=0.0.0.0
ENV PORT=$PORT

# 9. Comando final para arrancar la aplicación de Streamlit
#    Le decimos a Python que también busque el módulo compilado en la carpeta 'build'
CMD ["sh", "-c", "PYTHONPATH=$PYTHONPATH:build streamlit run app.py --server.port $PORT --server.address $HOST"]