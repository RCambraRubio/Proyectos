import numpy as np
import pandas as pd
from .common import RAIZ, leer_json, escribir_json

def tabla_ree(contenido):
    indicadores = [variables for variables in contenido['included'] if variables['attributes'].get('title') == 'Demanda']
    if len(indicadores) != 1:
        raise ValueError('REE: se esperaba exactamente un indicador Demanda')
    valores = indicadores[0]['attributes']['values']
    return pd.DataFrame({'date': [pd.Timestamp(v['datetime'][:10]) for v in valores], 'demand_mwh': [v['value'] for v in valores]})

def temperatura(valor):
    try:
        return float(str(valor).replace(',', '.'))
    except (TypeError, ValueError):
        return np.nan

def preparar_datos(configuracion):
    manifiesto = leer_json(RAIZ / 'data/raw/manifest.json')

    def contenidos(fuente):
        return [leer_json(RAIZ / p)['payload'] for p in manifiesto['files'].get(fuente, [])]
    ree = contenidos('ree')
    if not ree:
        raise ValueError('El manifiesto debe incluir REE; ejecuta download con las fuentes deseadas juntas')
    tabla = pd.concat([tabla_ree(p) for p in ree]).sort_values('date')
    if tabla.date.duplicated().any():
        raise ValueError('REE contiene fechas duplicadas')
    tabla = tabla.set_index('date').reindex(pd.date_range(manifiesto['start'], manifiesto['end'], freq='D'))
    tabla.index.name = 'date'
    tabla['demand_mwh'] = pd.to_numeric(tabla.demand_mwh, errors='coerce')
    if tabla.demand_mwh.isna().any() or (tabla.demand_mwh <= 0).any():
        raise ValueError('Demanda incompleta o no positiva. Se deben revisar las fechas o repetir la descarga con --actualizar; no se rellena la demanda ausente.')
    aemet = contenidos('aemet')
    if aemet:
        clima = pd.DataFrame([fila for lote in aemet for fila in lote])
        clima['date'] = pd.to_datetime(clima.fecha)
        clima['temp_c'] = clima.tmed.map(temperatura)
        clima = clima.drop_duplicates(['date', 'indicativo'])
        agrupado = clima.groupby('date').temp_c
        tabla['temp_c'] = agrupado.mean()
        tabla['stations_available'] = agrupado.count()
        if tabla.temp_c.notna().sum() == 0:
            raise ValueError('AEMET no contiene temperaturas válidas')
    return guardar(tabla, {'sources': list(manifiesto['files']), 'config': configuracion})

def actualizar_tabla(ruta, tabla):
    """Añadir fechas nuevas; corregir el archivo solo si cambia el histórico."""
    tabla = tabla.sort_index()
    if tabla.empty or tabla.index.has_duplicates:
        raise ValueError('El dataset debe tener fechas únicas y no estar vacío')
    if ruta.exists():
        anterior = pd.read_csv(ruta, index_col='date', parse_dates=['date'])
        if anterior.index.has_duplicates:
            raise ValueError('daily.csv contiene fechas duplicadas')
        combinada = tabla.combine_first(anterior).sort_index()
        combinada = combinada.reindex(columns=list(anterior.columns) + [c for c in tabla if c not in anterior])
        try:
            pd.testing.assert_frame_equal(combinada.loc[anterior.index], anterior, check_dtype=False, check_freq=False, atol=1e-08, rtol=1e-12)
            nuevos = combinada.loc[~combinada.index.isin(anterior.index)]
            if nuevos.empty:
                return anterior
            if anterior.index.is_monotonic_increasing and nuevos.index.min() > anterior.index.max():
                nuevos.to_csv(ruta, mode='a', header=False, index_label='date')
                return combinada
        except AssertionError:
            pass
        tabla = combinada
    temporal = ruta.with_suffix('.csv.tmp')
    tabla.to_csv(temporal, index_label='date')
    temporal.replace(ruta)
    return tabla

def guardar(tabla, metadatos):
    carpeta = RAIZ / 'data/processed'
    carpeta.mkdir(parents=True, exist_ok=True)
    tabla = actualizar_tabla(carpeta / 'daily.csv', tabla)
    escribir_json(carpeta / 'quality.json', {'rows': len(tabla), 'start': str(tabla.index.min().date()), 'end': str(tabla.index.max().date()), 'missing': {k: int(v) for k, v in tabla.isna().sum().items()}, **metadatos})
    return tabla

def crear_variables(tabla, configuracion):
    variables = pd.DataFrame(index=tabla.index)
    for retardo in (1, 2, 7, 14, 28):
        variables[f'lag_{retardo}'] = tabla.demand_mwh.shift(retardo)
    for ventana in (7, 28):
        variables[f'mean_{ventana}'] = tabla.demand_mwh.shift(1).rolling(ventana).mean()
    variables['weekday'] = tabla.index.dayofweek
    variables['annual_sin'] = np.sin(2 * np.pi * tabla.index.dayofyear / 365.25)
    variables['annual_cos'] = np.cos(2 * np.pi * tabla.index.dayofyear / 365.25)
    if 'temp_c' in tabla:
        variables['temp_lag'] = tabla.temp_c.shift(configuracion['availability_lag_days']).ffill(limit=7)
    return variables
