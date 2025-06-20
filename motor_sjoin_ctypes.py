import ctypes
import os

# --- 1. Cargar la biblioteca C++ compilada (.so) ---
try:
    # Construir la ruta absoluta a la biblioteca
    lib_path = os.path.join(os.path.dirname(__file__), 'procesador_sjoin.so')
    sjoin_lib = ctypes.CDLL(lib_path)
except OSError as e:
    # Este error es crítico, así que lo lanzamos para que la app principal lo capture.
    raise ImportError(f"No se pudo cargar la biblioteca C++ 'procesador_sjoin.so'. Error: {e}")

# --- 2. Definir las estructuras y firmas de las funciones C++ ---

# Estructura de datos para un punto, debe coincidir con la de C++
class Point(ctypes.Structure):
    _fields_ = [("lat", ctypes.c_double),
                ("lon", ctypes.c_double)]

# Firma de la función principal que realiza el cálculo
sjoin_lib.procesar_sismos_c.argtypes = [
    ctypes.POINTER(Point),
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.POINTER(ctypes.c_char_p),
    ctypes.c_int
]
sjoin_lib.procesar_sismos_c.restype = ctypes.c_char_p

# Firma de la función que libera la memoria en C++
sjoin_lib.liberar_memoria_c.argtypes = [ctypes.c_char_p]
sjoin_lib.liberar_memoria_c.restype = None

# --- 3. Función principal de Python que envuelve la lógica de ctypes ---

def realizar_sjoin_paralelo_cpp(coords_sismos, wkts_departamentos, nombres_departamentos):
    """
    Función de alto nivel que se comunica con la biblioteca C++.
    Recibe listas de Python y devuelve una lista de Python.
    """
    # --- a. Convertir datos de Python a tipos de ctypes ---
    num_sismos = len(coords_sismos)
    sismos_array = (Point * num_sismos)(*[Point(lat, lon) for lat, lon in coords_sismos])

    num_departamentos = len(wkts_departamentos)
    # Codificar los strings de Python a bytes (utf-8)
    wkts_array = (ctypes.c_char_p * num_departamentos)(*[s.encode('utf-8') for s in wkts_departamentos])
    nombres_array = (ctypes.c_char_p * num_departamentos)(*[s.encode('utf-8') for s in nombres_departamentos])

    # --- b. Llamar a la función de la biblioteca C++ ---
    resultado_c_ptr = sjoin_lib.procesar_sismos_c(
        sismos_array,
        num_sismos,
        wkts_array,
        nombres_array,
        num_departamentos
    )

    # --- c. Procesar el resultado y liberar la memoria ---
    # Decodificar el puntero a char de C a un string de Python
    resultado_string = resultado_c_ptr.decode('utf-8')

    # ¡MUY IMPORTANTE! Liberar la memoria que C++ asignó
    sjoin_lib.liberar_memoria_c(resultado_c_ptr)

    # Dividir el string para obtener la lista final de resultados
    resultados_finales = resultado_string.split('|||')

    return resultados_finales