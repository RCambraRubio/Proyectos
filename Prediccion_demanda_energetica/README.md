# ¿Cuánta electricidad usará España?

Este proyecto mira datos del pasado para intentar calcular cuánta electricidad necesitará España cada día durante las **próximas cuatro semanas (28 días)**. La cantidad se mide en **MWh**, una unidad de energía.

## ¿Qué se ha hecho?

1. **Recoger datos:** REE proporciona la demanda eléctrica y AEMET las temperaturas.
2. **Ordenarlos:** se reúne la información en una tabla por días y se comprueba si faltan datos. Esto se llama ETL.
3. **Probar siete formas de predecir:** una repite el valor de la semana anterior; las otras buscan patrones. Se llaman SARIMA, Holt-Winters, regresión regularizada, bosque aleatorio, potenciación por gradiente y perceptrón multicapa, que es una red neuronal.
4. **Comprobar los errores:** los modelos aprenden con días antiguos y se examinan con días posteriores.
5. **Mostrar los resultados:** un panel permite ver gráficos y comparar los modelos.

**Ya se ha ejecutado el proceso con datos reales.**

## ¿Qué hay en cada sitio?

| Archivo o carpeta | ¿Para qué sirve? |
| --- | --- |
| `energia/` | El código que descarga, ordena los datos y hace predicciones. |
| `data/raw/` | Los datos tal como llegan de cada fuente. |
| `data/processed/daily.csv` | Una única tabla: se añaden los días nuevos sin duplicar los anteriores. |
| `outputs/` | Solo los resultados del último entrenamiento. Se reemplazan al terminar el siguiente. |
| `app.py` | El panel con los gráficos. |
| `config.json` | Los ajustes: fechas, estaciones meteorológicas y días de prueba. |
| `.env` | La clave privada de AEMET, que debe mantenerse confidencial. |
| `scripts/` | Ayudas para ejecutar el proyecto y preparar una tarea diaria. |
| `tests/` | Pruebas que comprueban que el código funciona. |
| `requirements.txt` | La lista de herramientas que necesita Python. |
| `.venv/` | Las herramientas ya instaladas para este proyecto. |
| `.gitignore` | Indica qué archivos quedan fuera del control de versiones. |


## ¿Cómo se utiliza?

El primer paso es conseguir una clave privada de AEMET y añadirla al archivo .env
Los archivos de data/raw/ están comprimidos. El segundo paso es descomprimirlos.

El resto está preparado. Se abre PowerShell y se accede a la carpeta:

```powershell
cd ruta_del_proyecto\Prediccion_demanda_energetica
```

Para descargar lo que falta, ordenar los datos y volver a entrenar:

```powershell
.\.venv\Scripts\python.exe -m energia ejecutar
```

Para abrir los gráficos:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

**La previsión empieza mañana y cubre 28 días.** Si faltan datos recientes, también se calculan esos días intermedios. El panel muestra la curva diaria y el total de cada semana.

Para comprobar los modelos, se reservan las últimas cuatro semanas del histórico y se predicen usando solo los días anteriores. Después se comparan las predicciones con lo que pasó de verdad. Las cuatro semanas anteriores al examen sirven para elegir el modelo. La temperatura futura se mantiene en su último valor conocido: es una aproximación que todavía se puede mejorar.

Para recalcular la previsión usando los datos guardados:

```powershell
.\.venv\Scripts\python.exe -m energia entrenar
```
