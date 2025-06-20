#ifndef PROCESADOR_SJOIN_H
#define PROCESADOR_SJOIN_H

#include <vector>
#include <string>
#include <utility>

std::vector<std::string> realizar_sjoin_paralelo(
    const std::vector<std::pair<double, double>> &coords_sismos,
    const std::vector<std::string> &wkts_departamentos,
    const std::vector<std::string> &nombres_departamentos
);

#endif