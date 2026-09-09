import tempfile
import unittest
from pathlib import Path
import pandas as pd
from energia.etl import actualizar_tabla

class PruebasGuardado(unittest.TestCase):

    def test_anadir_repetir_y_corregir(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'daily.csv'
            primero = pd.DataFrame({'demand_mwh': [100.0, 200.0]}, index=pd.date_range('2024-01-01', periods=2, name='date'))
            actualizar_tabla(ruta, primero)
            original = ruta.read_bytes()
            fecha_modificacion = ruta.stat().st_mtime_ns
            actualizar_tabla(ruta, primero)
            self.assertEqual(ruta.stat().st_mtime_ns, fecha_modificacion)
            adicional = pd.DataFrame({'demand_mwh': [200.0, 300.0]}, index=pd.date_range('2024-01-02', periods=2, name='date'))
            combinada = actualizar_tabla(ruta, adicional)
            self.assertEqual(len(combinada), 3)
            self.assertTrue(ruta.read_bytes().startswith(original))
            adicional.iloc[0, 0] = 250
            combinada = actualizar_tabla(ruta, adicional)
            self.assertEqual(len(combinada), 3)
            self.assertEqual(combinada.loc['2024-01-02', 'demand_mwh'], 250)

    def test_columna_nueva_conserva_historico(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'daily.csv'
            fechas = pd.date_range('2024-01-01', periods=2, name='date')
            actualizar_tabla(ruta, pd.DataFrame({'demand_mwh': [100.0, 200.0]}, index=fechas))
            combinada = actualizar_tabla(ruta, pd.DataFrame({'demand_mwh': [200.0], 'temp_c': [18.0]}, index=fechas[1:]))
            self.assertEqual(len(combinada), 2)
            self.assertEqual(combinada.iloc[0].demand_mwh, 100)
            self.assertEqual(combinada.iloc[1].temp_c, 18)
