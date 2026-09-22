"""Test funcional para el Bug 06: compra de producto inexistente (KeyError).

El bug estaba en ``main.py`` línea 26, dentro de ``procesar_pedido``:

    producto = self.inventario[id_prod]

Si el ``id_producto`` de algún ítem del carrito no existía en el inventario,
Python reventaba con un ``KeyError`` SIN CONTROL a mitad del recorrido: el
pedido se perdía y el inventario quedaba a medias (los ítems anteriores ya se
habían descontado).

Este test garantiza que:

* la compra de un producto inexistente lance un error **controlado**
  (``ValueError`` con mensaje descriptivo, NO el ``KeyError`` crudo);
* la validación ocurra ANTES de tocar el inventario (pedido atómico);
* bonus: ``agregar_producto`` actualice nombre/precio de un producto ya
  existente y rechace precios/cantidades negativos.

Nota sobre aislamiento: en esta rama el Bug 01 (``{}`` como argumento por
defecto) sigue abierto, por eso TODAS las tiendas de este archivo se construyen
con ``inventario_inicial`` explícito para que cada test tenga su propio
inventario.

Ejecutar desde la raíz del repo:

    python3 -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

# Permite importar main.py esté donde esté el cwd al ejecutar el test
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import TiendaOnline  # noqa: E402


def tienda_con_stock():
    """Crea una tienda CON inventario propio (aislado de otros tests)."""
    return TiendaOnline(
        inventario_inicial={
            "P01": {"nombre": "Teclado Mecánico", "precio": 150000, "cantidad": 5},
            "P02": {"nombre": "Mouse Gamer", "precio": 80000, "cantidad": 3},
        }
    )


class TestPedidoConProductoInexistente(unittest.TestCase):
    """Bug principal: ``procesar_pedido`` reventaba con KeyError (línea 26)."""

    def test_producto_inexistente_lanza_error_controlado(self):
        """Debe ser ValueError con mensaje claro, no el KeyError crudo."""
        tienda = tienda_con_stock()
        carrito = [{"id_producto": "ZZZ", "cantidad": 1}]

        with self.assertRaises(ValueError) as ctx:
            tienda.procesar_pedido(carrito)

        mensaje = str(ctx.exception)
        self.assertIn("ZZZ", mensaje, "El error debe indicar QUÉ producto falta")
        self.assertIn("no existe", mensaje.lower())
        self.assertNotIsInstance(
            ctx.exception,
            KeyError,
            "El error ya no debe ser el KeyError sin control de antes",
        )

    def test_pedido_fallido_no_modifica_el_inventario(self):
        """Valida TODO el carrito antes de mutar: nada se descuenta si algo falta."""
        tienda = tienda_con_stock()
        carrito = [
            {"id_producto": "P01", "cantidad": 2},  # válido: ANTES se descontaba
            {"id_producto": "ZZZ", "cantidad": 1},  # no existe: KeyError después
        ]

        with self.assertRaises(ValueError):
            tienda.procesar_pedido(carrito)

        # El ítem válido NO debe haberse descontado (antes: pedido a medias)
        self.assertEqual(
            tienda.inventario["P01"]["cantidad"],
            5,
            "El inventario quedó corrupto: se descontó antes de fallar",
        )
        self.assertEqual(tienda.ventas_totales, 0.0)

    def test_reporta_el_primer_producto_faltante(self):
        """Con varios faltantes, el error identifica al primero del carrito."""
        tienda = tienda_con_stock()
        carrito = [
            {"id_producto": "NOEX1", "cantidad": 1},
            {"id_producto": "NOEX2", "cantidad": 2},
        ]

        with self.assertRaises(ValueError) as ctx:
            tienda.procesar_pedido(carrito)

        self.assertIn("NOEX1", str(ctx.exception))
        # Y el inventario sigue intacto
        self.assertEqual(tienda.inventario["P02"]["cantidad"], 3)


class TestBonusAgregarProducto(unittest.TestCase):
    """Bugs menores listados en la descripción del Bug 06."""

    def test_actualiza_nombre_y_precio_si_el_producto_ya_existe(self):
        """Antes solo sumaba cantidad y dejaba nombre/precio viejos."""
        tienda = TiendaOnline(inventario_inicial={})

        tienda.agregar_producto("P01", "Teclado Mecánico", 150000, 5)
        tienda.agregar_producto("P01", "Teclado Pro", 180000, 2)

        producto = tienda.inventario["P01"]
        self.assertEqual(producto["nombre"], "Teclado Pro")
        self.assertEqual(producto["precio"], 180000)
        self.assertEqual(producto["cantidad"], 7, "La cantidad debe SUMARSE (5 + 2)")

    def test_precio_negativo_lanza_error_controlado(self):
        """No debe registrar productos con precio negativo."""
        tienda = TiendaOnline(inventario_inicial={})

        with self.assertRaises(ValueError) as ctx:
            tienda.agregar_producto("P99", "Producto Roto", -100, 3)

        self.assertIn("precio", str(ctx.exception).lower())
        self.assertNotIn("P99", tienda.inventario, "Quedó registrado a pesar del error")

    def test_cantidad_negativa_lanza_error_controlado(self):
        """No debe registrar productos con cantidad negativa."""
        tienda = TiendaOnline(inventario_inicial={})

        with self.assertRaises(ValueError) as ctx:
            tienda.agregar_producto("P98", "Producto Roto", 1000, -3)

        self.assertIn("cantidad", str(ctx.exception).lower())
        self.assertNotIn("P98", tienda.inventario, "Quedó registrado a pesar del error")

    def test_precio_negativo_no_altera_un_producto_existente(self):
        """La validación ocurre ANTES de modificar el producto."""
        tienda = tienda_con_stock()

        with self.assertRaises(ValueError):
            tienda.agregar_producto("P01", "Nombre Nuevo", -1, 10)

        producto = tienda.inventario["P01"]
        self.assertEqual(producto["nombre"], "Teclado Mecánico")
        self.assertEqual(producto["precio"], 150000)
        self.assertEqual(producto["cantidad"], 5)


if __name__ == "__main__":
    unittest.main()
