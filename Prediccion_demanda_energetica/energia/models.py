import pickle
import tempfile
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from .common import RAIZ, ahora, escribir_json
from .etl import crear_variables

def crear_modelos(semilla):

    def cadena(modelo):
        return make_pipeline(SimpleImputer(strategy='median', keep_empty_features=True), StandardScaler(), modelo)
    return {'ridge': cadena(Ridge(alpha=10)), 'random_forest': cadena(RandomForestRegressor(n_estimators=150, min_samples_leaf=5, random_state=semilla, n_jobs=-1)), 'gradient_boosting': cadena(HistGradientBoostingRegressor(max_iter=150, max_leaf_nodes=15, random_state=semilla)), 'mlp': TransformedTargetRegressor(regressor=cadena(MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=500, shuffle=False, random_state=semilla)), transformer=StandardScaler())}

def ajustar_sarima(objetivo):
    return SARIMAX(np.asarray(objetivo), order=(1, 0, 0), seasonal_order=(1, 0, 0, 7), trend='c').fit(disp=False, maxiter=150)

def ajustar_holt_winters(objetivo):
    """Estacionalidad semanal aditiva y tendencia amortiguada; ajuste en GWh."""
    return ExponentialSmoothing(
        np.asarray(objetivo, dtype=float) / 1000,
        trend='add', damped_trend=True, seasonal='add',
        seasonal_periods=7, initialization_method='estimated',
    ).fit(optimized=True)

def calcular_errores(objetivo, prediccion):
    error = np.asarray(objetivo) - np.asarray(prediccion)
    return {'mae_mwh': float(np.abs(error).mean()), 'rmse_mwh': float(np.sqrt((error ** 2).mean())), 'wape_pct': float(100 * np.abs(error).sum() / np.abs(objetivo).sum())}

def ajustar_modelo(nombre, historico, configuracion):
    if nombre == 'seasonal_naive':
        return None
    if nombre == 'sarima':
        return ajustar_sarima(historico.demand_mwh.iloc[28:])
    if nombre == 'holt_winters':
        return ajustar_holt_winters(historico.demand_mwh.iloc[28:])
    modelo = crear_modelos(configuracion['seed'])[nombre]
    modelo.fit(crear_variables(historico, configuracion).iloc[28:], historico.demand_mwh.iloc[28:])
    return modelo

def predecir_periodo(nombre, modelo, historico, configuracion, pasos):
    """Pronóstico desde un único origen, sin incorporar observaciones futuras."""
    if pasos < 1:
        raise ValueError('El horizonte debe ser positivo')
    fechas = pd.date_range(historico.index[-1] + pd.Timedelta(days=1), periods=pasos)
    if nombre in ('sarima', 'holt_winters'):
        valores = np.asarray(modelo.forecast(pasos), dtype=float)
        if nombre == 'holt_winters':
            valores = valores * 1000  # Restituir MWh tras el ajuste en GWh.
    else:
        futuro = historico.reindex(historico.index.append(fechas)).copy()
        if 'temp_c' in futuro:
            fecha_corte = historico.index[-1] - pd.Timedelta(days=configuracion['availability_lag_days'] - 1)
            disponibles = historico.loc[:fecha_corte, 'temp_c'].dropna()
            futuro.loc[futuro.index > fecha_corte, 'temp_c'] = disponibles.iloc[-1] if len(disponibles) else np.nan
        valores = []
        for dia in fechas:
            if nombre == 'seasonal_naive':
                valor = float(futuro.loc[dia - pd.Timedelta(days=7), 'demand_mwh'])
            else:
                fila = crear_variables(futuro.loc[:dia], configuracion).iloc[[-1]]
                valor = float(modelo.predict(fila)[0])
            futuro.loc[dia, 'demand_mwh'] = valor
            valores.append(valor)
        valores = np.asarray(valores)
    if not np.isfinite(valores).all() or (valores <= 0).any():
        raise ValueError(f'Predicciones no válidas: {nombre}')
    return pd.Series(valores, index=fechas, name='demand_mwh')

def calcular_periodo(ultimo_dato, horizonte, hoy=None):
    hoy = pd.Timestamp.now(tz='Europe/Madrid').tz_localize(None).normalize() if hoy is None else pd.Timestamp(hoy).normalize()
    primero = max(hoy + pd.Timedelta(days=1), ultimo_dato + pd.Timedelta(days=1))
    hueco = (primero - ultimo_dato).days - 1
    return (primero, hueco, hueco + horizonte)

