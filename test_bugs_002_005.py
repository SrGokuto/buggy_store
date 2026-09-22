"""
Test funcionales para los bugs 002 y 005 corregidos en la rama fix-002/005.

Ejecución:
    python3 test_bugs_002_005.py
    python3 -m pytest test_bugs_002_005.py -v

Nota: el código aún contiene el bug 003 (typo 'ventas_totaIes'), fuera del
alcance de esta rama. Para poder procesar pedidos en los tests sin que el
sistema crashee, se inicializa ese atributo en la tienda de prueba.
"""

from main import TiendaOnline


def nueva_tienda():
    """Crea una TiendaOnline lista para probar los bugs 002 y 005.

    - Bug 001 (diccionario mutable compartido): se pasa un dict() nuevo a
      cada instancia para que los tests no compartan inventario entre sí.
    - Bug 003 (typo 'ventas_totaIes'): no es parte de esta rama, solo se
      inicializa el atributo para que 'procesar_pedido' no lance
      AttributeError durante los tests.
    """
    tienda = TiendaOnline(inventario_inicial={})
    tienda.ventas_totaIes = 0.0
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


# ================================= BUG 005 =================================
# No se debe poder comprar más unidades de las disponibles: el pedido debe
# rechazarse con ValueError y el inventario debe quedar intacto.

def test_compra_valida_descuenta_inventario_y_cobra_bien():
    tienda = nueva_tienda()
    tienda.agregar_producto("P", "Mouse", 50000, 5)

    total = tienda.procesar_pedido([{'id_producto': 'P', 'cantidad': 2}])

    assert total == 100000.0, f"Esperaba 100000.0 pero obtuve {total}"
    assert tienda.inventario["P"]["cantidad"] == 3, \
        f"Esperaba stock 3 pero quedó en {tienda.inventario['P']['cantidad']}"


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