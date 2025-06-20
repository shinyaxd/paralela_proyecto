# =============================================================================
# --- Etapa 1: El Constructor (Builder) ---
# CAMBIO: Usamos una imagen base de Python 3.12. Bookworm es la versión de
# Debian que viene con Python 3.11/3.12, por lo que es una mejor base.
# =============================================================================
FROM python:3.12-bookworm AS builder

# 1. Instalar dependencias del sistema operativo para la compilación.
#    (Esta parte no cambia)
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
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar TODO el código fuente del proyecto al contenedor.
COPY . .

# 5. Compilar el módulo C++. La lógica es la misma.
RUN mkdir build && \
    cd build && \
    cmake -Dpybind11_DIR=$(python3 -m pybind11 --cmakedir) .. && \
    make

# =============================================================================
# --- Etapa 2: El Ejecutor (Runner) ---
# CAMBIO: Usamos la imagen 'slim' de Python 3.12 para la etapa final.
# =============================================================================
FROM python:3.12-slim-bookworm

# 1. Instalar solo las dependencias de sistema para EJECUTAR la aplicación.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/*

# 2. Establecer el directorio de trabajo.
WORKDIR /app

# 3. Copiar los artefactos necesarios desde la etapa 'builder'.
#    a) CAMBIO: La ruta a site-packages ahora usa python3.12.
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
#    b) El código de la aplicación Python y los datos.
COPY --from=builder /app/app.py .
COPY --from=builder /app/Dataset_1960_2023_sismo.csv .
COPY --from=builder /app/img/ /app/img/
#    c) CAMBIO: El nombre del módulo compilado ahora usa la etiqueta de Python 3.12.
COPY --from=builder /app/build/motor_sjoin_cpp.cpython-312-x86_64-linux-gnu.so .

# 4. Exponer el puerto que usará Streamlit.
EXPOSE 8501

# 5. Variables de entorno para Render.
ENV HOST=0.0.0.0
ENV PORT=8501

# 6. Comando final para arrancar la aplicación.
CMD ["streamlit", "run", "app.py", "--server.port", "$PORT", "--server.address", "$HOST"]