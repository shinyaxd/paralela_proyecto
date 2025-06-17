# convertir_a_parquet.py
import pandas as pd

print("Leyendo el archivo CSV...")
df = pd.read_csv("Dataset_1960_2023_sismo.csv")

# Aquí podrías hacer cualquier limpieza única que necesites
# Por ejemplo, convertir las fechas al formato correcto
df['FECHA_UTC'] = pd.to_datetime(df['FECHA_UTC'], format='%Y%m%d', errors='coerce')

print("Guardando en formato Parquet...")
# 'engine='pyarrow'' es importante para el mejor rendimiento
df.to_parquet("Dataset_sismos.parquet", engine='pyarrow')

print("¡Conversión completada! Ahora puedes usar 'Dataset_sismos.parquet' en tu aplicación.")