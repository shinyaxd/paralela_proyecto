# Dockerfile Definitivo para Desplegar una App Streamlit con un Módulo C++

# 1. Usar una imagen base de Python completa para máxima compatibilidad
FROM python:3.11-bullseye

# 2. Instalar todas las dependencias del sistema operativo (OS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    cmake \
    libgeos-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 3. Establecer el directorio de trabajo
WORKDIR /app

# 4. Instalar las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar el resto de tu proyecto al contenedor
COPY . .

# 6. ¡Paso Clave! Compilar el módulo C++ DENTRO del contenedor usando CMake
RUN mkdir build && \
    cd build && \
    cmake .. && \
    make

# 7. Exponer el puerto que usará Streamlit
EXPOSE 8501

# 8. Variables de entorno que plataformas como Railway usan
ENV HOST=0.0.0.0
ENV PORT=$PORT

# 9. Comando final para arrancar tu aplicación
# Le decimos a Python que también busque el módulo compilado en la carpeta 'build'
# Asegúrate de que tu archivo principal se llame 'app.py'
CMD ["sh", "-c", "PYTHONPATH=$PYTHONPATH:build streamlit run app.py --server.port $PORT --server.address $HOST"]
