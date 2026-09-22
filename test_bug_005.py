"""
Test funcionales para el bug 005 corregido en la rama fix/bug005.

Ejecución:
    python3 test_bug_005.py
    python3 -m pytest test_bug_005.py -v

Notas:
- Bug 001 (diccionario mutable compartido): se pasa un dict() nuevo a cada
  instancia para que los tests no compartan inventario entre sí.
- Bug 003 (typo 'ventas_totaIes'): fuera del alcance de esta rama, solo se
  inicializa el atributo para que 'procesar_pedido' no lance AttributeError
  durante los tests.
"""

from main import TiendaOnline


def nueva_tienda():
    """Crea una TiendaOnline lista para probar el bug 005."""
    tienda = TiendaOnline(inventario_inicial={})
    tienda.ventas_totaIes = 0.0  # workaround bug 003
    return tienda


# ================================= BUG 005 =================================
# No se debe poder comprar más unidades de las disponibles: el pedido debe
# rechazarse con ValueError y el inventario debe quedar intacto.
# Antes del fix, comprar 5 con stock 1 dejaba el stock en -4.

def test_compra_que_excede_stock_lanza_error():
    tienda = nueva_tienda()
    tienda.agregar_producto("P", "Mouse", 50000, 1)

    try:
        tienda.procesar_pedido([{'id_producto': 'P', 'cantidad': 5}])
    except ValueError:
        return
    raise AssertionError("Comprar 5 con stock 1 debería lanzar ValueError")


def test_compra_excesiva_no_dana_el_inventario():
    tienda = nueva_tienda()
    tienda.agregar_producto("P", "Mouse", 50000, 1)

    try:
        tienda.procesar_pedido([{'id_producto': 'P', 'cantidad': 5}])
    except ValueError:
        pass

    assert tienda.inventario["P"]["cantidad"] == 1, \
        f"El stock no debe volverse negativo ni alterarse: quedó en {tienda.inventario['P']['cantidad']}"


def test_compra_valida_descuenta_inventario_y_cobra_bien():
    tienda = nueva_tienda()
    tienda.agregar_producto("P", "Mouse", 50000, 5)

    total = tienda.procesar_pedido([{'id_producto': 'P', 'cantidad': 2}])

    assert total == 100000.0, f"Esperaba 100000.0 pero obtuve {total}"
    assert tienda.inventario["P"]["cantidad"] == 3, \
        f"Esperaba stock 3 pero quedó en {tienda.inventario['P']['cantidad']}"


def test_comprar_exactamente_el_stock_disponible_es_valido():
    tienda = nueva_tienda()
    tienda.agregar_producto("P", "Mouse", 50000, 3)

    total = tienda.procesar_pedido([{'id_producto': 'P', 'cantidad': 3}])

    assert total == 150000.0, f"Esperaba 150000.0 pero obtuve {total}"
    assert tienda.inventario["P"]["cantidad"] == 0, \
        f"Esperaba stock 0 pero quedó en {tienda.inventario['P']['cantidad']}"


def test_compra_con_cantidad_cero_no_afecta_stock():
    tienda = nueva_tienda()
    tienda.agregar_producto("P", "Mouse", 50000, 3)

    total = tienda.procesar_pedido([{'id_producto': 'P', 'cantidad': 0}])

    assert total == 0.0, f"Esperaba 0.0 pero obtuve {total}"
    assert tienda.inventario["P"]["cantidad"] == 3, \
        f"El stock no debe cambiar: quedó en {tienda.inventario['P']['cantidad']}"


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