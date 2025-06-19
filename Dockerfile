# Dockerfile Definitivo y Corregido para Desplegar

# 1. Usar una imagen base oficial de Python sobre Linux
FROM python:3.11-slim

# 2. Instalar todas las dependencias del sistema operativo (OS)
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
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto de tu proyecto al contenedor
COPY . .

# 6. ¡Paso Clave! Compilar el módulo C++ DENTRO del contenedor usando CMake
RUN mkdir build && \
    cd build && \
    cmake .. && \
    make

# 7. Variables de entorno que Railway (o similar) necesita para servir la app
ENV HOST=0.0.0.0
ENV PORT=$PORT

# 8. Comando final para arrancar la aplicación de Streamlit
#    Le decimos a Python que también busque el módulo compilado en la carpeta 'build'
CMD ["sh", "-c", "PYTHONPATH=$PYTHONPATH:build streamlit run app.py --server.port $PORT --server.address $HOST"]