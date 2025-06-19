#include "procesador_sjoin.h"
#include <geos_c.h>
#include <vector>
#include <string>
#include <utility>
#include <omp.h>

void geos_notice_handler(const char* fmt, ...) { }
void geos_error_handler(const char* fmt, ...) { }

std::vector<std::string> realizar_sjoin_paralelo(
    const std::vector<std::pair<double, double>> &coords_sismos,
    const std::vector<std::string> &wkts_departamentos,
    const std::vector<std::string> &nombres_departamentos
) {
    initGEOS(geos_notice_handler, geos_error_handler);

    std::vector<GEOSGeometry*> departamentos;
    GEOSWKTReader* reader = GEOSWKTReader_create();

    for (const auto& wkt : wkts_departamentos) {
        GEOSGeometry* geom = GEOSWKTReader_read(reader, wkt.c_str());
        departamentos.push_back(geom);
    }

    std::vector<std::string> resultados(coords_sismos.size(), "Fuera de Perú");

    #pragma omp parallel for
    for (size_t i = 0; i < coords_sismos.size(); ++i) {
        GEOSGeometry* punto = GEOSGeom_createPointFromXY(coords_sismos[i].second, coords_sismos[i].first);

        if (!punto) continue;

        for (size_t j = 0; j < departamentos.size(); ++j) {
            if (departamentos[j] && GEOSContains(departamentos[j], punto)) {
                resultados[i] = nombres_departamentos[j];
                break;
            }
        }
        GEOSGeom_destroy(punto);
    }

    for (auto geom : departamentos) {
        GEOSGeom_destroy(geom);
    }

    GEOSWKTReader_destroy(reader);
    finishGEOS();

    return resultados;
}
