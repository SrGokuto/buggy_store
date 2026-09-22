"""
Test funcionales para el bug 002 corregido en la rama fix/bug002.

Ejecución:
    python3 test_bug_002.py
    python3 -m pytest test_bug_002.py -v

Notas:
- Bug 001 (diccionario mutable compartido): se pasa un dict() nuevo a cada
  instancia para que los tests no compartan inventario entre sí.
- Bug 003 (typo 'ventas_totaIes'): fuera del alcance de esta rama, solo se
  inicializa el atributo para que 'procesar_pedido' no lance AttributeError
  durante los tests.
"""

from main import TiendaOnline


def nueva_tienda():
    """Crea una TiendaOnline lista para probar el bug 002."""
    tienda = TiendaOnline(inventario_inicial={})
    tienda.ventas_totaIes = 0.0  # workaround bug 003
    return tienda


# ================================= BUG 002 =================================
# El cupón SENA2026 debe aplicar un 20% DE DESCUENTO (multiplicar por 0.80),
# no encarecer el pedido. Antes del fix se multiplicaba por 1.20.

def test_cupon_sena2026_aplica_20_porciento_de_descuento():
    tienda = nueva_tienda()
    tienda.agregar_producto("A", "Producto", 100, 10)

    total = tienda.procesar_pedido(
        [{'id_producto': 'A', 'cantidad': 1}], cupon_descuento="SENA2026")

    assert total == 80.0, f"Esperaba 80.0 (20% OFF de 100) pero obtuve {total}"


def test_cupon_no_debe_encarecer_el_pedido():
    tienda = nueva_tienda()
    tienda.agregar_producto("A", "Producto", 100, 10)

    subtotal = 100.0
    total = tienda.procesar_pedido(
        [{'id_producto': 'A', 'cantidad': 1}], cupon_descuento="SENA2026")

    assert total < subtotal, f"El descuento no debe subir el precio: {total} >= {subtotal}"


def test_sin_cupon_se_cobra_el_precio_completo():
    tienda = nueva_tienda()
    tienda.agregar_producto("A", "Producto", 100, 10)

    total = tienda.procesar_pedido([{'id_producto': 'A', 'cantidad': 2}])

    assert total == 200.0, f"Esperaba 200.0 sin cupón pero obtuve {total}"


def test_cupon_invalido_no_aplica_descuento():
    tienda = nueva_tienda()
    tienda.agregar_producto("A", "Producto", 100, 10)

    total = tienda.procesar_pedido(
        [{'id_producto': 'A', 'cantidad': 1}], cupon_descuento="CUPON_FAKE")

    assert total == 100.0, f"Un cupón inválido no debe descontar: obtuve {total}"


# ============================== MAIN RUNNER ================================
if __name__ == "__main__":
    import sys

    funciones = [f for n, f in sorted(globals().items())
                 if n.startswith("test_") and callable(f)]
    fallos = 0

    for func in funciones:
        try:
            func()
            print(f"PASS  {func.__name__}")
        except AssertionError as e:
            fallos += 1
            print(f"FAIL  {func.__name__}: {e}")
        except Exception as e:
            fallos += 1
            print(f"ERROR {func.__name__}: {type(e).__name__}: {e}")

    total = len(funciones)
    print(f"\nResultado: {total - fallos}/{total} tests pasaron")
    sys.exit(1 if fallos else 0)