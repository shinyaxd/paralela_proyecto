# =============================================================================
# --- Etapa 1: El Constructor (Builder) ---
# =============================================================================
FROM python:3.12-bookworm AS builder

# 1. Instalar dependencias del sistema operativo para la compilación.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    python3-dev \
    libgeos-dev \
    pkg-config

# 2. Establecer el directorio de trabajo y copiar los archivos de requerimientos.
WORKDIR /app
COPY requirements.txt .

# 3. Instalar las dependencias de Python.
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar TODO el código fuente del proyecto al contenedor.
COPY . .

# 5. ¡¡PASO DE DEPURACIÓN!!
#    Esta línea listará todos los archivos que se copiaron en el paso anterior.
#    Así podremos ver si el archivo .csv está realmente ahí.
RUN ls -laR

# 6. Compilar el módulo C++.
RUN mkdir build && \
    cd build && \
    cmake -Dpybind11_DIR=$(python3 -m pybind11 --cmakedir) .. && \
    make

# =============================================================================
# --- Etapa 2: El Ejecutor (Runner) ---
# (La segunda etapa no necesita cambios, pero se incluye para que el archivo esté completo)
# =============================================================================
FROM python:3.12-slim-bookworm

# Instalar solo las dependencias de sistema para EJECUTAR la aplicación.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgeos-c1v5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar los artefactos necesarios desde la etapa 'builder'.
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /app/app.py .
COPY --from=builder /app/Dataset_1960_2023_sismo.csv .
COPY --from=builder /app/img/ /app/img/
COPY --from=builder /app/build/motor_sjoin_cpp.cpython-312-x86_64-linux-gnu.so .

EXPOSE 8501
ENV HOST=0.0.0.0
ENV PORT=8501
CMD ["streamlit", "run", "app.py", "--server.port", "$PORT", "--server.address", "$HOST"]