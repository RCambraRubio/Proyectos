"""Descargas por meses, caché local y manifiestos sin credenciales."""
import os
import logging
import re
import time
from datetime import date, timedelta
from urllib.parse import urlsplit
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .common import RAIZ, ahora, escribir_json

def crear_sesion():
    cliente = requests.Session()
    reintentos = Retry(total=2, backoff_factor=1, status=0, raise_on_status=False, respect_retry_after_header=False, allowed_methods=['GET'])
    cliente.mount('https://', HTTPAdapter(max_retries=reintentos))
    cliente.headers['User-Agent'] = 'Prediccion_demanda_energetica/0.1'
    return cliente

def consultar_json(cliente, url, **opciones):
    servidor = urlsplit(url).hostname
    proveedor = {'opendata.aemet.es': 'AEMET', 'apidatos.ree.es': 'REE'}.get(servidor, 'proveedor de datos')
    for intento in range(5):
        if proveedor == 'AEMET':
            time.sleep(2.5)
        try:
            respuesta = cliente.get(url, timeout=60, **opciones)
        except requests.RequestException as excepcion:
            raise RuntimeError(f'{proveedor}: fallo de conexión ({type(excepcion).__name__}); se puede repetir la ejecución para reanudar.') from None
        estado = respuesta.status_code
        try:
            contenido = respuesta.json()
        except ValueError:
            contenido = None
        if estado == 200 and proveedor == 'AEMET' and isinstance(contenido, dict):
            try:
                estado = int(contenido.get('estado', estado))
            except (TypeError, ValueError):
                raise RuntimeError('AEMET: respuesta con estado inválido.') from None
        if estado in (429, 500, 502, 503, 504) and intento < 4:
            espera = 60 if estado == 429 else 5 * 2 ** intento
            cabecera = respuesta.headers.get('Retry-After')
            if cabecera:
                try:
                    espera = max(espera, Retry().parse_retry_after(cabecera))
                except Exception:
                    pass
            logging.warning('%s: HTTP/estado %s; reintento %s/4 en %.0f s', proveedor, estado, intento + 1, espera)
            respuesta.close()
            time.sleep(espera)
            continue
        if estado >= 400:
            explicacion = {429: 'límite de peticiones; se debe esperar y repetir la ejecución sin --actualizar', 401: 'credencial ausente, caducada o inválida', 403: 'acceso denegado', 404: 'recurso o periodo sin datos'}.get(estado, 'error del servicio')
            raise RuntimeError(f'{proveedor}: HTTP/estado {estado}, {explicacion}.') from None
        if contenido is None:
            raise RuntimeError(f'{proveedor}: respuesta JSON inválida (HTTP {estado}).') from None
        return contenido

def meses(inicio, fin):
    actual = date.fromisoformat(inicio)
    fin = date.fromisoformat(fin)
    if actual > fin:
        raise ValueError('start_date debe ser anterior a end_date')
    while actual <= fin:
        siguiente = (actual.replace(day=28) + timedelta(days=4)).replace(day=1)
        fin_bloque = min(fin, siguiente - timedelta(days=1))
        yield (actual.isoformat(), fin_bloque.isoformat())
        actual = fin_bloque + timedelta(days=1)

def descargar(configuracion, inicio, fin, proveedores, actualizar=False):
    load_dotenv(RAIZ / '.env')
    if 'aemet' in proveedores and (not os.getenv('AEMET_API_KEY')):
        raise ValueError('Se debe configurar AEMET_API_KEY en .env. Se puede descargar antes con --fuentes ree.')
    originales = RAIZ / 'data' / 'raw'
    manifiesto = {'created_at': ahora(), 'start': inicio, 'end': fin, 'files': {}}
    with crear_sesion() as cliente:

        def guardar_en_cache(fuente, clave, obtener):
            ruta = originales / fuente / f'{clave}.json'
            if actualizar or not ruta.exists():
                logging.info('Descargando %s: %s', fuente.upper(), clave)
                try:
                    contenido = obtener()
                except (RuntimeError, ValueError) as excepcion:
                    raise RuntimeError(f'{fuente.upper()} [{clave}]: {excepcion}') from None
                escribir_json(ruta, {'downloaded_at': ahora(), 'payload': contenido})
            manifiesto['files'].setdefault(fuente, []).append(str(ruta.relative_to(RAIZ)))
        for fuente in proveedores:
            if fuente == 'ree':
                for primero, ultimo in meses(inicio, fin):

                    def obtener_ree():
                        resultado = consultar_json(cliente, 'https://apidatos.ree.es/es/datos/demanda/evolucion', params={'start_date': primero + 'T00:00', 'end_date': ultimo + 'T23:59', 'time_trunc': 'day'})
                        if not resultado.get('included'):
                            raise ValueError('REE no devolvió indicadores de demanda')
                        return resultado
                    guardar_en_cache(fuente, f'{primero}_{ultimo}', obtener_ree)
            elif fuente == 'aemet':
                for estacion in configuracion['aemet_stations']:
                    if not re.fullmatch('[A-Za-z0-9]+', estacion):
                        raise ValueError('Indicativo AEMET inválido')
                    for primero, ultimo in meses(inicio, fin):

                        def obtener_aemet():
                            url = f'https://opendata.aemet.es/opendata/api/valores/climatologicos/diarios/datos/fechaini/{primero}T00:00:00UTC/fechafin/{ultimo}T23:59:59UTC/estacion/{estacion}'
                            resultado = consultar_json(cliente, url, headers={'api_key': os.environ['AEMET_API_KEY']})
                            if resultado.get('estado') != 200 or not resultado.get('datos'):
                                raise ValueError(f"AEMET no tiene datos para {estacion}, {primero}; estado {resultado.get('estado')}")
                            contenido = consultar_json(cliente, resultado['datos'])
                            if not isinstance(contenido, list) or not contenido:
                                raise ValueError('Respuesta AEMET vacía')
                            return contenido
                        guardar_en_cache(fuente, f'{estacion}_{primero}_{ultimo}', obtener_aemet)
    escribir_json(originales / 'manifest.json', manifiesto)
    return manifiesto
