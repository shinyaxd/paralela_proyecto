// bindings.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

// ¡ESTA LÍNEA ES LA SOLUCIÓN AL ERROR!
// Le dice a este archivo que la función "realizar_sjoin_paralelo" existe
// y le muestra su firma completa (argumentos y tipo de retorno).
#include "procesador_sjoin.h"

namespace py = pybind11;

PYBIND11_MODULE(motor_sjoin_cpp, m) {
    m.doc() = "Módulo C++ para realizar spatial joins en paralelo";

    // Ahora, cuando el compilador ve "&realizar_sjoin_paralelo",
    // ya sabe a qué te refieres gracias al .h que incluiste arriba.
    m.def(
        "realizar_sjoin_paralelo_cpp",
        &realizar_sjoin_paralelo,
        "Asigna un departamento a cada sismo usando C++ y OpenMP",
        py::arg("coords_sismos"),
        py::arg("wkts_departamentos"),
        py::arg("nombres_departamentos")
    );
}