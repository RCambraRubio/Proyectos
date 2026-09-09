import unittest
from unittest.mock import Mock, patch
from energia.sources import consultar_json

def respuesta(estado, contenido, headers=None):
    resultado = Mock(status_code=estado, headers=headers or {})
    resultado.json.return_value = contenido
    return resultado

class PruebasFuentes(unittest.TestCase):

    @patch('energia.sources.time.sleep')
    def test_limite_respeta_espera(self, pausa):
        cliente = Mock()
        cliente.get.side_effect = [respuesta(429, {}, {'Retry-After': '90'}), respuesta(200, [1])]
        self.assertEqual(consultar_json(cliente, 'https://opendata.aemet.es/test'), [1])
        self.assertEqual([c.args[0] for c in pausa.call_args_list], [2.5, 90, 2.5])

    @patch('energia.sources.time.sleep')
    def test_limite_json_sin_secretos(self, pausa):
        cliente = Mock()
        cliente.get.return_value = respuesta(200, {'estado': 429, 'descripcion': 'secret'})
        with self.assertRaises(RuntimeError) as avisos:
            consultar_json(cliente, 'https://opendata.aemet.es/test?api_key=secret')
        self.assertIn('429', str(avisos.exception))
        self.assertNotIn('secret', str(avisos.exception))
        self.assertEqual(cliente.get.call_count, 5)

    @patch('energia.sources.time.sleep')
    def test_clave_invalida_sin_reintento(self, pausa):
        cliente = Mock()
        cliente.get.return_value = respuesta(401, {})
        with self.assertRaisesRegex(RuntimeError, '401'):
            consultar_json(cliente, 'https://opendata.aemet.es/test')
        self.assertEqual(cliente.get.call_count, 1)

    @patch('energia.sources.time.sleep')
    def test_recuperacion_servidor(self, pausa):
        cliente = Mock()
        cliente.get.side_effect = [respuesta(503, {}), respuesta(200, {'ok': True})]
        self.assertEqual(consultar_json(cliente, 'https://apidatos.ree.es/test'), {'ok': True})
        pausa.assert_called_once_with(5)
