import pandas as pd
import streamlit as st
from energia.common import RAIZ, leer_json
from energia.etiquetas import tabla_visible, nombre_visible
st.set_page_config(page_title='Demanda eléctrica de España', page_icon='⚡', layout='wide')
st.title('Demanda eléctrica de España')
st.caption('Predicción diaria · energía en MWh · REE y AEMET')
carpeta = RAIZ / 'outputs'
if not (carpeta / 'run.json').exists():
    st.info('Aún no hay resultados. Se puede ejecutar python -m energia ejecutar desde la carpeta del proyecto.')
    st.stop()
ejecucion = leer_json(carpeta / 'run.json')
diario = pd.read_csv(RAIZ / 'data/processed/daily.csv', parse_dates=['date'])
if diario.date.max() > pd.Timestamp(ejecucion['forecast_origin']):
    st.info('El histórico contiene días posteriores al último entrenamiento. Se puede ejecutar python -m energia entrenar para actualizar los resultados.')
errores = pd.read_csv(carpeta / 'metrics.csv')
prediccion = pd.read_csv(carpeta / 'predictions.csv', parse_dates=['date'])
prevision = pd.read_csv(carpeta / 'forecast.csv', parse_dates=['date'])
columna_modelo, columna_total, columna_error = st.columns(3)
columna_modelo.metric('Modelo elegido en validación', nombre_visible(ejecucion['winner']))
columna_total.metric(f'Total previsto · {len(prevision)} días', f'{prevision.demand_mwh.sum():,.0f} MWh')
prueba = errores[(errores.model == ejecucion['winner']) & (errores.split == 'test')].iloc[0]
columna_error.metric('Error absoluto medio en la prueba final', f'{prueba.mae_mwh:,.0f} MWh')
st.caption(f"Último dato observado: {ejecucion['forecast_origin']}. Previsión del {prevision.date.min():%d/%m/%Y} al {prevision.date.max():%d/%m/%Y}.")
st.subheader('Previsión para las próximas cuatro semanas')
st.line_chart(tabla_visible(prevision.set_index('date')[['demand_mwh']]))
if 'week' in prevision:
    semanal = prevision.groupby('week').agg(desde=('date', 'min'), hasta=('date', 'max'), total_mwh=('demand_mwh', 'sum'))
    st.dataframe(tabla_visible(semanal))
st.caption('Se calculan también los días que faltan entre el último dato y mañana. La temperatura futura se mantiene en su último valor disponible: es un escenario aproximado.')
st.download_button('Descargar previsión diaria', tabla_visible(prevision).to_csv(index=False).encode('utf-8-sig'), 'prevision.csv', 'text/csv')
st.subheader('Histórico')
st.line_chart(tabla_visible(diario.set_index('date')[['demand_mwh']]))
st.subheader('Comparación de modelos')
st.dataframe(tabla_visible(errores), hide_index=True, width='stretch')
elegido = st.selectbox('Modelo', errores.model.unique(), format_func=nombre_visible)
seleccion = prediccion[(prediccion.model == elegido) & (prediccion.split == 'test')]
st.line_chart(tabla_visible(seleccion.set_index('date')[['actual_mwh', 'predicted_mwh']]))
st.caption(ejecucion['evaluation'] + '. Dentro de cada bloque se utilizan las propias predicciones, sin observar la demanda futura.')
if 'temp_c' in diario:
    st.subheader('Temperatura media de las estaciones seleccionadas (°C)')
    st.line_chart(tabla_visible(diario.set_index('date')[['temp_c']]))
st.download_button('Descargar métricas', tabla_visible(errores).to_csv(index=False).encode('utf-8-sig'), 'errores.csv', 'text/csv')
with st.expander('Configuración y avisos del entrenamiento'):
    st.json({nombre_visible(clave): valor for clave, valor in ejecucion['config'].items()})
    st.write(f"Avisos técnicos registrados durante el entrenamiento: {len(ejecucion.get('warnings', []))}.")
