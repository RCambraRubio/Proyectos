import unittest
import numpy as np
import pandas as pd
from energia.models import ajustar_modelo, predecir_periodo


class PruebasHoltWinters(unittest.TestCase):
    def test_patron_semanal_unidades_y_horizonte(self):
        patron = np.array([700000., 720000., 730000., 710000., 690000., 600000., 580000.])
        historico = pd.DataFrame({'demand_mwh': np.tile(patron, 40)},
                                index=pd.date_range('2024-01-01', periods=280))
        modelo = ajustar_modelo('holt_winters', historico, {})
        prevision = predecir_periodo('holt_winters', modelo, historico, {}, 34)
        self.assertEqual(len(prevision), 34)
        self.assertEqual(prevision.index[0], historico.index[-1] + pd.Timedelta(days=1))
        np.testing.assert_allclose(prevision, np.resize(patron, 34), atol=1000, rtol=0)
