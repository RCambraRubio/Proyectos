# Investigación operativa

La **investigación operativa** utiliza modelos matemáticos para elegir la mejor decisión posible con recursos limitados: qué producir, dónde ubicar almacenes o cómo asignar rutas y turnos.

## Cómo formular un problema

Identifica **datos**, **variables de decisión**, **objetivo** y **restricciones**. Después resuelve el modelo y comprueba que la solución cumple las condiciones y tiene sentido.

Por ejemplo, una fábrica quiere cubrir una demanda mínima al menor coste. Para productos `j` y recursos `i`, una formulación genérica es:

$$
\begin{aligned}
\min_x \quad & \sum_j c_j x_j \\
\text{sujeto a}\quad & \sum_j a_{ij}x_j \le b_i && \text{para cada recurso } i, \\
& x_j \ge d_j && \text{para cada producto } j, \\
& x_j \ge 0 && \text{para cada producto } j.
\end{aligned}
$$

- **Variable:** `x_j`, cantidad que fabricar del producto `j`.
- **Datos:** `c_j`, coste unitario; `a_ij`, consumo del recurso `i` por unidad de `j`; `b_i`, recurso disponible; `d_j`, demanda mínima.
- **Objetivo:** minimizar el coste total. **Restricciones:** respetar recursos y cubrir demanda. Si las unidades son indivisibles, se exige además que `x_j` sea entero.

## Formas de resolverlo

| Modelo o enfoque | Cuándo usarlo | Método habitual |
|---|---|---|
| Programación lineal | Relaciones lineales y cantidades divisibles | Símplex o punto interior |
| Entera o mixta | Decisiones sí/no o cantidades enteras | Ramificación y acotación, cortes |
| No lineal o cuadrática | Curvas o productos de variables | Optimización convexa o búsqueda global, según el modelo |
| Programación dinámica | Decisiones por etapas | Resolver y reutilizar estados |
| Grafos y redes | Rutas, flujos y precedencias | Caminos mínimos, flujo de coste mínimo |
| Restricciones | Muchas reglas de compatibilidad | Propagación y búsqueda con retroceso |
| Enumeración | Pocas combinaciones | Comparar todas las alternativas factibles |
| Heurísticas y metaheurísticas | Problemas demasiado grandes para métodos exactos | Búsqueda local, genéticos, recocido |
| Modelos estocásticos y simulación | Demanda o tiempos inciertos | Escenarios, Monte Carlo, eventos discretos |
| Fórmulas analíticas | Supuestos conocidos de inventarios o colas | EOQ, Erlang C |

Un modelo puede admitir varios métodos. **Factible** significa que cumple las restricciones; **óptimo**, que ninguna alternativa factible mejora el objetivo. Las heurísticas y la simulación no garantizan por sí solas encontrar el óptimo.

## Ejercicios

Los **15 notebooks `.ipynb`** están organizados en cuatro carpetas temáticas. En «Formas de resolverlo» usan los nombres exactos de la tabla anterior y marcan el enfoque **principal**, el **complementario** si lo hay y las **alternativas**. «Método elegido» repite esos nombres y explica la técnica concreta.

Abre, por ejemplo, el [plan maestro de producción](01_Problemas_de_Produccion_y_Operaciones/01_Master_Production_Schedule.ipynb) y selecciona un kernel de Python. Los resultados ya están guardados; para recalcularlos, ejecuta las celdas en orden. El código solo usa la biblioteca estándar de Python 3.9 o posterior.

Los datos son sintéticos y las instancias son pequeñas; aumentar su tamaño puede encarecer mucho la búsqueda. Los 15 ejemplos se comprobaron con un límite de cinco segundos por notebook.
