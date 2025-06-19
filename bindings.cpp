// nombre del archivo: bindings.cpp (VERSIÓN CON NUMPY)
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h> // Para manejar NumPy directamente

#include "procesador_sjoin.h" // 🔥 Correcto: solo incluir el header, no el .cpp

namespace py = pybind11;

// Función envoltorio compatible con NumPy
std::vector<std::string> realizar_sjoin_paralelo_from_numpy(
    py::array_t<double> coords_sismos_np, // Recibe array de NumPy
    const std::vector<std::string>& wkts_departamentos,
    const std::vector<std::string>& nombres_departamentos) {

    // Acceso directo a la memoria del array de NumPy
    auto buf = coords_sismos_np.request();
    double *ptr = static_cast<double *>(buf.ptr);

    std::vector<std::pair<double, double>> coords_sismos;
    coords_sismos.reserve(buf.shape[0]);

    for (ssize_t i = 0; i < buf.shape[0]; i++) {
        coords_sismos.emplace_back(ptr[i * 2], ptr[i * 2 + 1]);
    }

    return realizar_sjoin_paralelo(coords_sismos, wkts_departamentos, nombres_departamentos);
}

PYBIND11_MODULE(motor_sjoin_cpp, m) {
    m.doc() = "Módulo C++ para realizar spatial joins en paralelo con GEOS y OpenMP";

    // Exponemos la función compatible con NumPy
    m.def("realizar_sjoin_paralelo_cpp", &realizar_sjoin_paralelo_from_numpy,
        "Asigna un departamento a cada sismo usando C++ y NumPy",
        py::arg("coords_sismos_np"),
        py::arg("wkts_departamentos"),
        py::arg("nombres_departamentos"));
}
