// nombre del archivo: procesador_sjoin.cpp (Versión Definitiva y Segura)
#include <vector>
#include <string>
#include <memory>   // <-- IMPORTANTE: Para los punteros inteligentes (std::unique_ptr)
#include <omp.h>    // Para el paralelismo

// Cabeceras de la librería GEOS
#include <geos/geom/GeometryFactory.h>
#include <geos/geom/Point.h>
#include <geos/geom/Polygon.h>
#include <geos/geom/prep/PreparedGeometryFactory.h>
#include <geos/io/WKTReader.h>

// Usamos alias para que el código sea más legible y manejable
using GeometryPtr = std::unique_ptr<geos::geom::Geometry>;
using PreparedGeometryPtr = std::unique_ptr<const geos::geom::prep::PreparedGeometry>;

std::vector<std::string> realizar_sjoin_paralelo(
    const std::vector<std::pair<double, double>>& coords_sismos,
    const std::vector<std::string>& wkts_departamentos,
    const std::vector<std::string>& nombres_departamentos) {

    // Se crea una fábrica y un lector globales para la preparación inicial
    auto gf_global = geos::geom::GeometryFactory::create();
    geos::io::WKTReader reader(*gf_global);
    
    // Guardamos las geometrías originales en un vector de punteros inteligentes
    // para asegurarnos de que "viven" durante toda la función.
    std::vector<GeometryPtr> geoms_originales;
    std::vector<PreparedGeometryPtr> poligonos_preparados;

    for (const auto& wkt : wkts_departamentos) {
        // Creamos la geometría base y la guardamos
        geoms_originales.push_back(std::unique_ptr<geos::geom::Geometry>(reader.read(wkt)));
        
        // Verificamos que la geometría sea válida antes de prepararla
        if (geoms_originales.back()) {
            poligonos_preparados.emplace_back(geos::geom::prep::PreparedGeometryFactory::prepare(geoms_originales.back().get()));
        } else {
            poligonos_preparados.emplace_back(nullptr);
        }
    }

    std::vector<std::string> resultados(coords_sismos.size(), "Fuera de Perú");

    // Bloque paralelo
    #pragma omp parallel
    {
        // Cada hilo crea su propia "fábrica" local para evitar conflictos
        auto gf_thread_local = geos::geom::GeometryFactory::create();

        #pragma omp for
        for (size_t i = 0; i < coords_sismos.size(); ++i) {
            geos::geom::Coordinate coord(coords_sismos[i].second, coords_sismos[i].first); // (lon, lat)
            
            // Creamos el punto en un puntero inteligente. Su memoria se liberará sola.
            std::unique_ptr<geos::geom::Point> punto_sismo(gf_thread_local->createPoint(coord));

            if (!punto_sismo) {
                continue;
            }

            for (size_t j = 0; j < poligonos_preparados.size(); ++j) {
                // Verificamos que el puntero no sea nulo y hacemos la comprobación
                if (poligonos_preparados[j] && poligonos_preparados[j]->contains(punto_sismo.get())) {
                    resultados[i] = nombres_departamentos[j];
                    break; 
                }
            }
            // NO hay 'delete punto_sismo'. El unique_ptr lo hace automáticamente.
        }
    } // Fin del bloque paralelo

    // NO hay bucles de 'delete'. La memoria se gestiona sola gracias a los unique_ptr.

    return resultados;
}