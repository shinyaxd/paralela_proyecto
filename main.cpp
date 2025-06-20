// main.cpp
#include <iostream>
#include <vector>
#include <string>
#include <utility>
#include "procesador_sjoin.h" // Incluimos la declaración de nuestra función

// Declaramos la función que está definida en procesador_sjoin.cpp
// (Esto debería estar en procesador_sjoin.h, pero lo ponemos aquí por simplicidad si no lo tienes)
std::vector<std::string> realizar_sjoin_paralelo(
    const std::vector<std::pair<double, double>> &coords_sismos,
    const std::vector<std::string> &wkts_departamentos,
    const std::vector<std::string> &nombres_departamentos
);

int main() {
    // --- 1. Preparamos datos de prueba ---
    // Sismos de prueba (latitud, longitud)
    std::vector<std::pair<double, double>> coords_sismos = {
        {-12.0464, -77.0428}, // Lima (debería estar en Lima)
        {-16.4090, -71.5375}, // Arequipa (debería estar en Arequipa)
        {4.7110, -74.0721}    // Bogotá (debería estar Fuera de Perú)
    };

    // Geometrías de departamentos en formato WKT (Well-Known Text)
    // NOTA: Estos son polígonos cuadrados simplificados solo para la prueba.
    // Deberías cargar los WKT reales desde un archivo.
    std::vector<std::string> wkts_departamentos = {
        "POLYGON((-77.5 -11.5, -76.5 -11.5, -76.5 -12.5, -77.5 -12.5, -77.5 -11.5))", // Un cuadrado simple para Lima
        "POLYGON((-72.0 -16.0, -71.0 -16.0, -71.0 -17.0, -72.0 -17.0, -72.0 -16.0))"  // Un cuadrado simple para Arequipa
    };

    // Nombres correspondientes a los polígonos
    std::vector<std::string> nombres_departamentos = {
        "Lima",
        "Arequipa"
    };

    std::cout << "Procesando " << coords_sismos.size() << " sismos..." << std::endl;

    // --- 2. Llamamos a nuestra función de procesamiento paralelo ---
    std::vector<std::string> resultados = realizar_sjoin_paralelo(
        coords_sismos, 
        wkts_departamentos, 
        nombres_departamentos
    );

    // --- 3. Mostramos los resultados ---
    std::cout << "Resultados del análisis:" << std::endl;
    for (size_t i = 0; i < resultados.size(); ++i) {
        std::cout << "  - Sismo " << i + 1 
                  << " (Lat: " << coords_sismos[i].first << ", Lon: " << coords_sismos[i].second << ")"
                  << " -> Ubicación: " << resultados[i] << std::endl;
    }
    
    return 0; // Fin del programa
}