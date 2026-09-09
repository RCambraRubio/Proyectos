import unittest
import numpy as np
import pandas as pd
from energia.etl import crear_variables, tabla_ree
from energia.models import calcular_errores

class PruebasProceso(unittest.TestCase):

    def test_fecha_local_conservada(self):
        contenido = {'included': [{'attributes': {'title': 'Demanda', 'values': [{'datetime': '2025-01-01T00:00:00.000+01:00', 'value': 600000}]}}]}
        self.assertEqual(tabla_ree(contenido).date.iloc[0], pd.Timestamp('2025-01-01'))

    def test_futuro_no_modifica_variables_pasadas(self):
        tabla = pd.DataFrame({'demand_mwh': np.arange(100, dtype=float) + 100, 'temp_c': 20.0}, index=pd.date_range('2024-01-01', periods=100))
        configuracion = {'availability_lag_days': 5}
        original = crear_variables(tabla, configuracion)
        tabla.iloc[60:, :] = 999999
        modificado = crear_variables(tabla, configuracion)
        pd.testing.assert_frame_equal(original.iloc[:61], modificado.iloc[:61])

    def test_unidades_errores(self):
        resultado = calcular_errores(np.array([100.0, 200.0]), np.array([90.0, 210.0]))
        self.assertEqual(resultado['mae_mwh'], 10)
        self.assertAlmostEqual(resultado['wape_pct'], 100 * 20 / 300)
if __name__ == '__main__':
    unittest.main()
