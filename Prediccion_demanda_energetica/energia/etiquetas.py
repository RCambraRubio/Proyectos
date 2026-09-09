"""Nombres en castellano para presentar datos sin modificar los archivos originales."""

ETIQUETAS = {
    'date': 'Fecha', 'demand_mwh': 'Demanda (MWh)',
    'temp_c': 'Temperatura (°C)', 'stations_available': 'Estaciones disponibles',
    'model': 'Modelo', 'split': 'Periodo', 'evaluated_days': 'Días evaluados',
    'mae_mwh': 'Error absoluto medio (MWh)',
    'rmse_mwh': 'Raíz del error cuadrático medio (MWh)',
    'wape_pct': 'Error absoluto ponderado (%)',
    'actual_mwh': 'Demanda observada (MWh)', 'predicted_mwh': 'Demanda prevista (MWh)',
    'week': 'Semana', 'desde': 'Desde', 'hasta': 'Hasta', 'total_mwh': 'Total (MWh)',
    'seasonal_naive': 'Referencia semanal', 'sarima': 'SARIMA',
    'holt_winters': 'Holt-Winters',
    'ridge': 'Regresión regularizada', 'random_forest': 'Bosque aleatorio',
    'gradient_boosting': 'Potenciación por gradiente', 'mlp': 'Red neuronal',
    'validation': 'Validación', 'test': 'Prueba final',
    'start_date': 'Fecha inicial', 'end_date': 'Fecha final',
    'availability_lag_days': 'Días de retraso de publicación',
    'forecast_days': 'Días de previsión', 'aemet_stations': 'Estaciones de AEMET',
    'validation_days': 'Días de validación', 'test_days': 'Días de prueba', 'seed': 'Semilla aleatoria',
    'origin': 'Origen', 'lead_days': 'Días desde el origen',
}


def nombre_visible(valor):
    return ETIQUETAS.get(valor, valor)


def tabla_visible(tabla):
    resultado = tabla.copy()
    for columna in ('model', 'split'):
        if columna in resultado:
            resultado[columna] = resultado[columna].map(nombre_visible)
    resultado = resultado.rename(columns=ETIQUETAS)
    if resultado.index.name in ETIQUETAS:
        resultado.index.name = ETIQUETAS[resultado.index.name]
    return resultado
