import argparse
import logging
from datetime import date, timedelta
import pandas as pd
from .common import RAIZ, leer_json
from .etl import preparar_datos
from .models import entrenar
from .sources import descargar
from .etiquetas import tabla_visible, nombre_visible

def principal():
    analizador = argparse.ArgumentParser(description='Predicción diaria de demanda eléctrica española')
    analizador.add_argument('orden', choices=['descargar', 'etl', 'entrenar', 'ejecutar'])
    analizador.add_argument('--configuracion', default=str(RAIZ / 'config.json'))
    analizador.add_argument('--inicio')
    analizador.add_argument('--fin')
    analizador.add_argument('--fuentes', nargs='+', choices=['ree', 'aemet'], default=['ree', 'aemet'])
    analizador.add_argument('--actualizar', action='store_true', help='Volver a consultar la API y reemplazar caché')
    argumentos = analizador.parse_args()
    configuracion = leer_json(argumentos.configuracion)
    if configuracion['availability_lag_days'] < 1:
        analizador.error('availability_lag_days debe ser >= 1')
    inicio = argumentos.inicio or configuracion['start_date']
    fin = argumentos.fin or configuracion['end_date'] or (date.today() - timedelta(days=configuracion['availability_lag_days'])).isoformat()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    try:
        if argumentos.orden in ('descargar', 'ejecutar'):
            logging.info('Descargando %s: %s a %s', argumentos.fuentes, inicio, fin)
            descargar(configuracion, inicio, fin, argumentos.fuentes, argumentos.actualizar)
        if argumentos.orden in ('etl', 'ejecutar'):
            tabla = preparar_datos(configuracion)
        if argumentos.orden == 'entrenar':
            tabla = pd.read_csv(RAIZ / 'data/processed/daily.csv', index_col='date', parse_dates=['date'])
        if argumentos.orden in ('entrenar', 'ejecutar'):
            errores, ganador = entrenar(tabla, configuracion)
            print(tabla_visible(errores).to_string(index=False))
            print(f'Ganador por validación: {nombre_visible(ganador)}. Resultados: outputs/')
    except (ValueError, RuntimeError, OSError, KeyError) as excepcion:
        logging.error('Proceso interrumpido: %s', excepcion)
        raise SystemExit(1) from None
if __name__ == '__main__':
    principal()
