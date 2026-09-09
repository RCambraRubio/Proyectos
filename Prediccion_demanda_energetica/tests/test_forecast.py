import unittest
import numpy as np
import pandas as pd
from energia.models import predecir_periodo, calcular_periodo

class PruebasPrevision(unittest.TestCase):

    def test_referencia_semanal_sin_observaciones_futuras(self):
        historico = pd.DataFrame({'demand_mwh': np.arange(1.0, 36.0)}, index=pd.date_range('2024-01-01', periods=35))
        resultado = predecir_periodo('seasonal_naive', None, historico, {}, 28)
        np.testing.assert_array_equal(resultado, np.tile(np.arange(29.0, 36.0), 4))
        self.assertEqual(resultado.index[0], historico.index[-1] + pd.Timedelta(days=1))
        self.assertEqual(len(historico), 35)

    def test_periodo_cubre_hueco_y_cuatro_semanas(self):
        primero, hueco, pasos = calcular_periodo(pd.Timestamp('2026-09-02'), 28, '2026-09-08')
        self.assertEqual(primero, pd.Timestamp('2026-09-09'))
        self.assertEqual(hueco, 6)
        self.assertEqual(pasos, 34)

    def test_variables_usan_predicciones_y_clima_disponible(self):
        historico = pd.DataFrame({'demand_mwh': 100.0, 'temp_c': np.arange(40.0)}, index=pd.date_range('2024-01-01', periods=40))
        original = historico.copy()

        class Modelo:

            def predict(self, variables):
                assert variables.temp_lag.iloc[0] == 35
                return np.array([variables.lag_1.iloc[0] + 1])
        resultado = predecir_periodo('ridge', Modelo(), historico, {'availability_lag_days': 5}, 28)
        np.testing.assert_array_equal(resultado, np.arange(101.0, 129.0))
        pd.testing.assert_frame_equal(historico, original)