def entrenar(tabla, configuracion):
    horizonte = configuracion.get('forecast_days', 28)
    if not isinstance(horizonte, int) or horizonte < 1:
        raise ValueError('forecast_days debe ser un entero positivo')
    esperado = pd.date_range(tabla.index.min(), tabla.index.max(), name=tabla.index.name)
    if not tabla.index.equals(esperado) or tabla.demand_mwh.isna().any() or (tabla.demand_mwh <= 0).any():
        raise ValueError('Se necesita un histórico diario continuo con demanda positiva')
    primero, hueco, pasos = calcular_periodo(tabla.index[-1], horizonte)
    dias_validacion, dias_prueba = (configuracion['validation_days'], configuracion['test_days'])
    inicio_validacion = len(tabla) - dias_validacion - dias_prueba
    inicio_prueba = len(tabla) - dias_prueba
    if min(dias_validacion, dias_prueba) < horizonte or inicio_validacion < 208:
        raise ValueError('Faltan datos: se requieren 208 días previos al origen y al menos un horizonte completo en validación y prueba')
    filas, predicciones, registro_avisos = ([], [], [])
    nombres = ['seasonal_naive', 'sarima', 'holt_winters', *crear_modelos(configuracion['seed'])]
    for nombre in nombres:
        for particion, inicio, fin_bloque in [('validation', inicio_validacion, inicio_prueba), ('test', inicio_prueba, len(tabla))]:
            observaciones, estimaciones = ([], [])
            for bloque in range(inicio, fin_bloque - horizonte + 1, horizonte):
                historico = tabla.iloc[:bloque]
                with warnings.catch_warnings(record=True) as avisos:
                    warnings.simplefilter('always')
                    modelo = ajustar_modelo(nombre, historico, configuracion)
                    predicho = predecir_periodo(nombre, modelo, historico, configuracion, horizonte)
                registro_avisos.extend(({'model': nombre, 'split': particion, 'message': mensaje} for mensaje in sorted({str(w.message) for w in avisos})))
                observado = tabla.demand_mwh.iloc[bloque:bloque + horizonte]
                observaciones.extend(observado.to_numpy())
                estimaciones.extend(predicho.to_numpy())
                predicciones.extend(({'date': str(dia.date()), 'model': nombre, 'split': particion, 'origin': str(historico.index[-1].date()), 'lead_days': i + 1, 'actual_mwh': float(valor), 'predicted_mwh': float(estimado)} for i, (dia, valor, estimado) in enumerate(zip(observado.index, observado, predicho))))
            filas.append({'model': nombre, 'split': particion, 'evaluated_days': len(observaciones), **calcular_errores(np.array(observaciones), np.array(estimaciones))})
    errores = pd.DataFrame(filas)
    ganador = errores[errores.split == 'validation'].sort_values('mae_mwh').iloc[0].model
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter('always')
        modelo = ajustar_modelo(ganador, tabla, configuracion)
        prevision = predecir_periodo(ganador, modelo, tabla, configuracion, pasos).iloc[hueco:]
        registro_avisos.extend(({'model': ganador, 'split': 'final_fit', 'message': mensaje} for mensaje in sorted({str(w.message) for w in avisos})))
    destino = RAIZ / 'outputs'
    destino.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='energia-results-') as carpeta_temporal:
        salida = Path(carpeta_temporal)
        errores.to_csv(salida / 'metrics.csv', index=False)
        pd.DataFrame(predicciones).to_csv(salida / 'predictions.csv', index=False)
        tabla_prevision = prevision.rename_axis('date').reset_index()
        tabla_prevision['model'] = ganador
        tabla_prevision['week'] = np.arange(horizonte) // 7 + 1
        tabla_prevision.to_csv(salida / 'forecast.csv', index=False)
        with (salida / 'model.pkl').open('wb') as archivo:
            pickle.dump({'model': modelo, 'name': ganador, 'features': list(crear_variables(tabla, configuracion).columns), 'config': configuracion}, archivo)
        escribir_json(salida / 'run.json', {'created_at': ahora(), 'winner': ganador, 'config': configuracion, 'forecast_origin': str(tabla.index[-1].date()), 'horizon_days': horizonte, 'forecast_start': str(primero.date()), 'forecast_end': str(prevision.index[-1].date()), 'gap_days': hueco, 'recursive_steps': pasos, 'validation_start': str(tabla.index[inicio_validacion].date()), 'test_start': str(tabla.index[inicio_prueba].date()), 'evaluation': f'Bloques completos de {horizonte} días desde el último dato de cada origen; selección solo por validación. El pronóstico actual puede requerir pasos adicionales por retraso de los datos', 'exogenous_scenario': 'Temperatura constante desde el último valor disponible; no son previsiones meteorológicas.', 'warnings': registro_avisos})
        import shutil
        for nombre in ('metrics.csv', 'predictions.csv', 'forecast.csv', 'model.pkl', 'run.json'):
            pendiente = destino / (nombre + '.tmp')
            shutil.copyfile(salida / nombre, pendiente)
            pendiente.replace(destino / nombre)
    return (errores, ganador)
