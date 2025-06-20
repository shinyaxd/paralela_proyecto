# =============================================================================
# --- Etapa 1: El Constructor (Builder) ---
# En esta etapa instalamos todo lo necesario para COMPILAR el módulo C++
# y las dependencias de Python.
# =============================================================================
FROM python:3.11-bullseye AS builder

# 1. Instalar dependencias del sistema operativo para la compilación.
#    - build-essential: Contiene g++, make y otras herramientas esenciales.
#    - cmake: Para procesar tu CMakeLists.txt.
#    - python3-dev: Contiene las cabeceras de C de Python, necesarias para pybind11.
#    - libgeos-dev: La librería de desarrollo de GEOS, requerida por tu código C++.
#    - pkg-config: Herramienta que cmake usa para encontrar librerías como GEOS.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3-dev \
    libgeos-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 2. Establecer el directorio de trabajo y copiar los archivos de requerimientos.
WORKDIR /app
COPY requirements.txt .

# 3. Instalar las dependencias de Python.
#    Usamos --no-cache-dir para mantener la imagen más ligera.
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar TODO el código fuente del proyecto al contenedor.
COPY . .

# 5. Compilar el módulo C++ usando CMake.
#    Esto ejecutará los comandos de tu CMakeLists.txt y creará el archivo
#    del módulo dentro de la carpeta 'build'.
RUN mkdir build && \
    cd build && \
    cmake .. && \
    make

# =============================================================================
# --- Etapa 2: El Ejecutor (Runner) ---
# Esta es la imagen final que se desplegará. Es mucho más ligera y segura
# porque no contiene las herramientas de compilación.
# =============================================================================
FROM python:3.11-slim-bullseye

# 1. Instalar solo las dependencias de sistema para EJECUTAR la aplicación.
#    geopandas y tu módulo C++ necesitan 'libgeos-c1v5' en tiempo de ejecución.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/*

# 2. Establecer el directorio de trabajo.
WORKDIR /app

# 3. Copiar los artefactos necesarios desde la etapa 'builder'.
#    a) Las dependencias de Python ya instaladas.
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
#    b) El código de la aplicación Python y los datos.
COPY --from=builder /app/app.py .
COPY --from=builder /app/Dataset_1960_2023_sismo.csv .
#    c) ¡El módulo C++ compilado! Esta es la pieza clave.
#       El nombre exacto del archivo .so puede variar ligeramente.
COPY --from=builder /app/build/motor_sjoin_cpp.cpython-311-x86_64-linux-gnu.so .

# 4. Exponer el puerto que usará Streamlit.
EXPOSE 8501

# 5. Variables de entorno para compatibilidad con plataformas de despliegue.
#    Render usará la variable $PORT.
ENV HOST=0.0.0.0
ENV PORT=8501

# 6. Comando final para arrancar la aplicación.
#    No necesitas PYTHONPATH porque el módulo .so está en el mismo directorio que app.py.
CMD ["streamlit", "run", "app.py", "--server.port", "$PORT", "--server.address", "$HOST"]