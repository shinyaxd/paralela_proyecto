// Usa la API de C de GEOS para máxima estabilidad y seguridad
#include "procesador_sjoin.h"
#include <geos_c.h>
#include <vector>
#include <string>
#include <utility>
#include <omp.h>
#include <sstream> // Necesario para unir los resultados en un solo string
#include <cstring> // Necesario para strcpy

// Declaración de los manejadores de errores para GEOS.
// Usamos lambdas vacías más adelante, pero esto es por si se necesita una depuración más avanzada.
void geos_notice_handler(const char* message, void* userdata) { }
void geos_error_handler(const char* message, void* userdata) { }

/**
 * Esta es la función principal que hace el trabajo pesado. La marcamos como 'static'
 * para que solo sea visible dentro de este archivo. No será exportada directamente.
 * La función que exportaremos será la envoltura (wrapper) 'extern "C"'.
 */
std::vector<std::string> realizar_sjoin_paralelo(
    const std::vector<std::pair<double, double>> &coords_sismos,
    const std::vector<std::string> &wkts_departamentos,
    const std::vector<std::string> &nombres_departamentos
) {
    GEOSContextHandle_t geos_context_global = GEOS_init_r();
    GEOSContext_setNoticeMessageHandler_r(geos_context_global, geos_notice_handler, nullptr);
    GEOSContext_setErrorMessageHandler_r(geos_context_global, geos_error_handler, nullptr);
    
    GEOSWKTReader* reader = GEOSWKTReader_create_r(geos_context_global);
    std::vector<GEOSGeometry*> departamentos_geoms;
    std::vector<const GEOSPreparedGeometry*> departamentos_preparados;

    for (const auto& wkt : wkts_departamentos) {
        GEOSGeometry* geom = GEOSWKTReader_read_r(geos_context_global, reader, wkt.c_str());
        if (geom) {
            departamentos_geoms.push_back(geom);
            departamentos_preparados.push_back(GEOSPrepare_r(geos_context_global, geom));
        }
    }
    
    GEOSWKTReader_destroy_r(geos_context_global, reader);
    std::vector<std::string> resultados(coords_sismos.size(), "Fuera de Perú");

    #pragma omp parallel for
    for (size_t i = 0; i < coords_sismos.size(); ++i) {
        GEOSGeometry* punto = GEOSGeom_createPointFromXY_r(geos_context_global, coords_sismos[i].second, coords_sismos[i].first);
        if (!punto) continue;
        for (size_t j = 0; j < departamentos_preparados.size(); ++j) {
            if (departamentos_preparados[j] && GEOSPreparedContains_r(geos_context_global, departamentos_preparados[j], punto)) {
                resultados[i] = nombres_departamentos[j];
                break;
            }
        }
        GEOSGeom_destroy_r(geos_context_global, punto);
    }

    for (auto geom : departamentos_preparados) GEOSPreparedGeom_destroy_r(geos_context_global, geom);
    for (auto geom : departamentos_geoms) GEOSGeom_destroy_r(geos_context_global, geom);
    //GEOS_finish_r(geos_context_global);
    return resultados;
}

// ============================================================================
// PUENTE PARA PYTHON (LA PARTE MÁS IMPORTANTE PARA RESOLVER EL ERROR)
// ============================================================================

// Estructura simple para pasar coordenadas desde Python.
// Debe coincidir con la clase Point de ctypes en Python.
struct Point {
    double lat;
    double lon;
};

/**
 * El bloque 'extern "C"' es la clave para resolver el error 'undefined symbol'.
 * Le dice al compilador de C++ que no modifique los nombres de estas funciones,
 * para que Python pueda encontrarlas exactamente como están escritas.
 */
extern "C" {

    /**
     * @brief Función de envoltura para ser llamada desde Python.
     * Convierte los datos de C a C++, llama a la función principal y empaqueta el resultado.
     * @return Un único string con todos los resultados separados por '|||'.
     * ¡LA MEMORIA DE ESTE STRING DEBE SER LIBERADA DESDE PYTHON!
     */
    const char* procesar_sismos_c(
        const Point* sismos,
        int num_sismos,
        const char** wkts,
        const char** nombres,
        int num_departamentos
    ) {
        // 1. Convertir los datos de C (punteros, arrays) a tipos de C++ (std::vector)
        std::vector<std::pair<double, double>> coords_sismos_vec;
        coords_sismos_vec.reserve(num_sismos); // Buena práctica para evitar realocaciones
        for (int i = 0; i < num_sismos; ++i) {
            coords_sismos_vec.push_back({sismos[i].lat, sismos[i].lon});
        }

        std::vector<std::string> wkts_vec(wkts, wkts + num_departamentos);
        std::vector<std::string> nombres_vec(nombres, nombres + num_departamentos);

        // 2. Llamar a la función de C++ original (la que está marcada como 'static')
        std::vector<std::string> resultados_vec = realizar_sjoin_paralelo(coords_sismos_vec, wkts_vec, nombres_vec);

        // 3. Convertir el resultado (vector de strings) a un único string separado por un delimitador
        std::stringstream ss;
        for (size_t i = 0; i < resultados_vec.size(); ++i) {
            ss << resultados_vec[i] << (i == resultados_vec.size() - 1 ? "" : "|||");
        }
        std::string resultado_final = ss.str();

        // 4. Devolver como un string de C que Python pueda leer. Se crea una copia en memoria
        // que deberá ser liberada explícitamente para evitar fugas de memoria.
        char* resultado_c = new char[resultado_final.length() + 1];
        std::strcpy(resultado_c, resultado_final.c_str());
        return resultado_c;
    }

    /**
     * @brief Función para liberar la memoria del string creado en procesar_sismos_c.
     * Es crucial llamarla desde Python para evitar fugas de memoria.
     */
    void liberar_memoria_c(const char* ptr) {
        // Usamos delete[] porque la memoria fue creada con 'new char[]'
        delete[] ptr;
    }

} // Fin del bloque extern "C"