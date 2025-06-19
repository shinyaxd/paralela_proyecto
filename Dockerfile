# Dockerfile Definitivo para Desplegar una App Streamlit con un Módulo C++

# --- PASO 1: Usar una Imagen Base de Python sobre Linux ---
# Empezamos con un sistema operativo Linux (Debian) que ya tiene Python instalado.
FROM python:3.11-slim

# --- PASO 2: Instalar Dependencias del Sistema Operativo (OS) ---
# Esto es lo que no se puede hacer en plataformas simples. Aquí instalamos
# todo lo necesario para compilar C++ y para que GeoPandas funcione.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    cmake \
    libgeos-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# --- PASO 3: Configurar el Entorno de la Aplicación ---
# Establecemos el directorio de trabajo dentro del contenedor.
WORKDIR /app

# --- PASO 4: Instalar las Dependencias de Python ---
# Copiamos solo el archivo de requerimientos primero para aprovechar la caché de Docker.
# Si este archivo no cambia, Docker no volverá a ejecutar este paso en futuras construcciones.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- PASO 5: Copiar TODO el Código de tu Proyecto ---
# Copia el resto de tus archivos (.py, .cpp, .csv, CMakeLists.txt, etc.) al contenedor.
COPY . .

# --- PASO 6: Compilar el Módulo C++ (El Paso Clave) ---
# Usamos CMake, que es el método profesional y leerá tu CMakeLists.txt.
# Creamos una carpeta 'build', entramos, configuramos con cmake y compilamos con make.
RUN mkdir build && \
    cd build && \
    cmake .. && \
    make

# --- PASO 7: Configurar y Ejecutar la Aplicación ---
# Exponer el puerto que Streamlit usará.
EXPOSE 8501

# Variables de entorno que plataformas como Railway usan para asignar el puerto dinámicamente.
ENV HOST=0.0.0.0
ENV PORT=$PORT

# El comando final para arrancar la aplicación.
# Le decimos a Python que también busque en la carpeta 'build' para encontrar
# nuestro módulo C++ compilado (.so).
# Asegúrate de que tu archivo principal se llame 'app.py' o cámbialo aquí.
CMD ["sh", "-c", "PYTHONPATH=$PYTHONPATH:build streamlit run app.py --server.port $PORT --server.address $HOST"]