# =============================================================================
# --- Etapa 1: El Constructor (Builder) ---
# En esta etapa instalamos todo lo necesario para COMPILAR el módulo C++
# y las dependencias de Python.
# =============================================================================
FROM python:3.11-bullseye AS builder

# 1. Instalar dependencias del sistema operativo para la compilación.
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

# 3. Instalar las dependencias de Python (incluyendo pybind11).
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar TODO el código fuente del proyecto al contenedor.
COPY . .

# 5. Compilar el módulo C++. ¡ESTA ES LA LÍNEA CORREGIDA!
RUN mkdir build && \
    cd build && \
    cmake -Dpybind11_DIR=$(python3 -m pybind11 --cmakedir) .. && \
    make

# =============================================================================
# --- Etapa 2: El Ejecutor (Runner) ---
# Esta es la imagen final que se desplegará. Es más ligera y segura.
# =============================================================================
FROM python:3.11-slim-bullseye

# 1. Instalar solo las dependencias de sistema para EJECUTAR la aplicación.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/*

# 2. Establecer el directorio de trabajo.
WORKDIR /app

# 3. Copiar los artefactos necesarios desde la etapa 'builder'.
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /app/app.py .
COPY --from=builder /app/Dataset_1960_2023_sismo.csv .
COPY --from=builder /app/img/ /app/img/
COPY --from=builder /app/build/motor_sjoin_cpp.cpython-311-x86_64-linux-gnu.so .

# 4. Exponer el puerto que usará Streamlit.
EXPOSE 8501

# 5. Variables de entorno para Render.
ENV HOST=0.0.0.0
ENV PORT=8501

# 6. Comando final para arrancar la aplicación.
CMD ["streamlit", "run", "app.py", "--server.port", "$PORT", "--server.address", "$HOST"]