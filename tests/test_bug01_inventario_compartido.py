"""Test funcional para el Bug 01: inventario compartido entre instancias.

El bug estaba en ``main.py`` línea 4:

    def __init__(self, inventario_inicial={}):

El diccionario mutable como argumento por defecto se crea UNA sola vez, al
definir la clase, y todas las instancias de ``TiendaOnline`` comparten ese
mismo objeto. Este test garantiza que cada instancia tenga su propio
inventario aislado.

Ejecutar desde la raíz del repo:

    python3 -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

# Permite importar main.py esté donde esté el cwd al ejecutar el test
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import TiendaOnline  # noqa: E402


class TestInventarioNoCompartido(unittest.TestCase):
    """Verifica que ninguna instancia herede el inventario de otra."""

    def test_dos_instancias_no_comparten_el_mismo_diccionario(self):
        """Las instancias creadas sin argumentos deben tener dicts distintos."""
        tienda1 = TiendaOnline()
        tienda2 = TiendaOnline()

        self.assertIsNot(
            tienda1.inventario,
            tienda2.inventario,
            "Ambas tiendas apuntan al MISMO diccionario (argumento mutable por defecto)",
        )

    def test_producto_agregado_en_tienda1_no_aparece_en_tienda2(self):
        """Reproduce la 'Prueba 1' del código: tienda2 debe nacer vacía."""
        tienda1 = TiendaOnline()
        tienda1.agregar_producto("P01", "Teclado Mecánico", 150000, 5)

        tienda2 = TiendaOnline()

        self.assertEqual(
            tienda2.inventario,
            {},
            f"tienda2 ve productos que nunca agregó: {tienda2.inventario}",
        )
        self.assertNotIn("P01", tienda2.inventario)

    def test_mutaciones_de_una_instancia_no_afectan_a_las_demas(self):
        """Crear todas las instancias primero y mutar después (caso clásico)."""
        tiendas = [TiendaOnline() for _ in range(5)]

        tiendas[0].agregar_producto("P02", "Mouse Gamer", 80000, 3)

        for i, tienda in enumerate(tiendas[1:], start=2):
            self.assertEqual(
                tienda.inventario,
                {},
                f"tienda{i} heredó el inventario de tienda1",
            )

    def test_cada_instancia_tiene_un_inventario_vacio_al_nacer(self):
        """Ninguna tienda debe recibir datos 'fantasma' de creaciones previas."""
        TiendaOnline().agregar_producto("P03", "Monitor", 250000, 2)

        self.assertEqual(TiendaOnline().inventario, {})

    def test_inventario_inicial_explicito_se_respeta(self):
        """El parámetro opcional sigue funcionando cuando se pasa explícitamente."""
        inicial = {"P09": {"nombre": "Webcam HD", "precio": 90000, "cantidad": 2}}

        tienda = TiendaOnline(inventario_inicial=inicial)

        self.assertEqual(tienda.inventario, inicial)
        self.assertIn("P09", tienda.inventario)
        # Las demás tiendas no ven este inventario explícito
        self.assertEqual(TiendaOnline().inventario, {})


if __name__ == "__main__":
    unittest.main()
