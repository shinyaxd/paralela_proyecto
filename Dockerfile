FROM python:3.10-slim

# Instala dependencias necesarias
RUN apt-get update && apt-get install -y \
    g++ \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# Compila el módulo C++
RUN g++ -O3 -fPIC -shared -std=c++17 motor_sjoin_cpp.cpp -o motor_sjoin_cpp$(python3-config --extension-suffix)

# Instala dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["streamlit", "run", "blockThreadsv7.py", "--server.port=8000", "--server.enableCORS=false"]
